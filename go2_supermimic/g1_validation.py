"""Independent G1 walk suites, recorded before formal training."""

from go2_supermimic.validation import _backend_failures, _bounded, _rmse_valid

G1_FIXED_CASES = (
  ("stand", (0., 0., 0.)), ("forward_slow", (.3, 0., 0.)),
  ("forward", (.6, 0., 0.)), ("forward_fast", (1., 0., 0.)),
  ("left", (0., .3, 0.)), ("right", (0., -.3, 0.)),
  ("turn_left", (0., 0., .5)), ("turn_right", (0., 0., -.5)),
  ("mixed_left", (.6, .2, .5)), ("mixed_right", (.6, -.2, -.5)),
  ("upper_corner", (1.2, .3, .8)), ("lower_corner", (1.2, -.3, -.8)),
)
G1_GAIT_CASES = (
  ("stand", (0., 0., 0.)), ("slow", (.3, 0., 0.)),
  ("forward", (.6, 0., 0.)), ("fast", (1., 0., 0.)),
  ("left", (0., .3, 0.)), ("right", (0., -.3, 0.)), ("turn", (.6, 0., .5)),
)


def g1_velocity_failures(report: dict, noisy: bool = False) -> list[str]:
  failures = _backend_failures(report)
  for key, value in (("robot_kind", "g1"), ("seconds", 30), ("settle_seconds", 1),
                     ("environments", 96), ("observation_noise", noisy)):
    if report.get(key) != value:
      failures.append(key)
  cases = report.get("fixed", {}).get("cases", {})
  if set(cases) != {name for name, _ in G1_FIXED_CASES}:
    failures.append("fixed/coverage")
  if report.get("fixed", {}).get("seed") != 42:
    failures.append("fixed/seed")
  groups = []
  for name, command in G1_FIXED_CASES:
    case = cases.get(name, {})
    if tuple(case.get("command", ())) != command:
      failures.append(f"{name}/command")
    groups.append((name, case, (.1, .1, .1) if name == "stand" else (.3, .25, .3)))
  random = report.get("random", [])
  if sorted(r.get("seed", -1) for r in random) != [42, 123, 2026]:
    failures.append("random/coverage")
  groups += [(f"random/{r.get('seed')}", r.get("overall", {}), (.25, .18, .2)) for r in random]
  for name, group, limits in groups:
    if not _rmse_valid(group.get("rmse"), limits):
      failures.append(f"{name}/rmse")
    if group.get("falls") != 0:
      failures.append(f"{name}/falls")
    if not _bounded(group.get("samples_after_settling"), 1, float("inf")):
      failures.append(f"{name}/samples")
    if not _bounded(group.get("flight_fraction"), 0, .02):
      failures.append(f"{name}/flight")
  return failures


def g1_gait_failures(report: dict, baseline: dict) -> list[str]:
  failures = _backend_failures(report)
  for key, value in (("robot_kind", "g1"), ("seconds", 20), ("repeats", 8), ("seed", 42)):
    if report.get(key) != value:
      failures.append(key)
  if (report.get("style_metric") != "g1_heldout_pairs_v1"
      or baseline.get("style_metric") != "g1_heldout_pairs_v1"
      or report.get("style_metric_seed") != 1701
      or baseline.get("style_metric_seed") != 1701
      or baseline.get("robot_kind") != "g1"
      or not report.get("amp_motion_metadata")
      or report.get("amp_motion_metadata") != baseline.get("amp_motion_metadata")):
    failures.append("style_metric_provenance")
  cases = report.get("cases", {})
  if set(cases) != {name for name, _ in G1_GAIT_CASES}:
    failures.append("case_coverage")
  for name, command in G1_GAIT_CASES:
    case = cases.get(name, {})
    if tuple(case.get("command", ())) != command:
      failures.append(f"{name}/command")
    if not _rmse_valid(case.get("rmse"), (.25, .18, .2)):
      failures.append(f"{name}/rmse")
    if case.get("falls") != 0:
      failures.append(f"{name}/falls")
    if not _bounded(case.get("mean_base_height_m"), .65, 1.2):
      failures.append(f"{name}/height")
  if not _bounded(cases.get("stand", {}).get("stride_hz_per_foot"), 0, .3, strict=True):
    failures.append("stand/frequency")
  for name in ("forward", "fast"):
    case = cases.get(name, {})
    for key, low, high, strict in (
      ("stride_hz_per_foot", .5, 2.5, False), ("mean_air_time_s", .15, .6, False),
      ("mean_swing_clearance_m", .015, float("inf"), False),
      ("short_swing_fraction", 0, .3, True), ("stance_slide_m_s", 0, .2, True),
      ("flight_fraction", 0, .02, False), ("front_contact_alternation", .4, 1., False),
    ):
      if not _bounded(case.get(key), low, high, strict):
        failures.append(f"{name}/{key}")
    initial = baseline.get("style_distance", {}).get(name)
    value = report.get("style_distance", {}).get(name)
    if not (_bounded(initial, 1e-12, float("inf")) and _bounded(value, 0, .9 * initial)):
      failures.append(f"{name}/heldout_style_improvement")
  return failures


def g1_convergence_failures(velocity: list[dict], gait: list[dict],
                            noisy: dict, baseline: dict) -> list[str]:
  failures = []
  if len(velocity) != 3 or len(gait) != 3:
    return ["require_three_velocity_and_gait_checkpoints"]
  for key, expected in (("iteration", 0), ("robot_kind", "g1"), ("seconds", 20),
                        ("repeats", 8), ("seed", 42)):
    if baseline.get(key) != expected:
      failures.append(f"baseline/{key}")
  failures.extend(f"baseline/{key}" for key in _backend_failures(baseline))
  velocity = sorted(velocity, key=lambda r: r.get("iteration", -1))
  iterations = [r.get("iteration", -1) for r in velocity]
  if iterations[0] <= 0 or any(b - a != 1000 for a, b in zip(iterations, iterations[1:])):
    failures.append("checkpoint_spacing")
  by_path = {r.get("checkpoint"): r for r in gait}
  paths = {r.get("checkpoint") for r in velocity}
  if len(paths) != 3 or len(by_path) != 3 or baseline.get("checkpoint") in paths:
    failures.append("distinct_checkpoints")
  for report in velocity:
    prefix = str(report.get("iteration"))
    failures.extend(f"{prefix}/velocity/{f}" for f in g1_velocity_failures(report))
    paired = by_path.get(report.get("checkpoint"), {})
    if paired.get("iteration") != report.get("iteration"):
      failures.append(f"{prefix}/gait_checkpoint")
    failures.extend(f"{prefix}/gait/{f}" for f in g1_gait_failures(paired, baseline))
  if noisy.get("checkpoint") != velocity[-1].get("checkpoint") or noisy.get("iteration") != iterations[-1]:
    failures.append("noisy/final_checkpoint")
  failures.extend(f"noisy/{f}" for f in g1_velocity_failures(noisy, noisy=True))
  return failures
