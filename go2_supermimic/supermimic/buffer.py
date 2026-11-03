"""Per-environment ring replay with explicit terminal next states."""

import torch

from go2_supermimic.velocity import GAIT_DIM, NUM_JOINTS, STATE_DIM


class ReplayBuffer:
  def __init__(self, num_envs, length, obs_dim, device,
               state_dim=STATE_DIM, act_dim=NUM_JOINTS, gait_dim=GAIT_DIM):
    self.n, self.length, self.device = num_envs, length, device
    z = lambda *shape: torch.zeros(num_envs, length, *shape, device=device)
    self.s, self.next_s = z(state_dim), z(state_dim)
    self.a, self.a_prev = z(act_dim), z(act_dim)
    self.commands, self.command_time = z(3), z()
    self.gait = z(gait_dim)
    self.obs = torch.zeros(num_envs, length, obs_dim, device=device, dtype=torch.float16)
    self.done = torch.zeros(num_envs, length, device=device, dtype=torch.bool)
    self.ptr = self.size = 0

  def add(self, s, next_s, action, previous_action, obs, commands, command_time, done, gait=None):
    i = self.ptr
    for target, source in ((self.s, s), (self.next_s, next_s), (self.a, action),
                           (self.a_prev, previous_action), (self.obs, obs),
                           (self.commands, commands), (self.command_time, command_time),
                           (self.done, done)):
      target[:, i] = source
    self.gait[:, i] = gait if gait is not None else 0
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
            "command_time": self.command_time[env, idx], "gait": self.gait[env, idx]}

  def sample_pairs(self, batch):
    """Use stored pre-reset terminal states, never the next episode's reset."""
    if not self.size:
      raise ValueError("cannot sample empty replay")
    env = torch.randint(self.n, (batch,), device=self.device)
    idx = self._physical(torch.randint(self.size, (batch,), device=self.device))
    return self.s[env, idx], self.next_s[env, idx]

  def sample_transitions(self, batch: int, env_ids: torch.Tensor | None = None,
                         generator: torch.Generator | None = None) -> dict[str, torch.Tensor]:
    """Sample physical transitions without replacing terminal states by resets."""
    if not self.size or batch <= 0:
      raise ValueError("need a nonempty replay and a positive transition batch")
    if env_ids is None:
      env_ids = torch.arange(self.n, device=self.device)
    if not len(env_ids):
      raise ValueError("need at least one eligible environment")
    env = env_ids[torch.randint(len(env_ids), (batch,), device=self.device, generator=generator)]
    idx = self._physical(torch.randint(self.size, (batch,), device=self.device, generator=generator))
    return {"s": self.s[env, idx], "next_s": self.next_s[env, idx],
            "action": self.a[env, idx], "a_prev": self.a_prev[env, idx],
            "commands": self.commands[env, idx], "command_time": self.command_time[env, idx],
            "gait": self.gait[env, idx], "done": self.done[env, idx]}
