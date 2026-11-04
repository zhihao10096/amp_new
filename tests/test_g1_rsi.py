"""RSI commands use the sampled frame and never widen the walk task."""

from dataclasses import asdict

import pytest
import torch

from go2_supermimic import g1
from go2_supermimic.supermimic.train import TrainCfg


def test_reference_command_uses_body_frame_velocities_and_clamps_every_axis():
  frames = torch.zeros(3, 71)
  frames[:, 6] = 1.  # xyzw frame representation
  frames[0, [5, 6]] = 2**-.5  # yaw +90deg
  frames[0, 36:39] = torch.tensor([0., .7, .4])
  frames[0, 39:42] = torch.tensor([0., 0., .5])
  frames[1, 36:39] = torch.tensor([3., -2., 0.])
  frames[1, 41] = -2.
  frames[2, 36:39] = torch.tensor([-2., 2., 0.])
  frames[2, 41] = 2.
  actual = g1.reference_commands(frames, g1.walk_task().commands)
  torch.testing.assert_close(
    actual, torch.tensor([[.7, 0., .5], [1.2, -.3, -.8], [0., .3, .8]]),
    atol=1e-6, rtol=1e-6)


def test_alignment_is_opt_in_and_configuration_roundtrips():
  assert not TrainCfg(task="G1-AMP-Flat").amp_reset_command_alignment
  enabled = TrainCfg(task="G1-AMP-Flat", amp_reset_command_alignment=True)
  assert TrainCfg(**asdict(enabled)).amp_reset_command_alignment
  for task in ("Go2-Velocity-Flat", "A1-AMP-Flat", "G1-Velocity-Flat"):
    with pytest.raises(ValueError, match="requires G1-AMP-Flat"):
      TrainCfg(task=task, amp_reset_command_alignment=True)


def test_evaluation_keeps_old_height_and_tilt_limits_even_without_native_termination():
  from go2_supermimic.g1_validation import evaluation_falls
  state = torch.zeros(4, g1.STATE_DIM)
  state[:, 0], state[:, 3] = .78, -1.
  state[0, 0] = .3
  state[1, 3] = -.4
  native = torch.tensor([False, False, False, True])
  assert not g1.terminated(state, g1.walk_task()).any()
  assert evaluation_falls(state, native).tolist() == [True, True, False, True]


def test_final_motion_audit_reconstructs_the_actual_history_and_bundled_data():
  from scripts.check_amp_convergence import expected_motion_metadata
  pair = expected_motion_metadata("g1", {"amp_num_frames": 2})
  history = expected_motion_metadata("g1", {"amp_num_frames": 4})
  assert "num_frames" not in pair
  assert history["num_frames"] == 4 and history["sequence_span_s"] == .06
  assert history["motions"] == pair["motions"]
  assert history["schema"] == pair["schema"] == g1.DEFAULT_AMP_FEATURE_SCHEMA
