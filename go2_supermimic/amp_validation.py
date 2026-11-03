"""Predeclared A1 AMP flat-walking suites; Go2 Manager criteria stay separate."""

from go2_supermimic.validation import _backend_failures, _bounded, _rmse_valid

A1_FIXED_CASES = (
  ("stand", (0., 0., 0.)), ("forward_slow", (.5, 0., 0.)),
  ("forward", (1., 0., 0.)), ("forward_fast", (1.5, 0., 0.)),
  ("left", (0., .3, 0.)), ("right", (0., -.3, 0.)),
  ("turn_left", (0., 0., .5)), ("turn_right", (0., 0., -.5)),
  ("mixed_left", (.8, .2, .5)), ("mixed_right", (.8, -.2, -.5)),
  ("upper_corner", (1.5, .3, 1.)), ("lower_corner", (1.5, -.3, -1.)),
)
A1_GAIT_CASES = (
  ("stand", (0., 0., 0.)), ("slow", (.5, 0., 0.)),
  ("forward", (1., 0., 0.)), ("fast", (1.5, 0., 0.)),
  ("left", (0., .3, 0.)), ("right", (0., -.3, 0.)), ("turn", (.8, 0., .5)),
)


def a1_velocity_failures(report: dict, noisy: bool = False) -> list[str]:
  failures = _backend_failures(report)
  for key, value in (("robot_kind", "a1"), ("seconds", 30), ("settle_seconds", 1),
                     ("environments", 96), ("observation_noise", noisy)):
    if report.get(key) != value:
      failures.append(key)
  cases = report.get("fixed", {}).get("cases", {})
  if report.get("fixed", {}).get("seed") != 42:
    failures.append("fixed/seed")
  if set(cases) != {name for name, _ in A1_FIXED_CASES}:
    failures.append("fixed/coverage")
  groups = []
  for name, command in A1_FIXED_CASES:
    case = cases.get(name, {})
    if tuple(case.get("command", ())) != command:
      failures.append(f"{name}/command")
    groups.append((name, case, (.1, .1, .1) if name == "stand" else (.3, .25, .25)))
  random = report.get("random", [])
  if sorted(r.get("seed", -1) for r in random) != [42, 123, 2026]:
    failures.append("random/coverage")
  groups += [(f"random/{r.get('seed')}", r.get("overall", {}), (.2, .15, .15)) for r in random]
  for name, group, limits in groups:
    if not _rmse_valid(group.get("rmse"), limits):
      failures.append(f"{name}/rmse")
    if group.get("falls") != 0:
      failures.append(f"{name}/falls")
    if not _bounded(group.get("samples_after_settling"), 1, float("inf")):
      failures.append(f"{name}/samples")
  return failures


def a1_gait_failures(report: dict, baseline: dict) -> list[str]:
  failures = _backend_failures(report)
  for key, value in (("robot_kind", "a1"), ("seconds", 20), ("repeats", 8), ("seed", 42)):
    if report.get(key) != value:
      failures.append(key)
  cases = report.get("cases", {})
  if (report.get("style_metric") != "a1_heldout_pairs_v1"
      or baseline.get("style_metric") != "a1_heldout_pairs_v1"
      or report.get("style_metric_seed") != 1701
      or baseline.get("style_metric_seed") != 1701
      or baseline.get("robot_kind") != "a1"
      or report.get("amp_motion_metadata") != baseline.get("amp_motion_metadata")
      or not report.get("amp_motion_metadata")):
    failures.append("style_metric_provenance")
  if set(cases) != {name for name, _ in A1_GAIT_CASES}:
    failures.append("case_coverage")
  for name, command in A1_GAIT_CASES:
    case = cases.get(name, {})
    if tuple(case.get("command", ())) != command:
      failures.append(f"{name}/command")
    if not _rmse_valid(case.get("rmse"), (.2, .15, .15)):
      failures.append(f"{name}/rmse")
    if case.get("falls") != 0:
      failures.append(f"{name}/falls")
  if not _bounded(cases.get("stand", {}).get("stride_hz_per_foot"), 0, .3, strict=True):
    failures.append("stand/frequency")
  for name in ("forward", "fast"):
    case = cases.get(name, {})
    for key, low, high, strict in (
      ("stride_hz_per_foot", 0, 4.5, False), ("mean_air_time_s", .1, float("inf"), False),
      ("mean_swing_clearance_m", .012, float("inf"), False),
      ("short_swing_fraction", 0, .5, True), ("stance_slide_m_s", 0, .15, True),
    ):
      if not _bounded(case.get(key), low, high, strict):
        failures.append(f"{name}/{key}")
    reference = baseline.get("style_distance", {}).get(name)
    value = report.get("style_distance", {}).get(name)
    if not (_bounded(reference, 1e-12, float("inf"))
            and _bounded(value, 0, .9 * reference)):
      failures.append(f"{name}/heldout_style_improvement")
  return failures
