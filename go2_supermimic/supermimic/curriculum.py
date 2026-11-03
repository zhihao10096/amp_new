"""Gradually introduce gait regularization after learning basic locomotion."""

from dataclasses import replace

from go2_supermimic.velocity import VelocityTaskCfg

# The initial velocity task uses weak motion penalties. The final task and
# acceptance thresholds remain unchanged; only training rewards are scheduled.
INITIAL_WEIGHTS = {
  "orientation": -1.0,
  "base_height": -10.0,
  "joint_deviation": -0.05,
  "action_rate": -0.01,
  "joint_torque": -2e-5,
  "joint_velocity": 0.0,
  "energy": 0.0,
  "joint_limits": -1.0,
  "feet_air_time": 0.0,
  "air_time_variance": 0.0,
  "feet_slide": 0.0,
  "undesired_contacts": 0.0,
  "feet_clearance": 0.0,
  "feet_contact_without_command": 0.0,
  "gait_duration": 0.0,
  "diagonal_gait": 0.0,
}


def restore_curriculum_options(values: dict, saved: dict, arguments: list[str]) -> dict:
  """Inherit the saved schedule unless the caller explicitly overrides it."""
  result = dict(values)
  supplied = {arg.split("=", 1)[0] for arg in arguments}
  for name in ("reward_curriculum_start", "reward_curriculum_end"):
    if "--" + name.replace("_", "-") not in supplied:
      result[name] = saved.get(name, result[name])
  return result


def curriculum_fraction(iteration: int, start: int, end: int) -> float:
  if end == 0 or iteration >= end:
    return 1.0
  return min(1.0, max(0.0, (iteration - start) / max(1, end - start)))


def training_task(target: VelocityTaskCfg, fraction: float) -> VelocityTaskCfg:
  """Return independent training weights without modifying checkpoint settings."""
  if fraction == 1:
    return replace(target, rewards=replace(target.rewards))
  weights = {
    name: initial + fraction * (getattr(target.rewards, name) - initial)
    for name, initial in INITIAL_WEIGHTS.items()
  }
  return replace(
    target, rewards=replace(target.rewards, **weights),
    joint_deviation_gait_fraction=fraction * target.joint_deviation_gait_fraction)
