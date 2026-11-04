"""Temporal AMP must preserve physical episode boundaries and action gradients."""

from dataclasses import replace

import pytest
import torch

from go2_supermimic import g1
from go2_supermimic.supermimic.buffer import ReplayBuffer
from go2_supermimic.supermimic.imagine import ImagineCfg, Imagination
from go2_supermimic.supermimic.train import Actor, Critic, TrainCfg
from go2_supermimic.supermimic.world_model import WorldModel


def test_replay_sequences_and_seeds_preserve_resets_terminals_and_ring_wrap():
  buf = ReplayBuffer(2, 6, 4, "cpu", 3, 1, 1, amp_num_frames=4)
  ends = ({4, 7}, {5, 8})
  for step in range(10):
    state = torch.tensor([[step] * 3, [100 + step] * 3], dtype=torch.float32)
    action = torch.zeros(2, 1)
    buf.add(state, state + .5, action, action, torch.zeros(2, 4),
            torch.zeros(2, 3), torch.ones(2),
            torch.tensor([step in ends[0], step in ends[1]]))
  # Only logical indices >= 2 are eligible: every preceding transition is
  # physically retained, even when the ring itself has wrapped.
  for sample in (buf.sample_states(512), buf.sample_transitions(512)):
    for current, history in zip(sample["s"][:, 0], sample["amp_history"][:, :, 0]):
      env, step = int(current) // 100, int(current) % 100
      assert 6 <= step <= 9
      first = max([step - 2] + [x + 1 for x in ends[env] if step - 2 <= x < step])
      expected = torch.tensor([100 * env + max(step - 2, first),
                               100 * env + max(step - 1, first)], dtype=torch.float32)
      torch.testing.assert_close(history, expected)
  sequence = buf.sample_sequences(512)
  torch.testing.assert_close(sequence[:, -1] - sequence[:, -2],
                             torch.full_like(sequence[:, -1], .5))
  assert sequence.shape == (512, 4, 3)
  # There is no persistent state/feature-history replay allocation.
  assert sum(x.numel() for x in vars(buf).values() if isinstance(x, torch.Tensor)) < 400


@pytest.mark.parametrize("train", [True, False])
def test_expert_sequence_support_stays_inside_each_split_and_clip(train, monkeypatch):
  library = g1.MotionLibrary(feature_schema="g1_amp_70_feet_v1", num_frames=4)
  original, sampled = library.at_time, []

  def record(clips, times):
    sampled.append((clips.clone(), times.clone()))
    return original(clips, times)

  monkeypatch.setattr(library, "at_time", record)
  features = library.sample_sequences(2048, train=train)
  clips, times = [x.reshape(2048, 4) for x in sampled[0]]
  assert (clips == clips[:, :1]).all()
  torch.testing.assert_close(times[:, 1:] - times[:, :-1],
                             torch.full((2048, 3), .02), atol=2e-6, rtol=1e-5)
  lower = (times / library.durations[clips]).floor().long()
  upper = (times / library.durations[clips]).ceil().long()
  assert (lower >= (0 if train else library.splits[clips])).all()
  assert (upper < (library.splits[clips] if train else library.sizes[clips])).all()
  expected = g1.frame_features(
    original(clips.flatten(), times.flatten()), "g1_amp_70_feet_v1").reshape(2048, 4, 70)
  torch.testing.assert_close(features, expected)
  assert library.metadata["sequence_span_s"] == .06


def test_four_frame_option_preserves_rsi_distribution_and_independent_pair_metric():
  pair = g1.MotionLibrary(feature_schema="g1_amp_70_feet_v1")
  sequence = g1.MotionLibrary(feature_schema="g1_amp_70_feet_v1", num_frames=4)
  assert "num_frames" not in pair.metadata
  for method in ("sample_frames", "sample_pairs"):
    torch.manual_seed(71)
    a = getattr(pair, method)(256)
    torch.manual_seed(71)
    b = getattr(sequence, method)(256)
    torch.testing.assert_close(a, b, atol=0, rtol=0)


