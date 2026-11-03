"""Explicit CUDA comparison of eager and compiled BPTT; no simulator required."""

import argparse
import json
import time
from pathlib import Path

import torch

from go2_supermimic import velocity as v
from go2_supermimic.supermimic.curriculum import training_task
from go2_supermimic.supermimic.imagine import CRITIC_DIM, ImagineCfg, Imagination
from go2_supermimic.supermimic.train import Actor, Critic, load_checkpoint, task_from_dict
from go2_supermimic.supermimic.world_model import WorldModel


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--checkpoint", required=True)
  parser.add_argument("--batch", type=int, default=128)
  parser.add_argument("--horizon", type=int, default=8)
  parser.add_argument("--output", required=True)
  parser.add_argument("--fraction", type=float)
  args = parser.parse_args()
  # Compare the compiler itself without different TF32 rounding accumulating
  # through recurrent dynamics and the actor's observation history.
  torch.set_float32_matmul_precision("highest")
  torch.manual_seed(29)
  device = "cuda:0"
  checkpoint = load_checkpoint(args.checkpoint, device)
  task = task_from_dict(checkpoint["task_cfg"])
  task.observation_noise = False
  fraction = checkpoint.get("reward_curriculum_fraction", 1) if args.fraction is None else args.fraction
  task = training_task(task, fraction)
  actor = Actor(checkpoint["obs_dim"], tuple(checkpoint["cfg"]["actor_hidden"])).to(device)
  critic = Critic(CRITIC_DIM, tuple(checkpoint["cfg"]["critic_hidden"])).to(device)
  wm = WorldModel(tuple(checkpoint["cfg"]["wm_hidden"])).to(device)
  for name, model in (("actor", actor), ("critic", critic), ("world_model", wm)):
    model.load_state_dict(checkpoint[name])
  wm.requires_grad_(False)
  critic.requires_grad_(False)
  s = wm.in_norm.mean[:v.STATE_DIM].expand(args.batch, -1).clone()
  obs = actor.norm.mean.expand(args.batch, -1).clone()
  commands = torch.rand(args.batch, 3, device=device) * 2 - 1
  seed = {"s": s, "a_prev": torch.zeros(args.batch, 12, device=device), "obs": obs,
          "commands": commands, "command_time": torch.ones(args.batch, device=device) * 10,
          "gait": torch.zeros(args.batch, v.GAIT_DIM, device=device)}
  # Constants only enter analytic rewards; both paths receive identical values.
  consts = v.RobotConsts(
    default_q=torch.zeros(12, device=device),
    soft_limits=torch.tensor([[-3., 3.]], device=device).expand(12, 2),
    kp=torch.full((12,), 25., device=device), kd=torch.full((12,), .5, device=device),
    effort=torch.full((12,), 23.5, device=device), velocity=torch.full((12,), 30., device=device))
  results, timings = [], {}
  for enabled in (False, True):
    imagine = Imagination(ImagineCfg(horizon=args.horizon, compile=enabled), task, consts)
    torch.cuda.synchronize()
    started = time.monotonic()
    for repetition in range(3):
      actor.zero_grad(set_to_none=True)
      objective, data = imagine.rollout(wm, actor, critic, seed)
      objective.mean().backward()
      torch.cuda.synchronize()
      if repetition == 0:
        timings[f"{enabled}_first_seconds"] = time.monotonic() - started
        started = time.monotonic()
    timings[f"{enabled}_warm_seconds"] = (time.monotonic() - started) / 2
    gradients = torch.cat([p.grad.flatten() for p in actor.parameters()]).clone()
    results.append((objective.detach().clone(), data, gradients))
  for actual, expected in zip(results[1], results[0]):
    if isinstance(actual, dict):
      for key in actual:
        torch.testing.assert_close(actual[key], expected[key], atol=3e-5, rtol=3e-4)
    else:
      torch.testing.assert_close(actual, expected, atol=3e-5, rtol=3e-4)
      assert torch.isfinite(actual).all()
  result = {"passed": True, "checkpoint": args.checkpoint, "batch": args.batch,
            "horizon": args.horizon, "timings": timings,
            "actor_gradient_norm": results[0][2].norm().item(),
            "gradient_max_absolute_error": (results[1][2] - results[0][2]).abs().max().item()}
  path = Path(args.output)
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(json.dumps(result, indent=2) + "\n")
  print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
  main()
