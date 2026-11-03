from copy import deepcopy

from go2_supermimic.validation import (
  FIXED_CASES, GAIT_CASES, MANAGER_BACKEND, SEEDS,
  convergence_failures, gait_failures, velocity_failures,
)


def reports():
  group = {"rmse": [.02, .02, .02], "falls_per_minute": 0.,
           "samples_after_settling": 10000}
  velocity, gait = [], []
  for iteration in (3000, 4000, 5000):
    metadata = {"iteration": iteration, "checkpoint": f"model_{iteration}.pt",
                "environment_backend": MANAGER_BACKEND, "checkpoint_backend": MANAGER_BACKEND}
    velocity.append({
      **metadata, "seconds": 30, "settle_seconds": 1, "environments": 160,
      "observation_noise": False,
      "fixed": {"seed": 42, "overall": deepcopy(group),
                "cases": {name: {**deepcopy(group), "command": list(cmd)}
                          for name, cmd in FIXED_CASES}},
      "random": [{"seed": seed, "overall": deepcopy(group)} for seed in SEEDS],
    })
    gait.append({
      **metadata, "seconds": 20, "repeats": 8, "seed": 42,
      "cases": {name: {
        "command": list(cmd), "rmse": [.02, .02, .02], "falls": 0,
        "stride_hz_per_foot": .1 if name == "stand" else 2.5,
        "mean_air_time_s": .15, "mean_swing_clearance_m": .02,
        "short_swing_fraction": .1, "stance_slide_m_s": .05,
      } for name, cmd in GAIT_CASES},
    })
  noisy = deepcopy(velocity[-1])
  noisy["observation_noise"] = True
  return velocity, gait, noisy


def test_complete_three_checkpoint_run_meets_all_gates():
  velocity, gait, noisy = reports()
  assert convergence_failures(velocity, gait, noisy) == []


def test_empty_or_partial_coverage_cannot_prove_convergence():
  assert convergence_failures([], [], {}) == ["require_three_velocity_and_gait_checkpoints"]
  velocity, _, _ = reports()
  del velocity[0]["fixed"]["cases"]["upper_corner"]
  velocity[0]["random"].pop()
  failures = velocity_failures(velocity[0])
  assert "fixed/case_coverage" in failures and "random/seed_coverage" in failures


def test_wrong_commands_and_no_valid_samples_are_rejected():
  velocity, _, _ = reports()
  velocity[0]["fixed"]["cases"]["forward"]["command"] = [0, 0, 0]
  velocity[0]["random"][0]["overall"]["samples_after_settling"] = 0
  failures = velocity_failures(velocity[0])
  assert "fixed/forward/command" in failures
  assert "random/42/samples" in failures


def test_nonfinite_metrics_and_short_shuffling_fail_gait_gate():
  _, gait, _ = reports()
  gait[0]["cases"]["fast"]["mean_air_time_s"] = .09
  gait[0]["cases"]["forward"]["stance_slide_m_s"] = float("nan")
  failures = gait_failures(gait[0])
  assert "fast/mean_air_time_s" in failures
  assert "forward/stance_slide_m_s" in failures


def test_old_backend_and_unpaired_checkpoint_evidence_are_rejected():
  velocity, gait, noisy = reports()
  velocity[0]["checkpoint_backend"] = "legacy_direct"
  gait[0]["checkpoint"] = "different_model.pt"
  failures = convergence_failures(velocity, gait, noisy)
  assert "3000/velocity/checkpoint_backend" in failures
  assert "3000/gait_checkpoint" in failures


def test_nonconsecutive_and_duplicate_checkpoints_are_not_convergence():
  velocity, gait, noisy = reports()
  velocity[1]["iteration"] = 4500
  velocity[1]["checkpoint"] = velocity[0]["checkpoint"]
  failures = convergence_failures(velocity, gait, noisy)
  assert "checkpoint_spacing" in failures and "distinct_checkpoints" in failures


def test_noisy_final_evidence_must_match_last_checkpoint_and_enable_noise():
  velocity, gait, noisy = reports()
  noisy["checkpoint"] = velocity[0]["checkpoint"]
  noisy["observation_noise"] = False
  failures = convergence_failures(velocity, gait, noisy)
  assert "noisy/final_checkpoint" in failures
  assert "noisy/observation_noise" in failures
