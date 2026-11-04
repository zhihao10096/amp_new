"""Differentiable G1 ankle-link origins in pelvis coordinates, in meters.

Geometry comes from assets/robots/g1/configuration/g1_29dof_rev_1_0_physics.usd.
Its SHA256 and the feature convention are recorded in AMP checkpoint metadata.
Both legs are evaluated together; no simulator or USD import is needed.
"""

from __future__ import annotations

import torch

KINEMATICS_METADATA = {
  "schema": "g1_usd_ankle_origins_v1",
  "physics_sha256": "cde4ff0378183e4e2063df1fdcad4060df8247eaf1da777f45e2adea0b6dde22",
  "frame": "pelvis",
  "units": "meters",
  "feet": ["left_ankle_roll_link", "right_ankle_roll_link"],
}
LEG_INDICES = ((0, 1), (3, 4), (6, 7), (9, 10), (13, 14), (17, 18))
LEG_NAMES = ("hip_pitch", "hip_roll", "hip_yaw", "knee", "ankle_pitch", "ankle_roll")
_OFFSETS = (
  ((0., .06445199996232986, -.10270000249147415),
   (0., -.06445199996232986, -.10270000249147415)),
  ((0., .052000001072883606, -.03046499937772751),
   (0., -.052000001072883606, -.03046499937772751)),
  ((.025001000612974167, 0., -.12411999702453613),) * 2,
  ((-.0782729983329773, .0021488999482244253, -.17734000086784363),
   (-.0782729983329773, -.0021488999482244253, -.17734000086784363)),
  ((0., -9.444500028621405e-05, -.30000999569892883),
   (0., 9.444500028621405e-05, -.30000999569892883)),
  ((0., 0., -.01755799911916256),) * 2,
)
_JOINT_AXES = ("Y", "X", "Z", "Y", "Y")
_TILT_W, _TILT_Y = .9961786866188049, .08733857423067093
_TILT_COS = (_TILT_W ** 2 - _TILT_Y ** 2) / (_TILT_W ** 2 + _TILT_Y ** 2)
_TILT_SIN = 2 * _TILT_W * _TILT_Y / (_TILT_W ** 2 + _TILT_Y ** 2)


def _rotate_basis(x: torch.Tensor, y: torch.Tensor, z: torch.Tensor,
                  cosine: torch.Tensor | float, sine: torch.Tensor | float,
                  axis: str) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
  """Right-multiply a rotation's columns by a local axis rotation."""
  if axis == "X":
    return x, cosine * y + sine * z, -sine * y + cosine * z
  if axis == "Y":
    return cosine * x - sine * z, y, sine * x + cosine * z
  return cosine * x + sine * y, -sine * x + cosine * y, z


def foot_positions(q: torch.Tensor) -> torch.Tensor:
  """Absolute Lab-order 29 joint angles -> [..., left/right, xyz].

  All USD child anchors are zero and child-frame rotations are identity.
  The ankle-roll angle changes orientation, not the ankle-roll link origin.
  The state default pose must therefore be added before calling this function.
  """
  # Avoid indexing broadcast constant tensors: PyTorch 2.5.1 Inductor can
  # generate invalid Triton broadcast_to(constexpr, ...) for that expression.
  one = torch.ones_like(q[..., :1])
  side = torch.stack((one, -one), -2)
  one = torch.ones_like(side)
  zero = torch.zeros_like(one)
  x = torch.cat((one, zero, zero), -1)
  y = torch.cat((zero, one, zero), -1)
  z = torch.cat((zero, zero, one), -1)
  position = torch.zeros_like(x)
  for i in range(6):
    # The legs mirror y offsets; all x/z offsets are identical.
    dx, dy, dz = _OFFSETS[i][0]
    position = position + dx * x + dy * side * y + dz * z
    if i < 5:
      if i in (1, 3):
        sine = -_TILT_SIN if i == 1 else _TILT_SIN
        x, y, z = _rotate_basis(x, y, z, _TILT_COS, sine, "Y")
      left, right = LEG_INDICES[i]
      angle = torch.stack((q[..., left], q[..., right]), -1)[..., None]
      x, y, z = _rotate_basis(x, y, z, angle.cos(), angle.sin(), _JOINT_AXES[i])
  return position
