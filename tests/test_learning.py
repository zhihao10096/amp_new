from dataclasses import asdict
from types import SimpleNamespace

import pytest
import torch

from go2_supermimic import velocity as v
from go2_supermimic.supermimic.buffer import ReplayBuffer
from go2_supermimic.supermimic.imagine import CRITIC_DIM, ImagineCfg, Imagination
from go2_supermimic.supermimic.train import Actor, Critic, TrainCfg, Trainer, load_checkpoint, task_from_dict
from go2_supermimic.supermimic.world_model import RunningNorm, WorldModel, mlp
from test_velocity import consts, standing


def test_replay_wraparound_preserves_terminal_transitions_and_masks_resets():
  buf = ReplayBuffer(1, 4, v.FRAME_DIM, "cpu")
  for step in range(7):
    s = torch.full((1, v.STATE_DIM), float(step))
    a = torch.zeros(1, 12)
    # A terminal next state deliberately differs from the next episode's state.
    buf.add(s, s + 0.5, a, a, torch.zeros(1, v.FRAME_DIM), torch.zeros(1, 3),
            torch.ones(1), torch.tensor([step == 4]), torch.full((1, v.GAIT_DIM), float(step)))
  window = buf.sample_windows(8, 4)
  torch.testing.assert_close(window["states"][0, :, 0], torch.tensor([3., 4., 5., 6.]))
  torch.testing.assert_close(window["next_states"][0, :, 0], torch.tensor([3.5, 4.5, 5.5, 6.5]))
  torch.testing.assert_close(window["valid"], torch.tensor([[1., 1., 0., 0.]]).repeat(8, 1))
  seeds = buf.sample_states(8)
  assert seeds["obs"].dtype == torch.float32
  torch.testing.assert_close(seeds["gait"][:, 0], seeds["s"][:, 0])


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


def test_compiled_imagination_preserves_returns_and_actor_gradients(monkeypatch):
  """AOTAutograd must preserve credit through state, contacts and history."""
  compile_step = torch.compile
  monkeypatch.setattr(torch, "compile",
                      lambda fn, **kw: compile_step(fn, backend="aot_eager", fullgraph=True, **kw))
  torch.manual_seed(17)
  task = v.VelocityTaskCfg(history=2, observation_noise=False)
  wm = WorldModel((16,)).requires_grad_(False)
  wm.out_norm.var.fill_(1e-4)
  actor = Actor(v.FRAME_DIM * 2, (16,))
  critic = Critic(CRITIC_DIM, (16,)).requires_grad_(False)
  seed = {"s": standing(4), "a_prev": torch.zeros(4, 12),
          "obs": torch.randn(4, v.FRAME_DIM * 2), "commands": torch.randn(4, 3),
          "command_time": torch.ones(4) * 10, "gait": torch.ones(4, v.GAIT_DIM) * .1}
  eager = Imagination(ImagineCfg(horizon=3), task, consts())
  compiled = Imagination(ImagineCfg(horizon=3, compile=True), task, consts())
  expected, expected_data = eager.rollout(wm, actor, critic, seed)
  actual, actual_data = compiled.rollout(wm, actor, critic, seed)
  torch.testing.assert_close(actual, expected)
  for name in expected_data:
    torch.testing.assert_close(actual_data[name], expected_data[name])
  expected_grad = torch.autograd.grad(expected.sum(), tuple(actor.parameters()))
  actual_grad = torch.autograd.grad(actual.sum(), tuple(actor.parameters()))
  for actual, expected in zip(actual_grad, expected_grad):
    torch.testing.assert_close(actual, expected)


def test_reward_curriculum_reuses_compiled_graphs_and_matches_eager_gradients(monkeypatch):
  from go2_supermimic.supermimic.curriculum import training_task
  from torch._dynamo.backends.registry import lookup_backend

  backend, graphs = lookup_backend("aot_eager"), []

  def counting_backend(graph, inputs):
    graphs.append(graph)
    return backend(graph, inputs)

  compile_step = torch.compile
  monkeypatch.setattr(torch, "compile",
                      lambda fn, **kw: compile_step(fn, backend=counting_backend, fullgraph=True, **kw))
  torch.manual_seed(47)
  target = v.VelocityTaskCfg(history=2, observation_noise=False)
  wm = WorldModel((16,)).requires_grad_(False)
  wm.out_norm.var.fill_(1e-4)
  actor = Actor(v.FRAME_DIM * 2, (16,))
  critic = Critic(CRITIC_DIM, (16,)).requires_grad_(False)
  seed = {"s": standing(4), "a_prev": torch.zeros(4, 12),
          "obs": torch.randn(4, v.FRAME_DIM * 2), "commands": torch.randn(4, 3),
          "command_time": torch.ones(4) * 10, "gait": torch.ones(4, v.GAIT_DIM) * .1}
  compiled = Imagination(ImagineCfg(horizon=2, compile=True), target, consts())
  graph_counts = []
  for fraction in (0., .123, .5, .999, 1.):
    task = training_task(target, fraction)
    compiled.task = task
    compiled.update_reward_parameters()
    eager = Imagination(ImagineCfg(horizon=2), task, consts())
    expected, _ = eager.rollout(wm, actor, critic, seed)
    actual, _ = compiled.rollout(wm, actor, critic, seed)
    torch.testing.assert_close(actual, expected)
    expected_grad = torch.autograd.grad(expected.sum(), tuple(actor.parameters()))
    actual_grad = torch.autograd.grad(actual.sum(), tuple(actor.parameters()))
    for actual, expected in zip(actual_grad, expected_grad):
      torch.testing.assert_close(actual, expected)
    graph_counts.append(len(graphs))
  # Replay seeds are detached; subsequent imagined states carry gradients.
  # Both input variants may compile, but changing rewards must add no graphs.
  assert 1 <= graph_counts[0] <= 2
  assert all(count == graph_counts[0] for count in graph_counts)


