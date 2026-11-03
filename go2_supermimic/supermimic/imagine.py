"""Differentiable velocity tracking rollouts and TD(lambda) critic targets."""

from dataclasses import dataclass

import torch

from go2_supermimic import velocity as v
from go2_supermimic.amp import AMPDiscriminator
from go2_supermimic.task_api import task_api

CRITIC_DIM = v.STATE_DIM + v.GAIT_DIM + v.NUM_JOINTS + 4


@dataclass
class ImagineCfg:
  horizon: int = 32
  gamma: float = 0.99
  lam: float = 0.95
  dt: float = 0.02
  compile: bool = False


class Imagination:
  def __init__(self, cfg: ImagineCfg, task: v.VelocityTaskCfg, consts: v.RobotConsts,
               amp: AMPDiscriminator | None = None):
    self.cfg, self.task, self.consts = cfg, task, consts
    self.api = task_api("g1" if task.reward_profile == "g1_walk" else "go2")
    self.critic_dim = self.api.STATE_DIM + self.api.GAIT_DIM + self.api.NUM_JOINTS + 4
    self.amp = amp
    self.amp_weight = consts.default_q.new_zeros(())
    self.reward_parameters = consts.default_q.new_empty(len(self.api.REWARD_NAMES) + 1)
    self.update_reward_parameters()
    self._step_fn = torch.compile(self._step, dynamic=False) if cfg.compile else self._step

  def update_reward_parameters(self):
    values = [getattr(self.task.rewards, name) for name in self.api.REWARD_NAMES]
    self.reward_parameters.copy_(
      self.reward_parameters.new_tensor(values + [self.task.joint_deviation_gait_fraction]))

  @staticmethod
  def critic_input(s, previous_action, commands, remaining, gait):
    return torch.cat([s, previous_action, commands, remaining[:, None], gait], -1)

  def _step(self, s, previous, history, commands, remaining, gait, wm, actor):
    cfg, task = self.cfg, self.task
    api = self.api
    critic_in = self.critic_input(s, previous, commands, remaining, gait)
    action = actor(history).clamp(-task.action_clip, task.action_clip)
    next_s = wm(s, action, previous)
    death = api.termination_probability(next_s, task)
    reward, _ = api.reward(s, next_s, action, previous, commands,
                         self.consts, task, cfg.dt, death, gait,
                         self.reward_parameters if cfg.compile else None)
    if self.amp is not None:
      reward = reward + self.amp_weight * cfg.dt * self.amp.reward(
        s, next_s, self.consts.default_q, commands)
    gait, _ = api.advance_gait(gait, s[:, api.CONTACT], next_s[:, api.CONTACT], cfg.dt)
    commands, remaining = api.advance_commands(commands, remaining, cfg.dt, task.commands)
    frame = api.obs_frame(next_s, action, commands, task.observation_noise)
    history = api.push_history(history, frame, task.history)
    return next_s, action, history, commands, remaining, gait, reward, death, critic_in

  def rollout(self, wm, actor, critic, seed):
    cfg = self.cfg
    s, previous, history = seed["s"], seed["a_prev"], seed["obs"]
    commands, remaining = seed["commands"], seed["command_time"]
    gait = seed.get("gait", s.new_zeros(s.shape[0], self.api.GAIT_DIM))
    survival = torch.ones(s.shape[0], device=s.device)
    objective = torch.zeros_like(survival)
    rewards, survivals, inputs, continuations = [], [survival], [], []
    discount = 1.0
    for _ in range(cfg.horizon):
      s, previous, history, commands, remaining, gait, reward, death, critic_in = self._step_fn(
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
