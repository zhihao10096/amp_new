"""Native geometry, feature parity and differentiable control for feet AMP."""

import hashlib
import json
import pickle
from pathlib import Path

import torch

from go2_supermimic import g1
from go2_supermimic.g1_kinematics import KINEMATICS_METADATA, foot_positions

SCHEMA = "g1_amp_70_feet_v1"


def test_fk_matches_training_motion_body_positions_and_asset():
  assets = Path(g1.__file__).resolve().parents[1] / "assets"
  physics = assets / "robots/g1/configuration/g1_29dof_rev_1_0_physics.usd"
  assert hashlib.sha256(physics.read_bytes()).hexdigest() == KINEMATICS_METADATA["physics_sha256"]
  manifest = json.loads(g1.MANIFEST.read_text())
  names = manifest["key_body_names"]
  ids = [names.index(name) for name in KINEMATICS_METADATA["feet"]]
  for motion in manifest["motions"]:
    data = pickle.loads((g1.MANIFEST.parent / motion["file"]).read_bytes())
    n = int(len(data["dof_pos"]) * .8)
    q = torch.tensor(data["dof_pos"][:n])
    quat = torch.tensor(data["root_rot"][:n], dtype=q.dtype)
    root = torch.tensor(data["root_pos"][:n], dtype=q.dtype)
    actual = torch.tensor(data["key_body_pos"][:n], dtype=q.dtype)[:, ids]
    local = foot_positions(q)
    world = root[:, None, :] + g1.quat_apply(
      quat[:, None, :].expand(-1, 2, -1), local)
    torch.testing.assert_close(world, actual, atol=2e-6, rtol=2e-6)


def test_fk_gradient_and_batch_dimensions():
  torch.manual_seed(42)
  q = (torch.randn(2, 29, dtype=torch.float64) * .2).requires_grad_()
  assert torch.autograd.gradcheck(foot_positions, (q,))
  out = foot_positions(q)
  torch.testing.assert_close(foot_positions(q[0]), out[0])
  torch.testing.assert_close(foot_positions(q.reshape(1, 2, 29)), out[None])
  grad = torch.autograd.grad(out.square().sum(), q)[0]
  assert torch.isfinite(grad).all() and grad[:, :11].abs().sum() > 0


def test_feet_schema_parity_and_gradients():
  torch.manual_seed(42)
  library = g1.MotionLibrary(feature_schema=SCHEMA)
  frames = library.sample_frames(32)
  default = torch.randn(29)
  state = torch.zeros(32, 83)
  state[:, g1.Q] = frames[:, 7:36] - default
  state[:, g1.QD] = frames[:, 42:71]
  state[:, g1.V_B] = g1.quat_inverse_apply(frames[:, [6, 3, 4, 5]], frames[:, 36:39])
  state[:, g1.W_B] = g1.quat_inverse_apply(frames[:, [6, 3, 4, 5]], frames[:, 39:42])
  actual = g1.state_features(state, default, SCHEMA)
  torch.testing.assert_close(actual, g1.frame_features(frames, SCHEMA))
  torch.testing.assert_close(actual[:, :64],
                             g1.state_features(state, default, "g1_amp_64_velocity_v1"))
  assert library.metadata["kinematics"] == KINEMATICS_METADATA
  assert actual.shape == (32, 70)
  state.requires_grad_()
  feet = g1.state_features(state, default, SCHEMA)[:, -6:]
  grad = torch.autograd.grad(feet.square().sum(), state, retain_graph=True)[0]
  assert grad[:, g1.Q].abs().sum() > 0
  # FK features must not take the learned free foot-position channel as input.
  assert not grad[:, g1.FOOT_POS].any()
  disc = g1.AMPDiscriminator((16,), SCHEMA).requires_grad_(False)
  disc.reward(state, state + .01, default, torch.ones(32, 3)).sum().backward()
  assert torch.isfinite(state.grad).all() and state.grad.abs().sum() > 0
  for train in (True, False):
    a, b = library.sample_pairs(128, train=train)
    assert a.shape == b.shape == (128, 70)
    assert torch.isfinite(a).all() and torch.isfinite(b).all()
