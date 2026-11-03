"""Audit A1 AMP suites, independent initial style baseline and actual models."""

import argparse
import hashlib
import json
from pathlib import Path

import torch

from go2_supermimic.amp import DEFAULT_A1_MOTIONS, MotionLibrary
from go2_supermimic.amp_validation import a1_convergence_failures
from go2_supermimic.supermimic.train import load_checkpoint
from go2_supermimic.validation import MANAGER_BACKEND


def read_reports(paths):
  return [report for path in paths for report in json.loads(Path(path).read_text())]


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--benchmarks", nargs="+", required=True)
  parser.add_argument("--gaits", nargs="+", required=True)
  parser.add_argument("--baseline-gait", required=True)
  parser.add_argument("--noisy", required=True)
  parser.add_argument("--initial-checkpoint", required=True)
  parser.add_argument("--output", required=True)
  args = parser.parse_args()
  velocity, gait = read_reports(args.benchmarks), read_reports(args.gaits)
  noise, baseline = read_reports([args.noisy]), read_reports([args.baseline_gait])
  failures = []
  if len(noise) != 1 or len(baseline) != 1:
    failures.append("require_one_noisy_and_one_initial_gait_report")
  failures += a1_convergence_failures(
    velocity, gait, noise[0] if noise else {}, baseline[0] if baseline else {})
  initial_path = Path(args.initial_checkpoint).resolve()
  initial = load_checkpoint(initial_path, "cpu")
  expected_motion = MotionLibrary(DEFAULT_A1_MOTIONS, "cpu", dt=.02).metadata
  if (initial["iteration"] != 0 or initial["cfg"]["resume"]
      or initial.get("robot_kind") != "a1"
      or initial.get("environment_backend") != MANAGER_BACKEND
      or initial["cfg"]["task"] != "A1-AMP-Flat"
      or initial.get("amp_motion_metadata") != expected_motion):
    failures.append("initial_checkpoint_provenance")
  if not baseline or Path(baseline[0].get("checkpoint", "")).resolve() != initial_path:
    failures.append("baseline_not_initial_checkpoint")
  source = initial.get("training_origin", {})
  source_record = dict(source)
  if source.get("kind") == "warm_start":
    path = Path(source["checkpoint"])
    warm = load_checkpoint(path, "cpu")
    for name in ("actor", "world_model"):
      if any(key not in warm[name] or not torch.equal(t, warm[name][key])
             for key, t in initial[name].items()):
        failures.append(f"warm_start/{name}/initial_weights")
    source_record["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
  elif source.get("kind") != "random_initialization":
    failures.append("unverified_initial_training_origin")
  if any(initial[name]["state"] for name in ("opt_actor", "opt_critic", "opt_wm", "opt_amp")):
    failures.append("initial_optimizers_not_fresh")
  checkpoints = []
  for report in sorted(velocity, key=lambda r: r.get("iteration", -1)):
    path = Path(report["checkpoint"])
    checkpoint = load_checkpoint(path, "cpu")
    if (checkpoint.get("robot_kind") != "a1"
        or checkpoint.get("environment_backend") != MANAGER_BACKEND
        or checkpoint["cfg"]["task"] != "A1-AMP-Flat"
        or checkpoint.get("training_origin") != source
        or checkpoint["iteration"] != report["iteration"]
        or checkpoint["task_cfg"] != initial["task_cfg"]
        or checkpoint["dt"] != .02
        or checkpoint.get("amp_motion_metadata") != expected_motion):
      failures.append(f"{path.name}/checkpoint_provenance")
    if (checkpoint.get("reward_curriculum_fraction", 1.) != 1.
        or checkpoint.get("amp_reward_fraction") != 1.
        or checkpoint["cfg"]["amp_weight"] != initial["cfg"]["amp_weight"]
        or checkpoint["cfg"]["amp_weight"] <= 0):
      failures.append(f"{path.name}/incomplete_rewards")
    paired = next((r for r in gait if r.get("checkpoint") == report["checkpoint"]), {})
    if paired.get("amp_motion_metadata") != checkpoint.get("amp_motion_metadata"):
      failures.append(f"{path.name}/gait_motion_metadata")
    updates = {}
    for name, opt in (("actor", "opt_actor"), ("critic", "opt_critic"),
                      ("world_model", "opt_wm"), ("amp", "opt_amp")):
      tensors, states = checkpoint[name], checkpoint[opt]["state"]
      if not all(torch.isfinite(t).all() for t in tensors.values()):
        failures.append(f"{path.name}/{name}/nonfinite")
      if not any(not torch.equal(t, initial[name][key])
                 for key, t in tensors.items() if key.startswith("net.")):
        failures.append(f"{path.name}/{name}/not_updated")
      if (not states or any(
          state.get("step", 0) <= 0 or any(
            not torch.isfinite(t).all() for t in state.values() if isinstance(t, torch.Tensor))
          for state in states.values())):
        failures.append(f"{path.name}/{opt}/missing_or_nonfinite_updates")
      updates[name] = min((int(s.get("step", 0)) for s in states.values()), default=0)
    checkpoints.append({
      "path": str(path.resolve()), "iteration": checkpoint["iteration"],
      "env_steps": checkpoint["env_steps"], "optimizer_steps": updates,
      "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    })
  result = {"converged": not failures, "failures": failures,
            "checkpoints": checkpoints, "initial_checkpoint": str(initial_path),
            "initial_checkpoint_sha256": hashlib.sha256(initial_path.read_bytes()).hexdigest(),
            "training_origin": source_record, "amp_motion_metadata": expected_motion,
            "velocity_reports": args.benchmarks, "gait_reports": args.gaits,
            "baseline_gait_report": args.baseline_gait, "noisy_report": args.noisy}
  output = Path(args.output)
  output.parent.mkdir(parents=True, exist_ok=True)
  output.write_text(json.dumps(result, indent=2) + "\n")
  print(json.dumps(result, indent=2))
  if failures:
    raise SystemExit(1)


if __name__ == "__main__":
  main()
