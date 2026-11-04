"""G1 conventions and temporal isolation, exercised without Isaac Lab."""

import hashlib
import json
import pickle
from dataclasses import asdict, replace

import torch

from go2_supermimic import g1
from go2_supermimic.supermimic.buffer import ReplayBuffer
from go2_supermimic.supermimic.imagine import ImagineCfg, Imagination
from go2_supermimic.supermimic.train import Actor, Critic, task_from_dict
from go2_supermimic.supermimic.world_model import WorldModel


def test_bundled_walk_data_and_temporal_support():
  library = g1.MotionLibrary()
  assert len(library.metadata["motions"]) == 7
  for train in (True, False):
    ids, t = library.sample_times(4096, train)
    low = (t / library.durations[ids]).floor().long()
    high = ((t + library.dt) / library.durations[ids]).ceil().long()
    assert (low >= (0 if train else library.splits[ids])).all()
    assert (high < (library.splits[ids] if train else library.sizes[ids])).all()
    a, b = library.sample_pairs(256, train)
    assert a.shape == b.shape == (256, 61)
    assert torch.isfinite(a).all() and torch.isfinite(b).all()


def test_derivatives_do_not_leak_holdout_and_wxyz_is_correct(tmp_path):
  # A 90-degree yaw: world +y velocity must become body +x.
  n, dt = 20, .1
  quat = torch.tensor([2**-.5, 0., 0., 2**-.5]).expand(n, -1)
  pos = torch.zeros(n, 3)
  pos[:, 1] = torch.arange(n) * dt
  q = torch.arange(n)[:, None].expand(-1, 29) * .01
  filename = "Walk_B_fixture.pkl"
  def write(pos):
    raw = pickle.dumps({"fps": 1/dt, "root_pos": pos.numpy(), "root_rot": quat.numpy(),
                        "dof_pos": q.numpy()})
    (tmp_path / filename).write_bytes(raw)
    (tmp_path / "manifest.json").write_text(json.dumps({
      "joint_names": list(range(29)), "source_commit": "fixture",
      "motions": [{"file": filename, "sha256": hashlib.sha256(raw).hexdigest(), "weight": 1.}]}))
    return g1.MotionLibrary(str(tmp_path), train_fraction=.5)
  original = write(pos)
  modified_pos = pos.clone()
  modified_pos[10:] += 1000
  modified = write(modified_pos)
  torch.testing.assert_close(original.frames[:10], modified.frames[:10])
  f = original.frames[:1]
  body_velocity = g1.quat_inverse_apply(f[:, [6, 3, 4, 5]], f[:, 36:39])
  torch.testing.assert_close(body_velocity, torch.tensor([[1., 0., 0.]]), atol=1e-6, rtol=1e-6)
  torch.testing.assert_close(g1.frame_features(f)[:, 32:], torch.full((1, 29), .1))


def test_features_match_expert_and_amp_preserves_state_gradient():
  library = g1.MotionLibrary()
  f = library.sample_frames(32)
  default = torch.randn(29)
  s = torch.zeros(32, 83)
  s[:, g1.Q], s[:, g1.QD] = f[:, 7:36] - default, f[:, 42:71]
  s[:, g1.W_B] = g1.quat_inverse_apply(f[:, [6, 3, 4, 5]], f[:, 39:42])
  torch.testing.assert_close(g1.state_features(s, default), g1.frame_features(f))
  s.requires_grad_()
  disc = g1.AMPDiscriminator((16,)).requires_grad_(False)
  disc.reward(s, s + .01, default, torch.ones(32, 3)).mean().backward()
  assert torch.isfinite(s.grad).all() and s.grad.abs().sum() > 0
  assert not disc.reward(s, s, default, torch.zeros(32, 3)).any()



def test_velocity_feature_schema_matches_expert_and_changes_dimension():
  library = g1.MotionLibrary(feature_schema="g1_amp_64_velocity_v1")
  f = library.sample_frames(32)
  default = torch.randn(29)
  s = torch.zeros(32, 83)
  s[:, g1.Q], s[:, g1.QD] = f[:, 7:36] - default, f[:, 42:71]
  s[:, g1.V_B] = g1.quat_inverse_apply(f[:, [6, 3, 4, 5]], f[:, 36:39])
  s[:, g1.W_B] = g1.quat_inverse_apply(f[:, [6, 3, 4, 5]], f[:, 39:42])
  torch.testing.assert_close(
    g1.state_features(s, default, "g1_amp_64_velocity_v1"),
    g1.frame_features(f, "g1_amp_64_velocity_v1"))
  assert g1.state_features(s, default, "g1_amp_64_velocity_v1").shape[-1] == 64
  disc = g1.AMPDiscriminator((16,), "g1_amp_64_velocity_v1")
  features = disc.features(s, default)
  assert disc(features, features).shape == (32,)


