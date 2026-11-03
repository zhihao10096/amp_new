"""SuperMimic: collect in PhysX, fit dynamics, improve the policy in imagination."""

from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import torch
from torch import nn
from torch.utils.tensorboard import SummaryWriter

from go2_supermimic import velocity as v
from go2_supermimic.supermimic.buffer import ReplayBuffer
from go2_supermimic.supermimic.imagine import CRITIC_DIM, ImagineCfg, Imagination
from go2_supermimic.supermimic.world_model import RunningNorm, WorldModel, mlp

CHECKPOINT_FORMAT = "isaaclab_velocity_v2"
LEGACY_FORMAT = "isaaclab_velocity_v1"


@dataclass
class TrainCfg:
  task: str = "Go2-Velocity-Flat"
  num_envs: int = 1024
  iterations: int = 40000
  warmup_iterations: int = 300
  critic_warmup_iterations: int = 200
  collect_steps: int = 4
  buffer_len: int = 256
  action_noise: float = 0.1
  explore_frac: float = 0.25
  explore_noise: float = 0.3
  wm_hidden: tuple[int, ...] = (512, 512, 512)
  wm_window: int = 8
  wm_batch: int = 1024
  wm_updates: int = 2
  actor_hidden: tuple[int, ...] = (512, 256, 128)
  critic_hidden: tuple[int, ...] = (512, 256, 128)
  horizon: int = 32
  imag_batch: int = 2048
  critic_epochs: int = 3
  critic_minibatches: int = 4
  lr: float = 2e-4
  actor_lr_scale: float = 0.3
  actor_ramp_iterations: int = 500
  lr_decay_iterations: int = 30000
  lr_final_frac: float = 0.03
  grad_clip: float = 1.0
  resume: str = ""
  warm_start: str = ""
  continue_run: bool = False
  log_interval: int = 25
  save_interval: int = 1000
  seed: int = 0
  run_name: str = "velocity"
  log_root: str = "logs/supermimic"
  robot_usd: str = ""
  stop_file: str = ""
  """If this file exists, save at the next iteration boundary and exit."""

  def __post_init__(self):
    for name in ("num_envs", "iterations", "collect_steps", "buffer_len", "wm_window", "wm_batch",
                 "wm_updates", "horizon", "imag_batch", "critic_epochs", "critic_minibatches",
                 "log_interval", "save_interval", "lr_decay_iterations"):
      if getattr(self, name) <= 0:
        raise ValueError(f"{name} must be positive")
    if self.buffer_len < self.wm_window:
      raise ValueError("buffer_len must be at least wm_window")
    if self.imag_batch * self.horizon < self.critic_minibatches:
      raise ValueError("critic_minibatches exceeds the imagined transition count")
    if not 0 <= self.explore_frac <= 1:
      raise ValueError("explore_frac must be in [0, 1]")
    if self.continue_run and not self.resume:
      raise ValueError("continue_run requires resume")
    if self.warm_start and self.resume:
      raise ValueError("warm_start and resume are mutually exclusive")


class Actor(nn.Module):
  def __init__(self, obs_dim, hidden, act_dim=v.NUM_JOINTS):
    super().__init__()
    self.norm = RunningNorm(obs_dim)
    self.net = mlp(obs_dim, hidden, act_dim, act=nn.ELU)
    # Start close to the standing pose while the dynamics model warms up.
    nn.init.uniform_(self.net[-1].weight, -0.01, 0.01)
    nn.init.zeros_(self.net[-1].bias)

  def forward(self, obs):
    return self.net(self.norm(obs))


class Critic(nn.Module):
  def __init__(self, in_dim, hidden):
    super().__init__()
    self.norm = RunningNorm(in_dim)
    self.net = mlp(in_dim, hidden, 1, act=nn.ELU)

  def forward(self, x):
    return self.net(self.norm(x))


def load_checkpoint(path, device):
  checkpoint = torch.load(path, map_location=device, weights_only=False)
  if checkpoint.get("format") not in (CHECKPOINT_FORMAT, LEGACY_FORMAT):
    raise ValueError("This checkpoint is incompatible with Isaac Lab velocity tracking")
  return checkpoint


