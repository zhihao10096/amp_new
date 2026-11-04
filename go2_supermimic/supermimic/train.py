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
from go2_supermimic.amp import AMPDiscriminator, state_features
from go2_supermimic.supermimic.buffer import ReplayBuffer
from go2_supermimic.supermimic.curriculum import curriculum_fraction, training_task
from go2_supermimic.supermimic.imagine import CRITIC_DIM, ImagineCfg, Imagination
from go2_supermimic.supermimic.world_model import RunningNorm, WorldModel, mlp
from go2_supermimic.task_api import amp_api, task_api

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
  compile_imagination: bool = False
  """Compile the imagined step, including scheduled rewards held on device."""
  matmul_precision: str = "high"
  critic_epochs: int = 3
  critic_minibatches: int = 4
  critic_real_fraction: float = 0.
  """Replace this fraction of imagined critic targets by real one-step TD."""
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
  reward_curriculum_start: int = 0
  reward_curriculum_end: int = 0
  """Zero disables the curriculum; otherwise reach final rewards at this iteration."""
  amp_motion_files: str = ""
  amp_feature_schema: str = "g1_amp_61_v1"
  amp_num_frames: int = 2
  """Chronological discriminator frames; four-frame support is G1-only."""
  amp_hidden: tuple[int, ...] = (512, 256)
  amp_weight: float = .5
  amp_lr: float = 1e-4
  amp_batch: int = 2048
  amp_updates: int = 2
  amp_update_interval: int = 1
  """Update D every N iterations after WM warm-up; actor cadence is unchanged."""
  amp_grad_penalty: float = 10.
  amp_ramp_iterations: int = 1000
  amp_reference_reset_fraction: float = .5

  def __post_init__(self):
    if self.matmul_precision not in ("highest", "high", "medium"):
      raise ValueError("matmul_precision must be highest, high or medium")
    for name in ("num_envs", "iterations", "collect_steps", "buffer_len", "wm_window", "wm_batch",
                 "wm_updates", "horizon", "imag_batch", "critic_epochs", "critic_minibatches",
                 "log_interval", "save_interval", "lr_decay_iterations", "amp_batch",
                 "amp_updates", "amp_update_interval", "amp_ramp_iterations"):
      if getattr(self, name) <= 0:
        raise ValueError(f"{name} must be positive")
    if self.buffer_len < self.wm_window:
      raise ValueError("buffer_len must be at least wm_window")
    if (self.amp_num_frames not in (2, 4)
        or self.buffer_len < self.amp_num_frames - 1
        or (self.amp_num_frames != 2 and self.task != "G1-AMP-Flat")):
      raise ValueError("amp_num_frames must be 2, or 4 for G1 AMP with enough replay")
    if self.imag_batch * self.horizon < self.critic_minibatches:
      raise ValueError("critic_minibatches exceeds the imagined transition count")
    if not 0 <= self.explore_frac <= 1:
      raise ValueError("explore_frac must be in [0, 1]")
    if not 0 <= self.critic_real_fraction <= 1:
      raise ValueError("critic_real_fraction must be in [0, 1]")
    if self.continue_run and not self.resume:
      raise ValueError("continue_run requires resume")
    if self.warm_start and self.resume:
      raise ValueError("warm_start and resume are mutually exclusive")
    if not 0 <= self.reward_curriculum_start <= self.reward_curriculum_end:
      raise ValueError("reward curriculum requires 0 <= start <= end")
    if (self.amp_weight < 0 or self.amp_grad_penalty < 0 or self.amp_lr <= 0
        or not 0 <= self.amp_reference_reset_fraction <= 1):
      raise ValueError("invalid AMP reward, learning rate, penalty or reset fraction")


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
  if data.get("reward_profile") not in (
      "unitree_gait", "g1_walk", "g1_legged_lab_walk_v1"):
    for name in ("feet_clearance", "feet_contact_without_command", "gait_duration", "diagonal_gait"):
      weights[name] = 0.0
  if "reward_profile" not in data:
    data["reward_profile"] = "legacy"
    for name in ("joint_velocity", "energy", "feet_air_time", "air_time_variance",
                 "feet_slide", "undesired_contacts"):
      weights[name] = 0.0
  api = task_api("g1" if data.get("reward_profile", "").startswith("g1_") else "go2")
  reward_type = (api.LeggedLabRewardWeights if data.get("reward_profile")
                 == "g1_legged_lab_walk_v1" else api.RewardWeights)
  data["rewards"] = reward_type(**weights)
  return v.VelocityTaskCfg(**data)


