"""Checkpoint-aware robot selection. Import only after AppLauncher starts."""

from go2_supermimic.amp import AMPDiscriminator
from go2_supermimic.env.env_cfg import A1AmpEnvCfg, Go2VelocityEnvCfg
from go2_supermimic.supermimic.train import task_from_dict
from go2_supermimic.task_api import amp_api


def evaluation_config(checkpoint, num_envs, device, observation_noise=False):
  task = checkpoint["cfg"].get("task", "Go2-Velocity-Flat")
  if task not in ("Go2-Velocity-Flat", "A1-AMP-Flat", "G1-AMP-Flat",
                  "G1-Velocity-Flat"):
    raise ValueError(f"unsupported checkpoint task: {task}")
  cfg = A1AmpEnvCfg() if task == "A1-AMP-Flat" else Go2VelocityEnvCfg()
  if task in ("G1-AMP-Flat", "G1-Velocity-Flat"):
    from go2_supermimic.g1 import require_implicit_pd
    require_implicit_pd(checkpoint)
    from go2_supermimic.env.g1_cfg import G1AmpEnvCfg, G1VelocityEnvCfg
    cfg = G1AmpEnvCfg() if task == "G1-AMP-Flat" else G1VelocityEnvCfg()
  if checkpoint.get("robot_kind", "go2") != cfg.robot_kind:
    raise ValueError("checkpoint task and robot metadata disagree")
  cfg.scene.num_envs = num_envs
  cfg.sim.device = device
  cfg.task = task_from_dict(checkpoint["task_cfg"])
  cfg.task.observation_noise = observation_noise
  # Independent evaluation always starts from ordinary standing resets.
  cfg.amp_motion_files = ""
  cfg.amp_reference_reset_fraction = 0.
  cfg.amp_reset_command_alignment = False
  cfg.amp_enabled = "amp" in checkpoint
  cfg.amp_weight = checkpoint["cfg"].get("amp_weight", .5)
  if task == "G1-AMP-Flat":
    cfg.amp_num_frames = checkpoint["cfg"].get("amp_num_frames", 2)
    cfg.amp_feature_schema = checkpoint["cfg"].get(
      "amp_feature_schema", "g1_amp_61_v1")
  return task, cfg


def attach_evaluation_amp(env, checkpoint):
  if env.robot_kind == "g1":
    from go2_supermimic.g1 import require_implicit_pd
    require_implicit_pd(checkpoint)
  if "amp" not in checkpoint:
    env.amp_discriminator = None
    return
  if env.robot_kind == "g1":
    disc = amp_api(env.robot_kind).AMPDiscriminator(
      tuple(checkpoint["cfg"]["amp_hidden"]),
      checkpoint["cfg"].get("amp_feature_schema", "g1_amp_61_v1"),
      checkpoint["cfg"].get("amp_num_frames", 2),
      command_gate=env.cfg.task.reward_profile != "g1_legged_lab_walk_v1").to(env.device)
  else:
    disc = amp_api(env.robot_kind).AMPDiscriminator(
      tuple(checkpoint["cfg"]["amp_hidden"])).to(env.device)
  disc.load_state_dict(checkpoint["amp"])
  env.amp_discriminator = disc.eval().requires_grad_(False)
