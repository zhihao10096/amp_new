"""Simulator-independent commands, observations and rewards for velocity tracking.

These functions are used by both PhysX collection and differentiable imagination.
All velocities and commands are in the robot's body frame; yaw rate is in rad/s.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import torch

NUM_JOINTS = 12
STATE_DIM = 34
Z = slice(0, 1)
GRAV = slice(1, 4)
V_B = slice(4, 7)
W_B = slice(7, 10)
Q = slice(10, 22)
QD = slice(22, 34)
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
  orientation: float = -1.0
  base_height: float = -10.0
  joint_deviation: float = -0.05
  action_rate: float = -0.01
  joint_torque: float = -2e-5
  joint_acceleration: float = -2.5e-7
  joint_limits: float = -1.0
  terminated: float = -10.0


@dataclass
class VelocityTaskCfg:
  history: int = 5
  action_scale: float = 0.25
  action_clip: float = 4.0
  observation_noise: bool = True
  nominal_height: float = 0.30
  minimum_height: float = 0.16
  fall_angle_deg: float = 60.0
  tracking_variance: float = 0.25
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


def sample_commands(n: int, device, cfg: CommandCfg) -> tuple[torch.Tensor, torch.Tensor]:
  bounds = torch.tensor([cfg.lin_vel_x, cfg.lin_vel_y, cfg.ang_vel_z], device=device)
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


def reward(s0, s1, action, previous_action, commands, c: RobotConsts,
           cfg: VelocityTaskCfg, dt: float, done: torch.Tensor):
  q = s1[:, Q] + c.default_q
  terms = {
    "track_linear_velocity": torch.exp(
      -(s1[:, V_B][:, :2] - commands[:, :2]).square().sum(-1) / cfg.tracking_variance),
    "track_yaw_rate": torch.exp(-(s1[:, 9] - commands[:, 2]).square() / cfg.tracking_variance),
    "vertical_velocity": s1[:, 6].square(),
    "roll_pitch_rate": s1[:, W_B][:, :2].square().sum(-1),
    "orientation": s1[:, GRAV][:, :2].square().sum(-1),
    "base_height": (s1[:, 0] - cfg.nominal_height).square(),
    "joint_deviation": s1[:, Q].square().sum(-1),
    "action_rate": (action - previous_action).square().sum(-1),
    "joint_torque": motor_torque(s1, action, c, cfg).square().sum(-1),
    "joint_acceleration": ((s1[:, QD] - s0[:, QD]) / dt).square().sum(-1),
    "joint_limits": ((c.soft_limits[..., 0] - q).clamp(min=0)
                     + (q - c.soft_limits[..., 1]).clamp(min=0)).sum(-1),
    "terminated": done.float(),
  }
  return sum(getattr(cfg.rewards, name) * value for name, value in terms.items()) * dt, terms