class Trainer:
  def __init__(self, cfg: TrainCfg, env):
    self.cfg, self.env = cfg, env
    api = self.api = task_api(env.robot_kind)
    self.critic_dim = api.STATE_DIM + api.GAIT_DIM + api.NUM_JOINTS + 4
    self.device = env.device
    torch.manual_seed(cfg.seed)
    obs, _ = env.reset()
    self.obs = obs["policy"]
    self.wm = WorldModel(cfg.wm_hidden, api.STATE_DIM, api.NUM_JOINTS).to(self.device)
    self.actor = Actor(self.obs.shape[-1], cfg.actor_hidden, api.NUM_JOINTS).to(self.device)
    self.critic = Critic(self.critic_dim, cfg.critic_hidden).to(self.device)
    self.opt_wm = torch.optim.Adam(self.wm.parameters(), lr=cfg.lr)
    self.opt_actor = torch.optim.Adam(self.actor.parameters(), lr=cfg.lr, betas=(0.9, 0.95))
    self.opt_critic = torch.optim.Adam(self.critic.parameters(), lr=cfg.lr)
    if env.cfg.amp_enabled:
      if env.robot_kind == "g1":
        self.amp = amp_api(env.robot_kind).AMPDiscriminator(
          cfg.amp_hidden, cfg.amp_feature_schema, cfg.amp_num_frames,
          command_gate=env.cfg.task.reward_profile != "g1_legged_lab_walk_v1").to(self.device)
      else:
        self.amp = amp_api(env.robot_kind).AMPDiscriminator(cfg.amp_hidden).to(self.device)
    else:
      self.amp = None
    self.opt_amp = (torch.optim.Adam(self.amp.parameters(), lr=cfg.amp_lr, weight_decay=1e-4)
                    if self.amp is not None else None)
    self.env.amp_discriminator = self.amp
    self.buf = ReplayBuffer(cfg.num_envs, cfg.buffer_len, self.obs.shape[-1], self.device,
                            api.STATE_DIM, api.NUM_JOINTS, api.GAIT_DIM,
                            amp_num_frames=cfg.amp_num_frames)
    self.imag = Imagination(
      ImagineCfg(horizon=cfg.horizon, dt=env.step_dt, compile=cfg.compile_imagination),
      env.cfg.task, env.consts, amp=self.amp)
    self.ou = torch.zeros(cfg.num_envs, api.NUM_JOINTS, device=self.device)
    self.explore = torch.arange(cfg.num_envs, device=self.device) < int(cfg.explore_frac * cfg.num_envs)
    if cfg.critic_real_fraction:
      self.real_env_ids = (~self.explore).nonzero(as_tuple=True)[0]
      if not len(self.real_env_ids):
        self.real_env_ids = torch.arange(cfg.num_envs, device=self.device)
      self.real_generator = torch.Generator(device=self.device).manual_seed(cfg.seed + 3719)
    self.start_it = self.env_steps = 0
    self.training_origin = {
      "kind": "random_initialization", "seed": cfg.seed,
      "environment_backend": env.environment_backend}
    if cfg.resume:
      self.load(cfg.resume)
    elif cfg.warm_start:
      self.warm_start(cfg.warm_start)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
    self.log_dir = Path(cfg.log_root) / f"{stamp}_{cfg.run_name}"
    self.log_dir.mkdir(parents=True)
    (self.log_dir / "config.json").write_text(json.dumps(
      {"train": asdict(cfg), "task": asdict(env.cfg.task), "dt": env.step_dt,
       "environment_backend": env.environment_backend,
       "robot_kind": env.robot_kind,
       **({"actuator_model": api.ACTUATOR_MODEL} if env.robot_kind == "g1" else {}),
       "amp_motion_metadata": env.amp_motion.metadata if self.amp is not None else None,
       "training_origin": self.training_origin}, indent=2) + "\n")
    self.writer = SummaryWriter(str(self.log_dir))
    self.metrics = {}
    self.metric_steps = 0
    self.set_training_rewards(self.start_it)
    print(f"Log directory: {self.log_dir}", flush=True)

  def set_training_rewards(self, iteration):
    cfg = self.cfg
    self.reward_fraction = curriculum_fraction(
      iteration, cfg.reward_curriculum_start, cfg.reward_curriculum_end)
    task = training_task(self.env.cfg.task, self.reward_fraction)
    self.imag.task = task
    if cfg.compile_imagination:
      self.imag.update_reward_parameters()
    # Reward terms read the live task as well as their manager weights.
    self.env.training_task = task
    task_weight = 1.
    if getattr(self, "amp", None) is not None:
      self.amp_fraction = min(1., iteration / cfg.amp_ramp_iterations)
      task_weight, style_weight = self.imag.set_amp_weight(cfg.amp_weight * self.amp_fraction)
      term = self.env.reward_manager.get_term_cfg("amp_style")
      term.weight = style_weight
      self.env.reward_manager.set_term_cfg("amp_style", term)
    for name in self.env.cfg.task.rewards.__dataclass_fields__:
      term = self.env.reward_manager.get_term_cfg(name)
      weight = task_weight * getattr(task.rewards, name)
      if term.weight != weight:
        term.weight = weight
        self.env.reward_manager.set_term_cfg(name, term)

  def load(self, path):
    ckpt = load_checkpoint(path, self.device)
    if ckpt.get("robot_kind", "go2") != getattr(self.env, "robot_kind", "go2"):
      raise ValueError("resume requires the same robot; use warm-start for transfer")
    if ckpt.get("robot_kind") == "g1":
      from go2_supermimic.g1 import require_implicit_pd
      require_implicit_pd(ckpt)
    self.training_origin = ckpt.get("training_origin", {
      "kind": "imported_checkpoint", "checkpoint": str(Path(path).resolve()),
      "environment_backend": ckpt.get("environment_backend", "legacy_direct")})
    if ckpt["format"] != CHECKPOINT_FORMAT:
      raise ValueError("use --warm-start to migrate a v1 model to the contact-aware dynamics")
    if (asdict(task_from_dict(ckpt["task_cfg"])) != asdict(self.env.cfg.task)
        or ckpt["dt"] != self.env.step_dt):
      raise ValueError("checkpoint task settings differ from the current environment")
    for name, model in (("actor", self.actor), ("critic", self.critic), ("world_model", self.wm)):
      model.load_state_dict(ckpt[name])
    for name, opt in (("opt_actor", self.opt_actor), ("opt_critic", self.opt_critic), ("opt_wm", self.opt_wm)):
      opt.load_state_dict(ckpt[name])
    if getattr(self, "amp", None) is not None:
      if ckpt.get("amp_motion_metadata") != self.env.amp_motion.metadata:
        raise ValueError("AMP resume requires identical motion data and temporal split")
      self.amp.load_state_dict(ckpt["amp"])
      self.opt_amp.load_state_dict(ckpt["opt_amp"])
      for group in self.opt_amp.param_groups:
        group["lr"] = self.cfg.amp_lr
    if self.cfg.critic_real_fraction and "real_critic_rng_state" in ckpt:
      self.real_generator.set_state(ckpt["real_critic_rng_state"].cpu())
    if self.cfg.continue_run:
      self.start_it, self.env_steps = ckpt["iteration"], ckpt["env_steps"]
      self.env.common_step_counter = ckpt["sim_steps"]
    print(f"Loaded {path}; starting after iteration {self.start_it}", flush=True)

  @torch.no_grad()
  def warm_start(self, path):
    ckpt = load_checkpoint(path, self.device)
    if ckpt.get("robot_kind") == "g1" or getattr(
        getattr(self, "env", None), "robot_kind", None) == "g1":
      from go2_supermimic.g1 import require_implicit_pd
      require_implicit_pd(ckpt)
    self.training_origin = {
      "kind": "warm_start", "checkpoint": str(Path(path).resolve()),
      "environment_backend": ckpt.get("environment_backend", "legacy_direct")}
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
      values.update(extras["reward_terms"])
      if self.amp is not None:
        values["amp_real_style"] = extras["amp_style"].mean()
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

  def fit_amp(self):
    metrics = {}
    for _ in range(self.cfg.amp_updates):
      with torch.no_grad():
        if self.amp.num_frames != 2:
          states = self.buf.sample_sequences(self.cfg.amp_batch)
          policy = self.amp.features(states, self.env.consts.default_q)
          expert = self.env.amp_motion.sample_sequences(self.cfg.amp_batch, train=True)
        else:
          before, after = self.buf.sample_pairs(self.cfg.amp_batch)
          policy = (self.amp.features(before, self.env.consts.default_q),
                    self.amp.features(after, self.env.consts.default_q))
          if self.env.robot_kind == "g1":
            expert = self.env.amp_motion.sample_pairs(
              self.cfg.amp_batch, train=True, feature_schema=self.cfg.amp_feature_schema)
          else:
            expert = self.env.amp_motion.sample_pairs(self.cfg.amp_batch, train=True)
      loss, values = self.amp.loss(expert, policy, self.cfg.amp_grad_penalty)
      self._update(loss, self.amp, self.opt_amp)
      values["amp_loss"] = loss.detach()
      for key, value in values.items():
        metrics[key] = metrics.get(key, 0.) + value.item() / self.cfg.amp_updates
    metrics["amp_reward_fraction"] = self.amp_fraction
    return metrics

  def improve_policy(self, update_actor=True):
    frozen = (self.wm, self.critic) + ((self.amp,) if self.amp is not None else ())
    for model in frozen:
      model.requires_grad_(False)
    try:
      # Critic warm-up consumes detached trajectories; keeping the actor's
      # entire differentiable rollout alive here needlessly holds GPU memory.
      with torch.set_grad_enabled(update_actor):
        objective, data = self.imag.rollout(
          self.wm, self.actor, self.critic, self.buf.sample_states(self.cfg.imag_batch))
      norm = self._update(-objective.mean(), self.actor, self.opt_actor) if update_actor else 0
    finally:
      for model in frozen:
        model.requires_grad_(True)
    targets = self.imag.gae_targets(self.critic, data).reshape(-1)
    inputs = data["critic_in"][:, :-1].reshape(-1, self.imag.critic_dim)
    real_stats = {}
    count = int(len(inputs) * self.cfg.critic_real_fraction)
    if count:
      physical = self.buf.sample_transitions(count, self.real_env_ids, self.real_generator)
      real_inputs, real_targets = self.imag.real_targets(self.critic, physical)
      count = len(real_inputs)
      # Preserve the critic's total sample/update budget, even when command
      # expiries leave fewer eligible real targets than requested.
      inputs = torch.cat((inputs[count:], real_inputs))
      targets = torch.cat((targets[count:], real_targets))
      real_stats = {"critic_real_fraction": count / len(inputs),
                    "critic_real_target_mean": real_targets.mean().item() if count else 0.}
    self.critic.norm.update(inputs)
    losses = []
    for _ in range(self.cfg.critic_epochs):
      indices = torch.randperm(inputs.shape[0], device=self.device)
      for selected in indices.tensor_split(self.cfg.critic_minibatches):
        loss = (self.critic(inputs[selected]).squeeze(-1) - targets[selected]).square().mean()
        self._update(loss, self.critic, self.opt_critic)
        losses.append(loss.item())
    return {**real_stats, "imagined_return": objective.mean().item(), "actor_grad_norm": norm,
            "critic_loss": sum(losses) / len(losses),
            "imagined_survival": data["survival"][:, -1].mean().item()}

  def save(self, iteration):
    path = self.log_dir / f"model_{iteration}.pt"
    temporary = path.with_suffix(".tmp")
    payload = {"format": CHECKPOINT_FORMAT, "iteration": iteration,
                "robot_kind": self.env.robot_kind,
                "environment_backend": self.env.environment_backend,
                "training_origin": self.training_origin,
                "reward_curriculum_fraction": self.reward_fraction,
                "cfg": asdict(self.cfg), "task_cfg": asdict(self.env.cfg.task), "dt": self.env.step_dt,
                "env_steps": self.env_steps, "sim_steps": self.env.common_step_counter,
                "obs_dim": self.obs.shape[-1], "actor": self.actor.state_dict(),
                "critic": self.critic.state_dict(), "world_model": self.wm.state_dict(),
                "opt_actor": self.opt_actor.state_dict(), "opt_critic": self.opt_critic.state_dict(),
                "opt_wm": self.opt_wm.state_dict()}
    if self.cfg.critic_real_fraction:
      payload["real_critic_rng_state"] = self.real_generator.get_state()
    if self.amp is not None:
      payload.update(amp=self.amp.state_dict(), opt_amp=self.opt_amp.state_dict(),
                     amp_motion_metadata=self.env.amp_motion.metadata,
                     amp_reward_fraction=self.amp_fraction)
    if self.env.robot_kind == "g1":
      from go2_supermimic.g1 import ACTUATOR_MODEL
      payload["actuator_model"] = ACTUATOR_MODEL
    torch.save(payload, temporary)
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
      if self.start_it == 0:
        self.save(0)
      while self.buf.size < cfg.wm_window:
        self.collect()
      for iteration in range(self.start_it + 1, cfg.iterations + 1):
        self.set_training_rewards(iteration)
        fraction = min(iteration / cfg.lr_decay_iterations, 1)
        lr = cfg.lr * (cfg.lr_final_frac + (1 - cfg.lr_final_frac) * 0.5 * (1 + math.cos(math.pi * fraction)))
        actor_start = cfg.warmup_iterations + cfg.critic_warmup_iterations
        ramp = min(1.0, max(0, iteration - actor_start) / max(1, cfg.actor_ramp_iterations))
        for opt, scale in ((self.opt_wm, 1), (self.opt_actor, cfg.actor_lr_scale * ramp), (self.opt_critic, 1)):
          for group in opt.param_groups:
            group["lr"] = lr * scale
        self.collect()
        stats = {"wm_loss": self.fit_world_model(),
                 "reward_curriculum_fraction": self.reward_fraction}
        if self.amp is not None:
          stats["amp_reward_fraction"] = self.amp_fraction
          if (iteration > cfg.warmup_iterations
              and (iteration - cfg.warmup_iterations) % cfg.amp_update_interval == 0):
            stats.update(self.fit_amp())
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
