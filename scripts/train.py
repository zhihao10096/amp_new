"""Train Go2 velocity tracking with Isaac Lab and SuperMimic."""

import argparse
from dataclasses import fields

from isaaclab.app import AppLauncher

from go2_supermimic.supermimic.train import TrainCfg


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  defaults = TrainCfg()
  for item in fields(defaults):
    value = getattr(defaults, item.name)
    flag = "--" + item.name.replace("_", "-")
    if isinstance(value, bool):
      parser.add_argument(flag, action=argparse.BooleanOptionalAction, default=value)
    elif isinstance(value, tuple):
      parser.add_argument(flag, nargs="+", type=int, default=value)
    else:
      parser.add_argument(flag, type=type(value), default=value)
  AppLauncher.add_app_launcher_args(parser)
  args = parser.parse_args()
  cfg = TrainCfg(**{f.name: getattr(args, f.name) for f in fields(defaults)})
  if cfg.task != "Go2-Velocity-Flat":
    parser.error("the available task is Go2-Velocity-Flat")
  launcher = AppLauncher(args)
  env = None
  try:
    import gymnasium as gym
    import torch

    import go2_supermimic.env  # registers the Isaac Lab task after SimulationApp starts
    from go2_supermimic.env.env_cfg import Go2VelocityEnvCfg
    from go2_supermimic.supermimic.train import Trainer, load_checkpoint, task_from_dict

    torch.set_float32_matmul_precision("high")
    env_cfg = Go2VelocityEnvCfg()
    env_cfg.scene.num_envs = cfg.num_envs
    env_cfg.sim.device = args.device
    env_cfg.seed = cfg.seed
    if cfg.resume:
      ckpt = load_checkpoint(cfg.resume, "cpu")
      env_cfg.task = task_from_dict(ckpt["task_cfg"])
      # A checkpoint's architecture is part of its interface.
      for name in ("actor_hidden", "critic_hidden", "wm_hidden"):
        setattr(cfg, name, tuple(ckpt["cfg"][name]))
    if cfg.robot_usd:
      env_cfg.robot.spawn.usd_path = cfg.robot_usd
    env = gym.make(cfg.task, cfg=env_cfg).unwrapped
    Trainer(cfg, env).run()
  finally:
    if env is not None:
      env.close()
    launcher.app.close()


if __name__ == "__main__":
  main()
