"""Checkpoint-aware robot selection. Import only after AppLauncher starts."""

from go2_supermimic.amp import AMPDiscriminator
from go2_supermimic.env.env_cfg import A1AmpEnvCfg, Go2VelocityEnvCfg
from go2_supermimic.supermimic.train import task_from_dict


def evaluation_config(checkpoint, num_envs, device, observation_noise=False):
  task = checkpoint["cfg"].get("task", "Go2-Velocity-Flat")
  if task not in ("Go2-Velocity-Flat", "A1-AMP-Flat"):
    raise ValueError(f"unsupported checkpoint task: {task}")
  cfg = A1AmpEnvCfg() if task == "A1-AMP-Flat" else Go2VelocityEnvCfg()
  if checkpoint.get("robot_kind", "go2") != cfg.robot_kind:
    raise ValueError("checkpoint task and robot metadata disagree")
  cfg.scene.num_envs = num_envs
  cfg.sim.device = device
  cfg.task = task_from_dict(checkpoint["task_cfg"])
  cfg.task.observation_noise = observation_noise
  # Independent evaluation always starts from ordinary standing resets.
  cfg.amp_motion_files = ""
  cfg.amp_reference_reset_fraction = 0.
  cfg.amp_enabled = "amp" in checkpoint
  cfg.amp_weight = checkpoint["cfg"].get("amp_weight", .5)
  return task, cfg


def attach_evaluation_amp(env, checkpoint):
  if "amp" not in checkpoint:
    env.amp_discriminator = None
    return
  disc = AMPDiscriminator(tuple(checkpoint["cfg"]["amp_hidden"])).to(env.device)
  disc.load_state_dict(checkpoint["amp"])
  env.amp_discriminator = disc.eval().requires_grad_(False)
