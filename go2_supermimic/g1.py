"""G1 flat walk: pure Torch state, biped rewards and bundled expert motions.

Motion/feature conventions follow legged_lab f33a189; learning uses SuperMimic.
The original WXYZ poses are converted explicitly at interpolation boundaries.
"""

from __future__ import annotations

import hashlib
import json
import pickle
from dataclasses import dataclass, replace
from pathlib import Path

import torch

from go2_supermimic import velocity as quad
from go2_supermimic.amp import AMPDiscriminator as PairDiscriminator
from go2_supermimic.amp import MotionLibrary as PairMotionLibrary
from go2_supermimic.g1_discriminator import LeggedLabNorm
from go2_supermimic.supermimic.world_model import mlp
from go2_supermimic.g1_kinematics import (
  KINEMATICS_METADATA, LEG_INDICES, LEG_NAMES, foot_positions)

NUM_JOINTS, NUM_FEET = 29, 2
STATE_DIM, GAIT_DIM, AMP_DIM = 84, 8, 61
STATE_SCHEMA = "g1_state84_base_contact_v1"
TERMINATION_PROFILE = "g1_legged_lab_contact_v1"
DEFAULT_AMP_FEATURE_SCHEMA = "g1_amp_61_v1"
AMP_FEATURE_DIMS = {
  DEFAULT_AMP_FEATURE_SCHEMA: 61,
  "g1_amp_64_velocity_v1": 64,
  "g1_amp_70_feet_v1": 70,
}

def amp_feature_dim(feature_schema: str = DEFAULT_AMP_FEATURE_SCHEMA) -> int:
  try:
    return AMP_FEATURE_DIMS[feature_schema]
  except KeyError as exc:
    raise ValueError(f"unsupported G1 AMP feature schema: {feature_schema}") from exc
Z, GRAV, V_B, W_B = slice(0, 1), slice(1, 4), slice(4, 7), slice(7, 10)
Q, QD = slice(10, 39), slice(39, 68)
FOOT_POS, FOOT_VEL = slice(68, 74), slice(74, 80)
CONTACT, UNDESIRED_CONTACT = slice(80, 82), slice(82, 83)
BASE_CONTACT = slice(83, 84)
AIR, STANCE, LAST_AIR, LAST_STANCE = slice(0, 2), slice(2, 4), slice(4, 6), slice(6, 8)
OBS_TERMS = (("angular_velocity", 3), ("gravity", 3), ("command", 3),
             ("joint_position", 29), ("joint_velocity", 29), ("action", 29))
FRAME_DIM = sum(dim for _, dim in OBS_TERMS)
MANIFEST = Path(__file__).resolve().parents[1] / "assets/motions/g1/manifest.json"
DEFAULT_G1_MOTIONS = str(MANIFEST.parent)
ACTUATOR_MODEL = "g1_implicit_pd_v1"
REWARD_PROFILE = "g1_legged_lab_walk_v1"
LEG_JOINT_IDS = tuple(i for pair in LEG_INDICES for i in pair)
HIP_KNEE_IDS = tuple(i for pair in LEG_INDICES[:4] for i in pair)
ANKLE_IDS = tuple(i for pair in LEG_INDICES[4:] for i in pair)
HIP_DEVIATION_IDS = (3, 4, 6, 7)
WAIST_IDS = (2, 5, 8)
ARM_IDS = tuple(i for i in range(NUM_JOINTS) if i not in LEG_JOINT_IDS + WAIST_IDS)
CommandCfg, VelocityTaskCfg, RobotConsts = quad.CommandCfg, quad.VelocityTaskCfg, quad.RobotConsts
sample_commands, advance_commands = quad.sample_commands, quad.advance_commands


@dataclass
class RewardWeights(quad.RewardWeights):
  flight: float = -2.0
  feet_distance: float = -1.0


REWARD_NAMES = tuple(RewardWeights.__dataclass_fields__)


