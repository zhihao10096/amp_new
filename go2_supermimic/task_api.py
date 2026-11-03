"""Select simulator-independent robot interfaces without mutable global layouts."""

from go2_supermimic import velocity


def task_api(robot_kind: str):
  if robot_kind == "g1":
    from go2_supermimic import g1
    return g1
  if robot_kind not in ("go2", "a1"):
    raise ValueError(f"unsupported robot: {robot_kind}")
  return velocity


def amp_api(robot_kind: str):
  if robot_kind == "g1":
    from go2_supermimic import g1
    return g1
  from go2_supermimic import amp
  return amp
