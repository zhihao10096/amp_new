"""Manager terms and the shared simulator/imagination transition boundary."""

import torch

from isaaclab.envs.mdp.actions import JointPositionAction, JointPositionActionCfg
from isaaclab.managers import CommandTerm, CommandTermCfg
from isaaclab.utils import configclass
from isaaclab.utils.math import quat_apply, quat_from_euler_xyz, quat_mul

from go2_supermimic import velocity as v
from go2_supermimic.amp import leg_to_joint_order
from go2_supermimic.supermimic.state import robot_state


class Go2JointPositionAction(JointPositionAction):
  def process_actions(self, actions):
    self._env._state_before_action = robot_state(self._env).clone()
    if self._env._amp_state_history.shape[1]:
      self._env._amp_before_history = self._env.amp_history_for_state(
        self._env._state_before_action)
      self._env._amp_history_reset.zero_()
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
  env._amp_history_reset[env_ids] = True
  root = env.robot.data.default_root_state[env_ids].clone()
  root[:, :3] += env.scene.env_origins[env_ids]
  yaw = torch.rand(len(env_ids), device=env.device) * (2 * torch.pi)
  root[:, 3:7] = quat_from_euler_xyz(torch.zeros_like(yaw), torch.zeros_like(yaw), yaw)
  root[:, 7:] = 0
  joint_pos = env.robot.data.default_joint_pos[env_ids].clone()
  joint_pos += (torch.rand_like(joint_pos) - 0.5) * 0.1
  joint_vel = torch.zeros_like(joint_pos)
  if env.amp_motion is not None:
    frames = env.amp_motion.sample_frames(len(env_ids), train=True)
    use_reference = torch.rand(len(env_ids), device=env.device) < env.cfg.amp_reference_reset_fraction
    orientation = quat_mul(root[:, 3:7], frames[:, [6, 3, 4, 5]])
    root[:, 2] = torch.where(
      use_reference, frames[:, 2] + env.scene.env_origins[env_ids, 2], root[:, 2])
    root[:, 3:7] = torch.where(use_reference[:, None], orientation, root[:, 3:7])
    if env.robot_kind == "g1":
      # Source velocities are world-frame; only the added random yaw rotates them.
      yaw_quat = quat_from_euler_xyz(torch.zeros_like(yaw), torch.zeros_like(yaw), yaw)
      root[:, 7:10] = quat_apply(yaw_quat, frames[:, 36:39]) * use_reference[:, None]
      root[:, 10:13] = quat_apply(yaw_quat, frames[:, 39:42]) * use_reference[:, None]
      joint_pos = torch.where(use_reference[:, None], frames[:, 7:36], joint_pos)
      joint_vel = torch.where(use_reference[:, None], frames[:, 42:71], joint_vel)
    else:
      root[:, 7:10] = quat_apply(orientation, frames[:, 31:34]) * use_reference[:, None]
      root[:, 10:13] = quat_apply(orientation, frames[:, 34:37]) * use_reference[:, None]
      joint_pos = torch.where(use_reference[:, None], leg_to_joint_order(frames[:, 7:19]), joint_pos)
      joint_vel = torch.where(
        use_reference[:, None], leg_to_joint_order(frames[:, 37:49]), joint_vel)
  env.robot.write_root_pose_to_sim(root[:, :7], env_ids=env_ids)
  env.robot.write_root_velocity_to_sim(root[:, 7:], env_ids=env_ids)
  env.robot.write_joint_state_to_sim(joint_pos, joint_vel, env_ids=env_ids)


def capture_transition(env):
  """Snapshot once after physics, before any manager resets terminal robots."""
  if env._transition_step != env.common_step_counter:
    state = robot_state(env).clone()
    before = env._state_before_action
    commands = env.commands.clone()
    api = env.task_api
    done = api.terminated(state, env.cfg.task)
    _, terms = api.reward(
      before, state, env.actions, env.previous_actions, commands,
      env.consts, getattr(env, "training_task", env.cfg.task), env.step_dt, done, env.gait)
    env._reward_components = terms
    env.gait, _ = api.advance_gait(
      env.gait, before[:, api.CONTACT], state[:, api.CONTACT], env.step_dt)
    env.extras["transition"] = {
      "next_state": state, "commands": commands,
      "linear_error": (state[:, api.V_B][:, :2] - commands[:, :2]).norm(dim=-1),
      "yaw_error": (state[:, 9] - commands[:, 2]).abs(),
    }
    # Native reset logs contain episodic Python scalars; per-step tensor
    # metrics live separately so auto-reset cannot erase or mix them.
    env.extras["reward_terms"] = {
      f"reward/{name}": value.mean() for name, value in terms.items()}
    if env.cfg.amp_enabled:
      # RewardManager skips zero-weight terms during the AMP ramp. Keep the
      # per-transition score current even while that term contributes nothing.
      with torch.no_grad():
        env.extras["amp_style"] = (
          env.amp_discriminator.reward(
            before, state, env.consts.default_q, commands, env._amp_before_history)
          if env.amp_discriminator is not None else state.new_zeros(env.num_envs))
      if env._amp_state_history.shape[1]:
        env.extras["transition"]["amp_history"] = env._amp_before_history
        env._amp_state_history = torch.cat(
          (env._amp_before_history[:, 1:], before[:, None]), 1)
    env._transition_step = env.common_step_counter
  return env.extras["transition"]["next_state"]


def fallen(env):
  return env.task_api.terminated(capture_transition(env), env.cfg.task)


def reward_component(env, name: str):
  capture_transition(env)
  # RewardManager applies the configured weight and control dt exactly once.
  return env._reward_components[name]


def amp_style_reward(env):
  capture_transition(env)
  return env.extras["amp_style"]
