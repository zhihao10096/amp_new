"""Upstream torso termination must agree at native and imagined boundaries."""

from dataclasses import asdict

import pytest
import torch

from go2_supermimic import g1
from go2_supermimic.supermimic.train import task_from_dict


def states():
  s = torch.zeros(6, g1.STATE_DIM)
  s[:, 0], s[:, 3] = .78, -1.
  s[0, 0] = .199
  s[1, 0] = .2
  s[2, g1.BASE_CONTACT] = 1.
  s[3, g1.UNDESIRED_CONTACT] = 8.  # arm contact is a soft reward penalty
  s[4, g1.GRAV] = torch.tensor([1., 0., 0.])  # tilt alone is not a fall
  s[5, 0] = .3
  return s


def test_upstream_height_contact_and_tilt_have_independent_meaning():
  task, s = g1.walk_task(), states()
  assert task.minimum_height == .2 and task.termination_profile == g1.TERMINATION_PROFILE
  assert g1.terminated(s, task).tolist() == [True, False, True, False, False, False]
  assert g1.terminated(s, g1.legacy_walk_task()).tolist() == [
    True, True, False, False, True, True]
  assert asdict(task_from_dict(asdict(task))) == asdict(task)
  old = asdict(g1.legacy_walk_task())
  del old["termination_profile"]
  assert task_from_dict(old).termination_profile == "height_tilt"


def test_contact_and_height_relaxation_preserve_their_gradients_and_ignore_arm_contact():
  s = states().requires_grad_()
  probability = g1.termination_probability(s, g1.walk_task())
  assert probability[0] > .5 and probability[2] > .999
  assert probability[3:5].max() < 1e-4
  assert probability[5] < .002  # 0.3 m remains inside the height relaxation tail
  probability.sum().backward()
  assert torch.isfinite(s.grad).all()
  assert s.grad[0, 0] < 0 and s.grad[0, g1.BASE_CONTACT] > 0
  assert not s.grad[:, g1.UNDESIRED_CONTACT].any()
  assert not s.grad[:, g1.GRAV].any()


@pytest.mark.parametrize("schema,dim", [(None, 83), (g1.STATE_SCHEMA, 83), ("invalid", 84)])
def test_training_rejects_missing_or_inconsistent_contact_state(schema, dim):
  checkpoint = {"actuator_model": g1.ACTUATOR_MODEL, "state_schema": schema,
                "world_model": {"out_norm.mean": torch.zeros(dim)}}
  with pytest.raises(ValueError, match="old 83-dimensional dynamics"):
    g1.require_trainable_state(checkpoint)


def test_new_schema_is_trainable_and_actor_feature_interface_is_unchanged():
  g1.require_trainable_state({
    "actuator_model": g1.ACTUATOR_MODEL, "state_schema": g1.STATE_SCHEMA,
    "world_model": {"out_norm.mean": torch.zeros(g1.STATE_DIM)}})
  s = states()
  for schema in g1.AMP_FEATURE_DIMS:
    torch.testing.assert_close(
      g1.state_features(s, torch.zeros(29), schema),
      g1.state_features(s[:, :83], torch.zeros(29), schema))
