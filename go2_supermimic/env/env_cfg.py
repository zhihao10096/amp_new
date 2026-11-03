"""Isaac Lab / PhysX configuration for the Go2 velocity task."""

import isaaclab.sim as sim_utils
from isaaclab.envs import DirectRLEnvCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass
from isaaclab_assets import UNITREE_GO2_CFG

from go2_supermimic.velocity import FRAME_DIM, VelocityTaskCfg


@configclass
class Go2VelocityEnvCfg(DirectRLEnvCfg):
  decimation = 4
  episode_length_s = 20.0
  action_space = 12
  observation_space = FRAME_DIM * 5
  state_space = 0
  sim = sim_utils.SimulationCfg(
    dt=0.005, render_interval=4,
    physics_material=sim_utils.RigidBodyMaterialCfg(
      static_friction=0.8, dynamic_friction=0.8, restitution=0.0),
  )
  scene = InteractiveSceneCfg(num_envs=1024, env_spacing=4.0, replicate_physics=True)
  robot = UNITREE_GO2_CFG.replace(prim_path="/World/envs/env_.*/Robot")
  task = VelocityTaskCfg()
