"""Read the translation/yaw-invariant dynamics state from Isaac Lab."""

import torch

from go2_supermimic.velocity import RobotConsts


def robot_state(env) -> torch.Tensor:
  d = env.robot.data
  from isaaclab.utils.math import quat_rotate_inverse

  feet = env.foot_body_ids
  quat = d.root_quat_w[:, None, :].expand(-1, 4, -1).reshape(-1, 4)
  relative = d.body_pos_w[:, feet] - d.root_pos_w[:, None, :]
  foot_pos = quat_rotate_inverse(quat, relative.reshape(-1, 3)).reshape(-1, 12)
  foot_vel = quat_rotate_inverse(quat, d.body_lin_vel_w[:, feet].reshape(-1, 3)).reshape(-1, 12)
  forces = env.contact_sensor.data.net_forces_w_history.norm(dim=-1).amax(dim=1)
  contact = (forces[:, env.foot_sensor_ids] > 1).float()
  undesired = (forces[:, env.undesired_sensor_ids] > 1).float().sum(-1, keepdim=True)
  return torch.cat([
    d.root_pos_w[:, 2:3] - env.scene.env_origins[:, 2:3],
    d.projected_gravity_b, d.root_lin_vel_b, d.root_ang_vel_b,
    d.joint_pos - d.default_joint_pos, d.joint_vel,
    foot_pos, foot_vel, contact, undesired,
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