@dataclass
class LeggedLabRewardWeights(RewardWeights):
  track_linear_velocity: float = 1.
  track_yaw_rate: float = 2.
  vertical_velocity: float = -.2
  roll_pitch_rate: float = -.05
  orientation: float = -1.
  base_height: float = 0.
  joint_deviation: float = 0.
  action_rate: float = -.005
  joint_torque: float = -2e-6
  joint_velocity: float = 0.
  energy: float = 0.
  joint_acceleration: float = -1.25e-7
  joint_limits: float = -1.
  feet_air_time: float = .75
  air_time_variance: float = 0.
  feet_slide: float = -.1
  undesired_contacts: float = -1.
  feet_clearance: float = 0.
  feet_contact_without_command: float = 0.
  gait_duration: float = 0.
  diagonal_gait: float = 0.
  terminated: float = -200.
  flight: float = 0.
  feet_distance: float = 0.
  joint_deviation_hip: float = -.1
  joint_deviation_arms: float = -.05
  joint_deviation_waist: float = -.1


def amp_reward_coefficients(cfg: VelocityTaskCfg, weight: float) -> tuple[float, float]:
  if cfg.reward_profile != REWARD_PROFILE:
    return 1., weight
  if not 0 <= weight <= 1:
    raise ValueError("legged_lab AMP style mixing fraction must be in [0, 1]")
  # legged_lab uses task_style_lerp=.5 and style_reward_scale=2.
  return 1 - weight, 2 * weight


def require_implicit_pd(checkpoint: dict) -> None:
  """Never import a world model learned with the historical G1 DC actuator."""
  if checkpoint.get("actuator_model") != ACTUATOR_MODEL:
    raise ValueError(
      "G1 checkpoint actuator model is incompatible: expected "
      f"{ACTUATOR_MODEL}, got {checkpoint.get('actuator_model', 'legacy DC PD')}. "
      "Start a fresh G1 run; old DC dynamics cannot be resumed, warm-started "
      "or evaluated as implicit PD.")


def require_trainable_state(checkpoint: dict) -> None:
  """Actor evaluation can read old states; learned dynamics cannot be padded."""
  require_implicit_pd(checkpoint)
  if (checkpoint.get("state_schema") != STATE_SCHEMA
      or checkpoint["world_model"]["out_norm.mean"].numel() != STATE_DIM):
    raise ValueError(
      f"G1 training requires {STATE_SCHEMA}; old 83-dimensional dynamics have no "
      "base-contact channel. Start a fresh run instead of padding the world model.")


def terminated(s: torch.Tensor, cfg: VelocityTaskCfg) -> torch.Tensor:
  if cfg.termination_profile == "height_tilt":
    return quad.terminated(s, cfg)
  if cfg.termination_profile != TERMINATION_PROFILE:
    raise ValueError(f"unsupported G1 termination profile: {cfg.termination_profile}")
  return (s[:, 0] < cfg.minimum_height) | (s[:, BASE_CONTACT].squeeze(-1) > .5)


def termination_probability(s: torch.Tensor, cfg: VelocityTaskCfg) -> torch.Tensor:
  """Smooth union using the same height/contact inputs as native termination."""
  if cfg.termination_profile == "height_tilt":
    return quad.termination_probability(s, cfg)
  if cfg.termination_profile != TERMINATION_PROFILE:
    raise ValueError(f"unsupported G1 termination profile: {cfg.termination_profile}")
  low = torch.sigmoid((cfg.minimum_height - s[:, 0]) / .015)
  contact = torch.sigmoid((s[:, BASE_CONTACT].squeeze(-1) - .5) / .04)
  return 1 - (1 - low) * (1 - contact)


def legacy_walk_task() -> VelocityTaskCfg:
  return VelocityTaskCfg(
    reward_profile="g1_walk", action_scale=.25, nominal_height=.78, minimum_height=.5,
    swing_height=.12, target_air_time=.25, target_stance_time=.35,
    commands=CommandCfg(lin_vel_x=(0., 1.2), lin_vel_y=(-.3, .3), ang_vel_z=(-.8, .8)),
    rewards=RewardWeights(
      track_linear_velocity=1.5, track_yaw_rate=1., vertical_velocity=-.2,
      roll_pitch_rate=-.05, orientation=-1., base_height=-5., joint_deviation=-.03,
      action_rate=-.005, joint_torque=-2e-6, joint_velocity=0., energy=-1e-5,
      joint_acceleration=-1.25e-7, joint_limits=-1., feet_air_time=.75,
      air_time_variance=0., feet_slide=-.1, undesired_contacts=-1.,
      feet_clearance=.15, feet_contact_without_command=.5, gait_duration=-.5,
      diagonal_gait=0., terminated=-50.))