def test_g1_replay_imagination_and_task_roundtrip():
  torch.manual_seed(42)
  task = replace(g1.walk_task(), history=2, observation_noise=False)
  assert asdict(task_from_dict(asdict(task))) == asdict(task)
  c = g1.RobotConsts(
    torch.zeros(29), torch.tensor([[-3., 3.]]).expand(29, -1),
    torch.full((29,), 40.), torch.ones(29), torch.full((29,), 25.), torch.full((29,), 37.))
  wm = WorldModel((16,), 83, 29).requires_grad_(False)
  wm.net[-1].weight.data.mul_(.001)
  actor, critic = Actor(192, (16,), 29), Critic(124, (16,)).requires_grad_(False)
  s = torch.zeros(8, 83)
  s[:, 0], s[:, 3], s[:, g1.CONTACT] = .78, -1., 1.
  buf = ReplayBuffer(8, 8, 192, "cpu", 83, 29, 8)
  buf.add(s, s, torch.zeros(8, 29), torch.zeros(8, 29), torch.randn(8, 192),
          torch.ones(8, 3) * .2, torch.full((8,), 10.), torch.zeros(8, dtype=torch.bool),
          torch.zeros(8, 8))
  imag = Imagination(ImagineCfg(horizon=3), task, c, g1.AMPDiscriminator((16,)).requires_grad_(False))
  imag.amp_weight.fill_(.5)
  objective, data = imag.rollout(wm, actor, critic, buf.sample_states(8))
  (-objective.mean()).backward()
  assert data["critic_in"].shape == (8, 4, 124)
  assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in actor.net.parameters())
  assert sum(p.grad.abs().sum() for p in actor.net.parameters()) > 0
  assert torch.isfinite(imag.gae_targets(critic, data)).all()


def test_g1_acceptance_rejects_running_and_incomplete_evidence():
  from go2_supermimic.g1_validation import G1_FIXED_CASES, G1_GAIT_CASES
  from go2_supermimic.g1_validation import g1_gait_failures, g1_velocity_failures
  from go2_supermimic.validation import MANAGER_BACKEND
  common = {"environment_backend": MANAGER_BACKEND, "checkpoint_backend": MANAGER_BACKEND,
            "robot_kind": "g1"}
  speed = {**common, "seconds": 30, "settle_seconds": 1, "environments": 96,
           "observation_noise": False,
           "fixed": {"seed": 42, "cases": {
             name: {"command": command, "rmse": [0., 0., 0.], "falls": 0,
                    "samples_after_settling": 100, "flight_fraction": 0.}
             for name, command in G1_FIXED_CASES}},
           "random": [{"seed": seed, "overall": {
             "rmse": [0., 0., 0.], "falls": 0, "samples_after_settling": 100,
             "flight_fraction": 0.}} for seed in (42, 123, 2026)]}
  assert not g1_velocity_failures(speed)
  speed["fixed"]["cases"]["forward"]["flight_fraction"] = .03
  assert "forward/flight" in g1_velocity_failures(speed)
  speed["random"].pop()
  assert "random/coverage" in g1_velocity_failures(speed)
  baseline = {**common, "style_metric": "g1_heldout_pairs_v1", "style_metric_seed": 1701,
              "amp_motion_metadata": {"fixture": True}, "style_distance": {"forward": 1., "fast": 1.}}
  gait = {**baseline, "seconds": 20, "repeats": 8, "seed": 42,
          "style_distance": {"forward": .8, "fast": .8},
          "cases": {name: {
            "command": command, "rmse": [0., 0., 0.], "falls": 0, "mean_base_height_m": .78,
            "stride_hz_per_foot": 0. if name == "stand" else 1.,
            "mean_air_time_s": .25, "mean_swing_clearance_m": .03, "short_swing_fraction": 0.,
            "stance_slide_m_s": .05, "flight_fraction": 0., "front_contact_alternation": .6}
            for name, command in G1_GAIT_CASES}}
  assert not g1_gait_failures(gait, baseline)
  gait["cases"]["fast"]["mean_air_time_s"] = .03
  gait["style_distance"]["forward"] = .95
  assert "fast/mean_air_time_s" in g1_gait_failures(gait, baseline)
  assert "forward/heldout_style_improvement" in g1_gait_failures(gait, baseline)
