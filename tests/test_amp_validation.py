from copy import deepcopy

from go2_supermimic.amp_validation import (
  A1_FIXED_CASES, A1_GAIT_CASES, a1_convergence_failures, a1_gait_failures,
)
from go2_supermimic.validation import MANAGER_BACKEND


def reports():
  common = {"robot_kind": "a1", "environment_backend": MANAGER_BACKEND,
            "checkpoint_backend": MANAGER_BACKEND}
  metric = {"style_metric": "a1_heldout_pairs_v1", "style_metric_seed": 1701,
            "amp_motion_metadata": {"schema": "a1_amp_43_v1", "motions": ["test"]}}
  baseline = {**common, **metric, "checkpoint": "model_0.pt", "iteration": 0,
              "seconds": 20, "repeats": 8, "seed": 42,
              "style_distance": {"forward": 1., "fast": 1.}}
  velocity, gait = [], []
  for iteration in (3000, 4000, 5000):
    identity = {**common, "checkpoint": f"model_{iteration}.pt", "iteration": iteration}
    group = {"rmse": [.02, .02, .02], "falls": 0, "samples_after_settling": 1000}
    velocity.append({
      **identity, "seconds": 30, "settle_seconds": 1, "environments": 96,
      "observation_noise": False,
      "fixed": {"seed": 42, "cases": {name: dict(group, command=list(cmd))
                                     for name, cmd in A1_FIXED_CASES}},
      "random": [{"seed": seed, "overall": dict(group)} for seed in (42, 123, 2026)],
    })
    gait.append({
      **identity, **deepcopy(metric), "seconds": 20, "repeats": 8, "seed": 42,
      "style_distance": {"forward": .8, "fast": .8},
      "cases": {name: {
        "command": list(cmd), "rmse": [.02, .02, .02], "falls": 0,
        "stride_hz_per_foot": .1 if name == "stand" else 3.,
        "mean_air_time_s": .15, "mean_swing_clearance_m": .02,
        "short_swing_fraction": .1, "stance_slide_m_s": .08,
      } for name, cmd in A1_GAIT_CASES},
    })
  noisy = dict(deepcopy(velocity[-1]), observation_noise=True)
  return velocity, gait, noisy, baseline


def test_complete_a1_run_requires_three_spaced_models_and_initial_style_baseline():
  velocity, gait, noisy, baseline = reports()
  assert not a1_convergence_failures(velocity, gait, noisy, baseline)
  baseline["iteration"] = 1000
  assert "baseline/iteration" in a1_convergence_failures(velocity, gait, noisy, baseline)
  velocity[1]["iteration"] = 3500
  assert "checkpoint_spacing" in a1_convergence_failures(velocity, gait, noisy, baseline)
  assert a1_convergence_failures([], [], {}, {}) == [
    "require_three_velocity_and_gait_checkpoints"]


def test_a1_style_gate_requires_both_speeds_and_matching_expert_holdout():
  _, gait, _, baseline = reports()
  gait[0]["style_distance"]["fast"] = .91
  assert "fast/heldout_style_improvement" in a1_gait_failures(gait[0], baseline)
  gait[0]["amp_motion_metadata"]["motions"] = ["different_split"]
  assert "style_metric_provenance" in a1_gait_failures(gait[0], baseline)


def test_a1_gates_reject_falls_missing_pairs_wrong_noise_and_poor_gait():
  velocity, gait, noisy, baseline = reports()
  gait[0]["cases"]["fast"]["mean_air_time_s"] = .09
  gait[0]["cases"]["left"]["falls"] = 1
  gait[1]["checkpoint"] = "unpaired.pt"
  noisy["observation_noise"] = False
  failures = a1_convergence_failures(velocity, gait, noisy, baseline)
  assert "3000/gait/fast/mean_air_time_s" in failures
  assert "3000/gait/left/falls" in failures
  assert "4000/gait_checkpoint" in failures
  assert "noisy/observation_noise" in failures
