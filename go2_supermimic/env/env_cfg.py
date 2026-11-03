"""Manager-based Isaac Lab configurations for Go2 tracking and A1 AMP."""

from dataclasses import fields

import isaaclab.envs.mdp as lab_mdp
import isaaclab.sim as sim_utils
from isaaclab.assets import AssetBaseCfg
from isaaclab.envs import ManagerBasedRLEnvCfg
from isaaclab.managers import EventTermCfg, ObservationGroupCfg, ObservationTermCfg
from isaaclab.managers import RewardTermCfg, TerminationTermCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sensors import ContactSensorCfg
from isaaclab.utils import configclass
from isaaclab.utils.noise import AdditiveUniformNoiseCfg
from isaaclab_assets import UNITREE_A1_CFG, UNITREE_GO2_CFG

from go2_supermimic.amp import DEFAULT_A1_MOTIONS
from go2_supermimic.env import mdp
from go2_supermimic.velocity import CommandCfg, VelocityTaskCfg


@configclass
class Go2SceneCfg(InteractiveSceneCfg):
  ground = AssetBaseCfg(
    prim_path="/World/ground", collision_group=-1,
    spawn=sim_utils.GroundPlaneCfg(
      size=(10000.0, 10000.0),
      physics_material=sim_utils.RigidBodyMaterialCfg(
        static_friction=0.8, dynamic_friction=0.8, restitution=0.0)))
  robot = UNITREE_GO2_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")
  contact_sensor = ContactSensorCfg(
    prim_path="{ENV_REGEX_NS}/Robot/.*", history_length=4,
    track_air_time=True, update_period=0.005)
  light = AssetBaseCfg(
    prim_path="/World/light",
    spawn=sim_utils.DomeLightCfg(intensity=2000.0, color=(0.75, 0.75, 0.75)))


@configclass
class CommandsCfg:
  base_velocity = mdp.BodyVelocityCommandCfg(resampling_time_range=(6.0, 10.0))


@configclass
class ActionsCfg:
  joint_position = mdp.Go2JointPositionActionCfg(
    asset_name="robot", joint_names=[".*"], scale=0.25, use_default_offset=True)


@configclass
class ObservationsCfg:
  @configclass
  class PolicyCfg(ObservationGroupCfg):
    # Term-major history is the actor's public interface.
    angular_velocity = ObservationTermCfg(
      func=lab_mdp.base_ang_vel, noise=AdditiveUniformNoiseCfg(n_min=-.2, n_max=.2))
    gravity = ObservationTermCfg(
      func=lab_mdp.projected_gravity, noise=AdditiveUniformNoiseCfg(n_min=-.05, n_max=.05))
    command = ObservationTermCfg(
      func=lab_mdp.generated_commands, params={"command_name": "base_velocity"})
    joint_position = ObservationTermCfg(
      func=lab_mdp.joint_pos_rel, noise=AdditiveUniformNoiseCfg(n_min=-.01, n_max=.01))
    joint_velocity = ObservationTermCfg(
      func=lab_mdp.joint_vel_rel, noise=AdditiveUniformNoiseCfg(n_min=-1.5, n_max=1.5))
    action = ObservationTermCfg(func=lab_mdp.last_action)
    history_length = 5
    flatten_history_dim = True
    enable_corruption = True
    concatenate_terms = True

  policy = PolicyCfg()


@configclass
class EventsCfg:
  reset_robot = EventTermCfg(func=mdp.reset_robot, mode="reset")


@configclass
class TerminationsCfg:
  time_out = TerminationTermCfg(func=lab_mdp.time_out, time_out=True)
  fall = TerminationTermCfg(func=mdp.fallen)


@configclass
class Go2VelocityEnvCfg(ManagerBasedRLEnvCfg):
  robot_kind: str = "go2"
  foot_radius: float = .022
  undesired_contact_patterns: tuple[str, ...] = ("Head_.*", ".*_hip", ".*_thigh", ".*_calf")
  amp_enabled: bool = False
  amp_motion_files: str = ""
  amp_reference_reset_fraction: float = .5
  amp_weight: float = .5
  decimation = 4
  episode_length_s = 20.0
  sim = sim_utils.SimulationCfg(
    dt=0.005, render_interval=4,
    physics_material=sim_utils.RigidBodyMaterialCfg(
      static_friction=0.8, dynamic_friction=0.8, restitution=0.0))
  scene = Go2SceneCfg(num_envs=1024, env_spacing=4.0, replicate_physics=True)
  commands = CommandsCfg()
  actions = ActionsCfg()
  observations = ObservationsCfg()
  events = EventsCfg()
  terminations = TerminationsCfg()
  rewards = {}
  task = VelocityTaskCfg()

  def configure_task(self):
    """Resolve checkpoint/task overrides before managers are constructed."""
    # The default patch buffer fits small scenes, but mass landing and resets
    # need more contacts at large environment counts. Allow 32 patches/robot,
    # including non-foot contacts, without reducing the physics fidelity.
    self.sim.physx.gpu_max_rigid_patch_count = max(
      self.sim.physx.gpu_max_rigid_patch_count, 32 * self.scene.num_envs)
    self.commands.base_velocity.resampling_time_range = self.task.commands.resampling_time
    self.actions.joint_position.scale = self.task.action_scale
    self.actions.joint_position.raw_clip = self.task.action_clip
    self.observations.policy.history_length = self.task.history
    self.observations.policy.enable_corruption = self.task.observation_noise
    self.rewards = {
      item.name: RewardTermCfg(
        func=mdp.reward_component, weight=getattr(self.task.rewards, item.name),
        params={"name": item.name})
      for item in fields(self.task.rewards)
    }
    if self.amp_enabled:
      self.rewards["amp_style"] = RewardTermCfg(func=mdp.amp_style_reward, weight=self.amp_weight)


@configclass
class A1SceneCfg(Go2SceneCfg):
  robot = UNITREE_A1_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")


@configclass
class A1AmpEnvCfg(Go2VelocityEnvCfg):
  robot_kind = "a1"
  foot_radius = .02
  undesired_contact_patterns = ("trunk", ".*_hip", ".*_thigh", ".*_calf")
  scene = A1SceneCfg(num_envs=1024, env_spacing=4.0, replicate_physics=True)
  amp_enabled = True
  amp_motion_files = DEFAULT_A1_MOTIONS
  task = VelocityTaskCfg(
    swing_height=.058,
    commands=CommandCfg(lin_vel_x=(0., 1.5), lin_vel_y=(-.3, .3), ang_vel_z=(-1., 1.)))