def walk_task() -> VelocityTaskCfg:
  """The 16 upstream task terms, restricted to this project's flat walk range."""
  return replace(legacy_walk_task(), reward_profile=REWARD_PROFILE,
                 termination_profile=TERMINATION_PROFILE, minimum_height=.2,
                 rewards=LeggedLabRewardWeights())


def obs_frame(s: torch.Tensor, action: torch.Tensor, commands: torch.Tensor,
              noise: bool = False) -> dict[str, torch.Tensor]:
  frame = {"angular_velocity": s[:, W_B], "gravity": s[:, GRAV], "command": commands,
           "joint_position": s[:, Q], "joint_velocity": s[:, QD], "action": action}
  if noise:
    for name, width in (("angular_velocity", .2), ("gravity", .05),
                        ("joint_position", .01), ("joint_velocity", 1.5)):
      frame[name] = frame[name] + (2 * torch.rand_like(frame[name]) - 1) * width
  return frame


def push_history(history: torch.Tensor, frame: dict[str, torch.Tensor], h: int) -> torch.Tensor:
  blocks, offset = [], 0
  for name, dim in OBS_TERMS:
    block = history[:, offset:offset + h * dim]
    blocks.append(torch.cat((block[:, dim:], frame[name]), -1))
    offset += h * dim
  return torch.cat(blocks, -1)


def advance_gait(gait: torch.Tensor, contact0: torch.Tensor, contact1: torch.Tensor,
                 dt: float) -> tuple[torch.Tensor, torch.Tensor]:
  c0, c1 = contact0.clamp(0, 1), contact1.clamp(0, 1)
  c0, c1 = c0.square() * (3 - 2 * c0), c1.square() * (3 - 2 * c1)
  touchdown, liftoff = (1 - c0) * c1, c0 * (1 - c1)
  air, stance = gait[:, AIR] + dt, gait[:, STANCE] + dt
  return torch.cat((air * (1 - c1), stance * c1,
                    torch.lerp(gait[:, LAST_AIR], air, touchdown),
                    torch.lerp(gait[:, LAST_STANCE], stance, liftoff)), -1), touchdown


def motor_torque(s: torch.Tensor, action: torch.Tensor, c: RobotConsts,
                 cfg: VelocityTaskCfg) -> torch.Tensor:
  """Differentiable estimate of implicit PD effort, with fixed torque limits.

  This matches Isaac Lab's ImplicitActuator effort estimate at the same state.
  PhysX integrates the actual PD drive implicitly; this is not its exact
  solver torque. Damping still depends on joint speed, but the cap does not.
  """
  torque = c.kp * (cfg.action_scale * action - s[:, Q]) - c.kd * s[:, QD]
  return torch.maximum(torch.minimum(torque, c.effort), -c.effort)


def reward(s0, s1, action, previous_action, commands, c: RobotConsts,
           cfg: VelocityTaskCfg, dt: float, done: torch.Tensor, gait=None, parameters=None):
  if cfg.reward_profile == REWARD_PROFILE:
    return _legged_lab_reward(
      s0, s1, action, previous_action, commands, c, cfg, dt, done, gait, parameters)
  return _legacy_reward(
    s0, s1, action, previous_action, commands, c, cfg, dt, done, gait, parameters)


def yaw_frame_velocity(s: torch.Tensor) -> torch.Tensor:
  """Recover yaw-frame velocity from body velocity and projected gravity.

  R_y(pitch) R_x(roll) removes tilt without requiring the yaw discarded by our
  invariant state. The epsilon only regularizes invalid imagined gravity near
  the Euler singularity; native unit gravity below the fall limit is exact.
  """
  gravity = s[:, GRAV]
  gravity = gravity / gravity.norm(dim=-1, keepdim=True).clamp(min=1e-6)
  gx, gy, gz = gravity.unbind(-1)
  cp = (gy.square() + gz.square() + 1e-12).sqrt()
  sr, cr = -gy / cp, -gz / cp
  vx, vy, vz = s[:, V_B].unbind(-1)
  return torch.stack((cp * vx + gx * sr * vy + gx * cr * vz,
                      cr * vy - sr * vz,
                      -(gravity * s[:, V_B]).sum(-1)), -1)


