"""G1 flat walk: pure Torch state, biped rewards and bundled expert motions.

Motion/feature conventions follow legged_lab f33a189; learning uses SuperMimic.
The original WXYZ poses are converted explicitly at interpolation boundaries.
"""

from __future__ import annotations

import hashlib
import json
import pickle
from dataclasses import dataclass
from pathlib import Path

import torch

from go2_supermimic import velocity as quad
from go2_supermimic.amp import AMPDiscriminator as PairDiscriminator
from go2_supermimic.amp import MotionLibrary as PairMotionLibrary

NUM_JOINTS, NUM_FEET = 29, 2
STATE_DIM, GAIT_DIM, AMP_DIM = 83, 8, 61
Z, GRAV, V_B, W_B = slice(0, 1), slice(1, 4), slice(4, 7), slice(7, 10)
Q, QD = slice(10, 39), slice(39, 68)
FOOT_POS, FOOT_VEL = slice(68, 74), slice(74, 80)
CONTACT, UNDESIRED_CONTACT = slice(80, 82), slice(82, 83)
AIR, STANCE, LAST_AIR, LAST_STANCE = slice(0, 2), slice(2, 4), slice(4, 6), slice(6, 8)
OBS_TERMS = (("angular_velocity", 3), ("gravity", 3), ("command", 3),
             ("joint_position", 29), ("joint_velocity", 29), ("action", 29))
FRAME_DIM = sum(dim for _, dim in OBS_TERMS)
MANIFEST = Path(__file__).resolve().parents[1] / "assets/motions/g1/manifest.json"
DEFAULT_G1_MOTIONS = str(MANIFEST.parent)
CommandCfg, VelocityTaskCfg, RobotConsts = quad.CommandCfg, quad.VelocityTaskCfg, quad.RobotConsts
sample_commands, advance_commands = quad.sample_commands, quad.advance_commands
terminated, termination_probability = quad.terminated, quad.termination_probability


@dataclass
class RewardWeights(quad.RewardWeights):
  flight: float = -2.0
  feet_distance: float = -1.0


REWARD_NAMES = tuple(RewardWeights.__dataclass_fields__)


def walk_task() -> VelocityTaskCfg:
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
  qd = s[:, QD]
  torque = c.kp * (cfg.action_scale * action - s[:, Q]) - c.kd * qd
  upper = (c.effort * (1 - qd / c.velocity)).clamp(min=0).minimum(c.effort)
  lower = (c.effort * (-1 - qd / c.velocity)).clamp(max=0).maximum(-c.effort)
  return torch.maximum(torch.minimum(torque, upper), lower)


def reward(s0, s1, action, previous_action, commands, c: RobotConsts,
           cfg: VelocityTaskCfg, dt: float, done: torch.Tensor, gait=None, parameters=None):
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


def state_features(s: torch.Tensor, default_q: torch.Tensor) -> torch.Tensor:
  return torch.cat((s[..., W_B], s[..., Q] + default_q, s[..., QD]), -1)


def frame_features(f: torch.Tensor) -> torch.Tensor:
  q = f[..., [6, 3, 4, 5]]
  return torch.cat((quat_inverse_apply(q, f[..., 39:42]), f[..., 7:36], f[..., 42:71]), -1)


class AMPDiscriminator(PairDiscriminator):
  features = staticmethod(state_features)

  def __init__(self, hidden: tuple[int, ...] = (512, 256)):
    super().__init__(hidden, feature_dim=AMP_DIM)


class MotionLibrary(PairMotionLibrary):
  """Trusted, SHA-verified project copies; derivatives never cross the holdout."""

  def __init__(self, files: str = DEFAULT_G1_MOTIONS, device="cpu", dt: float = .02,
               train_fraction: float = .8):
    if not 0 < train_fraction < 1 or dt <= 0:
      raise ValueError("invalid motion dt/split")
    directory = Path(files)
    manifest = json.loads((directory / "manifest.json").read_text())
    self.joint_names = manifest["joint_names"]
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
          or min(split - 1, n - split - 1) * frame_dt <= dt
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

  def sample_pairs(self, batch: int, train: bool = True) -> tuple[torch.Tensor, torch.Tensor]:
    clips, times = self.sample_times(batch, train)
    return frame_features(self.at_time(clips, times)), frame_features(self.at_time(clips, times + self.dt))


@torch.no_grad()
def heldout_style_distance(pairs: torch.Tensor, library: MotionLibrary,
                           command_vx: float) -> float:
  """Independent speed-conditioned temporal holdout distance, without D scores."""
  if pairs.ndim != 2 or pairs.shape[-1] != 2 * AMP_DIM or len(pairs) < 128:
    raise ValueError("G1 style evaluation needs at least 128 real transition pairs")
  a, b = library.sample_pairs(4096, train=True)
  scale = torch.cat((a, b), -1).std(0, unbiased=False).clamp(min=.05)
  clips, times = library.sample_times(16384, train=False)
  fa, fb = library.at_time(clips, times), library.at_time(clips, times + library.dt)
  vx = (quat_inverse_apply(fa[:, [6, 3, 4, 5]], fa[:, 36:39])[:, 0]
        + quat_inverse_apply(fb[:, [6, 3, 4, 5]], fb[:, 36:39])[:, 0]) * .5
  keep = (vx - command_vx).abs() < .35
  reference = torch.cat((frame_features(fa[keep]), frame_features(fb[keep])), -1)
  if len(reference) < 128:
    raise ValueError("insufficient held-out walk data in requested speed band")
  reference = reference[:2048] / scale
  distances = [torch.cdist(query / scale, reference).square().min(-1).values
               for query in pairs.split(256)]
  return (torch.cat(distances).mean() / (2 * AMP_DIM)).item()
