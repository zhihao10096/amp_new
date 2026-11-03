"""Explicit A1 Manager/AMP GPU integration and compiled-gradient regression."""

import argparse
import json
import traceback
from dataclasses import replace
from pathlib import Path

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", default="logs/amp_a1/integration.json")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
launcher = AppLauncher(args)
env = None
try:
  import torch
  import gymnasium as gym
  from isaaclab.envs import ManagerBasedRLEnv

  import go2_supermimic.env
  from go2_supermimic import velocity as v
  from go2_supermimic.amp import AMPDiscriminator, a1_foot_positions
  from go2_supermimic.env.env_cfg import A1AmpEnvCfg
  from go2_supermimic.supermimic.imagine import CRITIC_DIM, ImagineCfg, Imagination
  from go2_supermimic.supermimic.state import robot_state
  from go2_supermimic.supermimic.train import Actor, Critic
  from go2_supermimic.supermimic.world_model import WorldModel

  torch.set_float32_matmul_precision("highest")
  cfg = A1AmpEnvCfg()
  cfg.scene.num_envs = 32
  cfg.sim.device = args.device
  cfg.seed = 23
  cfg.task.observation_noise = False
  cfg.task.commands.resampling_time = (.04, .06)
  cfg.episode_length_s = .12
  env = gym.make("A1-AMP-Flat", cfg=cfg).unwrapped
  assert isinstance(env, ManagerBasedRLEnv) and type(env).step is ManagerBasedRLEnv.step
  assert type(env)._reset_idx is ManagerBasedRLEnv._reset_idx
  assert env.robot_kind == "a1"
  assert "Head_.*" not in cfg.undesired_contact_patterns
  assert "amp_style" in env.reward_manager.active_terms
  disc = AMPDiscriminator((32, 16)).to(env.device).requires_grad_(False)
  disc.norm.update(torch.cat(env.amp_motion.sample_pairs(1024)))
  env.amp_discriminator = disc
  obs, _ = env.reset()
  n, resets, falls, resamples, max_fk_error = env.num_envs, 0, 0, 0, 0.
  for step in range(30):
    weight = 0. if step < 4 else (.123 if step < 8 else cfg.amp_weight)
    term_cfg = env.reward_manager.get_term_cfg("amp_style")
    term_cfg.weight = weight
    env.reward_manager.set_term_cfg("amp_style", term_cfg)
    if step == 8:
      root = env.robot.data.root_state_w[:1].clone()
      root[:, 3:7] = root.new_tensor([[0., 1., 0., 0.]])
      env.robot.write_root_pose_to_sim(root[:, :7], env_ids=torch.tensor([0], device=env.device))
    before = robot_state(env).clone()
    previous, commands, remaining = env.actions.clone(), env.commands.clone(), env.command_time.clone()
    history, gait = obs["policy"].clone(), env.gait.clone()
    action = torch.randn(n, 12, device=env.device) * .1
    obs, actual, term, trunc, extras = env.step(action)
    state = extras["transition"]["next_state"]
    base, _ = v.reward(before, state, action, previous, commands, env.consts,
                       cfg.task, env.step_dt, term, gait)
    style = disc.reward(before, state, env.consts.default_q, commands)
    torch.testing.assert_close(actual, base + weight * env.step_dt * style)
    torch.testing.assert_close(extras["amp_style"], style)
    fk = a1_foot_positions(state[:, v.Q] + env.consts.default_q)
    max_fk_error = max(max_fk_error, (fk - state[:, v.FOOT_POS]).abs().max().item())
    done = term | trunc
    frame = v.obs_frame(robot_state(env), env.actions, env.commands)
    expected = v.push_history(history, frame, cfg.task.history)
    repeated = torch.cat([frame[name].repeat(1, cfg.task.history) for name, _ in v.OBS_TERMS], -1)
    expected[done] = repeated[done]
    torch.testing.assert_close(obs["policy"], expected)
    assert not env.gait[done].any()
    resets += done.sum().item()
    falls += term.sum().item()
    resamples += ((remaining <= env.step_dt) & ~done).sum().item()
  assert resets and falls and resamples
  assert max_fk_error < 1e-5, max_fk_error
  # Evaluation must also work from an ordinary standing reset without motion data.
  env.cfg.amp_reference_reset_fraction = 0.
  env.set_command((.8, 0., 0.))
  obs, _ = env.reset()
  for _ in range(10):
    obs, _, _, _, _ = env.step(torch.zeros(n, 12, device=env.device))
    torch.testing.assert_close(env.commands, env.fixed_command)

  task = replace(cfg.task, observation_noise=False)
  wm = WorldModel((32,)).to(env.device).requires_grad_(False)
  wm.out_norm.var.fill_(1e-4)
  actor = Actor(obs["policy"].shape[-1], (32,)).to(env.device)
  critic = Critic(CRITIC_DIM, (32,)).to(env.device).requires_grad_(False)
  seed = {"s": robot_state(env).clone(), "a_prev": env.actions.clone(),
          "obs": obs["policy"].clone(), "commands": env.commands.clone(),
          # Compare identical inputs without two independent resampling draws.
          "command_time": torch.full((n,), 10., device=env.device), "gait": env.gait.clone()}
  eager = Imagination(ImagineCfg(horizon=4), task, env.consts, disc)
  compiled = Imagination(ImagineCfg(horizon=4, compile=True), task, env.consts, disc)
  differences = []
  for weight in (.0, .123, .5):
    eager.amp_weight.fill_(weight)
    compiled.amp_weight.fill_(weight)
    a, _ = eager.rollout(wm, actor, critic, seed)
    b, _ = compiled.rollout(wm, actor, critic, seed)
    print(f"compile weight={weight}: return max error={(a - b).abs().max().item()}", flush=True)
    torch.testing.assert_close(a, b)
    ga = torch.autograd.grad(a.sum(), tuple(actor.parameters()))
    gb = torch.autograd.grad(b.sum(), tuple(actor.parameters()))
    for x, y in zip(ga, gb):
      torch.testing.assert_close(x, y)
    differences.append({"weight": weight, "return_max_error": (a - b).abs().max().item(),
                        "actor_gradient_max_error": max((x - y).abs().max().item()
                                                         for x, y in zip(ga, gb))})
  assert all(p.grad is None for model in (wm, critic, disc) for p in model.parameters())
  result = {"passed": True, "robot_kind": env.robot_kind, "resets": resets,
            "falls": falls, "command_resamples": resamples,
            "fk_max_error_m": max_fk_error, "compiled": differences,
            "motion_metadata": env.amp_motion.metadata}
  path = Path(args.output)
  path.parent.mkdir(exist_ok=True, parents=True)
  path.write_text(json.dumps(result, indent=2) + "\n")
  print(json.dumps(result, indent=2), flush=True)
except Exception:
  traceback.print_exc()
  raise
finally:
  if env is not None:
    env.close()
  launcher.app.close()
