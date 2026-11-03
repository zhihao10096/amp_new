"""Evaluate an Isaac Lab velocity checkpoint and optionally record environment 0."""

import argparse
import json
import math
from pathlib import Path

from isaaclab.app import AppLauncher


def annotate_frame(frame, command, velocity, elapsed):
  import numpy as np
  from PIL import Image, ImageDraw, ImageFont

  image = Image.fromarray(frame)
  draw = ImageDraw.Draw(image)
  draw.rectangle((12, 12, 610, 105), fill=(20, 24, 30))
  font = ImageFont.load_default(size=18)
  target = "  ".join(f"{name} {value:+.2f}" for name, value in zip(("vx", "vy", "yaw"), command))
  actual = "  ".join(f"{name} {value:+.2f}" for name, value in zip(("vx", "vy", "yaw"), velocity))
  draw.text((24, 20), f"Go2 velocity tracking   {elapsed:.2f} s   [m/s, m/s, rad/s]",
            fill="white", font=font)
  draw.text((24, 48), "target:  " + target, fill=(140, 210, 255), font=font)
  draw.text((24, 76), "actual:  " + actual, fill=(160, 240, 170), font=font)
  return np.asarray(image)


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("task", nargs="?", default="Go2-Velocity-Flat", choices=["Go2-Velocity-Flat"])
  parser.add_argument("--checkpoint", required=True)
  parser.add_argument("--num-envs", type=int, default=64)
  parser.add_argument("--seconds", type=float, default=30)
  parser.add_argument("--command", nargs=3, type=float, metavar=("VX", "VY", "YAW_RATE"))
  parser.add_argument("--seed", type=int, default=42)
  parser.add_argument("--video", help="MP4 path (records environment 0 at 25 fps).")
  parser.add_argument("--metrics-json")
  parser.add_argument("--width", type=int, default=960)
  parser.add_argument("--height", type=int, default=540)
  parser.add_argument("--robot-usd", default="")
  AppLauncher.add_app_launcher_args(parser)
  args = parser.parse_args()
  if args.num_envs <= 0 or not math.isfinite(args.seconds) or args.seconds < 0.02:
    parser.error("num-envs must be positive and seconds must be at least 0.02")
  if args.command and not all(math.isfinite(value) for value in args.command):
    parser.error("command values must be finite")
  if args.video:
    args.enable_cameras = True
  launcher = AppLauncher(args)
  env = video = None
  try:
    import gymnasium as gym
    import torch

    import go2_supermimic.env
    from go2_supermimic.env.env_cfg import Go2VelocityEnvCfg
    from go2_supermimic.supermimic.train import Actor, load_checkpoint, task_from_dict

    ckpt = load_checkpoint(args.checkpoint, args.device)
    cfg = Go2VelocityEnvCfg()
    cfg.scene.num_envs = args.num_envs
    cfg.sim.device = args.device
    cfg.seed = args.seed
    cfg.task = task_from_dict(ckpt["task_cfg"])
    cfg.task.observation_noise = False
    if args.robot_usd:
      cfg.robot.spawn.usd_path = args.robot_usd
    cfg.viewer.resolution = (args.width, args.height)
    cfg.viewer.origin_type = "asset_root"
    cfg.viewer.asset_name = "robot"
    cfg.viewer.eye = (3.0, 3.0, 2.0)
    cfg.viewer.lookat = (0.0, 0.0, 0.2)
    env = gym.make(args.task, cfg=cfg, render_mode="rgb_array" if args.video else None).unwrapped
    if args.command is not None:
      env.set_command(args.command)
    obs, _ = env.reset()
    actor = Actor(ckpt["obs_dim"], tuple(ckpt["cfg"]["actor_hidden"])).to(env.device)
    actor.load_state_dict(ckpt["actor"])
    actor.eval()
    if args.video:
      import mediapy
      Path(args.video).parent.mkdir(parents=True, exist_ok=True)
      video = mediapy.VideoWriter(args.video, shape=(args.height, args.width), fps=25)
      video.__enter__()
    count = max(1, round(args.seconds / env.step_dt))
    squared = torch.zeros(3, device=env.device)
    measured = torch.zeros(3, device=env.device)
    commanded = torch.zeros(3, device=env.device)
    reward_sum = falls = timeouts = 0.0
    with torch.inference_mode():
      for step in range(count):
        obs, reward, term, trunc, extras = env.step(actor(obs["policy"]))
        transition = extras["transition"]
        state, commands = transition["next_state"], transition["commands"]
        velocity = state[:, [4, 5, 9]]
        squared += (velocity - commands).square().sum(0)
        measured += velocity.sum(0)
        commanded += commands.sum(0)
        reward_sum += reward.sum().item()
        falls += term.sum().item()
        timeouts += trunc.sum().item()
        if video is not None and step % 2 == 0:
          frame = env.render()
          if frame is None:
            raise RuntimeError("Isaac Sim returned no video frame")
          video.add_image(annotate_frame(frame, commands[0].tolist(), velocity[0].tolist(),
                                          (step + 1) * env.step_dt))
    samples = count * env.num_envs
    rmse = (squared / samples).sqrt().tolist()
    metrics = {"task": args.task, "checkpoint": str(Path(args.checkpoint).resolve()),
               "num_envs": env.num_envs, "seconds": count * env.step_dt, "seed": args.seed,
               "command": args.command, "rmse_vx_m_s": rmse[0], "rmse_vy_m_s": rmse[1],
               "rmse_yaw_rad_s": rmse[2], "mean_command": (commanded / samples).tolist(),
               "mean_velocity": (measured / samples).tolist(),
               "mean_reward_per_step": reward_sum / samples,
               "falls": int(falls), "timeouts": int(timeouts),
               "falls_per_minute": falls * 60 / (env.num_envs * count * env.step_dt)}
    print(json.dumps(metrics, indent=2), flush=True)
    if args.metrics_json:
      path = Path(args.metrics_json)
      path.parent.mkdir(parents=True, exist_ok=True)
      path.write_text(json.dumps(metrics, indent=2) + "\n")
  finally:
    if video is not None:
      video.__exit__(None, None, None)
    if env is not None:
      env.close()
    launcher.app.close()


if __name__ == "__main__":
  main()
