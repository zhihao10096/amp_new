"""Measure contact timing, foot clearance, slip and effort in PhysX."""

import argparse
import json
import math
import traceback
from pathlib import Path

from isaaclab.app import AppLauncher

from go2_supermimic.validation import GAIT_CASES as CASES


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--checkpoints", nargs="+", required=True)
  parser.add_argument("--output", required=True)
  parser.add_argument("--seconds", type=float, default=20)
  parser.add_argument("--repeats", type=int, default=8)
  parser.add_argument("--seed", type=int, default=42)
  AppLauncher.add_app_launcher_args(parser)
  args = parser.parse_args()
  if args.repeats <= 0 or not math.isfinite(args.seconds) or args.seconds < 1.2:
    parser.error("repeats must be positive and seconds must be at least 1.2")
  launcher = AppLauncher(args)
  env = None
  try:
    import gymnasium as gym
    import torch

    import go2_supermimic.env
    from go2_supermimic import velocity as v
    from go2_supermimic.env.env_cfg import Go2VelocityEnvCfg
    from go2_supermimic.supermimic.train import Actor, load_checkpoint

    cfg = Go2VelocityEnvCfg()
    cfg.scene.num_envs = len(CASES) * args.repeats
    cfg.sim.device = args.device
    cfg.seed = args.seed
    cfg.task.observation_noise = False
    env = gym.make("Go2-Velocity-Flat", cfg=cfg).unwrapped
    commands = torch.tensor([c for _, c in CASES], device=env.device).repeat_interleave(args.repeats, 0)
    env.set_command(commands)
    steps = round(args.seconds / env.step_dt)
    results = []
    for path in args.checkpoints:
      checkpoint = load_checkpoint(path, env.device)
      actor = Actor(checkpoint["obs_dim"], tuple(checkpoint["cfg"]["actor_hidden"])).to(env.device)
      actor.load_state_dict(checkpoint["actor"])
      actor.eval()
      obs, _ = env.reset(seed=args.seed)
      n = env.num_envs
      z = lambda: torch.zeros(n, device=env.device)
      sums = {name: z() for name in (
        "samples", "falls", "touchdowns", "air_sum", "stance_sum", "short_swings",
        "clearance_sum", "swing_samples", "slide_sum", "contact_samples", "joint_velocity_sq",
        "torque_sq", "power", "action_delta_sq", "diagonal_sync", "front_alternation")}
      sq = torch.zeros(n, 3, device=env.device)
      velocities = torch.zeros_like(sq)
      age = torch.zeros(n, device=env.device)
      previous_action = env.actions.clone()
      # Environment buffers survive this scope and are mutated by the next reset.
      with torch.no_grad():
        for _ in range(steps):
          action = actor(obs["policy"])
          obs, _, term, trunc, extras = env.step(action)
          s = extras["transition"]["next_state"]
          measured = s[:, [4, 5, 9]]
          keep = age >= 1.0
          contact = s[:, v.CONTACT] > .5
          sensor = env.contact_sensor
          foot = env.foot_sensor_ids
          touchdown = sensor.compute_first_contact(env.step_dt)[:, foot] & keep[:, None]
          last_air = sensor.data.last_air_time[:, foot]
          # Ignore the reset's initial landing, whose long "air" started at spawn.
          touchdown &= ~((age < 1.2)[:, None]) & ~(term | trunc)[:, None]
          count = touchdown.sum(-1)
          sums["touchdowns"] += count
          sums["air_sum"] += (last_air * touchdown).sum(-1)
          sums["short_swings"] += ((last_air < .08) & touchdown).sum(-1)
          last_stance = sensor.data.last_contact_time[:, foot]
          sums["stance_sum"] += (last_stance * touchdown).sum(-1)
          pos = s[:, v.FOOT_POS].reshape(n, 4, 3)
          height = s[:, v.Z] - (pos * s[:, v.GRAV][:, None, :]).sum(-1)
          # USD foot body origins are sphere centres, radius 0.022 m.
          clearance = (height - .022).clamp(min=0)
          swing = ~contact & keep[:, None]
          sums["clearance_sum"] += (clearance * swing).sum(-1)
          sums["swing_samples"] += swing.sum(-1)
          footvel = s[:, v.FOOT_VEL].reshape(n, 4, 3)
          g = s[:, v.GRAV][:, None, :]
          horizontal = footvel - (footvel * g).sum(-1, keepdim=True) * g
          stance = contact & keep[:, None]
          sums["slide_sum"] += (horizontal.norm(dim=-1) * stance).sum(-1)
          sums["contact_samples"] += stance.sum(-1)
          sums["joint_velocity_sq"] += s[:, v.QD].square().mean(-1) * keep
          sums["torque_sq"] += env.robot.data.applied_torque.square().mean(-1) * keep
          sums["power"] += (env.robot.data.applied_torque * s[:, v.QD]).abs().sum(-1) * keep
          sums["action_delta_sq"] += (env.actions - previous_action).square().mean(-1) * keep
          previous_action = env.actions.clone()
          sums["diagonal_sync"] += (((contact[:, 0] == contact[:, 3]).float()
                                     + (contact[:, 1] == contact[:, 2]).float()) / 2) * keep
          sums["front_alternation"] += (contact[:, 0] != contact[:, 1]).float() * keep
          sums["samples"] += keep
          sums["falls"] += term
          sq += (measured - commands).square() * keep[:, None]
          velocities += measured * keep[:, None]
          age += env.step_dt
          age[term | trunc] = 0
      cases = {}
      for i, (name, cmd) in enumerate(CASES):
        ids = slice(i * args.repeats, (i + 1) * args.repeats)
        x = {k: t[ids].sum().item() for k, t in sums.items()}
        samples, touches = max(x["samples"], 1), max(x["touchdowns"], 1)
        cases[name] = {
          "command": list(cmd), "velocity": (velocities[ids].sum(0) / samples).tolist(),
          "rmse": (sq[ids].sum(0) / samples).sqrt().tolist(),
          "falls": int(x["falls"]), "stride_hz_per_foot": x["touchdowns"] / (samples * env.step_dt * 4),
          "mean_air_time_s": x["air_sum"] / touches,
          "mean_stance_time_s": x["stance_sum"] / touches,
          "short_swing_fraction": x["short_swings"] / touches,
          "mean_swing_clearance_m": x["clearance_sum"] / max(x["swing_samples"], 1),
          "stance_slide_m_s": x["slide_sum"] / max(x["contact_samples"], 1),
          "joint_velocity_rms": (x["joint_velocity_sq"] / samples)**.5,
          "torque_rms": (x["torque_sq"] / samples)**.5,
          "absolute_joint_power_w": x["power"] / samples,
          "action_delta_rms": (x["action_delta_sq"] / samples)**.5,
          "diagonal_contact_sync": x["diagonal_sync"] / samples,
          "front_contact_alternation": x["front_alternation"] / samples,
        }
      result = {"checkpoint": str(Path(path).resolve()), "iteration": checkpoint["iteration"],
                "environment_backend": env.environment_backend,
                "checkpoint_backend": checkpoint.get("environment_backend", "legacy_direct"),
                "seconds": args.seconds, "repeats": args.repeats, "seed": args.seed, "cases": cases}
      results.append(result)
      print(json.dumps(result, indent=2), flush=True)
      output = Path(args.output)
      output.parent.mkdir(parents=True, exist_ok=True)
      output.write_text(json.dumps(results, indent=2) + "\n")
  except Exception:
    traceback.print_exc()
    raise
  finally:
    if env is not None:
      env.close()
    launcher.app.close()


if __name__ == "__main__":
  main()