def test_reject_incompatible_legacy_checkpoint_and_invalid_replay_config(tmp_path):
  path = tmp_path / "legacy.pt"
  torch.save({"actor": {}}, path)
  with pytest.raises(ValueError, match="incompatible"):
    load_checkpoint(path, "cpu")
  with pytest.raises(ValueError, match="buffer_len"):
    TrainCfg(buffer_len=2, wm_window=8)
  with pytest.raises(ValueError, match="continue_run"):
    TrainCfg(continue_run=True)


def test_v1_warm_start_preserves_actor_and_original_dynamics(tmp_path):
  torch.manual_seed(5)
  from torch import nn
  old = nn.Module()
  old.net = mlp(34 + 24, (16, 16), 34)
  old.in_norm = RunningNorm(58)
  old.out_norm = RunningNorm(34)
  actor = Actor(v.FRAME_DIM * 5, (16,))
  path = tmp_path / "v1.pt"
  torch.save({"format": "isaaclab_velocity_v1", "actor": actor.state_dict(),
              "world_model": old.state_dict()}, path)
  trainer = Trainer.__new__(Trainer)
  trainer.device = "cpu"
  trainer.actor = Actor(v.FRAME_DIM * 5, (16,))
  trainer.wm = WorldModel((16, 16))
  trainer.warm_start(path)
  state = standing(8)
  state[:, v.FOOT_POS] = torch.randn(8, 12)
  action, prev = torch.randn(8, 12), torch.randn(8, 12)
  with torch.no_grad():
    expected = state[:, :34] + old.out_norm.unnormalize(
      old.net(old.in_norm(torch.cat([state[:, :34], action, prev], -1))))
    actual = trainer.wm(state, action, prev)
  torch.testing.assert_close(actual[:, :34], expected)
  torch.testing.assert_close(actual[:, 34:], state[:, 34:])
  observation = torch.randn(8, v.FRAME_DIM * 5)
  torch.testing.assert_close(trainer.actor(observation), actor(observation))


def test_old_task_settings_keep_the_original_reward_definition():
  data = {"commands": {}, "rewards": {"joint_deviation": -.05, "action_rate": -.01}}
  task = task_from_dict(data)
  assert task.reward_profile == "legacy"
  assert task.rewards.feet_air_time == task.rewards.feet_slide == task.rewards.energy == 0


def test_reference_checkpoint_resumes_after_adding_optional_gait_settings(tmp_path):
  original = asdict(v.VelocityTaskCfg())
  original["reward_profile"] = "unitree_reference"
  for key in ("feet_clearance", "feet_contact_without_command", "gait_duration", "diagonal_gait"):
    del original["rewards"][key]
  for key in ("swing_height", "clearance_variance", "target_air_time", "target_stance_time"):
    del original[key]
  restored = task_from_dict(original)
  assert restored.rewards.gait_duration == restored.rewards.feet_clearance == 0
  trainer = Trainer.__new__(Trainer)
  trainer.device = "cpu"
  trainer.cfg = TrainCfg(continue_run=True, resume="checkpoint.pt")
  trainer.env = SimpleNamespace(cfg=SimpleNamespace(task=restored), step_dt=.02)
  trainer.actor = Actor(v.FRAME_DIM * 5, (8,))
  trainer.critic = Critic(CRITIC_DIM, (8,))
  trainer.wm = WorldModel((8,))
  for name, model in (("actor", trainer.actor), ("critic", trainer.critic), ("wm", trainer.wm)):
    setattr(trainer, "opt_" + name, torch.optim.Adam(model.parameters()))
  path = tmp_path / "reference.pt"
  torch.save({
    "format": "isaaclab_velocity_v2", "task_cfg": original, "dt": .02,
    "iteration": 42, "env_steps": 8192, "sim_steps": 16,
    "actor": trainer.actor.state_dict(), "critic": trainer.critic.state_dict(),
    "world_model": trainer.wm.state_dict(),
    **{name: getattr(trainer, name).state_dict() for name in ("opt_actor", "opt_critic", "opt_wm")},
  }, path)
  trainer.load(path)
  assert trainer.start_it == 42 and trainer.env_steps == 8192
  assert trainer.env.common_step_counter == 16
  trainer.env.cfg.task.rewards.feet_clearance = .5
  with pytest.raises(ValueError, match="task settings differ"):
    trainer.load(path)
