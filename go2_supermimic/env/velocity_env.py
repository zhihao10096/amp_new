"""Vectorized Go2 body-frame velocity tracking in Isaac Lab."""

import torch

import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation
from isaaclab.envs import DirectRLEnv
from isaaclab.utils.math import quat_from_euler_xyz

from go2_supermimic import velocity as v
from go2_supermimic.env.env_cfg import Go2VelocityEnvCfg
from go2_supermimic.supermimic.state import robot_consts, robot_state


class Go2VelocityEnv(DirectRLEnv):
  cfg: Go2VelocityEnvCfg

  def __init__(self, cfg: Go2VelocityEnvCfg, render_mode=None, **kwargs):
    cfg.observation_space = v.FRAME_DIM * cfg.task.history
    super().__init__(cfg, render_mode, **kwargs)
    self.consts = robot_consts(self)
    self.actions = torch.zeros(self.num_envs, v.NUM_JOINTS, device=self.device)
    self.previous_actions = torch.zeros_like(self.actions)
    self.commands = torch.zeros(self.num_envs, 3, device=self.device)
    self.command_time = torch.zeros(self.num_envs, device=self.device)
    self.history = torch.zeros(self.num_envs, cfg.observation_space, device=self.device)
    self.previous_state = robot_state(self).clone()
    self.fixed_command = None

  def _setup_scene(self):
    self.robot = Articulation(self.cfg.robot)
    self.scene.articulations["robot"] = self.robot
    ground_cfg = sim_utils.GroundPlaneCfg(
      size=(10000.0, 10000.0), physics_material=self.cfg.sim.physics_material)
    ground_cfg.func("/World/ground", ground_cfg)
    self.scene.clone_environments(copy_from_source=False)
    self.scene.filter_collisions(global_prim_paths=["/World/ground"])
    light = sim_utils.DomeLightCfg(intensity=2000.0, color=(0.75, 0.75, 0.75))
    light.func("/World/light", light)

  def _pre_physics_step(self, actions):
    self.extras["log"] = {}
    self.previous_state = robot_state(self).clone()
    self.previous_actions = self.actions.clone()
    self.actions = actions.clamp(-self.cfg.task.action_clip, self.cfg.task.action_clip).clone()

  def _apply_action(self):
    self.robot.set_joint_position_target(
      self.robot.data.default_joint_pos + self.cfg.task.action_scale * self.actions)

  def _get_dones(self):
    return (v.terminated(robot_state(self), self.cfg.task),
            self.episode_length_buf >= self.max_episode_length)

  def _get_rewards(self):
    state = robot_state(self)
    reward, terms = v.reward(self.previous_state, state, self.actions, self.previous_actions,
                             self.commands, self.consts, self.cfg.task, self.step_dt,
                             self.reset_terminated)
    # DirectRLEnv automatically resets before returning observations. Preserve
    # terminal states here so replay learns falls instead of reset teleports.
    self.extras["transition"] = {
      "next_state": state.clone(), "commands": self.commands.clone(),
      "linear_error": (state[:, v.V_B][:, :2] - self.commands[:, :2]).norm(dim=-1),
      "yaw_error": (state[:, 9] - self.commands[:, 2]).abs(),
    }
    self.extras["log"] = {f"reward/{name}": value.mean() for name, value in terms.items()}
    if self.fixed_command is None:
      self.commands, self.command_time = v.advance_commands(
        self.commands, self.command_time, self.step_dt, self.cfg.task.commands)
    return reward

  def _get_observations(self):
    frame = v.obs_frame(robot_state(self), self.actions, self.commands,
                        noise=self.cfg.task.observation_noise)
    self.history = v.push_history(self.history, frame, self.cfg.task.history)
    return {"policy": self.history}

  def _reset_idx(self, env_ids):
    if env_ids is None:
      env_ids = self.robot._ALL_INDICES
    self.robot.reset(env_ids)
    super()._reset_idx(env_ids)
    self.actions[env_ids] = 0
    self.previous_actions[env_ids] = 0
    self.history[env_ids] = 0
    commands, remaining = v.sample_commands(len(env_ids), self.device, self.cfg.task.commands)
    self.commands[env_ids] = commands if self.fixed_command is None else self.fixed_command[env_ids]
    self.command_time[env_ids] = remaining
    root = self.robot.data.default_root_state[env_ids].clone()
    root[:, :3] += self.scene.env_origins[env_ids]
    yaw = torch.rand(len(env_ids), device=self.device) * (2 * torch.pi)
    root[:, 3:7] = quat_from_euler_xyz(torch.zeros_like(yaw), torch.zeros_like(yaw), yaw)
    root[:, 7:] = 0
    joint_pos = self.robot.data.default_joint_pos[env_ids].clone()
    joint_pos += (torch.rand_like(joint_pos) - 0.5) * 0.1
    self.robot.write_root_pose_to_sim(root[:, :7], env_ids=env_ids)
    self.robot.write_root_velocity_to_sim(root[:, 7:], env_ids=env_ids)
    self.robot.write_joint_state_to_sim(joint_pos, torch.zeros_like(joint_pos), env_ids=env_ids)

  def set_command(self, command):
    """Hold one command or one per environment; None restores random sampling."""
    if command is None:
      self.fixed_command = None
      return
    values = torch.as_tensor(command, device=self.device, dtype=torch.float32)
    if values.shape == (3,):
      values = values.expand(self.num_envs, -1)
    if values.shape != (self.num_envs, 3) or not torch.isfinite(values).all():
      raise ValueError("command must be finite, with shape (3,) or (num_envs, 3)")
    self.fixed_command = values.clone()
    self.commands[:] = values