def task_from_dict(data):
  data = dict(data)
  data["commands"] = v.CommandCfg(**data["commands"])
  weights = dict(data["rewards"])
  if data.get("reward_profile") != "unitree_gait":
    for name in ("feet_clearance", "feet_contact_without_command", "gait_duration", "diagonal_gait"):
      weights[name] = 0.0
  if "reward_profile" not in data:
    data["reward_profile"] = "legacy"
    for name in ("joint_velocity", "energy", "feet_air_time", "air_time_variance",
                 "feet_slide", "undesired_contacts"):
      weights[name] = 0.0
  data["rewards"] = v.RewardWeights(**weights)
  return v.VelocityTaskCfg(**data)


class Trainer:
  def __init__(self, cfg: TrainCfg, env):
    self.cfg, self.env = cfg, env
    self.device = env.device
    torch.manual_seed(cfg.seed)
    obs, _ = env.reset()
    self.obs = obs["policy"]
    self.wm = WorldModel(cfg.wm_hidden).to(self.device)
    self.actor = Actor(self.obs.shape[-1], cfg.actor_hidden).to(self.device)
    self.critic = Critic(CRITIC_DIM, cfg.critic_hidden).to(self.device)
    self.opt_wm = torch.optim.Adam(self.wm.parameters(), lr=cfg.lr)
    self.opt_actor = torch.optim.Adam(self.actor.parameters(), lr=cfg.lr, betas=(0.9, 0.95))
    self.opt_critic = torch.optim.Adam(self.critic.parameters(), lr=cfg.lr)
    self.buf = ReplayBuffer(cfg.num_envs, cfg.buffer_len, self.obs.shape[-1], self.device)
    self.imag = Imagination(ImagineCfg(horizon=cfg.horizon, dt=env.step_dt), env.cfg.task, env.consts)
    self.ou = torch.zeros(cfg.num_envs, v.NUM_JOINTS, device=self.device)
    self.explore = torch.arange(cfg.num_envs, device=self.device) < int(cfg.explore_frac * cfg.num_envs)
    self.start_it = self.env_steps = 0
    if cfg.resume:
      self.load(cfg.resume)
    elif cfg.warm_start:
      self.warm_start(cfg.warm_start)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
    self.log_dir = Path(cfg.log_root) / f"{stamp}_{cfg.run_name}"
    self.log_dir.mkdir(parents=True)
    (self.log_dir / "config.json").write_text(json.dumps(
      {"train": asdict(cfg), "task": asdict(env.cfg.task), "dt": env.step_dt}, indent=2) + "\n")
    self.writer = SummaryWriter(str(self.log_dir))
    self.metrics = {}
    self.metric_steps = 0
    print(f"Log directory: {self.log_dir}", flush=True)

  def load(self, path):
    ckpt = load_checkpoint(path, self.device)
    if ckpt["format"] != CHECKPOINT_FORMAT:
      raise ValueError("use --warm-start to migrate a v1 model to the contact-aware dynamics")
    if (asdict(task_from_dict(ckpt["task_cfg"])) != asdict(self.env.cfg.task)
        or ckpt["dt"] != self.env.step_dt):
      raise ValueError("checkpoint task settings differ from the current environment")
    for name, model in (("actor", self.actor), ("critic", self.critic), ("world_model", self.wm)):
      model.load_state_dict(ckpt[name])
    for name, opt in (("opt_actor", self.opt_actor), ("opt_critic", self.opt_critic), ("opt_wm", self.opt_wm)):
      opt.load_state_dict(ckpt[name])
    if self.cfg.continue_run:
      self.start_it, self.env_steps = ckpt["iteration"], ckpt["env_steps"]
      self.env.common_step_counter = ckpt["sim_steps"]
    print(f"Loaded {path}; starting after iteration {self.start_it}", flush=True)

  @torch.no_grad()
  def warm_start(self, path):
    ckpt = load_checkpoint(path, self.device)
    self.actor.load_state_dict(ckpt["actor"])
    if ckpt["format"] == CHECKPOINT_FORMAT:
      self.wm.load_state_dict(ckpt["world_model"])
    else:
      # Preserve the old state/action mapping while adding foot channels.
      old, new = ckpt["world_model"], self.wm.state_dict()
      old_dim, new_dim = v.BASE_STATE_DIM, v.STATE_DIM
      mapping = list(range(old_dim)) + list(range(new_dim, new_dim + 2 * v.NUM_JOINTS))
      for name, tensor in old.items():
        if name == "net.0.weight":
          new[name].zero_()
          new[name][:, mapping] = tensor
        elif name in ("in_norm.mean", "in_norm.var"):
          new[name][mapping] = tensor
        elif name in ("out_norm.mean", "out_norm.var"):
          new[name][:old_dim] = tensor
        elif name == f"net.{len(self.wm.net) - 1}.weight":
          new[name].zero_()
          new[name][:old_dim] = tensor
        elif name == f"net.{len(self.wm.net) - 1}.bias":
          new[name].zero_()
          new[name][:old_dim] = tensor
        elif new[name].shape == tensor.shape:
          new[name] = tensor
        else:
          raise ValueError(f"cannot migrate world-model parameter {name}")
      # New foot channels have no historical statistics; refit all dynamics
      # normalization from the warm-up collection instead of diluting them
      # with the old model's millions of samples.
      new["in_norm.count"].fill_(1e-4)
      new["out_norm.count"].fill_(1e-4)
      self.wm.load_state_dict(new)
    print(f"Warm-started actor/dynamics from {path}; fresh critic/optimizers for new rewards", flush=True)

  @torch.no_grad()
  def collect(self):
    from go2_supermimic.supermimic.state import robot_state

    for _ in range(self.cfg.collect_steps):
      s = robot_state(self.env).clone()
      previous = self.env.actions.clone()
      commands, remaining = self.env.commands.clone(), self.env.command_time.clone()
      gait = self.env.gait.clone()
      action = self.actor(self.obs)
      dt = self.env.step_dt
      self.ou = self.ou * (1 - 2 * dt) + self.cfg.explore_noise * (4 * dt)**0.5 * torch.randn_like(action)
      noise = torch.where(self.explore[:, None], self.ou, self.cfg.action_noise * torch.randn_like(action))
      action = (action + noise).clamp(-self.env.cfg.task.action_clip, self.env.cfg.task.action_clip)
      obs, reward, term, trunc, extras = self.env.step(action)
      next_s = extras["transition"]["next_state"]
      if not (torch.isfinite(next_s).all() & torch.isfinite(reward).all()):
        raise FloatingPointError("nonfinite PhysX transition")
      done = term | trunc
      self.buf.add(s, next_s, action, previous, self.obs, commands, remaining, done, gait)
      self.wm.update_stats(s, action, previous, next_s)
      self.actor.norm.update(self.obs)
      self.ou[done] = 0
      self.obs = obs["policy"]
      self.env_steps += self.env.num_envs
      self.metric_steps += 1
      values = {"real_reward": reward.mean(), "falls": term.sum(),
                "timeouts": trunc.sum(),
                "linear_error": extras["transition"]["linear_error"].mean(),
                "yaw_error": extras["transition"]["yaw_error"].mean()}
      values.update(extras["log"])
      # One batched read instead of synchronizing for every reward scalar.
      scalars = torch.stack([value.float() for value in values.values()]).tolist()
      for name, value in zip(values, scalars):
        self.metrics[name] = self.metrics.get(name, 0) + value

  def _update(self, loss, model, optimizer):
    if not torch.isfinite(loss):
      raise FloatingPointError("nonfinite training loss")
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    norm = nn.utils.clip_grad_norm_(model.parameters(), self.cfg.grad_clip, error_if_nonfinite=True)
    optimizer.step()
    return norm.item()

  def fit_world_model(self):
    losses = []
    for _ in range(self.cfg.wm_updates):
      batch = self.buf.sample_windows(self.cfg.wm_batch, self.cfg.wm_window)
      loss = self.wm.loss(**batch)
      self._update(loss, self.wm, self.opt_wm)
      losses.append(loss.item())
    return sum(losses) / len(losses)

  def improve_policy(self, update_actor=True):
    for model in (self.wm, self.critic):
      model.requires_grad_(False)
    try:
      objective, data = self.imag.rollout(
        self.wm, self.actor, self.critic, self.buf.sample_states(self.cfg.imag_batch))
      norm = self._update(-objective.mean(), self.actor, self.opt_actor) if update_actor else 0
    finally:
      for model in (self.wm, self.critic):
        model.requires_grad_(True)
    targets = self.imag.gae_targets(self.critic, data).reshape(-1)
    inputs = data["critic_in"][:, :-1].reshape(-1, CRITIC_DIM)
    self.critic.norm.update(inputs)
    losses = []
    for _ in range(self.cfg.critic_epochs):
      indices = torch.randperm(inputs.shape[0], device=self.device)
      for selected in indices.tensor_split(self.cfg.critic_minibatches):
        loss = (self.critic(inputs[selected]).squeeze(-1) - targets[selected]).square().mean()
        self._update(loss, self.critic, self.opt_critic)
        losses.append(loss.item())
    return {"imagined_return": objective.mean().item(), "actor_grad_norm": norm,
            "critic_loss": sum(losses) / len(losses),
            "imagined_survival": data["survival"][:, -1].mean().item()}

  def save(self, iteration):
    path = self.log_dir / f"model_{iteration}.pt"
    temporary = path.with_suffix(".tmp")
    torch.save({"format": CHECKPOINT_FORMAT, "iteration": iteration,
                "cfg": asdict(self.cfg), "task_cfg": asdict(self.env.cfg.task), "dt": self.env.step_dt,
                "env_steps": self.env_steps, "sim_steps": self.env.common_step_counter,
                "obs_dim": self.obs.shape[-1], "actor": self.actor.state_dict(),
                "critic": self.critic.state_dict(), "world_model": self.wm.state_dict(),
                "opt_actor": self.opt_actor.state_dict(), "opt_critic": self.opt_critic.state_dict(),
                "opt_wm": self.opt_wm.state_dict()}, temporary)
    temporary.replace(path)
    print(f"Saved {path}", flush=True)
    return path

  def run(self):
    cfg = self.cfg
    started = time.monotonic()
    interval_started = started
    interval_env_steps = self.env_steps
    interval_iteration = self.start_it
    try:
      while self.buf.size < cfg.wm_window:
        self.collect()
      for iteration in range(self.start_it + 1, cfg.iterations + 1):
        fraction = min(iteration / cfg.lr_decay_iterations, 1)
        lr = cfg.lr * (cfg.lr_final_frac + (1 - cfg.lr_final_frac) * 0.5 * (1 + math.cos(math.pi * fraction)))
        actor_start = cfg.warmup_iterations + cfg.critic_warmup_iterations
        ramp = min(1.0, max(0, iteration - actor_start) / max(1, cfg.actor_ramp_iterations))
        for opt, scale in ((self.opt_wm, 1), (self.opt_actor, cfg.actor_lr_scale * ramp), (self.opt_critic, 1)):
          for group in opt.param_groups:
            group["lr"] = lr * scale
        self.collect()
        stats = {"wm_loss": self.fit_world_model()}
        if iteration > cfg.warmup_iterations:
          stats.update(self.improve_policy(update_actor=iteration > actor_start))
        if iteration % cfg.log_interval == 0 or iteration == cfg.iterations:
          now = time.monotonic()
          seconds = max(now - interval_started, 1e-6)
          stats["env_samples_per_second"] = (self.env_steps - interval_env_steps) / seconds
          stats["iterations_per_second"] = (iteration - interval_iteration) / seconds
          stats["imagined_samples_per_second"] = (
            cfg.imag_batch * cfg.horizon * max(0, iteration - max(interval_iteration, cfg.warmup_iterations))
            / seconds)
          stats.update({key: value / self.metric_steps for key, value in self.metrics.items()})
          stats["falls_per_minute"] = self.metrics["falls"] * 60 / (
            self.metric_steps * self.env.num_envs * self.env.step_dt)
          for key, value in stats.items():
            self.writer.add_scalar(f"train/{key}", value, iteration)
          self.writer.flush()
          print(f"it {iteration}/{cfg.iterations} | {time.monotonic() - started:.1f}s | "
                + " | ".join(f"{key} {value:.5g}" for key, value in stats.items()), flush=True)
          self.metrics.clear()
          self.metric_steps = 0
          interval_started, interval_env_steps, interval_iteration = now, self.env_steps, iteration
        if iteration % cfg.save_interval == 0 or iteration == cfg.iterations:
          self.save(iteration)
        if cfg.stop_file and Path(cfg.stop_file).exists():
          if iteration % cfg.save_interval != 0 and iteration != cfg.iterations:
            self.save(iteration)
          print(f"Stopped at iteration {iteration} after checkpoint request {cfg.stop_file}", flush=True)
          break
    finally:
      self.writer.close()
