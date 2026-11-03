import pytest
import torch

from go2_supermimic import velocity as v
from go2_supermimic.supermimic.buffer import ReplayBuffer
from go2_supermimic.supermimic.imagine import CRITIC_DIM, ImagineCfg, Imagination
from go2_supermimic.supermimic.train import Actor, Critic, TrainCfg, load_checkpoint
from go2_supermimic.supermimic.world_model import RunningNorm, WorldModel
from test_velocity import consts, standing


def test_replay_wraparound_preserves_terminal_transitions_and_masks_resets():
  buf = ReplayBuffer(1, 4, v.FRAME_DIM, "cpu")
  for step in range(7):
    s = torch.full((1, v.STATE_DIM), float(step))
    a = torch.zeros(1, 12)
    # A terminal next state deliberately differs from the next episode's state.
    buf.add(s, s + 0.5, a, a, torch.zeros(1, v.FRAME_DIM), torch.zeros(1, 3),
            torch.ones(1), torch.tensor([step == 4]))
  window = buf.sample_windows(8, 4)
  torch.testing.assert_close(window["states"][0, :, 0], torch.tensor([3., 4., 5., 6.]))
  torch.testing.assert_close(window["next_states"][0, :, 0], torch.tensor([3.5, 4.5, 5.5, 6.5]))
  torch.testing.assert_close(window["valid"], torch.tensor([[1., 1., 0., 0.]]).repeat(8, 1))
  assert buf.sample_states(8)["obs"].dtype == torch.float32


def test_running_norm_merges_batches_correctly():
  torch.manual_seed(3)
  x = torch.randn(1000, 5) * 3 + 2
  norm = RunningNorm(5)
  norm.update(x[:100])
  norm.update(x[100:])
  torch.testing.assert_close(norm.mean, x.mean(0), atol=2e-6, rtol=2e-6)
  torch.testing.assert_close(norm.var, x.var(0, unbiased=False), atol=2e-6, rtol=2e-6)
  torch.testing.assert_close(norm.unnormalize(norm(x)), x, atol=2e-6, rtol=2e-6)


def test_world_model_masks_reset_teleports_in_autoregressive_loss():
  wm = WorldModel((16,))
  states = torch.zeros(4, 3, v.STATE_DIM)
  actions = torch.zeros(4, 3, 12)
  targets = torch.ones_like(states) * 0.02
  valid = torch.tensor([[1., 1., 0.]]).repeat(4, 1)
  first = wm.loss(states, targets, actions, actions, valid)
  targets[:, 2] = 1000  # reset jump must not affect dynamics learning
  second = wm.loss(states, targets, actions, actions, valid)
  torch.testing.assert_close(first, second)
  second.backward()
  assert all(torch.isfinite(p.grad).all() for p in wm.parameters())


def test_imagination_backpropagates_to_actor_with_frozen_dynamics_and_critic():
  torch.manual_seed(1)
  cfg = v.VelocityTaskCfg(history=2, observation_noise=False)
  wm = WorldModel((32, 32)).requires_grad_(False)
  actor = Actor(v.FRAME_DIM * 2, (32,))
  critic = Critic(CRITIC_DIM, (32,)).requires_grad_(False)
  s = standing(8)
  commands = torch.tensor([[0.8, 0.1, 0.2]]).repeat(8, 1)
  obs = v.push_history(torch.zeros(8, v.FRAME_DIM * 2),
                       v.obs_frame(s, torch.zeros(8, 12), commands), 2)
  wm.out_norm.var.fill_(0.0001)
  imagine = Imagination(ImagineCfg(horizon=4), cfg, consts())
  objective, data = imagine.rollout(wm, actor, critic, {
    "s": s, "a_prev": torch.zeros(8, 12), "obs": obs, "commands": commands,
    "command_time": torch.ones(8)})
  (-objective.mean()).backward()
  grads = [p.grad for p in actor.parameters()]
  assert all(g is not None and torch.isfinite(g).all() for g in grads)
  assert sum(g.abs().sum() for g in grads) > 0
  assert all(p.grad is None for p in wm.parameters())
  assert all(p.grad is None for p in critic.parameters())
  targets = imagine.gae_targets(critic, data)
  assert targets.shape == (8, 4) and torch.isfinite(targets).all()
  # A zero continuation excludes all future bootstrapping.
  data["continuation"][:, 1] = 0
  targets = imagine.gae_targets(critic, data)
  torch.testing.assert_close(targets[:, 1], data["rewards"][:, 1])


def test_reject_incompatible_legacy_checkpoint_and_invalid_replay_config(tmp_path):
  path = tmp_path / "legacy.pt"
  torch.save({"actor": {}}, path)
  with pytest.raises(ValueError, match="incompatible"):
    load_checkpoint(path, "cpu")
  with pytest.raises(ValueError, match="buffer_len"):
    TrainCfg(buffer_len=2, wm_window=8)
  with pytest.raises(ValueError, match="continue_run"):
    TrainCfg(continue_run=True)