def _legged_lab_reward(s0, s1, action, previous_action, commands, c: RobotConsts,
                       cfg: VelocityTaskCfg, dt: float, done: torch.Tensor,
                       gait=None, parameters=None):
  """Upstream formulas with explicit control-step torque/acceleration proxies."""
  q, qd = s1[:, Q] + c.default_q, s1[:, QD]
  torque = motor_torque(s1, action, c, cfg)
  still = commands[:, :2].norm(dim=-1) < .06
  moving = commands[:, :2].norm(dim=-1) > .1
  limits = ((c.soft_limits[..., 0] - q).clamp(min=0)
            + (q - c.soft_limits[..., 1]).clamp(min=0))
  gravity = s1[:, GRAV]
  gravity = gravity / gravity.norm(dim=-1, keepdim=True).clamp(min=1e-6)
  world_wz = -(gravity * s1[:, W_B]).sum(-1)
  terms = {
    "track_linear_velocity": torch.exp(
      -(yaw_frame_velocity(s1)[:, :2] - commands[:, :2]).square().sum(-1)
      / cfg.tracking_variance),
    "track_yaw_rate": torch.exp(-(world_wz - commands[:, 2]).square()
                               / cfg.tracking_variance),
    "orientation": s1[:, GRAV][:, :2].square().sum(-1),
    "vertical_velocity": s1[:, 6].square(),
    "roll_pitch_rate": s1[:, W_B][:, :2].square().sum(-1),
    "joint_torque": torque[:, LEG_JOINT_IDS].square().sum(-1),
    "joint_acceleration": ((qd - s0[:, QD])[:, HIP_KNEE_IDS] / dt).square().sum(-1),
    "action_rate": (action - previous_action).square().sum(-1),
    "joint_limits": limits[:, ANKLE_IDS].sum(-1),
    "joint_deviation_hip": s1[:, Q][:, HIP_DEVIATION_IDS].abs().sum(-1) * still,
    "joint_deviation_arms": s1[:, Q][:, ARM_IDS].abs().sum(-1) * still,
    "joint_deviation_waist": s1[:, Q][:, WAIST_IDS].abs().sum(-1) * still,
    "undesired_contacts": s1[:, UNDESIRED_CONTACT].squeeze(-1).clamp(min=0),
    "terminated": done.float(),
  }
  if gait is not None:
    following, _ = advance_gait(gait, s0[:, CONTACT], s1[:, CONTACT], dt)
    contact = s1[:, CONTACT].clamp(0, 1)
    single = contact[:, 0] * (1 - contact[:, 1]) + contact[:, 1] * (1 - contact[:, 0])
    velocity = s1[:, FOOT_VEL].reshape(-1, 2, 3)
    horizontal = velocity - (velocity * gravity[:, None]).sum(-1, keepdim=True) * gravity[:, None]
    terms.update({
      "feet_air_time": (following[:, AIR] + following[:, STANCE]).min(-1).values.clamp(max=.4)
                       * single * moving,
      "feet_slide": (horizontal.norm(dim=-1) * contact).sum(-1),
    })
  names = tuple(cfg.rewards.__dataclass_fields__)
  for name in names:
    if name not in terms:
      terms[name] = s1.new_zeros(s1.shape[0])
  weights = (s1.new_tensor([getattr(cfg.rewards, name) for name in names])
             if parameters is None else parameters[:-1])
  return (torch.stack([terms[name] for name in names], -1) * weights).sum(-1) * dt, terms


