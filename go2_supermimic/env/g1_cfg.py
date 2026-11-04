"""Native Lab 2.1 G1 29DOF plane configuration; no upstream PPO dependency."""

from pathlib import Path

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import ArticulationCfg
from isaaclab.utils import configclass

from go2_supermimic.env.env_cfg import Go2SceneCfg, Go2VelocityEnvCfg
from go2_supermimic.g1 import DEFAULT_AMP_FEATURE_SCHEMA, DEFAULT_G1_MOTIONS, walk_task

G1_USD = str(Path(__file__).resolve().parents[2] / "assets/robots/g1/g1_29dof_rev_1_0.usd")


def motor(names, effort, speed, stiffness, damping) -> ImplicitActuatorCfg:
  # Preserve legged_lab's PhysX PD drives and constant effort limits.
  return ImplicitActuatorCfg(
    joint_names_expr=names, effort_limit_sim=effort, velocity_limit_sim=speed,
    stiffness=stiffness, damping=damping, armature=.01)


@configclass
class G1SceneCfg(Go2SceneCfg):
  robot = ArticulationCfg(
    prim_path="{ENV_REGEX_NS}/Robot",
    spawn=sim_utils.UsdFileCfg(
      usd_path=G1_USD, activate_contact_sensors=True,
      rigid_props=sim_utils.RigidBodyPropertiesCfg(
        disable_gravity=False, retain_accelerations=False, linear_damping=0.,
        angular_damping=0., max_linear_velocity=1000., max_angular_velocity=1000.,
        max_depenetration_velocity=1.),
      articulation_props=sim_utils.ArticulationRootPropertiesCfg(
        enabled_self_collisions=True, solver_position_iteration_count=8,
        solver_velocity_iteration_count=4)),
    init_state=ArticulationCfg.InitialStateCfg(
      pos=(0., 0., .8),
      joint_pos={
        ".*_hip_pitch_joint": -.1, ".*_knee_joint": .3, ".*_ankle_pitch_joint": -.2,
        ".*_shoulder_pitch_joint": .3, "left_shoulder_roll_joint": .25,
        "right_shoulder_roll_joint": -.25, ".*_elbow_joint": .97,
        "left_wrist_roll_joint": .15, "right_wrist_roll_joint": -.15},
      joint_vel={".*": 0.}),
    actuators={
      "hip_yaw_pitch": motor(
        [".*_hip_pitch_joint", ".*_hip_yaw_joint", "waist_yaw_joint"], 88., 32.,
        {".*_hip_.*": 100., "waist_yaw_joint": 200.},
        {".*_hip_.*": 2., "waist_yaw_joint": 5.}),
      "hip_roll_knee": motor(
        [".*_hip_roll_joint", ".*_knee_joint"], 139., 20.,
        {".*_hip_roll_joint": 100., ".*_knee_joint": 150.},
        {".*_hip_roll_joint": 2., ".*_knee_joint": 4.}),
      "body_arms_ankles": motor(
        [".*_shoulder_.*", ".*_elbow_joint", ".*_wrist_roll_joint",
         ".*_ankle_.*", "waist_roll_joint", "waist_pitch_joint"], 25., 37., 40.,
        {".*_shoulder_.*": 1., ".*_elbow_joint": 1., ".*_wrist_roll_joint": 1.,
         ".*_ankle_.*": 2., "waist_.*": 5.}),
      "wrists": motor([".*_wrist_pitch_joint", ".*_wrist_yaw_joint"], 5., 22., 40., 1.),
    })


@configclass
class G1AmpEnvCfg(Go2VelocityEnvCfg):
  robot_kind = "g1"
  foot_names = ("left_ankle_roll_link", "right_ankle_roll_link")
  foot_radius = .04
  undesired_contact_patterns = (
    "pelvis", "torso_link", ".*_knee_link", ".*_elbow_link", ".*_wrist_.*")
  scene = G1SceneCfg(num_envs=1024, env_spacing=4., replicate_physics=True)
  amp_enabled = True
  amp_motion_files = DEFAULT_G1_MOTIONS
  amp_feature_schema = DEFAULT_AMP_FEATURE_SCHEMA
  task = walk_task()

  def configure_task(self):
    super().configure_task()
    if self.task.reward_profile == "g1_legged_lab_walk_v1":
      self.undesired_contact_patterns = (".*_elbow_link", ".*_wrist_.*")


@configclass
class G1VelocityEnvCfg(G1AmpEnvCfg):
  """G1 flat velocity task used to build a cold-start locomotion policy.

  The task, robot, plane and reward definition are shared with G1 AMP. Only
  the motion library and discriminator are disabled so this checkpoint can be
  used as the same-robot warm start for the subsequent AMP stage.
  """

  amp_enabled = False
  amp_motion_files = ""
