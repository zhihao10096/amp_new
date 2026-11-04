import copy

import pytest
import torch

from go2_supermimic import g1
from go2_supermimic.g1_discriminator import LeggedLabNorm
from go2_supermimic.supermimic.train import TrainCfg


def test_policy_moments_exclude_experts_and_update_after_optimizer():
  torch.manual_seed(511)
  disc = g1.AMPDiscriminator((32, 16), num_frames=4, profile="legged_lab_v1")
  optimizer = torch.optim.Adam(disc.optimizer_groups(), lr=1e-5)
  policies = [torch.randn(32, 4, 61), torch.randn(32, 4, 61) + 2.]
  seen = []
  for policy in policies:
    before = copy.deepcopy(disc.norm.state_dict())
    loss, _ = disc.loss(torch.randn_like(policy) + 100., policy, 40.)
    assert torch.isfinite(loss)
    for key, value in before.items():
      assert torch.equal(disc.norm.state_dict()[key], value)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    disc.update_normalization(policy)
    seen.append(policy.flatten(0, 1))
    pooled = torch.cat(seen)
    torch.testing.assert_close(disc.norm.mean, pooled.mean(0), atol=1e-6, rtol=1e-5)
    torch.testing.assert_close(disc.norm.var, pooled.var(0, unbiased=False), atol=1e-6, rtol=1e-5)
    assert disc.norm.count == len(pooled)
  assert [group["weight_decay"] for group in optimizer.param_groups] == [1e-4, .1]
  ids = [id(p) for group in optimizer.param_groups for p in group["params"]]
  assert len(ids) == len(set(ids)) == len(list(disc.parameters()))


def test_upstream_norm_has_no_clipping_and_never_mutates_in_forward():
  norm = LeggedLabNorm(3)
  norm.update(torch.zeros(16, 3))
  count = norm.count.clone()
  x = torch.full((2, 3), 1000., requires_grad=True)
  normalized = norm(x)
  torch.testing.assert_close(normalized, torch.full_like(x, 100_000.))
  normalized.sum().backward()
  torch.testing.assert_close(x.grad, torch.full_like(x, 100.))
  assert torch.equal(norm.count, count)
  norm.eval()
  norm.update(torch.ones(4, 3))
  assert torch.equal(norm.count, count)
  norm.train()
  norm.count.fill_(100_000_000)
  norm.update(torch.ones(4, 3))
  assert norm.count == 100_000_000 and not norm.mean.any()


def test_legacy_profile_preserves_scores_and_joint_statistics():
  torch.manual_seed(511)
  default = g1.AMPDiscriminator((32, 16), num_frames=4)
  torch.manual_seed(511)
  explicit = g1.AMPDiscriminator((32, 16), num_frames=4, profile="legacy")
  expert, policy = torch.randn(32, 4, 61), torch.randn(32, 4, 61) + 1
  loss_a, _ = default.loss(expert, policy)
  loss_b, _ = explicit.loss(expert, policy)
  assert torch.equal(loss_a, loss_b)
  for key, value in default.state_dict().items():
    assert torch.equal(value, explicit.state_dict()[key])
  before = explicit.norm.count.clone()
  explicit.update_normalization(policy)
  assert torch.equal(before, explicit.norm.count)
  with pytest.raises(ValueError, match="requires G1"):
    TrainCfg(task="A1-AMP-Flat", amp_discriminator_profile="legged_lab_v1")
