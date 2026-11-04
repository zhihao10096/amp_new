"""Compare imagined action-return gradients with paired physical interventions."""
import argparse
import hashlib
import json
from pathlib import Path

from isaaclab.app import AppLauncher


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--checkpoint", required=True)
  parser.add_argument("--output", required=True)
  parser.add_argument("--samples", type=int, default=32)
  parser.add_argument("--warmup", type=int, default=8)
  AppLauncher.add_app_launcher_args(parser)
  args = parser.parse_args()
  if args.samples < 2 or args.warmup < 1:
    parser.error("require at least two groups and a physical warm-up")
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
    groups, branches = args.samples, 10
    cfg.scene.num_envs, cfg.sim.device, cfg.seed = groups * branches, args.device, 1701
    cfg.task = task_from_dict(checkpoint["task_cfg"])
    cfg.task.observation_noise = False
    cfg.amp_num_frames = checkpoint["cfg"]["amp_num_frames"]
    cfg.amp_feature_schema = checkpoint["cfg"]["amp_feature_schema"]
    cfg.amp_reference_reset_fraction = 0.
    cfg.amp_reset_command_alignment = False
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
    ids = torch.arange(groups, device=env.device) * branches
    leg_mask = torch.zeros(29, device=env.device)
    leg_mask[list(g1.LEG_JOINT_IDS)] = 1

    class FirstAction:
      def __init__(self, action):
        self.first = action

      def __call__(self, history):
        if self.first is None:
          return actor(history)
        action, self.first = self.first, None
        return action

    results = {}
    for mode, fraction in (("ordinary", 0.), ("reference", 1.)):
      with torch.no_grad():
        env.cfg.amp_reference_reset_fraction = fraction
        env.reset(seed=1701)
        root = env.robot.data.root_state_w[ids].clone()
        root[:, :3] -= env.scene.env_origins[ids]
        root = root.repeat_interleave(branches, 0)
        root[:, :3] += env.scene.env_origins
        q = env.robot.data.joint_pos[ids].clone().repeat_interleave(branches, 0)
        qd = env.robot.data.joint_vel[ids].clone().repeat_interleave(branches, 0)
        env.robot.write_root_pose_to_sim(root[:, :7])
        env.robot.write_root_velocity_to_sim(root[:, 7:])
        env.robot.write_joint_state_to_sim(q, qd)
        env.command_time.copy_(env.command_time[ids].clone().repeat_interleave(branches))
        env.gait.zero_()
        env.action_manager.reset()
        env._amp_history_reset.fill_(True)
        env._transition_step = -1
        env.contact_sensor.reset()
        env.sim.forward()
        env.scene.update(env.step_dt)
        env.observation_manager.reset()
        obs = env.observation_manager.compute()
        warm_alive = torch.ones(env.num_envs, dtype=torch.bool, device=env.device)
        for _ in range(args.warmup):
          action = actor(obs["policy"]).clamp(-cfg.task.action_clip, cfg.task.action_clip)
          obs, _, term, trunc, _ = env.step(action)
          warm_alive &= ~(term | trunc)
        valid_groups = warm_alive.reshape(groups, branches).all(-1)
        state = robot_state(env).clone()
        seed = {"s": state, "obs": obs["policy"].clone(), "a_prev": env.actions.clone(),
                "commands": env.commands.clone(), "command_time": env.command_time.clone(),
                "gait": env.gait.clone(), "amp_history": env.amp_history_for_state(state).clone()}
        one = {name: value[ids].clone() for name, value in seed.items()}
        nominal = actor(one["obs"]).clamp(-cfg.task.action_clip, cfg.task.action_clip)
        zero_state_rms = float((state[ids] - state[ids + branches - 1]).square().mean().sqrt())
      first = nominal.detach().requires_grad_(True)
      objective, _ = imagine.rollout(wm, FirstAction(first), critic, one)
      gradient = torch.autograd.grad(objective.sum(), first)[0].detach()
      assert torch.isfinite(gradient).all()
      with torch.no_grad():
        full = gradient / gradient.square().mean(-1, keepdim=True).sqrt().clamp(min=1e-8)
        legs = gradient * leg_mask
        legs = legs / legs.square().mean(-1, keepdim=True).sqrt().clamp(min=1e-8)
        delta = torch.zeros(groups, branches, 29, device=env.device)
        interventions = []
        for start, direction, name in ((1, full, "all_joints"), (5, legs, "legs_only")):
          for offset, epsilon in ((0, .1), (2, .3)):
            delta[:, start + offset] = epsilon * direction
            delta[:, start + offset + 1] = -epsilon * direction
            interventions.append((start + offset, epsilon, name))
        first_actions = (actor(seed["obs"]) + delta.flatten(0, 1)).clamp(
          -cfg.task.action_clip, cfg.task.action_clip)
        model_actor = FirstAction(first_actions)
        s, prior, history = seed["s"], seed["a_prev"], seed["obs"]
        command, remaining, gait, amp_history = (
          seed["commands"], seed["command_time"], seed["gait"], seed["amp_history"])
        physical_alive = torch.ones(env.num_envs, dtype=torch.bool, device=env.device)
        model_alive = torch.ones(env.num_envs, device=env.device)
        physical_reward = torch.zeros(env.num_envs, device=env.device)
        model_reward = torch.zeros_like(physical_reward)
        reports = {}
        for step in range(1, 33):
          action = first_actions if step == 1 else actor(obs["policy"]).clamp(
            -cfg.task.action_clip, cfg.task.action_clip)
          obs, reward, term, trunc, extra = env.step(action)
          physical_reward += imagine.cfg.gamma ** (step - 1) * physical_alive * reward
          physical_alive &= ~(term | trunc)
          s, prior, history, command, remaining, gait, r, death, _, amp_history = imagine._step(
            s, prior, history, command, remaining, gait, amp_history, wm, model_actor)
          model_reward += imagine.cfg.gamma ** (step - 1) * model_alive * r
          model_alive *= 1 - death
          if step not in (1, 4, 8, 16, 32):
            continue
          after = extra["transition"]["next_state"]
          actual_context = imagine.critic_input(after, action, env.commands, env.command_time, env.gait)
          physical_target = physical_reward + imagine.cfg.gamma ** step * physical_alive * critic(
            actual_context).squeeze(-1)
          model_target = model_reward + imagine.cfg.gamma ** step * model_alive * critic(
            imagine.critic_input(s, prior, command, remaining, gait)).squeeze(-1)
          a, b = (x.reshape(groups, branches)[valid_groups]
                  for x in (physical_target, model_target))
          ar, br = (x.reshape(groups, branches)[valid_groups]
                    for x in (physical_reward, model_reward))
          zero = a[:, 0] - a[:, -1]
          row = {"valid_groups": int(valid_groups.sum()),
                 "zero_return_difference_rms": float(zero.square().mean().sqrt()),
                 "actual_baseline_return": float(a[:, 0].mean()),
                 "model_baseline_return": float(b[:, 0].mean()),
                 "directions": {}}
          for index, epsilon, name in interventions:
            actual = (a[:, index] - a[:, index + 1]) / (2 * epsilon)
            predicted = (b[:, index] - b[:, index + 1]) / (2 * epsilon)
            key = name + "/" + str(epsilon)
            row["directions"][key] = {
              "actual_bootstrap_slope_mean": float(actual.mean()),
              "model_bootstrap_slope_mean": float(predicted.mean()),
              "actual_reward_slope_mean": float(((ar[:, index] - ar[:, index + 1]) / (2 * epsilon)).mean()),
              "model_reward_slope_mean": float(((br[:, index] - br[:, index + 1]) / (2 * epsilon)).mean()),
              "actual_positive_fraction": float((actual > 0).float().mean()),
              "model_positive_fraction": float((predicted > 0).float().mean()),
              "direction_cosine": float(torch.nn.functional.cosine_similarity(
                actual[None], predicted[None])),
              "actual_plus_gain_mean": float((a[:, index] - a[:, 0]).mean()),
              "actual_minus_gain_mean": float((a[:, index + 1] - a[:, 0]).mean()),
            }
          reports[str(step)] = row
        assert valid_groups.any()
        results[mode] = {"warmup_zero_state_rms": zero_state_rms,
                         "first_action_gradient_rms": float(gradient.square().mean().sqrt()),
                         "horizons": reports}
    result = {"checkpoint": str(Path(args.checkpoint).resolve()),
              "checkpoint_sha256": hashlib.sha256(Path(args.checkpoint).read_bytes()).hexdigest(),
              "iteration": checkpoint["iteration"], "actuator_model": g1.ACTUATOR_MODEL,
              "state_schema": g1.STATE_SCHEMA, "samples": groups, "branches": branches,
              "warmup_steps": args.warmup, "command": [.6, 0., 0.], "results": results,
              "note": "Frozen diagnostic, not policy optimization or MPC. Directions are gradients "
                      "of the 32-step model objective with respect to its first action, normalized "
                      "to action RMS=1. Plus/minus interventions occur only at the first step; "
                      "later actions use the same frozen actor on each branch's own history. "
                      "Bootstrap uses the same critic and is not unbiased full-episode return. "
                      "Two unperturbed branches quantify physical pairing noise."}
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
