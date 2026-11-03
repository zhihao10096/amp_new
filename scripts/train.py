"""Train Go2/G1 velocity tracking or A1/G1 AMP with Isaac Lab/SuperMimic."""

import argparse
import sys
import traceback
from dataclasses import fields

from isaaclab.app import AppLauncher

from go2_supermimic.supermimic.train import TrainCfg
from go2_supermimic.supermimic.curriculum import restore_curriculum_options


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
  values = {f.name: getattr(args, f.name) for f in fields(defaults)}
  resume_checkpoint = None
  if args.resume:
    from go2_supermimic.supermimic.train import load_checkpoint
    resume_checkpoint = load_checkpoint(args.resume, "cpu")
    values = restore_curriculum_options(values, resume_checkpoint["cfg"], sys.argv[1:])
    supplied = {x.split("=", 1)[0] for x in sys.argv[1:]}
    for name in values:
      if (name in ("task", "critic_real_fraction") or name.startswith("amp_")) and (
          "--" + name.replace("_", "-") not in supplied):
        values[name] = resume_checkpoint["cfg"].get(name, values[name])
  if values["task"] == "A1-AMP-Flat" and not values["amp_motion_files"]:
    from go2_supermimic.amp import DEFAULT_A1_MOTIONS
    values["amp_motion_files"] = DEFAULT_A1_MOTIONS
  if values["task"] == "G1-AMP-Flat" and not values["amp_motion_files"]:
    from go2_supermimic.g1 import DEFAULT_G1_MOTIONS
    values["amp_motion_files"] = DEFAULT_G1_MOTIONS
  cfg = TrainCfg(**values)
  if cfg.task not in ("Go2-Velocity-Flat", "A1-AMP-Flat", "G1-AMP-Flat",
                      "G1-Velocity-Flat"):
    parser.error("available tasks: Go2-Velocity-Flat, A1-AMP-Flat, "
                 "G1-AMP-Flat, G1-Velocity-Flat")
  launcher = AppLauncher(args)
  env = None
  try:
    import gymnasium as gym
    import torch

    import go2_supermimic.env  # registers the Isaac Lab task after SimulationApp starts
    from go2_supermimic.env.env_cfg import A1AmpEnvCfg, Go2VelocityEnvCfg
    from go2_supermimic.supermimic.train import Trainer, load_checkpoint, task_from_dict

    torch.set_float32_matmul_precision(cfg.matmul_precision)
    env_cfg = A1AmpEnvCfg() if cfg.task == "A1-AMP-Flat" else Go2VelocityEnvCfg()
    if cfg.task in ("G1-AMP-Flat", "G1-Velocity-Flat"):
      from go2_supermimic.env.g1_cfg import G1AmpEnvCfg, G1VelocityEnvCfg
      env_cfg = G1AmpEnvCfg() if cfg.task == "G1-AMP-Flat" else G1VelocityEnvCfg()
    env_cfg.scene.num_envs = cfg.num_envs
    env_cfg.sim.device = args.device
    env_cfg.seed = cfg.seed
    if env_cfg.amp_enabled:
      env_cfg.amp_motion_files = cfg.amp_motion_files
      env_cfg.amp_weight = cfg.amp_weight
      env_cfg.amp_reference_reset_fraction = cfg.amp_reference_reset_fraction
    if cfg.resume or cfg.warm_start:
      ckpt = (resume_checkpoint if resume_checkpoint is not None
              else load_checkpoint(cfg.warm_start, "cpu"))
      if cfg.resume:
        env_cfg.task = task_from_dict(ckpt["task_cfg"])
      # A checkpoint's architecture is part of its interface.
      for name in ("actor_hidden", "critic_hidden", "wm_hidden"):
        setattr(cfg, name, tuple(ckpt["cfg"][name]))
    if cfg.robot_usd:
      env_cfg.scene.robot.spawn.usd_path = cfg.robot_usd
    env = gym.make(cfg.task, cfg=env_cfg).unwrapped
    Trainer(cfg, env).run()
  except Exception:
    # Kit shutdown can terminate the process before Python prints the traceback.
    traceback.print_exc()
    raise
  finally:
    if env is not None:
      env.close()
    launcher.app.close()


if __name__ == "__main__":
  main()
