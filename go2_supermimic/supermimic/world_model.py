"""Normalized deterministic dynamics, fit on autoregressive transition windows."""

import torch
from torch import nn

from go2_supermimic.velocity import NUM_JOINTS, STATE_DIM


class RunningNorm(nn.Module):
  def __init__(self, dim: int, eps: float = 1e-4, clip: float = 10.0):
    super().__init__()
    self.register_buffer("mean", torch.zeros(dim))
    self.register_buffer("var", torch.ones(dim))
    self.register_buffer("count", torch.tensor(eps))
    self.clip = clip

  @torch.no_grad()
  def update(self, x):
    x = x.reshape(-1, x.shape[-1])
    if x.shape[0] == 0:
      return
    mean, var, count = x.mean(0), x.var(0, unbiased=False), x.shape[0]
    delta, total = mean - self.mean, self.count + count
    self.mean.add_(delta * count / total)
    self.var.copy_((self.var * self.count + var * count
                    + delta.square() * self.count * count / total) / total)
    self.count.copy_(total)

  def forward(self, x):
    return ((x - self.mean) / (self.var.sqrt() + 1e-6)).clamp(-self.clip, self.clip)

  def unnormalize(self, x):
    return x * (self.var.sqrt() + 1e-6) + self.mean


def mlp(in_dim, hidden, out_dim, act=nn.SiLU):
  layers = []
  for size in hidden:
    layers.extend([nn.Linear(in_dim, size), act()])
    in_dim = size
  layers.append(nn.Linear(in_dim, out_dim))
  return nn.Sequential(*layers)


class WorldModel(nn.Module):
  def __init__(self, hidden=(512, 512, 512)):
    super().__init__()
    in_dim = STATE_DIM + 2 * NUM_JOINTS
    self.net = mlp(in_dim, hidden, STATE_DIM)
    self.in_norm = RunningNorm(in_dim)
    self.out_norm = RunningNorm(STATE_DIM)

  def update_stats(self, s, action, previous_action, next_state):
    self.in_norm.update(torch.cat([s, action, previous_action], -1))
    self.out_norm.update(next_state - s)

  def forward(self, s, action, previous_action):
    x = torch.cat([s, action, previous_action], -1)
    return s + self.out_norm.unnormalize(self.net(self.in_norm(x)))

  def loss(self, states, next_states, actions, previous_actions, valid):
    s = states[:, 0]
    total = s.new_zeros(())
    scale = self.out_norm.var.sqrt() + 1e-6
    for j in range(actions.shape[1]):
      s = self(s, actions[:, j], previous_actions[:, j])
      error = ((s - next_states[:, j]) / scale).square().mean(-1)
      total = total + (error * valid[:, j]).sum()
    return total / valid.sum().clamp(min=1)
