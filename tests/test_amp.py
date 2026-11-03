import json
from pathlib import Path

import pytest
import torch

from go2_supermimic import velocity as v
from go2_supermimic.amp import (
  AMPDiscriminator, MotionLibrary, a1_foot_positions, frame_features,
  leg_to_joint_order, slerp_xyzw, state_features,
)


def motion_file(tmp_path):
  frames = torch.zeros(100, 61)
  frames[:, 0] = torch.arange(100) * .01
  frames[:, 2] = .32
  frames[:, 6] = 1
  frames[:, 31] = 1
  frames[:, 7:19] = torch.arange(12) * .03
  path = tmp_path / "motion.json"
  path.write_text(json.dumps({"FrameDuration": .01, "MotionWeight": 1,
                              "Frames": frames.tolist()}))
  return path


def test_bundled_a1_motions_match_manifest_and_have_train_holdout_pairs():
  from go2_supermimic.amp import DEFAULT_A1_MOTIONS

  root = Path(__file__).resolve().parents[1]
  manifest = json.loads((root / "assets/motions/a1/manifest.json").read_text())
  paths = [root / name for name in DEFAULT_A1_MOTIONS.split(",")]
  assert [p.name for p in paths] == [entry["file"] for entry in manifest["files"]]
  library = MotionLibrary(",".join(map(str, paths)), "cpu")
  for stored, expected in zip(library.metadata["motions"], manifest["files"]):
    for key in ("sha256", "frames", "frame_dt", "weight"):
      assert stored[key] == expected[key]
    assert "assets/motions/a1" in stored["path"]
  for train in (True, False):
    before, after = library.sample_pairs(128, train=train)
    assert before.shape == after.shape == (128, 43)
    assert torch.isfinite(before).all() and torch.isfinite(after).all()


def test_a1_usd_straight_leg_geometry_and_joint_order():
  torch.testing.assert_close(
    leg_to_joint_order(torch.arange(12)), torch.tensor([0, 3, 6, 9, 1, 4, 7, 10, 2, 5, 8, 11]))
  feet = a1_foot_positions(torch.zeros(1, 12)).reshape(4, 3)
  torch.testing.assert_close(feet, torch.tensor([
    [.1805, .1308, -.4], [.1805, -.1308, -.4],
    [-.1805, .1308, -.4], [-.1805, -.1308, -.4]]))


def test_expert_and_robot_features_share_units_and_order(tmp_path):
  lib = MotionLibrary(str(motion_file(tmp_path)), "cpu")
  frame = lib.sample_frames(8)
  default = torch.linspace(-.1, .1, 12)
  state = torch.zeros(8, v.STATE_DIM)
  state[:, v.Q] = leg_to_joint_order(frame[:, 7:19]) - default
  state[:, v.QD] = leg_to_joint_order(frame[:, 37:49])
  state[:, v.Z], state[:, v.V_B], state[:, v.W_B] = frame[:, 2:3], frame[:, 31:34], frame[:, 34:37]
  torch.testing.assert_close(state_features(state, default), frame_features(frame))


def test_motion_timing_holdout_and_no_clip_boundary_pair(tmp_path):
  lib = MotionLibrary(str(motion_file(tmp_path)), "cpu", dt=.02)
  for train in (True, False):
    ids, times = lib.sample_times(200, train)
    a, b = lib.at_time(ids, times), lib.at_time(ids, times + .02)
    torch.testing.assert_close(b[:, 0] - a[:, 0], torch.full((200,), .02))
    if train:
      assert b[:, 0].max() < .8
    else:
      assert a[:, 0].min() >= .8
    assert b[:, 0].max() <= .99
  path = motion_file(tmp_path)
  data = json.loads(path.read_text())
  data["FrameDuration"] = 0
  path.write_text(json.dumps(data))
  with pytest.raises(ValueError, match="invalid AMP"):
    MotionLibrary(str(path), "cpu")


def test_quaternion_antipodes_and_shortest_arc():
  a = torch.tensor([[0., 0., 0., 1.], [0., 0., 0., 1.]])
  b = torch.tensor([[0., 0., 0., -1.], [0., 0., 1., 0.]])
  actual = slerp_xyzw(a, b, torch.full((2, 1), .5))
  torch.testing.assert_close(actual[0], a[0])
  torch.testing.assert_close(actual[1], torch.tensor([0., 0., 2**-.5, 2**-.5]))


def test_frozen_discriminator_retains_policy_state_gradients():
  torch.manual_seed(3)
  disc = AMPDiscriminator((32, 16)).requires_grad_(False)
  before = torch.randn(8, v.STATE_DIM)
  after = torch.randn_like(before).requires_grad_()
  commands = torch.ones(8, 3)
  reward = disc.reward(before, after, torch.zeros(12), commands)
  reward.sum().backward()
  assert torch.isfinite(after.grad).all() and after.grad.norm() > 1e-5
  assert all(p.grad is None for p in disc.parameters())
  assert not disc.reward(before, after, torch.zeros(12), torch.zeros_like(commands)).any()


