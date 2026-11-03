"""Simulator-independent commands, observations and rewards for velocity tracking.

These functions are used by both PhysX collection and differentiable imagination.
All velocities and commands are in the robot's body frame; yaw rate is in rad/s.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache

import torch

NUM_JOINTS = 12
BASE_STATE_DIM = 34
STATE_DIM = 63
GAIT_DIM = 16
Z = slice(0, 1)
GRAV = slice(1, 4)
V_B = slice(4, 7)
W_B = slice(7, 10)
Q = slice(10, 22)
QD = slice(22, 34)
FOOT_POS = slice(34, 46)  # body-frame foot positions relative to the root
FOOT_VEL = slice(46, 58)  # absolute foot velocity, rotated into body frame
CONTACT = slice(58, 62)   # FL, FR, RL, RR; binary in PhysX, soft in imagination
UNDESIRED_CONTACT = slice(62, 63)
AIR = slice(0, 4)
STANCE = slice(4, 8)
LAST_AIR = slice(8, 12)
LAST_STANCE = slice(12, 16)
OBS_TERMS = (("angular_velocity", 3), ("gravity", 3), ("command", 3),
             ("joint_position", 12), ("joint_velocity", 12), ("action", 12))
FRAME_DIM = sum(dim for _, dim in OBS_TERMS)


@dataclass
class CommandCfg:
  lin_vel_x: tuple[float, float] = (-1.0, 1.5)
  lin_vel_y: tuple[float, float] = (-0.6, 0.6)
  ang_vel_z: tuple[float, float] = (-1.0, 1.0)
  resampling_time: tuple[float, float] = (6.0, 10.0)
  standing_fraction: float = 0.1

  def __post_init__(self):
    for name in ("lin_vel_x", "lin_vel_y", "ang_vel_z", "resampling_time"):
      lo, hi = getattr(self, name)
      if lo > hi or (name == "resampling_time" and lo <= 0):
        raise ValueError(f"invalid {name}: {(lo, hi)}")
    if not 0 <= self.standing_fraction <= 1:
      raise ValueError("standing_fraction must be in [0, 1]")


@dataclass
class RewardWeights:
  track_linear_velocity: float = 1.5
  track_yaw_rate: float = 0.75
  vertical_velocity: float = -2.0
  roll_pitch_rate: float = -0.05
  orientation: float = -2.5
  base_height: float = 0.0
  joint_deviation: float = -0.7
  action_rate: float = -0.1
  joint_torque: float = -2e-4
  joint_velocity: float = -0.001
  energy: float = -2e-5
  joint_acceleration: float = -2.5e-7
  joint_limits: float = -10.0
  feet_air_time: float = 0.1
  air_time_variance: float = -1.0
  feet_slide: float = -0.3
  undesired_contacts: float = -1.0
  feet_clearance: float = 0.5
  feet_contact_without_command: float = 0.5
  gait_duration: float = -8.0
  diagonal_gait: float = 0.3
  terminated: float = -10.0


REWARD_NAMES = tuple(RewardWeights.__dataclass_fields__)
REWARD_INDEX = {name: index for index, name in enumerate(REWARD_NAMES)}


@dataclass
class VelocityTaskCfg:
  reward_profile: str = "unitree_gait"
  history: int = 5
  action_scale: float = 0.25
  action_clip: float = 4.0
  observation_noise: bool = True
  nominal_height: float = 0.30
  minimum_height: float = 0.16
  fall_angle_deg: float = 60.0
  tracking_variance: float = 0.25
  air_time_threshold: float = 0.5
  stand_still_scale: float = 5.0
  stand_velocity_threshold: float = 0.3
  joint_deviation_gait_fraction: float = 1.0
  """Blend the initial squared deviation into the final gait norm penalty."""
  swing_height: float = 0.06  # foot body centre, including 0.022 m foot radius
  clearance_variance: float = 0.01
  target_air_time: float = 0.18
  target_stance_time: float = 0.18
  commands: CommandCfg = field(default_factory=CommandCfg)
  rewards: RewardWeights = field(default_factory=RewardWeights)


@dataclass
class RobotConsts:
  default_q: torch.Tensor
  soft_limits: torch.Tensor
  kp: torch.Tensor
  kd: torch.Tensor
  effort: torch.Tensor
  velocity: torch.Tensor


@lru_cache(maxsize=32)
def _command_bounds(device: str, ranges: tuple) -> torch.Tensor:
  # Imagination invokes this each step. Recreating a CUDA tensor from Python
  # values would otherwise force a host/device copy in every imagined step.
  return torch.tensor(ranges, device=device)


def sample_commands(n: int, device, cfg: CommandCfg) -> tuple[torch.Tensor, torch.Tensor]:
  ranges = tuple(tuple(pair) for pair in (cfg.lin_vel_x, cfg.lin_vel_y, cfg.ang_vel_z))
  bounds = _command_bounds(str(device), ranges)
  commands = bounds[:, 0] + torch.rand(n, 3, device=device) * (bounds[:, 1] - bounds[:, 0])
  commands[torch.rand(n, device=device) < cfg.standing_fraction] = 0
  lo, hi = cfg.resampling_time
  remaining = lo + torch.rand(n, device=device) * (hi - lo)
  return commands, remaining


def advance_commands(commands, remaining, dt: float, cfg: CommandCfg):
  """Resample expired commands after computing the reward for the current action."""
  remaining = remaining - dt
  expired = remaining <= 0
  new_commands, new_remaining = sample_commands(commands.shape[0], commands.device, cfg)
  return (torch.where(expired[:, None], new_commands, commands),
          torch.where(expired, new_remaining, remaining))


def obs_frame(s: torch.Tensor, action: torch.Tensor, commands: torch.Tensor,
              noise: bool = False) -> dict[str, torch.Tensor]:
  frame = {"angular_velocity": s[:, W_B], "gravity": s[:, GRAV], "command": commands,
           "joint_position": s[:, Q], "joint_velocity": s[:, QD], "action": action}
  if noise:
    for name, width in (("angular_velocity", 0.2), ("gravity", 0.05),
                        ("joint_position", 0.01), ("joint_velocity", 1.5)):
      frame[name] = frame[name] + (2 * torch.rand_like(frame[name]) - 1) * width
  return frame


def push_history(history: torch.Tensor, frame: dict[str, torch.Tensor], h: int) -> torch.Tensor:
  """Term-major history, oldest to newest within each term."""
  blocks, offset = [], 0
  for name, dim in OBS_TERMS:
    block = history[:, offset:offset + h * dim]
    blocks.append(torch.cat([block[:, dim:], frame[name]], -1))
    offset += h * dim
  return torch.cat(blocks, -1)


def terminated(s: torch.Tensor, cfg: VelocityTaskCfg) -> torch.Tensor:
  return ((s[:, 0] < cfg.minimum_height)
          | (s[:, 3] > -math.cos(math.radians(cfg.fall_angle_deg))))


def termination_probability(s: torch.Tensor, cfg: VelocityTaskCfg) -> torch.Tensor:
  """Smooth union of the same height and orientation limits used by PhysX."""
  low = torch.sigmoid((cfg.minimum_height - s[:, 0]) / 0.015)
  tilt = torch.sigmoid((s[:, 3] + math.cos(math.radians(cfg.fall_angle_deg))) / 0.04)
  return 1 - (1 - low) * (1 - tilt)


def motor_torque(s: torch.Tensor, action: torch.Tensor, c: RobotConsts,
                 cfg: VelocityTaskCfg) -> torch.Tensor:
  """The Go2 DC motor's PD law and speed-dependent torque saturation."""
  qd = s[:, QD]
  torque = c.kp * (cfg.action_scale * action - s[:, Q]) - c.kd * qd
  upper = (c.effort * (1 - qd / c.velocity)).clamp(min=0).minimum(c.effort)
  lower = (c.effort * (-1 - qd / c.velocity)).clamp(max=0).maximum(-c.effort)
  return torch.maximum(torch.minimum(torque, upper), lower)


