"""Audit imagined first-action or actor-step gains with physical interventions."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from isaaclab.app import AppLauncher


def main() -> None:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--checkpoint", required=True)
  parser.add_argument("--output", required=True)
  parser.add_argument("--samples", type=int, default=128)
  parser.add_argument("--warmup", type=int, default=8)
  parser.add_argument("--seed", type=int, default=1701)
  parser.add_argument("--steps", type=int, default=128)
  parser.add_argument("--epsilons", type=float, nargs="+", default=[.01, .03, .1])
  parser.add_argument("--intervention", choices=("first_action", "policy_step"),
                      default="first_action")
  AppLauncher.add_app_launcher_args(parser)
  args = parser.parse_args()
  if (args.samples < 2 or args.warmup < 1 or args.steps < 32
      or any(not 0 < e < 1 for e in args.epsilons)
      or len(set(args.epsilons)) != len(args.epsilons)):
    parser.error("require groups, warm-up, >=32 steps and distinct epsilons in (0, 1)")
  if Path(args.output).exists():
    parser.error("output already exists; use a new path to preserve evidence")
  launcher = AppLauncher(args)
  env = None
  try:
    import gymnasium as gym
    import torch

    import go2_supermimic.env
    from go2_supermimic import g1
    from go2_supermimic.g1_validation import evaluation_falls
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
    groups = args.samples
    branches = 6 if args.intervention == "policy_step" else 2 + 4 * len(args.epsilons)
    cfg.scene.num_envs, cfg.sim.device, cfg.seed = groups * branches, args.device, args.seed
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
    # Roles are randomized within each physical clone group. Fixed role slots
    # can otherwise turn contact/origin differences into an apparent effect.
    generator = torch.Generator(device=env.device).manual_seed(args.seed + 1)
    role_slots = torch.rand(groups, branches, device=env.device,
                            generator=generator).argsort(-1)
    role_ids = ids[:, None] + role_slots
    seed_ids = role_ids[:, 0]
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

    class RolePolicy:
      def __init__(self, candidates):
        self.candidates = candidates

      def __call__(self, history):
        action = actor(history).clone()
        for role, candidate in self.candidates.items():
          action[role_ids[:, role]] = candidate(history[role_ids[:, role]])
        return action

    def paired_summary(values):
      """Resample clone groups, preserving the within-group intervention pair."""
      n = values.numel()
      if not n:
        return {"count": 0, "mean": None, "ci95": None}
      resamples = torch.randint(n, (2048, n), device=env.device, generator=generator)
      means = values[resamples].mean(-1)
      return {"count": n, "mean": float(values.mean()),
              "std": float(values.std()) if n > 1 else 0.,
              "ci95": torch.quantile(means, means.new_tensor([.025, .975])).tolist()}

    def role_values(values, valid):
      return values[role_ids][valid]

    results = {}
    for mode, fraction in (("ordinary", 0.), ("reference", 1.)):
      with torch.no_grad():
        env.cfg.amp_reference_reset_fraction = fraction
        env.reset(seed=args.seed)
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
          # Use the same control for every clone during contact warm-up.
          action = actor(obs["policy"][ids]).clamp(
            -cfg.task.action_clip, cfg.task.action_clip).repeat_interleave(branches, 0)
          obs, _, term, trunc, _ = env.step(action)
          warm_alive &= ~(term | trunc)
        valid_groups = warm_alive.reshape(groups, branches).all(-1)
        if int(valid_groups.sum()) < 2:
          raise RuntimeError("too few surviving clone groups for a paired estimate")
        state = robot_state(env).clone()
        seed = {"s": state, "obs": obs["policy"].clone(), "a_prev": env.actions.clone(),
                "commands": env.commands.clone(), "command_time": env.command_time.clone(),
                "gait": env.gait.clone(), "amp_history": env.amp_history_for_state(state).clone()}
        one = {name: value[seed_ids].clone() for name, value in seed.items()}
        nominal = actor(one["obs"]).clamp(-cfg.task.action_clip, cfg.task.action_clip)
        pairing = {
          name: float((value[role_ids[:, 0]] - value[role_ids[:, -1]]).square().mean().sqrt())
          for name, value in seed.items()}
      step_info = {}
      candidates = {}
      if args.intervention == "policy_step":
        # Restore the production Adam moments and perform exactly one temporary
        # actor update. WM, D, critic, observation norm and checkpoint stay fixed.
        candidate = copy.deepcopy(actor).requires_grad_(True)
        optimizer = torch.optim.Adam(candidate.parameters(), betas=(.9, .95))
        optimizer.load_state_dict(copy.deepcopy(checkpoint["opt_actor"]))
        train_cfg = checkpoint["cfg"]
        iteration = checkpoint["iteration"] + 1
        fraction = min(iteration / train_cfg["lr_decay_iterations"], 1.)
        lr = train_cfg["lr"] * (
          train_cfg["lr_final_frac"] + (1 - train_cfg["lr_final_frac"]) * .5
          * (1 + math.cos(math.pi * fraction)))
        actor_start = train_cfg["warmup_iterations"] + train_cfg["critic_warmup_iterations"]
        ramp = min(1., max(0, iteration - actor_start) / max(1, train_cfg["actor_ramp_iterations"]))
        for group in optimizer.param_groups:
          group["lr"] = lr * train_cfg["actor_lr_scale"] * ramp
        objective, _ = imagine.rollout(wm, candidate, critic, one)
        optimizer.zero_grad(set_to_none=True)
        (-objective.mean()).backward()
        grad_norm = torch.nn.utils.clip_grad_norm_(
          candidate.parameters(), train_cfg["grad_clip"], error_if_nonfinite=True)
        optimizer.step()
        candidate.requires_grad_(False)
        with torch.no_grad():
          base_parameters = dict(actor.named_parameters())
          changes = {name: parameter - base_parameters[name]
                     for name, parameter in candidate.named_parameters()}
          step_info = {"unclipped_gradient_norm": float(grad_norm),
                       "actor_lr": optimizer.param_groups[0]["lr"],
                       "baseline_model_objective": float(objective.mean()),
                       "parameter_delta_rms": float(torch.cat(
                         [change.flatten() for change in changes.values()]).square().mean().sqrt()),
                       "candidates": {}}
          for role, scale in ((1, 1.), (2, -1.), (3, .25), (4, -.25)):
            version = copy.deepcopy(actor)
            for name, parameter in version.named_parameters():
              parameter.add_(scale * changes[name])
            candidates[role] = version
            prediction, _ = imagine.rollout(wm, version, critic, one)
            difference = version(one["obs"]) - nominal
            step_info["candidates"][str(scale)] = {
              "model_objective_gain": float(prediction.mean() - objective.mean()),
              "seed_action_delta_rms": float(difference.square().mean().sqrt())}
        physical_actor = RolePolicy(candidates)
        model_actor = physical_actor
        interventions = [(1, 1., "adam_full"), (3, .25, "adam_quarter")]
        gradient_rms = None
      else:
        first = nominal.detach().requires_grad_(True)
        objective, _ = imagine.rollout(wm, FirstAction(first), critic, one)
        gradient = torch.autograd.grad(objective.sum(), first)[0].detach()
        assert torch.isfinite(gradient).all()
        gradient_rms = float(gradient.square().mean().sqrt())
      with torch.no_grad():
        if args.intervention == "first_action":
          full = gradient / gradient.square().mean(-1, keepdim=True).sqrt().clamp(min=1e-8)
          legs = gradient * leg_mask
          legs = legs / legs.square().mean(-1, keepdim=True).sqrt().clamp(min=1e-8)
          delta = torch.zeros(groups, branches, 29, device=env.device)
          interventions = []
          for start, direction, name in (
              (1, full, "all_joints"), (1 + 2 * len(args.epsilons), legs, "legs_only")):
            for i, epsilon in enumerate(args.epsilons):
              offset = 2 * i
              delta[:, start + offset] = epsilon * direction
              delta[:, start + offset + 1] = -epsilon * direction
              interventions.append((start + offset, epsilon, name))
          first_actions = torch.empty_like(seed["a_prev"])
          first_actions[role_ids] = (nominal[:, None] + delta).clamp(
            -cfg.task.action_clip, cfg.task.action_clip)
          model_actor = FirstAction(first_actions)
          physical_actor = actor
        s, prior, history = seed["s"], seed["a_prev"], seed["obs"]
        command, remaining, gait, amp_history = (
          seed["commands"], seed["command_time"], seed["gait"], seed["amp_history"])
        physical_alive = torch.ones(env.num_envs, dtype=torch.bool, device=env.device)
        strict_alive = physical_alive.clone()
        model_alive = torch.ones(env.num_envs, device=env.device)
        physical_reward = torch.zeros(env.num_envs, device=env.device)
        model_reward = torch.zeros_like(physical_reward)
        reports = {}
        for step in range(1, args.steps + 1):
          action = (first_actions if step == 1 and args.intervention == "first_action"
                    else physical_actor(obs["policy"]).clamp(-cfg.task.action_clip, cfg.task.action_clip))
          obs, reward, term, trunc, extra = env.step(action)
          physical_reward += imagine.cfg.gamma ** (step - 1) * physical_alive * reward
          physical_alive &= ~(term | trunc)
          after = extra["transition"]["next_state"]
          strict_alive &= ~evaluation_falls(after, term)
          # The learned objective has horizon 32. Longer reports measure
          # physical consequences only, without extrapolating WM beyond it.
          if step <= 32:
            s, prior, history, command, remaining, gait, r, death, _, amp_history = imagine._step(
              s, prior, history, command, remaining, gait, amp_history, wm, model_actor)
            model_reward += imagine.cfg.gamma ** (step - 1) * model_alive * r
            model_alive *= 1 - death
          if step not in (1, 4, 8, 16, 32, 64, args.steps):
            continue
          actual_context = imagine.critic_input(after, action, env.commands, env.command_time, env.gait)
          physical_target = physical_reward + imagine.cfg.gamma ** step * physical_alive * critic(
            actual_context).squeeze(-1)
          a = role_values(physical_target, valid_groups)
          ar = role_values(physical_reward, valid_groups)
          if step <= 32:
            model_target = model_reward + imagine.cfg.gamma ** step * model_alive * critic(
              imagine.critic_input(s, prior, command, remaining, gait)).squeeze(-1)
            b, br = (role_values(x, valid_groups) for x in (model_target, model_reward))
          zero = a[:, 0] - a[:, -1]
          row = {"valid_groups": int(valid_groups.sum()),
                 "zero_return_difference_rms": float(zero.square().mean().sqrt()),
                 "zero_bootstrap_difference": paired_summary(zero),
                 "zero_reward_difference": paired_summary(ar[:, 0] - ar[:, -1]),
                 "actual_baseline_return": float(a[:, 0].mean()),
                 "actual_baseline_discounted_reward": float(ar[:, 0].mean()),
                 "directions": {}}
          if step <= 32:
            row["model_baseline_return"] = float(b[:, 0].mean())
          for index, epsilon, name in interventions:
            actual = (a[:, index] - a[:, index + 1]) / (2 * epsilon)
            key = name + "/" + str(epsilon)
            baseline = (a[:, 0] + a[:, -1]) / 2
            baseline_reward = (ar[:, 0] + ar[:, -1]) / 2
            row["directions"][key] = {
              "actual_bootstrap_slope": paired_summary(actual),
              "actual_reward_slope": paired_summary(
                (ar[:, index] - ar[:, index + 1]) / (2 * epsilon)),
              "actual_positive_fraction": float((actual > 0).float().mean()),
              "actual_plus_bootstrap_gain": paired_summary(a[:, index] - baseline),
              "actual_minus_bootstrap_gain": paired_summary(a[:, index + 1] - baseline),
              "actual_plus_reward_gain": paired_summary(ar[:, index] - baseline_reward),
              "actual_minus_reward_gain": paired_summary(ar[:, index + 1] - baseline_reward),
              "native_survival_plus": float(role_values(physical_alive.float(), valid_groups)[:, index].mean()),
              "strict_survival_plus": float(role_values(strict_alive.float(), valid_groups)[:, index].mean()),
            }
            if step <= 32:
              predicted = (b[:, index] - b[:, index + 1]) / (2 * epsilon)
              row["directions"][key].update({
                "model_bootstrap_slope": paired_summary(predicted),
                "model_reward_slope": paired_summary(
                  (br[:, index] - br[:, index + 1]) / (2 * epsilon)),
                "model_plus_bootstrap_gain": paired_summary(
                  b[:, index] - (b[:, 0] + b[:, -1]) / 2),
                "model_plus_reward_gain": paired_summary(
                  br[:, index] - (br[:, 0] + br[:, -1]) / 2),
                "model_positive_fraction": float((predicted > 0).float().mean()),
                "samplewise_slope_cosine": float(torch.nn.functional.cosine_similarity(
                  actual[None], predicted[None])),
              })
          reports[str(step)] = row
        assert valid_groups.any()
        results[mode] = {"warmup_zero_pairing_rms": pairing,
                         "first_action_gradient_rms": gradient_rms,
                         "temporary_policy_step": step_info,
                         "role_to_slot": role_slots.cpu().tolist(),
                         "horizons": reports}
    result = {"checkpoint": str(Path(args.checkpoint).resolve()),
              "checkpoint_sha256": hashlib.sha256(Path(args.checkpoint).read_bytes()).hexdigest(),
              "iteration": checkpoint["iteration"], "actuator_model": g1.ACTUATOR_MODEL,
              "state_schema": g1.STATE_SCHEMA, "samples": groups, "branches": branches,
              "warmup_steps": args.warmup, "seed": args.seed,
              "steps": args.steps, "epsilons": args.epsilons,
              "audit_schema": "randomized_paired_return_v3",
              "intervention": args.intervention,
              "command": [.6, 0., 0.], "results": results,
              "note": "Diagnostic only; no checkpoint is written. In first_action mode, directions "
                      "are gradients of the 32-step model objective with respect to its first "
                      "action, normalized to action RMS=1. Interventions affect only that action, "
                      "using a shared nominal first action; later actions use the frozen actor. "
                      "In policy_step mode, roles apply +/-1 and +/-0.25 times a single restored-"
                      "Adam parameter delta at every step. Candidate updates use this reset-"
                      "conditioned seed batch, not production replay; normalizers, WM, critic "
                      "and D stay fixed. Bootstrap uses the same critic and is not unbiased full-"
                      "episode return. Roles are randomized within clone groups; contact warm-up "
                      "uses common actions. Visible histories can differ; RMS is reported. CI95 "
                      "uses 2048 clone-group bootstrap resamples, conditional on this reset "
                      "distribution, without multiple-comparison correction. Two zero branches "
                      "measure pairing noise. After step 32 only physical outcomes are reported."}
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