def _legacy_reward(s0, s1, action, previous_action, commands, c: RobotConsts,
                   cfg: VelocityTaskCfg, dt: float, done: torch.Tensor,
                   gait=None, parameters=None):
  q, qd = s1[:, Q] + c.default_q, s1[:, QD]
  torque = motor_torque(s1, action, c, cfg)
  moving = commands.norm(dim=-1) > .1
  # Match the Go2 cold-start curriculum while preserving the final G1 walk
  # reward: early training uses a smooth squared joint penalty, then blends to
  # the reference walk L1 deviation. The compiled imagination path passes the
  # scheduled fraction through ``parameters[-1]``.
  gait_deviation = s1[:, Q].abs().sum(-1) * torch.where(
    moving, 1., cfg.stand_still_scale)
  fraction = (cfg.joint_deviation_gait_fraction if parameters is None
              else parameters[-1])
  deviation = ((1 - fraction) * s1[:, Q].square().sum(-1)
               + fraction * gait_deviation)
  terms = {
    "track_linear_velocity": torch.exp(
      -(s1[:, V_B][:, :2] - commands[:, :2]).square().sum(-1) / cfg.tracking_variance),
    "track_yaw_rate": torch.exp(-(s1[:, 9] - commands[:, 2]).square() / cfg.tracking_variance),
    "vertical_velocity": s1[:, 6].square(),
    "roll_pitch_rate": s1[:, W_B][:, :2].square().sum(-1),
    "orientation": s1[:, GRAV][:, :2].square().sum(-1),
    "base_height": (s1[:, 0] - cfg.nominal_height).square(),
    "joint_deviation": deviation,
    "action_rate": (action - previous_action).square().sum(-1),
    "joint_torque": torque.square().sum(-1), "joint_velocity": qd.square().sum(-1),
    "energy": (torque * qd).abs().sum(-1),
    "joint_acceleration": ((qd - s0[:, QD]) / dt).square().sum(-1),
    "joint_limits": ((c.soft_limits[..., 0] - q).clamp(min=0)
                     + (q - c.soft_limits[..., 1]).clamp(min=0)).sum(-1),
    "terminated": done.float(),
  }
  if gait is not None:
    following, touchdown = advance_gait(gait, s0[:, CONTACT], s1[:, CONTACT], dt)
    pos, vel = s1[:, FOOT_POS].reshape(-1, 2, 3), s1[:, FOOT_VEL].reshape(-1, 2, 3)
    gravity = s1[:, GRAV][:, None, :]
    horizontal = vel - (vel * gravity).sum(-1, keepdim=True) * gravity
    height = s1[:, Z] - (pos * gravity).sum(-1)
    contact = s1[:, CONTACT].clamp(0, 1)
    single = contact[:, 0] * (1 - contact[:, 1]) + contact[:, 1] * (1 - contact[:, 0])
    terms.update({
      "feet_air_time": (following[:, AIR] + following[:, STANCE]).min(-1).values.clamp(max=.4)
                       * single * moving,
      "air_time_variance": following[:, LAST_AIR].var(-1),
      "feet_slide": (horizontal.norm(dim=-1) * contact).sum(-1),
      "undesired_contacts": s1[:, UNDESIRED_CONTACT].squeeze(-1),
      "feet_clearance": torch.exp(
        -((height - cfg.swing_height).square()
          * torch.tanh(2 * horizontal.norm(dim=-1))).sum(-1) / cfg.clearance_variance) * moving,
      "feet_contact_without_command": contact.mean(-1) * ~moving,
      "gait_duration": ((following[:, LAST_AIR].clamp(max=.8) - cfg.target_air_time).square()
                        + (following[:, LAST_STANCE].clamp(max=.8)
                           - cfg.target_stance_time).square()).sum(-1) * moving,
      "diagonal_gait": single * moving,
      "flight": (1 - contact).prod(-1),
      "feet_distance": (.15 - (pos[:, 0, 1] - pos[:, 1, 1]).abs()).clamp(min=0),
    })
  for name in REWARD_NAMES:
    if name not in terms:
      terms[name] = s1.new_zeros(s1.shape[0])
  weights = (s1.new_tensor([getattr(cfg.rewards, name) for name in REWARD_NAMES])
             if parameters is None else parameters[:-1])
  total = (torch.stack([terms[name] for name in REWARD_NAMES], -1) * weights).sum(-1) * dt
  return total, terms


def quat_apply(q: torch.Tensor, xyz: torch.Tensor) -> torch.Tensor:
  """WXYZ quaternion, matching Isaac Lab 2.1."""
  t = 2 * torch.cross(q[..., 1:], xyz, dim=-1)
  return xyz + q[..., :1] * t + torch.cross(q[..., 1:], t, dim=-1)


def quat_inverse_apply(q: torch.Tensor, xyz: torch.Tensor) -> torch.Tensor:
  return quat_apply(torch.cat((q[..., :1], -q[..., 1:]), -1), xyz)


def reference_commands(frames: torch.Tensor, cfg: CommandCfg) -> torch.Tensor:
  """Use the exact RSI frame's body velocity, clamped to the walk-only range."""
  quat = frames[:, [6, 3, 4, 5]]
  linear = quat_inverse_apply(quat, frames[:, 36:39])
  angular = quat_inverse_apply(quat, frames[:, 39:42])
  return torch.stack((linear[:, 0].clamp(*cfg.lin_vel_x),
                      linear[:, 1].clamp(*cfg.lin_vel_y),
                      angular[:, 2].clamp(*cfg.ang_vel_z)), -1)