def test_discriminator_retains_gradients_through_every_frame_and_updates():
  torch.manual_seed(71)
  disc = g1.AMPDiscriminator((32,), "g1_amp_70_feet_v1", num_frames=4)
  states = (torch.randn(8, 4, 83) * .05).requires_grad_()
  disc.requires_grad_(False)
  reward = disc.reward(states[:, 2], states[:, 3], torch.zeros(29),
                       torch.ones(8, 3), states[:, :2])
  reward.sum().backward()
  assert all(states.grad[:, i].abs().sum() > 0 for i in range(4))
  assert torch.isfinite(states.grad).all()
  assert all(p.grad is None for p in disc.parameters())
  with pytest.raises(ValueError, match="history"):
    disc.reward(states[:, 2], states[:, 3], torch.zeros(29), torch.ones(8, 3))
  disc.requires_grad_(True)
  initial = disc.net[0].weight.detach().clone()
  opt = torch.optim.Adam(disc.parameters(), lr=1e-3)
  loss, metrics = disc.loss(torch.randn(16, 4, 70), torch.randn(16, 4, 70))
  opt.zero_grad()
  loss.backward()
  opt.step()
  assert metrics["amp_gradient_penalty"] > 0
  assert not torch.equal(initial, disc.net[0].weight)


@pytest.fixture
def isolated_compile_cache():
  # Independent task/schema tests share Dynamo's per-code-object cache. Their
  # combined specializations must not exhaust a single training process's
  # cache limit merely because the entire CPU suite runs in one interpreter.
  torch._dynamo.reset()
  yield
  torch._dynamo.reset()


def test_four_frame_imagination_compile_preserves_amp_only_actor_gradient(
    monkeypatch, isolated_compile_cache):
  compile_step = torch.compile
  monkeypatch.setattr(torch, "compile",
                      lambda fn, **kw: compile_step(fn, backend="aot_eager", fullgraph=True, **kw))
  torch.manual_seed(71)
  task = replace(g1.walk_task(), history=2, observation_noise=False)
  for name in task.rewards.__dataclass_fields__:
    setattr(task.rewards, name, 0.)
  consts = g1.RobotConsts(
    torch.zeros(29), torch.tensor([[-3., 3.]]).expand(29, -1), torch.full((29,), 40.),
    torch.ones(29), torch.full((29,), 25.), torch.full((29,), 37.))
  wm = WorldModel((16,), 83, 29).requires_grad_(False)
  wm.out_norm.var.fill_(1e-4)
  actor, critic = Actor(192, (16,), 29), Critic(124, (16,)).requires_grad_(False)
  for p in critic.parameters():
    p.zero_()
  disc = g1.AMPDiscriminator((16,), "g1_amp_70_feet_v1", 4).requires_grad_(False)
  state = torch.zeros(4, 83)
  state[:, 0], state[:, 3], state[:, g1.CONTACT] = .78, -1., 1.
  seed = {"s": state, "a_prev": torch.zeros(4, 29), "obs": torch.randn(4, 192),
          "commands": torch.ones(4, 3) * .2, "command_time": torch.full((4,), 10.),
          "gait": torch.zeros(4, 8), "amp_history": state[:, None].expand(-1, 2, -1)}
  eager = Imagination(ImagineCfg(horizon=4), task, consts, disc)
  compiled = Imagination(ImagineCfg(horizon=4, compile=True), task, consts, disc)
  for weight in (0., .5):
    eager.set_amp_weight(weight)
    compiled.set_amp_weight(weight)
    expected, data = eager.rollout(wm, actor, critic, seed)
    actual, actual_data = compiled.rollout(wm, actor, critic, seed)
    torch.testing.assert_close(actual, expected)
    for name in data:
      torch.testing.assert_close(actual_data[name], data[name])
    gradients = torch.autograd.grad(expected.sum(), tuple(actor.parameters()))
    compiled_gradients = torch.autograd.grad(actual.sum(), tuple(actor.parameters()))
    for a, b in zip(gradients, compiled_gradients):
      torch.testing.assert_close(a, b)
    magnitude = sum(g.abs().sum() for g in gradients)
    assert magnitude > 0 if weight else magnitude == 0


def test_reject_invalid_history_configuration_and_insufficient_replay():
  with pytest.raises(ValueError, match="amp_num_frames"):
    TrainCfg(amp_num_frames=4)
  with pytest.raises(ValueError, match="amp_num_frames"):
    TrainCfg(task="G1-AMP-Flat", amp_num_frames=3)
  with pytest.raises(ValueError, match="room"):
    ReplayBuffer(1, 2, 4, "cpu", amp_num_frames=4)
  buf = ReplayBuffer(1, 4, 4, "cpu", amp_num_frames=4)
  with pytest.raises(ValueError, match="history"):
    buf.sample_states(1)
