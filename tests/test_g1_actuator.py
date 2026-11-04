"""G1 fixed effort limits and protection against importing old DC dynamics."""

from types import SimpleNamespace

import pytest
import torch

from go2_supermimic import g1
from go2_supermimic.supermimic.train import Trainer


def test_g1_pd_retains_full_drive_and_braking_torque_at_high_speed():
  c = g1.RobotConsts(
    torch.zeros(29), torch.tensor([[-3., 3.]] * 29),
    torch.full((29,), 100.), torch.full((29,), 2.),
    torch.full((29,), 88.), torch.full((29,), 32.))
  state = torch.zeros(4, g1.STATE_DIM)
  state[:, g1.QD] = torch.tensor([0., 32., -32., 16.])[:, None]
  state[:, g1.Q] = torch.tensor([0., -1., 1., -1.])[:, None]
  action = torch.tensor([4., 4., -4., 4.])[:, None].expand(-1, 29).clone()
  torque = g1.motor_torque(state, action, c, g1.walk_task())
  torch.testing.assert_close(torque[:, 0], torch.tensor([88., 88., -88., 88.]))
  # At identical unsaturated PD demand, changing speed cannot change the cap.
  action = ((state[:, g1.Q] + (20. + c.kd * state[:, g1.QD]) / c.kp) / .25
            ).requires_grad_()
  torque = g1.motor_torque(state, action, c, g1.walk_task())
  torch.testing.assert_close(torque, torch.full_like(torque, 20.))
  torque.sum().backward()
  torch.testing.assert_close(action.grad, torch.full_like(action, 25.))


@pytest.mark.parametrize("model", [None, "g1_dc_pd_v1", "unknown"])
def test_g1_rejects_old_or_unknown_actuator_checkpoints(model):
  checkpoint = {} if model is None else {"actuator_model": model}
  with pytest.raises(ValueError, match="old DC dynamics"):
    g1.require_implicit_pd(checkpoint)


def test_g1_accepts_implicit_checkpoint():
  g1.require_implicit_pd({"actuator_model": g1.ACTUATOR_MODEL})


@pytest.mark.parametrize("operation", ["load", "warm_start"])
def test_g1_trainer_rejects_dc_world_model_before_loading_weights(tmp_path, operation):
  path = tmp_path / "old_dc.pt"
  torch.save({"format": "isaaclab_velocity_v2", "robot_kind": "g1"}, path)
  trainer = Trainer.__new__(Trainer)
  trainer.device = "cpu"
  trainer.env = SimpleNamespace(robot_kind="g1")
  with pytest.raises(ValueError, match="old DC dynamics"):
    getattr(trainer, operation)(path)
