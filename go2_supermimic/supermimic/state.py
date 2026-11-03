"""Read the translation/yaw-invariant dynamics state from Isaac Lab."""

import torch

from go2_supermimic.velocity import RobotConsts


def robot_state(env) -> torch.Tensor:
  d = env.robot.data
  return torch.cat([
    d.root_pos_w[:, 2:3] - env.scene.env_origins[:, 2:3],
    d.projected_gravity_b, d.root_lin_vel_b, d.root_ang_vel_b,
    d.joint_pos - d.default_joint_pos, d.joint_vel,
  ], -1)


def robot_consts(env) -> RobotConsts:
  d = env.robot.data
  motor = env.robot.actuators["base_legs"]
  return RobotConsts(
    default_q=d.default_joint_pos[0].clone(),
    soft_limits=d.soft_joint_pos_limits[0].clone(),
    kp=motor.stiffness[0].clone(), kd=motor.damping[0].clone(),
    effort=motor.effort_limit[0].clone(), velocity=motor.velocity_limit[0].clone(),
  )