def state_features(s: torch.Tensor, default_q: torch.Tensor,
                   feature_schema: str = DEFAULT_AMP_FEATURE_SCHEMA) -> torch.Tensor:
  base = torch.cat((s[..., W_B], s[..., Q] + default_q, s[..., QD]), -1)
  if feature_schema == DEFAULT_AMP_FEATURE_SCHEMA:
    return base
  if feature_schema == "g1_amp_64_velocity_v1":
    return torch.cat((s[..., V_B], base), -1)
  if feature_schema == "g1_amp_70_feet_v1":
    # Use the same USD FK for expert, physical and imagined states. This does
    # not replace the learned foot channels used by the world model/rewards.
    feet = foot_positions(s[..., Q] + default_q).flatten(-2)
    return torch.cat((s[..., V_B], base, feet), -1)
  amp_feature_dim(feature_schema)
  raise AssertionError("unreachable feature schema")


def frame_features(f: torch.Tensor,
                   feature_schema: str = DEFAULT_AMP_FEATURE_SCHEMA) -> torch.Tensor:
  q = f[..., [6, 3, 4, 5]]
  base = torch.cat((quat_inverse_apply(q, f[..., 39:42]), f[..., 7:36],
                    f[..., 42:71]), -1)
  if feature_schema == DEFAULT_AMP_FEATURE_SCHEMA:
    return base
  if feature_schema == "g1_amp_64_velocity_v1":
    return torch.cat((quat_inverse_apply(q, f[..., 36:39]), base), -1)
  if feature_schema == "g1_amp_70_feet_v1":
    feet = foot_positions(f[..., 7:36]).flatten(-2)
    return torch.cat((quat_inverse_apply(q, f[..., 36:39]), base, feet), -1)
  amp_feature_dim(feature_schema)
  raise AssertionError("unreachable feature schema")


class AMPDiscriminator(PairDiscriminator):
  def __init__(self, hidden: tuple[int, ...] = (512, 256),
               feature_schema: str = DEFAULT_AMP_FEATURE_SCHEMA, num_frames: int = 2,
               command_gate: bool = True, profile: str = "legacy"):
    if profile not in ("legacy", "legged_lab_v1"):
      raise ValueError(f"unknown G1 discriminator profile: {profile}")
    self.feature_schema = feature_schema
    self.profile = profile
    super().__init__(hidden, feature_dim=amp_feature_dim(feature_schema),
                     num_frames=num_frames, command_gate=command_gate)
    if profile == "legged_lab_v1":
      self.norm = LeggedLabNorm(amp_feature_dim(feature_schema))
      self.net = mlp(num_frames * amp_feature_dim(feature_schema), hidden, 1,
                     act=torch.nn.ELU)

  def features(self, state: torch.Tensor, default_q: torch.Tensor) -> torch.Tensor:
    return state_features(state, default_q, self.feature_schema)

  def optimizer_groups(self) -> list[dict]:
    if self.profile == "legacy":
      return [{"params": self.parameters(), "weight_decay": 1e-4}]
    return [{"params": self.net[:-1].parameters(), "weight_decay": 1e-4},
            {"params": self.net[-1].parameters(), "weight_decay": .1}]

  def loss(self, expert: tuple[torch.Tensor, torch.Tensor] | torch.Tensor,
           policy: tuple[torch.Tensor, torch.Tensor] | torch.Tensor,
           penalty: float = 10.) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    if self.profile == "legacy":
      return super().loss(expert, policy, penalty)
    if isinstance(expert, tuple):
      expert, policy = torch.stack(expert, 1), torch.stack(policy, 1)
    if (expert.ndim != 3 or expert.shape[1:] != policy.shape[1:]
        or expert.shape[1] != self.num_frames):
      raise ValueError("invalid AMP expert/policy temporal sequences")
    positive = self.norm(expert).flatten(1).detach().requires_grad_()
    expert_score = self.net(positive).squeeze(-1)
    policy_score = self.sequence_score(policy.detach())
    return self._score_loss(positive, expert_score, policy_score, penalty)

  @torch.no_grad()
  def update_normalization(self, policy: tuple[torch.Tensor, torch.Tensor] | torch.Tensor) -> None:
    # The legacy loss already updates joint expert/policy moments. The upstream
    # profile updates policy-only moments after the optimizer step.
    if self.profile == "legged_lab_v1":
      if isinstance(policy, tuple):
        policy = torch.stack(policy, 1)
      self.norm.update(policy.flatten(0, 1))


