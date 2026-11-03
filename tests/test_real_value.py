"""Physical value targets must preserve the pre-reset transition semantics."""

from dataclasses import fields, replace

import pytest
import torch

from go2_supermimic import g1, velocity
from go2_supermimic.supermimic.buffer import ReplayBuffer
from go2_supermimic.supermimic.imagine import ImagineCfg, Imagination
from go2_supermimic.supermimic.train import TrainCfg


@pytest.mark.parametrize("api", [velocity, g1])
def test_real_td_distinguishes_falls_timeouts_and_command_expiries(api):
  task = g1.walk_task() if api is g1 else velocity.VelocityTaskCfg()
  task = replace(task, rewards=api.RewardWeights(**{
    item.name: -50. if item.name == "terminated" else 0.
    for item in fields(api.RewardWeights)}))
  n, nj = 4, api.NUM_JOINTS
  consts = api.RobotConsts(
    torch.zeros(nj), torch.tensor([[-3., 3.]]).expand(nj, -1),
    torch.ones(nj), torch.ones(nj), torch.full((nj,), 25.), torch.full((nj,), 30.))
  state = torch.zeros(n, api.STATE_DIM)
  state[:, 0], state[:, 3] = task.nominal_height, -1.
  after = state.clone()
  after[2, 0] = .05  # A fall that coincides with a command expiry still trains.
  gait = torch.zeros(n, api.GAIT_DIM)
  gait[:, 0] = .1
  batch = {
    "s": state.requires_grad_(), "next_s": after.requires_grad_(),
    "action": torch.full((n, nj), .2), "a_prev": torch.full((n, nj), .4),
    "commands": torch.full((n, 3), .2),
    "command_time": torch.tensor([10., 10., .01, .01]), "gait": gait,
    "done": torch.tensor([False, True, True, False]),
  }

  class ContextCritic(torch.nn.Module):
    def forward(self, x):
      # These fields deliberately differ from post-reset action/time/gait.
      return (x[:, 0] + x[:, api.STATE_DIM] + x[:, -api.GAIT_DIM - 1]
              + x[:, -api.GAIT_DIM]).unsqueeze(-1)

  class ConstantAMP:
    def reward(self, before, after, default_q, commands):
      return before.new_full((len(before),), 2.)

  imagine = Imagination(ImagineCfg(), task, consts, ConstantAMP())
  imagine.amp_weight.fill_(.5)
  inputs, target = imagine.real_targets(ContextCritic(), batch)
  expected_value = task.nominal_height + .2 + 9.98 + .12
  # Reward and AMP each receive dt once; falls get no bootstrap, timeouts do.
  torch.testing.assert_close(
    target, torch.tensor([.02 + .99 * expected_value, .02 + .99 * expected_value, -.98]))
  assert inputs.shape == (3, api.STATE_DIM + nj + 4 + api.GAIT_DIM)
  torch.testing.assert_close(inputs[:, api.STATE_DIM], torch.full((3,), .4))
  torch.testing.assert_close(inputs[:, -api.GAIT_DIM], torch.full((3,), .1))
  assert not target.requires_grad and not inputs.requires_grad
  assert batch["s"].grad is None and batch["next_s"].grad is None


def test_real_replay_uses_eligible_envs_and_an_independent_rng_after_wraparound():
  buf = ReplayBuffer(2, 2, 4, "cpu")
  for step in range(4):
    state = torch.tensor([step, step + 10.]).unsqueeze(-1).expand(-1, velocity.STATE_DIM)
    action = torch.zeros(2, velocity.NUM_JOINTS)
    buf.add(state, state + .5, action, action, torch.zeros(2, 4), torch.zeros(2, 3),
            torch.full((2,), 10.), torch.tensor([False, step == 2]))
  generator = torch.Generator().manual_seed(987)
  ambient_rng = torch.get_rng_state().clone()
  sampled = buf.sample_transitions(128, torch.tensor([1]), generator)
  assert torch.equal(ambient_rng, torch.get_rng_state())
  assert set(sampled["s"][:, 0].tolist()) == {12., 13.}
  torch.testing.assert_close(sampled["next_s"], sampled["s"] + .5)
  assert sampled["done"].any() and not sampled["done"].all()
  with pytest.raises(ValueError, match="eligible"):
    buf.sample_transitions(4, torch.tensor([], dtype=torch.long))
  for fraction in (-.1, 1.1):
    with pytest.raises(ValueError, match="critic_real_fraction"):
      TrainCfg(critic_real_fraction=fraction)
