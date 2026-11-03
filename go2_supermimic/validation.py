"""Simulator-free acceptance checks for complete manager environment reports."""

import math

MANAGER_BACKEND = "isaaclab_manager_based_v1"
FIXED_CASES = (
  ("stand", (0., 0., 0.)),
  ("forward_slow", (.5, 0., 0.)), ("forward", (1., 0., 0.)),
  ("forward_fast", (1.5, 0., 0.)),
  ("backward_slow", (-.5, 0., 0.)), ("backward", (-1., 0., 0.)),
  ("left_slow", (0., .3, 0.)), ("right_slow", (0., -.3, 0.)),
  ("left", (0., .6, 0.)), ("right", (0., -.6, 0.)),
  ("turn_left_slow", (0., 0., .5)), ("turn_right_slow", (0., 0., -.5)),
  ("turn_left", (0., 0., 1.)), ("turn_right", (0., 0., -1.)),
  ("mixed_left", (.8, .3, .5)), ("mixed_right", (.8, -.3, -.5)),
  ("mixed_backward_left", (-.7, .3, .5)),
  ("mixed_backward_right", (-.7, -.3, -.5)),
  ("upper_corner", (1.5, .6, 1.)), ("lower_corner", (-1., -.6, -1.)),
)
GAIT_CASES = (
  ("stand", (0., 0., 0.)), ("slow", (.5, 0., 0.)), ("forward", (1., 0., 0.)),
  ("fast", (1.5, 0., 0.)), ("backward", (-.7, 0., 0.)),
  ("left", (0., .4, 0.)), ("turn", (.8, 0., .5)),
)
SEEDS = (42, 123, 2026)


def _bounded(value, low, high, strict=False):
  return (isinstance(value, (float, int)) and math.isfinite(value)
          and low <= value and (value < high if strict else value <= high))


def _rmse_valid(values, limits):
  return (isinstance(values, (list, tuple)) and len(values) == 3
          and all(_bounded(e, 0, t) for e, t in zip(values, limits)))


def _backend_failures(report):
  return [key for key in ("environment_backend", "checkpoint_backend")
          if report.get(key) != MANAGER_BACKEND]


def velocity_failures(report: dict, noisy: bool = False) -> list[str]:
  failures = _backend_failures(report)
  for key, expected in (("seconds", 30), ("settle_seconds", 1),
                        ("environments", 160), ("observation_noise", noisy)):
    if report.get(key) != expected:
      failures.append(key)
  fixed = report.get("fixed", {})
  if fixed.get("seed") != 42:
    failures.append("fixed/seed")
  cases = fixed.get("cases", {})
  if set(cases) != {name for name, _ in FIXED_CASES}:
    failures.append("fixed/case_coverage")
  groups = [("fixed/overall", fixed.get("overall", {}), None, .1)]
  for name, command in FIXED_CASES:
    case = cases.get(name, {})
    if tuple(case.get("command", ())) != command:
      failures.append(f"fixed/{name}/command")
    limits = (.1, .1, .1) if name == "stand" else (.3, .25, .25)
    groups.append((f"fixed/{name}", case, limits, .5))
  random = report.get("random", [])
  if sorted(r.get("seed", -1) for r in random) != sorted(SEEDS):
    failures.append("random/seed_coverage")
  for item in random:
    groups.append((f"random/{item.get('seed')}", item.get("overall", {}), (.2, .15, .15), .1))
  for name, group, limits, fall_limit in groups:
    if not _rmse_valid(group.get("rmse"), limits or (float("inf"),) * 3):
      failures.append(f"{name}/rmse")
    if not _bounded(group.get("falls_per_minute"), 0, fall_limit):
      failures.append(f"{name}/falls")
    if not _bounded(group.get("samples_after_settling"), 1, float("inf")):
      failures.append(f"{name}/samples")
  return failures


def gait_failures(report: dict) -> list[str]:
  failures = _backend_failures(report)
  for key, expected in (("seconds", 20), ("repeats", 8), ("seed", 42)):
    if report.get(key) != expected:
      failures.append(key)
  cases = report.get("cases", {})
  if set(cases) != {name for name, _ in GAIT_CASES}:
    failures.append("case_coverage")
  for name, command in GAIT_CASES:
    case = cases.get(name, {})
    if tuple(case.get("command", ())) != command:
      failures.append(f"{name}/command")
    if not _rmse_valid(case.get("rmse"), (.2, .15, .15)):
      failures.append(f"{name}/rmse")
    if case.get("falls") != 0:
      failures.append(f"{name}/falls")
  if not _bounded(cases.get("stand", {}).get("stride_hz_per_foot"), 0, .3, strict=True):
    failures.append("stand/frequency")
  for name, original_hz in (("forward", 6.040898314014752), ("fast", 8.713119072708114)):
    case = cases.get(name, {})
    for metric, low, high, strict in (
      ("stride_hz_per_foot", 0, .7 * original_hz, False),
      ("mean_air_time_s", .1, float("inf"), False),
      ("mean_swing_clearance_m", .012, float("inf"), False),
      ("short_swing_fraction", 0, .5, True),
      ("stance_slide_m_s", 0, .15, True),
    ):
      if not _bounded(case.get(metric), low, high, strict):
        failures.append(f"{name}/{metric}")
  return failures


def convergence_failures(velocity: list[dict], gait: list[dict], noisy: dict) -> list[str]:
  """Require a complete, ordered three-checkpoint run and matching final noise test."""
  failures = []
  if len(velocity) != 3 or len(gait) != 3:
    return ["require_three_velocity_and_gait_checkpoints"]
  velocity = sorted(velocity, key=lambda r: r.get("iteration", -1))
  gait_by_path = {r.get("checkpoint"): r for r in gait}
  iterations = [r.get("iteration", -1) for r in velocity]
  if iterations[0] <= 0 or any(b - a != 1000 for a, b in zip(iterations, iterations[1:])):
    failures.append("checkpoint_spacing")
  if len(gait_by_path) != 3 or len({r.get("checkpoint") for r in velocity}) != 3:
    failures.append("distinct_checkpoints")
  for report in velocity:
    prefix = str(report.get("iteration"))
    failures.extend(f"{prefix}/velocity/{f}" for f in velocity_failures(report))
    paired = gait_by_path.get(report.get("checkpoint"), {})
    if paired.get("iteration") != report.get("iteration"):
      failures.append(f"{prefix}/gait_checkpoint")
    failures.extend(f"{prefix}/gait/{f}" for f in gait_failures(paired))
  if (noisy.get("checkpoint") != velocity[-1].get("checkpoint")
      or noisy.get("iteration") != iterations[-1]):
    failures.append("noisy/final_checkpoint")
  failures.extend(f"noisy/{f}" for f in velocity_failures(noisy, noisy=True))
  return failures