class MotionLibrary(PairMotionLibrary):
  """Trusted, SHA-verified project copies; derivatives never cross the holdout."""

  def __init__(self, files: str = DEFAULT_G1_MOTIONS, device="cpu", dt: float = .02,
               train_fraction: float = .8,
               feature_schema: str = DEFAULT_AMP_FEATURE_SCHEMA, num_frames: int = 2):
    if not 0 < train_fraction < 1 or dt <= 0:
      raise ValueError("invalid motion dt/split")
    if num_frames not in (2, 4):
      raise ValueError("AMP num_frames must be 2 or 4")
    self.num_frames = num_frames
    amp_feature_dim(feature_schema)
    self.feature_schema = feature_schema
    directory = Path(files)
    manifest = json.loads((directory / "manifest.json").read_text())
    self.joint_names = manifest["joint_names"]
    if feature_schema == "g1_amp_70_feet_v1":
      for indices, name in zip(LEG_INDICES, LEG_NAMES):
        if [self.joint_names[i] for i in indices] != [
            f"left_{name}_joint", f"right_{name}_joint"]:
          raise ValueError("G1 foot kinematics requires the bundled Lab joint order")
    self.device, self.dt = device, dt
    frames, sizes, splits, durations, weights, metadata = [], [], [], [], [], []
    for item in manifest["motions"]:
      name = item["file"]
      if not name.startswith("Walk_B") or "run" in name.lower() or Path(name).name != name:
        raise ValueError("G1 walk requires an explicit walk-only manifest")
      raw = (directory / name).read_bytes()
      if hashlib.sha256(raw).hexdigest() != item["sha256"]:
        raise ValueError(f"motion SHA256 mismatch: {name}")
      data = pickle.loads(raw)  # trusted project file, checked against bundled manifest
      pos = torch.as_tensor(data["root_pos"], dtype=torch.float32)
      quat = torch.as_tensor(data["root_rot"], dtype=torch.float32)
      joints = torch.as_tensor(data["dof_pos"], dtype=torch.float32)
      n, frame_dt = len(pos), 1. / float(data["fps"])
      split = int(n * train_fraction)
      if (pos.shape != (n, 3) or quat.shape != (n, 4) or joints.shape != (n, 29)
          or min(split, n - split) < 3 or not 0 < frame_dt < float("inf")
          or min(split - 1, n - split - 1) * frame_dt <= (num_frames - 1) * dt
          or not torch.isfinite(torch.cat((pos, quat, joints), -1)).all()
          or (quat.norm(dim=-1) < 1e-6).any()):
        raise ValueError(f"invalid G1 motion {name}")
      quat = torch.nn.functional.normalize(quat, dim=-1)
      pieces = []
      for lo, hi in ((0, split), (split, n)):
        p, q, j = pos[lo:hi], quat[lo:hi], joints[lo:hi]
        vel, qd = (p[1:] - p[:-1]) / frame_dt, (j[1:] - j[:-1]) / frame_dt
        # q_next * conjugate(q_current) gives world-frame angular velocity.
        a, b = q[1:], torch.cat((q[:-1, :1], -q[:-1, 1:]), -1)
        qw = a[:, :1] * b[:, :1] - (a[:, 1:] * b[:, 1:]).sum(-1, keepdim=True)
        qv = (a[:, :1] * b[:, 1:] + b[:, :1] * a[:, 1:]
              + torch.cross(a[:, 1:], b[:, 1:], dim=-1))
        qv = qv * torch.where(qw < 0, -1., 1.)
        length = qv.norm(dim=-1, keepdim=True)
        omega = 2 * torch.atan2(length, qw.abs()) * qv / length.clamp(min=1e-8) / frame_dt
        vel, omega, qd = [torch.cat((x, x[-1:]), 0) for x in (vel, omega, qd)]
        pieces.append(torch.cat((p, q[:, [1, 2, 3, 0]], j, vel, omega, qd), -1))
      frames.append(torch.cat(pieces))
      sizes.append(n); splits.append(split); durations.append(frame_dt); weights.append(item["weight"])
      metadata.append({**item, "split_frame": split})
    if not frames:
      raise ValueError("empty walk manifest")
    self.frames = torch.cat(frames).to(device)
    self.offsets = torch.tensor([0] + sizes[:-1], device=device).cumsum(0)
    self.sizes, self.splits = [torch.tensor(x, device=device) for x in (sizes, splits)]
    self.durations = torch.tensor(durations, device=device)
    self.weights = torch.tensor(weights, device=device)
    self.weights /= self.weights.sum()
    self.metadata = {"schema": "g1_amp_61_v1", "dt": dt, "train_fraction": train_fraction,
                     "source_commit": manifest["source_commit"],
                     "joint_names": self.joint_names, "motions": metadata}
    if feature_schema != DEFAULT_AMP_FEATURE_SCHEMA:
      self.metadata["schema"] = feature_schema
      self.metadata["feature_schema"] = feature_schema
    if feature_schema == "g1_amp_70_feet_v1":
      self.metadata["kinematics"] = KINEMATICS_METADATA.copy()
    # Keep historical two-frame metadata byte-for-byte compatible. RSI and the
    # independent pair metric still use sample_times' original two-frame span.
    if num_frames != 2:
      self.metadata["num_frames"] = num_frames
      self.metadata["sequence_span_s"] = (num_frames - 1) * dt

  def sample_sequences(self, batch: int, train: bool = True) -> torch.Tensor:
    """All frames and interpolation supports remain in one clip and split."""
    clips = torch.multinomial(self.weights, batch, replacement=True)
    frame_dt, split, size = self.durations[clips], self.splits[clips], self.sizes[clips]
    low = torch.zeros_like(frame_dt) if train else split * frame_dt
    high = ((split - 1) if train else (size - 1)) * frame_dt - (
      self.num_frames - 1) * self.dt
    times = low + torch.rand(batch, device=self.device) * (high - low)
    times = times[:, None] + torch.arange(
      self.num_frames, device=self.device)[None] * self.dt
    ids = clips[:, None].expand(-1, self.num_frames)
    frames = self.at_time(ids.flatten(), times.flatten()).reshape(batch, self.num_frames, -1)
    return frame_features(frames, self.feature_schema)

  def sample_pairs(self, batch: int, train: bool = True,
                   feature_schema: str | None = None) -> tuple[torch.Tensor, torch.Tensor]:
    schema = self.feature_schema if feature_schema is None else feature_schema
    amp_feature_dim(schema)
    clips, times = self.sample_times(batch, train)
    return (frame_features(self.at_time(clips, times), schema),
            frame_features(self.at_time(clips, times + self.dt), schema))


