"""Evaluate the full velocity command range with fixed cases and random seeds."""

import argparse
import json
import traceback
from pathlib import Path

from isaaclab.app import AppLauncher

from go2_supermimic.validation import FIXED_CASES as CASES


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--checkpoints", nargs="+", required=True)
  parser.add_argument("--output", required=True)
  parser.add_argument("--repeats", type=int, default=8)
  parser.add_argument("--seconds", type=float, default=30)
  parser.add_argument("--settle-seconds", type=float, default=1)
  parser.add_argument("--seeds", nargs="+", type=int, default=[42, 123, 2026])
  parser.add_argument("--observation-noise", action="store_true",
                      help="Evaluate with the same sensor noise as training.")
  AppLauncher.add_app_launcher_args(parser)
  args = parser.parse_args()
  if args.repeats < 1 or args.seconds <= args.settle_seconds or args.settle_seconds < 0:
    parser.error("repeats must be positive, with seconds > settle-seconds >= 0")
  launcher = AppLauncher(args)
  env = None
  try:
    import gymnasium as gym
    import torch

    import go2_supermimic.env
    from go2_supermimic.amp_validation import A1_FIXED_CASES
    from go2_supermimic.g1_validation import G1_FIXED_CASES
    from go2_supermimic.env.factory import attach_evaluation_amp, evaluation_config
    from go2_supermimic.supermimic.train import Actor, load_checkpoint

    checkpoints = [load_checkpoint(path, args.device) for path in args.checkpoints]
    cases = A1_FIXED_CASES if checkpoints[0].get("robot_kind") == "a1" else CASES
    if checkpoints[0].get("robot_kind") == "g1":
      cases = G1_FIXED_CASES
    task_name, cfg = evaluation_config(
      checkpoints[0], len(cases) * args.repeats, args.device, args.observation_noise)
    cfg.seed = args.seeds[0]
    env = gym.make(task_name, cfg=cfg).unwrapped
    steps = round(args.seconds / env.step_dt)
    settling = round(args.settle_seconds / env.step_dt)
    commands = torch.tensor([cmd for _, cmd in cases], device=env.device).repeat_interleave(args.repeats, 0)
    results = []

    @torch.inference_mode()
    def measure(actor, seed, fixed):
      env.set_command(commands if fixed else None)
      obs, _ = env.reset(seed=seed)
      n = env.num_envs
      sq = torch.zeros(n, 3, device=env.device)
      full_sq = torch.zeros_like(sq)
      velocity_sum = torch.zeros_like(sq)
      samples = torch.zeros(n, device=env.device)
      falls = torch.zeros(n, device=env.device)
      flight = torch.zeros_like(falls)
      previous = env.commands.clone()
      age = torch.zeros(n, device=env.device, dtype=torch.long)
      for _ in range(steps):
        obs, _, term, trunc, extras = env.step(actor(obs["policy"]))
        transition = extras["transition"]
        actual = transition["next_state"][:, [4, 5, 9]]
        target = transition["commands"]
        age = torch.where((target != previous).any(-1), torch.zeros_like(age), age)
        error = (actual - target).square()
        full_sq += error
        keep = age >= settling
        sq += error * keep[:, None]
        velocity_sum += actual * keep[:, None]
        samples += keep
        if env.robot_kind == "g1":
          from go2_supermimic.g1_validation import evaluation_falls
          falls += evaluation_falls(transition["next_state"], term)
        else:
          falls += term
        contact = transition["next_state"][:, env.task_api.CONTACT]
        flight += (contact < .5).all(-1) * keep
        age += 1
        age[term | trunc] = 0
        previous = target.clone()
      if not (samples > 0).all():
        raise RuntimeError("some environments produced no samples after settling")

      def summarize(ids):
        return {"rmse": (sq[ids].sum(0) / samples[ids].sum()).sqrt().tolist(),
                "full_rmse": (full_sq[ids].mean(0) / steps).sqrt().tolist(),
                "mean_velocity": (velocity_sum[ids].sum(0) / samples[ids].sum()).tolist(),
                "falls": int(falls[ids].sum().item()),
                "falls_per_minute": falls[ids].mean().item() * 60 / (steps * env.step_dt),
                "flight_fraction": (flight[ids].sum() / samples[ids].sum()).item(),
                "samples_after_settling": int(samples[ids].sum().item())}

      result = {"seed": seed, "overall": summarize(slice(None))}
      if fixed:
        result["cases"] = {
          name: {"command": list(cmd),
                 **summarize(slice(i * args.repeats, (i + 1) * args.repeats))}
          for i, (name, cmd) in enumerate(cases)}
      return result

    for path, checkpoint in zip(args.checkpoints, checkpoints):
      if (checkpoint["task_cfg"] != checkpoints[0]["task_cfg"] or checkpoint["dt"] != env.step_dt
          or checkpoint.get("robot_kind", "go2") != env.robot_kind):
        raise ValueError("benchmark checkpoints must use identical task settings")
      attach_evaluation_amp(env, checkpoint)
      actor = Actor(checkpoint["obs_dim"], tuple(checkpoint["cfg"]["actor_hidden"]),
                    env.robot.num_joints).to(env.device)
      actor.load_state_dict(checkpoint["actor"])
      actor.eval()
      print(f"Benchmark iteration {checkpoint['iteration']}: fixed command suite", flush=True)
      fixed = measure(actor, args.seeds[0], True)
      print(f"Fixed: {fixed['overall']}", flush=True)
      random = []
      for seed in args.seeds:
        measured = measure(actor, seed, False)
        random.append(measured)
        print(f"Random seed {seed}: {measured['overall']}", flush=True)
      result = {"checkpoint": str(Path(path).resolve()), "iteration": checkpoint["iteration"],
                "environment_backend": env.environment_backend,
                "checkpoint_backend": checkpoint.get("environment_backend", "legacy_direct"),
                "robot_kind": env.robot_kind,
                "seconds": steps * env.step_dt, "settle_seconds": settling * env.step_dt,
                "observation_noise": cfg.task.observation_noise,
                "environments": env.num_envs, "fixed": fixed, "random": random}
      if env.robot_kind == "g1":
        from go2_supermimic.g1_validation import G1_FALL_DEFINITION
        result["fall_definition"] = G1_FALL_DEFINITION
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
