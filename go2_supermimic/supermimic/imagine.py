"""Differentiable velocity tracking rollouts and TD(lambda) critic targets."""

from dataclasses import dataclass

import torch

from go2_supermimic import velocity as v

CRITIC_DIM = v.STATE_DIM + v.GAIT_DIM + v.NUM_JOINTS + 4


@dataclass
class ImagineCfg:
  horizon: int = 32
  gamma: float = 0.99
  lam: float = 0.95
  dt: float = 0.02
  compile: bool = False


class Imagination:
  def __init__(self, cfg: ImagineCfg, task: v.VelocityTaskCfg, consts: v.RobotConsts):
    self.cfg, self.task, self.consts = cfg, task, consts
    self._step_fn = torch.compile(self._step, dynamic=False) if cfg.compile else self._step
    self.use_compiled_step = True

  @staticmethod
  def critic_input(s, previous_action, commands, remaining, gait):
    return torch.cat([s, previous_action, commands, remaining[:, None], gait], -1)

  def _step(self, s, previous, history, commands, remaining, gait, wm, actor):
    cfg, task = self.cfg, self.task
    critic_in = self.critic_input(s, previous, commands, remaining, gait)
    action = actor(history).clamp(-task.action_clip, task.action_clip)
    next_s = wm(s, action, previous)
    death = v.termination_probability(next_s, task)
    reward, _ = v.reward(s, next_s, action, previous, commands,
                         self.consts, task, cfg.dt, death, gait)
    gait, _ = v.advance_gait(gait, s[:, v.CONTACT], next_s[:, v.CONTACT], cfg.dt)
    commands, remaining = v.advance_commands(commands, remaining, cfg.dt, task.commands)
    frame = v.obs_frame(next_s, action, commands, task.observation_noise)
    history = v.push_history(history, frame, task.history)
    return next_s, action, history, commands, remaining, gait, reward, death, critic_in

  def rollout(self, wm, actor, critic, seed):
    cfg = self.cfg
    s, previous, history = seed["s"], seed["a_prev"], seed["obs"]
    commands, remaining = seed["commands"], seed["command_time"]
    gait = seed.get("gait", s.new_zeros(s.shape[0], v.GAIT_DIM))
    survival = torch.ones(s.shape[0], device=s.device)
    objective = torch.zeros_like(survival)
    rewards, survivals, inputs, continuations = [], [survival], [], []
    discount = 1.0
    step_fn = self._step_fn if self.use_compiled_step else self._step
    for _ in range(cfg.horizon):
      s, previous, history, commands, remaining, gait, reward, death, critic_in = step_fn(
        s, previous, history, commands, remaining, gait, wm, actor)
      inputs.append(critic_in)
      objective = objective + discount * survival * reward
      survival = survival * (1 - death)
      continuations.append(1 - death)
      survivals.append(survival)
      rewards.append(reward)
      discount *= cfg.gamma
    inputs.append(self.critic_input(s, previous, commands, remaining, gait))
    objective = objective + discount * survival * critic(inputs[-1]).squeeze(-1)
    return objective, {
      "rewards": torch.stack(rewards, 1).detach(),
      "survival": torch.stack(survivals, 1).detach(),
      "continuation": torch.stack(continuations, 1).detach(),
      "critic_in": torch.stack(inputs, 1).detach(),
    }

  @torch.no_grad()
  def gae_targets(self, critic, data):
    cfg = self.cfg
    rewards = data["rewards"]
    values = critic(data["critic_in"]).squeeze(-1)
    targets = torch.zeros_like(rewards)
    following = values[:, -1]
    for t in reversed(range(rewards.shape[1])):
      following = rewards[:, t] + cfg.gamma * data["continuation"][:, t] * (
        (1 - cfg.lam) * values[:, t + 1] + cfg.lam * following)
      targets[:, t] = following
    return targets