@torch.no_grad()
def heldout_style_distance(pairs: torch.Tensor, library: MotionLibrary,
                           command_vx: float,
                           feature_schema: str = DEFAULT_AMP_FEATURE_SCHEMA) -> float:
  """Independent speed-conditioned temporal holdout distance, without D scores."""
  feature_dim = amp_feature_dim(feature_schema)
  if pairs.ndim != 2 or pairs.shape[-1] != 2 * feature_dim or len(pairs) < 128:
    raise ValueError("G1 style evaluation needs at least 128 real transition pairs")
  a, b = library.sample_pairs(4096, train=True)
  scale = torch.cat((a, b), -1).std(0, unbiased=False).clamp(min=.05)
  clips, times = library.sample_times(16384, train=False)
  fa, fb = library.at_time(clips, times), library.at_time(clips, times + library.dt)
  vx = (quat_inverse_apply(fa[:, [6, 3, 4, 5]], fa[:, 36:39])[:, 0]
        + quat_inverse_apply(fb[:, [6, 3, 4, 5]], fb[:, 36:39])[:, 0]) * .5
  keep = (vx - command_vx).abs() < .35
  reference = torch.cat((frame_features(fa[keep], feature_schema),
                          frame_features(fb[keep], feature_schema)), -1)
  if len(reference) < 128:
    raise ValueError("insufficient held-out walk data in requested speed band")
  reference = reference[:2048] / scale
  distances = [torch.cdist(query / scale, reference).square().min(-1).values
               for query in pairs.split(256)]
  return (torch.cat(distances).mean() / (2 * feature_dim)).item()
