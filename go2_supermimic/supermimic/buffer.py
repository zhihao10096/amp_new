"""Per-environment ring replay with explicit terminal next states."""

import torch

from go2_supermimic.velocity import NUM_JOINTS, STATE_DIM


class ReplayBuffer:
  def __init__(self, num_envs, length, obs_dim, device):
    self.n, self.length, self.device = num_envs, length, device
    z = lambda *shape: torch.zeros(num_envs, length, *shape, device=device)
    self.s, self.next_s = z(STATE_DIM), z(STATE_DIM)
    self.a, self.a_prev = z(NUM_JOINTS), z(NUM_JOINTS)
    self.commands, self.command_time = z(3), z()
    self.obs = torch.zeros(num_envs, length, obs_dim, device=device, dtype=torch.float16)
    self.done = torch.zeros(num_envs, length, device=device, dtype=torch.bool)
    self.ptr = self.size = 0

  def add(self, s, next_s, action, previous_action, obs, commands, command_time, done):
    i = self.ptr
    for target, source in ((self.s, s), (self.next_s, next_s), (self.a, action),
                           (self.a_prev, previous_action), (self.obs, obs),
                           (self.commands, commands), (self.command_time, command_time),
                           (self.done, done)):
      target[:, i] = source
    self.ptr = (i + 1) % self.length
    self.size = min(self.size + 1, self.length)

  def _physical(self, logical):
    return (self.ptr - self.size + logical) % self.length

  def sample_windows(self, batch, k):
    if not 1 <= k <= self.size:
      raise ValueError(f"need {k} transitions; buffer contains {self.size}")
    env = torch.randint(self.n, (batch,), device=self.device)[:, None]
    start = torch.randint(self.size - k + 1, (batch, 1), device=self.device)
    idx = self._physical(start + torch.arange(k, device=self.device))
    done = self.done[env, idx]
    # The terminal transition itself is valid; exclude subsequent reset episodes.
    valid = torch.cat([torch.ones_like(done[:, :1]), ~done[:, :-1]], 1).float().cumprod(1)
    return {"states": self.s[env, idx], "next_states": self.next_s[env, idx],
            "actions": self.a[env, idx], "previous_actions": self.a_prev[env, idx],
            "valid": valid}

  def sample_states(self, batch):
    if not self.size:
      raise ValueError("cannot sample empty replay")
    env = torch.randint(self.n, (batch,), device=self.device)
    idx = self._physical(torch.randint(self.size, (batch,), device=self.device))
    return {"s": self.s[env, idx], "a_prev": self.a_prev[env, idx],
            "obs": self.obs[env, idx].float(), "commands": self.commands[env, idx],
            "command_time": self.command_time[env, idx]}
