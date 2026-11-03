"""Register the Isaac Lab Go2 velocity and A1 AMP flat tasks.

Import after AppLauncher has started Isaac Sim. Pure Torch modules do not import
this package, so unit tests and checkpoint inspection need no simulator.
"""

import gymnasium as gym

TASK_ID = "Go2-Velocity-Flat"

gym.register(
  id=TASK_ID,
  entry_point="go2_supermimic.env.velocity_env:Go2VelocityEnv",
  disable_env_checker=True,
  kwargs={"env_cfg_entry_point": "go2_supermimic.env.env_cfg:Go2VelocityEnvCfg"},
)

gym.register(
  id="A1-AMP-Flat",
  entry_point="go2_supermimic.env.velocity_env:Go2VelocityEnv",
  disable_env_checker=True,
  kwargs={"env_cfg_entry_point": "go2_supermimic.env.env_cfg:A1AmpEnvCfg"},
)
