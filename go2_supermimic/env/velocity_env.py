"""Manager-based Go2 task with a SuperMimic transition adapter."""

import torch

from isaaclab.envs import ManagerBasedRLEnv

from go2_supermimic import velocity as v
from go2_supermimic.amp import MotionLibrary
from go2_supermimic.env.env_cfg import Go2VelocityEnvCfg
from go2_supermimic.supermimic.state import robot_consts, robot_state


class Go2VelocityEnv(ManagerBasedRLEnv):
  """Use Isaac Lab's step/reset lifecycle; managers implement the task."""

  cfg: Go2VelocityEnvCfg
  environment_backend = "isaaclab_manager_based_v1"

  def __init__(self, cfg: Go2VelocityEnvCfg, render_mode=None, **kwargs):
    cfg.configure_task()
    super().__init__(cfg, render_mode, **kwargs)

  def load_managers(self):
    self.robot_kind = self.cfg.robot_kind
    self.robot = self.scene["robot"]
    self.contact_sensor = self.scene["contact_sensor"]
    foot_names = ["FL_foot", "FR_foot", "RL_foot", "RR_foot"]
    self.foot_body_ids, _ = self.robot.find_bodies(foot_names, preserve_order=True)
    self.foot_sensor_ids, _ = self.contact_sensor.find_bodies(foot_names, preserve_order=True)
    self.undesired_sensor_ids, _ = self.contact_sensor.find_bodies(
      list(self.cfg.undesired_contact_patterns))
    self.consts = robot_consts(self)
    self.amp_discriminator = None
    self.amp_motion = (
      MotionLibrary(self.cfg.amp_motion_files, self.device, self.step_dt)
      if self.cfg.amp_enabled and self.cfg.amp_motion_files else None)
    self.gait = torch.zeros(self.num_envs, v.GAIT_DIM, device=self.device)
    self._state_before_action = robot_state(self).clone()
    self._transition_step = -1
    super().load_managers()

  @property
  def actions(self):
    return self.action_manager.action

  @property
  def previous_actions(self):
    return self.action_manager.prev_action

  @property
  def commands(self):
    return self.command_manager.get_command("base_velocity")

  @property
  def command_time(self):
    return self.command_manager.get_term("base_velocity").time_left

  @property
  def fixed_command(self):
    return self.command_manager.get_term("base_velocity").fixed_command

  def set_command(self, command):
    """Hold one command or one per environment, including across resets."""
    self.command_manager.get_term("base_velocity").set_command(command)