def advance_gait(gait: torch.Tensor, contact0: torch.Tensor, contact1: torch.Tensor,
                 dt: float) -> tuple[torch.Tensor, torch.Tensor]:
  """Contact-event timers shared by PhysX and differentiable imagination.

  Binary contacts implement exact control-step timers. Predicted contacts use
  the continuous relaxation of the same update so rewards retain gradients.
  """
  c0, c1 = contact0.clamp(0, 1), contact1.clamp(0, 1)
  # Smoothstep suppresses low-probability "leaks" that would otherwise reset
  # an imagined swing timer every step. Binary real contacts stay unchanged.
  c0, c1 = c0.square() * (3 - 2 * c0), c1.square() * (3 - 2 * c1)
  touchdown, liftoff = (1 - c0) * c1, c0 * (1 - c1)
  air, stance = gait[:, AIR] + dt, gait[:, STANCE] + dt
  last_air = torch.lerp(gait[:, LAST_AIR], air, touchdown)
  last_stance = torch.lerp(gait[:, LAST_STANCE], stance, liftoff)
  return torch.cat([air * (1 - c1), stance * c1, last_air, last_stance], -1), touchdown


def reward(s0, s1, action, previous_action, commands, c: RobotConsts,
           cfg: VelocityTaskCfg, dt: float, done: torch.Tensor, gait=None, parameters=None):
  """Optional device parameters hold scheduled weights and the formula blend."""
  q = s1[:, Q] + c.default_q
  torque = motor_torque(s1, action, c, cfg)
  if cfg.reward_profile == "legacy":
    deviation = s1[:, Q].square().sum(-1)
  else:
    moving = ((commands.norm(dim=-1) > 0)
              | (s1[:, V_B][:, :2].norm(dim=-1) > cfg.stand_velocity_threshold))
    gait_deviation = s1[:, Q].norm(dim=-1) * torch.where(moving, 1.0, cfg.stand_still_scale)
    fraction = cfg.joint_deviation_gait_fraction if parameters is None else parameters[-1]
    deviation = (1 - fraction) * s1[:, Q].square().sum(-1) + fraction * gait_deviation
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
    "joint_torque": torque.square().sum(-1),
    "joint_velocity": s1[:, QD].square().sum(-1),
    "energy": (torque * s1[:, QD]).abs().sum(-1),
    "joint_acceleration": ((s1[:, QD] - s0[:, QD]) / dt).square().sum(-1),
    "joint_limits": ((c.soft_limits[..., 0] - q).clamp(min=0)
                     + (q - c.soft_limits[..., 1]).clamp(min=0)).sum(-1),
    "terminated": done.float(),
  }
  if gait is not None:
    following, touchdown = advance_gait(gait, s0[:, CONTACT], s1[:, CONTACT], dt)
    foot_vel = s1[:, FOOT_VEL].reshape(-1, 4, 3)
    # Remove the world-vertical component using gravity in body coordinates.
    gravity = s1[:, GRAV].unsqueeze(1)
    horizontal = foot_vel - (foot_vel * gravity).sum(-1, keepdim=True) * gravity
    contact = s1[:, CONTACT].clamp(0, 1)
    moving = commands.norm(dim=-1) > 0.1
    foot_pos = s1[:, FOOT_POS].reshape(-1, 4, 3)
    height = s1[:, Z] - (foot_pos * gravity).sum(-1)
    clearance_cost = ((height - cfg.swing_height).square()
                      * torch.tanh(2 * horizontal.norm(dim=-1))).sum(-1)
    duration_cost = ((following[:, LAST_AIR].clamp(max=0.5) - cfg.target_air_time).square()
                     + (following[:, LAST_STANCE].clamp(max=0.5)
                        - cfg.target_stance_time).square()).sum(-1)
    # A phase-free version of the reference contact gait reward: diagonal
    # feet move together and the two front feet alternate.
    same = lambda a, b: a * b + (1 - a) * (1 - b)
    diagonal = (same(contact[:, 0], contact[:, 3]) + same(contact[:, 1], contact[:, 2])) / 2
    opposite = 1 - same(contact[:, 0], contact[:, 1])
    terms.update({
      "feet_air_time": ((following[:, LAST_AIR] - cfg.air_time_threshold) * touchdown).sum(-1)
                       * (commands[:, :2].norm(dim=-1) > 0.1),
      "air_time_variance": (following[:, LAST_AIR].clamp(max=0.5).var(dim=-1)
                            + following[:, LAST_STANCE].clamp(max=0.5).var(dim=-1)),
      "feet_slide": (horizontal.norm(dim=-1) * contact).sum(-1),
      "undesired_contacts": s1[:, UNDESIRED_CONTACT].squeeze(-1).clamp(min=0),
      "feet_clearance": torch.exp(-clearance_cost / cfg.clearance_variance) * moving,
      "feet_contact_without_command": contact.sum(-1) * ~moving,
      "gait_duration": duration_cost * moving,
      "diagonal_gait": .5 * (diagonal + opposite) * moving,
    })
  total = sum((getattr(cfg.rewards, name) if parameters is None
               else parameters[REWARD_INDEX[name]]) * value for name, value in terms.items())
  return total * dt, terms
