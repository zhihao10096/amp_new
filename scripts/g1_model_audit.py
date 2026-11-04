"""Audit a frozen G1 actor and learned model against matching PhysX rollouts."""

import argparse
import hashlib
import json
from pathlib import Path

from isaaclab.app import AppLauncher


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--checkpoint", required=True)
  parser.add_argument("--output", required=True)
  parser.add_argument("--num-envs", type=int, default=128)
  parser.add_argument("--steps", type=int, default=64)
  parser.add_argument("--seed", type=int, default=1701)
  AppLauncher.add_app_launcher_args(parser)
  args = parser.parse_args()
  if args.num_envs < 1 or args.steps < 32:
    parser.error("require positive environments and at least 32 steps")
  launcher = AppLauncher(args)
  env = None
  try:
    import gymnasium as gym
    import torch

    import go2_supermimic.env
    from go2_supermimic import g1
    from go2_supermimic.env.factory import attach_evaluation_amp
    from go2_supermimic.env.g1_cfg import G1AmpEnvCfg
    from go2_supermimic.supermimic.imagine import ImagineCfg, Imagination
    from go2_supermimic.supermimic.state import robot_state
    from go2_supermimic.supermimic.train import Actor, Critic, load_checkpoint, task_from_dict
    from go2_supermimic.supermimic.world_model import WorldModel

    torch.set_num_threads(2)
    torch.set_float32_matmul_precision("highest")
    checkpoint = load_checkpoint(args.checkpoint, args.device)
    g1.require_trainable_state(checkpoint)
    cfg = G1AmpEnvCfg()
    cfg.scene.num_envs, cfg.sim.device, cfg.seed = args.num_envs, args.device, args.seed
    cfg.task = task_from_dict(checkpoint["task_cfg"])
    cfg.task.observation_noise = False
    cfg.amp_reference_reset_fraction = 0.
    cfg.amp_reset_command_alignment = False
    cfg.amp_num_frames = checkpoint["cfg"]["amp_num_frames"]
    cfg.amp_feature_schema = checkpoint["cfg"]["amp_feature_schema"]
    cfg.amp_weight = checkpoint["cfg"]["amp_weight"]
    env = gym.make("G1-AMP-Flat", cfg=cfg).unwrapped
    attach_evaluation_amp(env, checkpoint)
    actor = Actor(checkpoint["obs_dim"], tuple(checkpoint["cfg"]["actor_hidden"]), 29).to(env.device)
    critic = Critic(g1.STATE_DIM + g1.GAIT_DIM + 33, tuple(checkpoint["cfg"]["critic_hidden"])).to(env.device)
    wm = WorldModel(tuple(checkpoint["cfg"]["wm_hidden"]), g1.STATE_DIM, 29).to(env.device)
    for model, key in ((actor, "actor"), (critic, "critic"), (wm, "world_model")):
      model.load_state_dict(checkpoint[key])
      model.eval().requires_grad_(False)
    imagine = Imagination(ImagineCfg(horizon=32, dt=env.step_dt), cfg.task, env.consts,
                          env.amp_discriminator)
    imagine.set_amp_weight(cfg.amp_weight)
    env.set_command((.6, 0., 0.))
    horizons = [h for h in (1, 4, 8, 16, 32, 64) if h <= args.steps]
    groups = {"height": g1.Z, "gravity": g1.GRAV, "linear_velocity": g1.V_B,
              "angular_velocity": g1.W_B, "joint_position": g1.Q,
              "joint_velocity": g1.QD, "feet": g1.FOOT_POS, "contact": g1.CONTACT,
              "base_contact": g1.BASE_CONTACT}
    results = {}
    with torch.no_grad():
      for mode, fraction in (("ordinary", 0.), ("reference", 1.)):
        env.cfg.amp_reference_reset_fraction = fraction
        obs, _ = env.reset(seed=args.seed)
        initial = robot_state(env).clone()
        seed = {"s": initial, "obs": obs["policy"].clone(),
                "a_prev": env.actions.clone(), "commands": env.commands.clone(),
                "command_time": env.command_time.clone(), "gait": env.gait.clone(),
                "amp_history": env.amp_history_for_state(initial).clone()}
        states, following, actions, previous, dones = [], [], [], [], []
        physical_alive = torch.ones(env.num_envs, dtype=torch.bool, device=env.device)
        model_alive = torch.ones(env.num_envs, device=env.device)
        physical_return = torch.zeros(env.num_envs, device=env.device)
        model_return = torch.zeros_like(physical_return)
        s, prior, history = seed["s"], seed["a_prev"], seed["obs"]
        commands, remaining, gait = seed["commands"], seed["command_time"], seed["gait"]
        amp_history = seed["amp_history"]
        critic_in = imagine.critic_input(s, prior, commands, remaining, gait)
        seed_value = critic(critic_in).squeeze(-1)
        closed = {}
        actual_clipping = []
        for step in range(1, args.steps + 1):
          before, previous_action = robot_state(env).clone(), env.actions.clone()
          action = actor(obs["policy"]).clamp(-cfg.task.action_clip, cfg.task.action_clip)
          x = torch.cat((before, action, previous_action), -1)
          normalized = (x - wm.in_norm.mean) / (wm.in_norm.var.sqrt() + 1e-6)
          actual_clipping.append((normalized.abs() >= wm.in_norm.clip).float().mean())
          obs, reward, term, trunc, extra = env.step(action)
          after = extra["transition"]["next_state"].clone()
          states.append(before)
          following.append(after)
          actions.append(action)
          previous.append(previous_action)
          dones.append(term | trunc)
          physical_return += imagine.cfg.gamma ** (step - 1) * physical_alive * reward
          physical_alive &= ~(term | trunc)
          s, prior, history, commands, remaining, gait, model_reward, death, _, amp_history = (
            imagine._step(s, prior, history, commands, remaining, gait, amp_history, wm, actor))
          model_return += imagine.cfg.gamma ** (step - 1) * model_alive * model_reward
          model_alive *= 1 - death
          if step in horizons:
            # For surviving rows these are the native post-step gait/command
            # values. Terminal rows have zero bootstrap weight.
            actual_context = imagine.critic_input(
              after, action, env.commands, env.command_time, env.gait)
            actual_target = physical_return + (
              imagine.cfg.gamma ** step * physical_alive * critic(actual_context).squeeze(-1))
            model_target = model_return + imagine.cfg.gamma ** step * model_alive * critic(
              imagine.critic_input(s, prior, commands, remaining, gait)).squeeze(-1)
            closed[str(step)] = {
              "actual_discounted_reward": float(physical_return.mean()),
              "model_discounted_reward": float(model_return.mean()),
              "actual_bootstrapped_return": float(actual_target.mean()),
              "model_bootstrapped_return": float(model_target.mean()),
              "bootstrap_difference_rmse": float((actual_target - model_target).square().mean().sqrt()),
              "physical_survival": float(physical_alive.float().mean()),
              "model_survival": float(model_alive.mean()),
              "model_height": float(s[:, 0].mean()),
              "model_base_contact": float(s[:, g1.BASE_CONTACT].mean()),
            }
        states, following, actions, previous, dones = (
          torch.stack(items) for items in (states, following, actions, previous, dones))
        errors = {}
        for horizon in horizons:
          starts = torch.arange(0, args.steps - horizon + 1, 8, device=env.device)
          t = starts[:, None].expand(-1, env.num_envs).reshape(-1)
          ids = torch.arange(env.num_envs, device=env.device).repeat(len(starts))
          prediction = states[t, ids]
          valid = torch.ones(len(t), dtype=torch.bool, device=env.device)
          for offset in range(horizon):
            prediction = wm(prediction, actions[t + offset, ids], previous[t + offset, ids])
            if offset < horizon - 1:
              valid &= ~dones[t + offset, ids]
          error = prediction[valid] - following[t + horizon - 1, ids][valid]
          assert torch.isfinite(prediction).all(), (mode, horizon)
          errors[str(horizon)] = {
            "valid_windows": int(valid.sum()),
            "groups": {name: float(error[:, sl].square().mean().sqrt()) if len(error) else None
                       for name, sl in groups.items()},
          }
        results[mode] = {"closed_loop": closed, "open_loop": errors,
                         "seed_value": float(seed_value.mean()),
                         "action_abs_quantiles": torch.quantile(
                           actions.abs(), actions.new_tensor([.5, .9, .99])).tolist(),
                         "action_clip_fraction": float((actions.abs() >= cfg.task.action_clip).float().mean()),
                         "physical_wm_input_clip_fraction": float(torch.stack(actual_clipping).mean())}
        actor.requires_grad_(True)
        with torch.enable_grad():
          objective, _ = imagine.rollout(wm, actor, critic, seed)
          gradients = torch.autograd.grad(objective.mean(), tuple(actor.parameters()))
          assert torch.isfinite(objective).all() and all(torch.isfinite(g).all() for g in gradients)
          results[mode]["actor_gradient_norm"] = float(sum(g.square().sum() for g in gradients).sqrt())
        actor.requires_grad_(False)
    result = {"checkpoint": str(Path(args.checkpoint).resolve()),
              "checkpoint_sha256": hashlib.sha256(Path(args.checkpoint).read_bytes()).hexdigest(),
              "iteration": checkpoint["iteration"], "state_schema": g1.STATE_SCHEMA,
              "actuator_model": g1.ACTUATOR_MODEL, "reward_profile": cfg.task.reward_profile,
              "amp_num_frames": cfg.amp_num_frames, "amp_weight": cfg.amp_weight,
              "steps": args.steps, "num_envs": env.num_envs, "seed": args.seed,
              "environment_backend": env.environment_backend, "results": results,
              "note": "Frozen model diagnostic at fixed 0.6 m/s. Ordinary/reference resets "
                      "reported separately; actual terminal next states and AMP history preserved. "
                      "Bootstrap targets are not full episode Monte Carlo returns. No training."}
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2), flush=True)
  finally:
    if env is not None:
      env.close()
    launcher.app.close()


if __name__ == "__main__":
  main()