def test_discriminator_lsgan_and_gradient_penalty_update():
  torch.manual_seed(5)
  disc = AMPDiscriminator((32, 16))
  opt = torch.optim.Adam(disc.parameters(), lr=1e-3)
  initial = [x.detach().clone() for x in disc.parameters()]
  expert = (torch.randn(32, 43), torch.randn(32, 43))
  policy = (torch.randn(32, 43) + 1, torch.randn(32, 43) + 1)
  for _ in range(3):
    loss, metrics = disc.loss(expert, policy)
    assert torch.isfinite(loss) and metrics["amp_gradient_penalty"] > 0
    opt.zero_grad()
    loss.backward()
    opt.step()
  assert any(not torch.equal(a, b) for a, b in zip(initial, disc.parameters()))


def test_amp_imagination_compilation_preserves_reward_and_actor_gradient(monkeypatch):
  from dataclasses import fields
  from go2_supermimic.supermimic.imagine import CRITIC_DIM, ImagineCfg, Imagination
  from go2_supermimic.supermimic.train import Actor, Critic
  from go2_supermimic.supermimic.world_model import WorldModel
  from test_velocity import consts, standing

  compile_step = torch.compile
  monkeypatch.setattr(torch, "compile",
                      lambda fn, **kw: compile_step(fn, backend="aot_eager", fullgraph=True, **kw))
  torch.manual_seed(61)
  task = v.VelocityTaskCfg(history=2, observation_noise=False)
  for item in fields(task.rewards):
    setattr(task.rewards, item.name, 0.)
  wm = WorldModel((16,)).requires_grad_(False)
  wm.out_norm.var.fill_(1e-4)
  actor = Actor(v.FRAME_DIM * 2, (16,))
  critic = Critic(CRITIC_DIM, (16,)).requires_grad_(False)
  for parameter in critic.parameters():
    parameter.zero_()
  amp = AMPDiscriminator((16,)).requires_grad_(False)
  seed = {"s": standing(4), "a_prev": torch.zeros(4, 12),
          "obs": torch.randn(4, v.FRAME_DIM * 2), "commands": torch.ones(4, 3),
          "command_time": torch.full((4,), 10.), "gait": torch.zeros(4, v.GAIT_DIM)}
  eager = Imagination(ImagineCfg(horizon=3), task, consts(), amp)
  compiled = Imagination(ImagineCfg(horizon=3, compile=True), task, consts(), amp)
  for weight in (0., .2, .5):
    eager.amp_weight.fill_(weight)
    compiled.amp_weight.fill_(weight)
    expected, _ = eager.rollout(wm, actor, critic, seed)
    actual, _ = compiled.rollout(wm, actor, critic, seed)
    torch.testing.assert_close(actual, expected)
    grads = torch.autograd.grad(expected.sum(), tuple(actor.parameters()))
    compiled_grads = torch.autograd.grad(actual.sum(), tuple(actor.parameters()))
    for a, b in zip(grads, compiled_grads):
      torch.testing.assert_close(a, b)
    magnitude = sum(g.abs().sum() for g in grads)
    assert magnitude > 0 if weight else magnitude == 0
  assert all(p.grad is None for model in (wm, critic, amp) for p in model.parameters())


def test_heldout_style_distance_is_independent_and_rejects_missing_data(tmp_path):
  from go2_supermimic.amp import heldout_style_distance
  lib = MotionLibrary(str(motion_file(tmp_path)), "cpu")
  pairs = torch.cat(lib.sample_pairs(128), -1)
  matched = heldout_style_distance(pairs, lib, 1.)
  changed = pairs.clone()
  changed[:, :12] += .2
  assert matched < 1e-5
  assert heldout_style_distance(changed, lib, 1.) > .1
  with pytest.raises(ValueError, match="128"):
    heldout_style_distance(pairs[:4], lib, 1.)
  with pytest.raises(ValueError, match="speed band"):
    heldout_style_distance(pairs, lib, 3.)


def test_a1_acceptance_rejects_go2_incomplete_and_falling_reports():
  from go2_supermimic.amp_validation import A1_FIXED_CASES, a1_velocity_failures
  from go2_supermimic.validation import MANAGER_BACKEND
  group = {"rmse": [.05, .05, .05], "falls": 0, "samples_after_settling": 100}
  report = {"robot_kind": "a1", "seconds": 30, "settle_seconds": 1, "environments": 96,
            "observation_noise": False, "environment_backend": MANAGER_BACKEND,
            "checkpoint_backend": MANAGER_BACKEND,
            "fixed": {"seed": 42, "cases": {name: dict(group, command=cmd)
                                           for name, cmd in A1_FIXED_CASES}},
            "random": [{"seed": seed, "overall": dict(group)} for seed in (42, 123, 2026)]}
  assert not a1_velocity_failures(report)
  report["robot_kind"] = "go2"
  assert "robot_kind" in a1_velocity_failures(report)
  report["robot_kind"] = "a1"
  report["random"][0]["overall"]["falls"] = 1
  assert "random/42/falls" in a1_velocity_failures(report)
  del report["fixed"]["cases"]["upper_corner"]
  assert "fixed/coverage" in a1_velocity_failures(report)
