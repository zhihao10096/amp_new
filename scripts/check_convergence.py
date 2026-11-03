"""Audit full manager-based convergence reports and actual checkpoint provenance."""

import argparse
import hashlib
import json
from pathlib import Path

import torch

from go2_supermimic.validation import MANAGER_BACKEND, convergence_failures


def read_reports(paths):
  return [report for path in paths for report in json.loads(Path(path).read_text())]


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--benchmarks", nargs="+", required=True)
  parser.add_argument("--gaits", nargs="+", required=True)
  parser.add_argument("--noisy", required=True)
  parser.add_argument("--initial-checkpoint", required=True)
  parser.add_argument("--output", required=True)
  args = parser.parse_args()
  velocity, gait = read_reports(args.benchmarks), read_reports(args.gaits)
  noise = read_reports([args.noisy])
  failures = [] if len(noise) == 1 else ["require_one_final_noisy_report"]
  failures += convergence_failures(velocity, gait, noise[0] if noise else {})
  initial = torch.load(args.initial_checkpoint, map_location="cpu", weights_only=False)
  if (initial["iteration"] != 0 or initial["cfg"]["resume"] or initial["cfg"]["warm_start"]
      or initial.get("environment_backend") != MANAGER_BACKEND
      or initial.get("training_origin", {}).get("kind") != "random_initialization"):
    failures.append("initial_checkpoint_not_random_manager_initialization")
  checkpoints = []
  for report in sorted(velocity, key=lambda r: r["iteration"]):
    path = Path(report["checkpoint"])
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    if (checkpoint.get("environment_backend") != MANAGER_BACKEND
        or checkpoint.get("training_origin") != initial.get("training_origin")
        or checkpoint["iteration"] != report["iteration"]
        or checkpoint["task_cfg"] != initial["task_cfg"]):
      failures.append(f"{path.name}/checkpoint_provenance")
    if checkpoint.get("reward_curriculum_fraction", 1.0) != 1.0:
      failures.append(f"{path.name}/incomplete_reward_curriculum")
    for name in ("actor", "critic", "world_model"):
      tensors = checkpoint[name]
      if not all(torch.isfinite(t).all() for t in tensors.values()):
        failures.append(f"{path.name}/{name}/nonfinite")
      if not any(not torch.equal(t, initial[name][key])
                 for key, t in tensors.items() if key.startswith("net.")):
        failures.append(f"{path.name}/{name}/not_updated")
    if any(not checkpoint[name]["state"] for name in ("opt_actor", "opt_critic", "opt_wm")):
      failures.append(f"{path.name}/missing_optimizer_updates")
    checkpoints.append({
      "path": str(path.resolve()), "iteration": checkpoint["iteration"],
      "env_steps": checkpoint["env_steps"],
      "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    })
  result = {"converged": not failures, "failures": failures, "checkpoints": checkpoints,
            "initial_checkpoint": str(Path(args.initial_checkpoint).resolve()),
            "environment_backend": MANAGER_BACKEND,
            "velocity_reports": args.benchmarks, "gait_reports": args.gaits,
            "noisy_report": args.noisy}
  output = Path(args.output)
  output.parent.mkdir(parents=True, exist_ok=True)
  output.write_text(json.dumps(result, indent=2) + "\n")
  print(json.dumps(result, indent=2))
  if failures:
    raise SystemExit(1)


if __name__ == "__main__":
  main()
