"""Manager terms and the shared simulator/imagination transition boundary."""

import torch

from isaaclab.envs.mdp.actions import JointPositionAction, JointPositionActionCfg
from isaaclab.managers import CommandTerm, CommandTermCfg
from isaaclab.utils import configclass
from isaaclab.utils.math import quat_from_euler_xyz

from go2_supermimic import velocity as v
from go2_supermimic.supermimic.state import robot_state


class Go2JointPositionAction(JointPositionAction):
  def process_actions(self, actions):
    self._env._state_before_action = robot_state(self._env).clone()
    # Isaac Lab 2.1 passes a view of the caller's input, not its own action
    # buffer. Preserve that input and publish the clipped action to managers.
    clipped = actions.clamp(-self.cfg.raw_clip, self.cfg.raw_clip)
    self._env.action_manager.action.copy_(clipped)
    super().process_actions(clipped)


@configclass
class Go2JointPositionActionCfg(JointPositionActionCfg):
  class_type = Go2JointPositionAction
  raw_clip: float = 4.0


class BodyVelocityCommand(CommandTerm):
  def __init__(self, cfg, env):
    super().__init__(cfg, env)
    self._command = torch.zeros(self.num_envs, 3, device=self.device)
    self.fixed_command = None

  @property
  def command(self):
    return self._command

  def _resample_command(self, env_ids):
    commands, _ = v.sample_commands(len(env_ids), self.device, self._env.cfg.task.commands)
    self._command[env_ids] = commands if self.fixed_command is None else self.fixed_command[env_ids]

  def _update_command(self):
    pass

  def _update_metrics(self):
    pass

  def set_command(self, command):
    if command is None:
      self.fixed_command = None
      return
    values = torch.as_tensor(command, device=self.device, dtype=torch.float32)
    if values.shape == (3,):
      values = values.expand(self.num_envs, -1)
    if values.shape != (self.num_envs, 3) or not torch.isfinite(values).all():
      raise ValueError("command must be finite, with shape (3,) or (num_envs, 3)")
    self.fixed_command = values.clone()
    self._command[:] = values


@configclass
class BodyVelocityCommandCfg(CommandTermCfg):
  class_type = BodyVelocityCommand


def reset_robot(env, env_ids):
  """Reset event: random yaw/joints, standing root state and cleared gait."""
  env.gait[env_ids] = 0
  root = env.robot.data.default_root_state[env_ids].clone()
  root[:, :3] += env.scene.env_origins[env_ids]
  yaw = torch.rand(len(env_ids), device=env.device) * (2 * torch.pi)
  root[:, 3:7] = quat_from_euler_xyz(torch.zeros_like(yaw), torch.zeros_like(yaw), yaw)
  root[:, 7:] = 0
  joint_pos = env.robot.data.default_joint_pos[env_ids].clone()
  joint_pos += (torch.rand_like(joint_pos) - 0.5) * 0.1
  env.robot.write_root_pose_to_sim(root[:, :7], env_ids=env_ids)
  env.robot.write_root_velocity_to_sim(root[:, 7:], env_ids=env_ids)
  env.robot.write_joint_state_to_sim(joint_pos, torch.zeros_like(joint_pos), env_ids=env_ids)


def capture_transition(env):
  """Snapshot once after physics, before any manager resets terminal robots."""
  if env._transition_step != env.common_step_counter:
    state = robot_state(env).clone()
    before = env._state_before_action
    commands = env.commands.clone()
    done = v.terminated(state, env.cfg.task)
    _, terms = v.reward(
      before, state, env.actions, env.previous_actions, commands,
      env.consts, env.cfg.task, env.step_dt, done, env.gait)
    env._reward_components = terms
    env.gait, _ = v.advance_gait(
      env.gait, before[:, v.CONTACT], state[:, v.CONTACT], env.step_dt)
    env.extras["transition"] = {
      "next_state": state, "commands": commands,
      "linear_error": (state[:, v.V_B][:, :2] - commands[:, :2]).norm(dim=-1),
      "yaw_error": (state[:, 9] - commands[:, 2]).abs(),
    }
    # Native reset logs contain episodic Python scalars; per-step tensor
    # metrics live separately so auto-reset cannot erase or mix them.
    env.extras["reward_terms"] = {
      f"reward/{name}": value.mean() for name, value in terms.items()}
    env._transition_step = env.common_step_counter
  return env.extras["transition"]["next_state"]


def fallen(env):
  return v.terminated(capture_transition(env), env.cfg.task)


def reward_component(env, name: str):
  capture_transition(env)
  # RewardManager applies the configured weight and control dt exactly once.
  return env._reward_components[name]
