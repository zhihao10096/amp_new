"""Explicit G1 GPU boundary checks, including real/imagined rewards and resets."""

import argparse
import json
import traceback
from dataclasses import replace
from pathlib import Path

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", default="logs/amp_g1/integration.json")
parser.add_argument("--compile", action="store_true")
parser.add_argument("--amp-feature-schema", default="g1_amp_61_v1")
parser.add_argument("--amp-num-frames", type=int, default=2)
parser.add_argument("--legacy-rewards", action="store_true")
parser.add_argument("--align-reset-commands", action="store_true")
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
launcher = AppLauncher(args)
env = None
try:
  import gymnasium as gym
  import torch
  import go2_supermimic.env
  from go2_supermimic import g1
  from go2_supermimic.env import mdp
  from go2_supermimic.env.g1_cfg import G1AmpEnvCfg
  from go2_supermimic.supermimic.imagine import ImagineCfg, Imagination
  from go2_supermimic.supermimic.state import robot_state
  from go2_supermimic.supermimic.train import Actor, Critic
  from go2_supermimic.supermimic.world_model import WorldModel
  from isaaclab.envs import ManagerBasedRLEnv
  from isaaclab.actuators import ImplicitActuator
  from isaaclab.utils.types import ArticulationActions
  from isaaclab.managers import SceneEntityCfg
  import isaaclab.envs.mdp as lab_mdp

  torch.set_float32_matmul_precision("highest")
  cfg = G1AmpEnvCfg()
  if args.legacy_rewards:
    cfg.task = g1.legacy_walk_task()
  cfg.scene.num_envs = 32
  cfg.sim.device = args.device
  cfg.task.observation_noise = False
  cfg.task.commands.resampling_time = (.12, .18)
  cfg.episode_length_s = .8
  cfg.amp_reference_reset_fraction = .5
  cfg.amp_reset_command_alignment = args.align_reset_commands
  cfg.amp_feature_schema = args.amp_feature_schema
  cfg.amp_num_frames = args.amp_num_frames
  env = gym.make("G1-AMP-Flat", cfg=cfg).unwrapped
  native_checks = 0
  original_capture = mdp.capture_transition
  base_sensor = SceneEntityCfg("contact_sensor", body_ids=env.base_contact_sensor_ids)

  def checked_capture(current_env):
    global native_checks
    state = original_capture(current_env)
    contact = lab_mdp.illegal_contact(current_env, 1., base_sensor)
    torch.testing.assert_close(state[:, g1.BASE_CONTACT].squeeze(-1), contact.float())
    if cfg.task.termination_profile == g1.TERMINATION_PROFILE:
      native = contact | lab_mdp.root_height_below_minimum(current_env, .2)
      torch.testing.assert_close(g1.terminated(state, cfg.task), native)
    native_checks += 1
    return state

  mdp.capture_transition = checked_capture
  assert type(env).step is ManagerBasedRLEnv.step
  assert type(env)._reset_idx is ManagerBasedRLEnv._reset_idx
  assert env.robot.joint_names == env.amp_motion.joint_names
  assert env.robot.num_joints == 29
  if cfg.task.reward_profile == g1.REWARD_PROFILE:
    penalized = [env.contact_sensor.body_names[i] for i in env.undesired_sensor_ids]
    assert len(penalized) == 8 and all("elbow" in name or "wrist" in name for name in penalized)
  assert all(type(motor) is ImplicitActuator for motor in env.robot.actuators.values())
  # Explicit DC drives write zero Kp/Kd into PhysX. These must be real PD drives.
  stiffness = env.robot.root_physx_view.get_dof_stiffnesses().to(env.device)
  damping = env.robot.root_physx_view.get_dof_dampings().to(env.device)
  torch.testing.assert_close(stiffness, env.consts.kp.expand_as(stiffness))
  torch.testing.assert_close(damping, env.consts.kd.expand_as(damping))
  # At equal states the differentiable reward proxy must match Lab's own
  # implicit effort estimate, including at the former DC speed boundary.
  motor_estimate_error = 0.
  for fraction in (0., .5, 1., -1.):
    probe = torch.zeros(32, g1.STATE_DIM, device=env.device)
    probe[:, g1.QD] = fraction * env.consts.velocity
    probe[:, g1.Q] = -.5 if fraction >= 0 else .5
    action = torch.full((32, 29), 4. if fraction >= 0 else -4., device=env.device)
    expected = g1.motor_torque(probe, action, env.consts, cfg.task)
    estimate = torch.zeros_like(expected)
    for motor in env.robot.actuators.values():
      ids = motor.joint_indices
      targets = ArticulationActions(
        joint_positions=(env.consts.default_q + cfg.task.action_scale * action)[:, ids],
        joint_velocities=torch.zeros_like(action[:, ids]),
        joint_efforts=torch.zeros_like(action[:, ids]))
      motor.compute(targets, (env.consts.default_q + probe[:, g1.Q])[:, ids],
                    probe[:, g1.QD][:, ids])
      estimate[:, ids] = motor.applied_effort
      assert targets.joint_positions is not None
      assert not targets.joint_efforts.any()  # PhysX receives position targets, not PD torques.
    error = (expected - estimate).abs().max().item()
    motor_estimate_error = max(motor_estimate_error, error)
    torch.testing.assert_close(expected, estimate, atol=2e-5, rtol=2e-5)
  disc = g1.AMPDiscriminator(
    (32, 16), args.amp_feature_schema, args.amp_num_frames,
    command_gate=cfg.task.reward_profile != g1.REWARD_PROFILE).to(env.device).requires_grad_(False)
  disc.norm.update(torch.cat(env.amp_motion.sample_pairs(1024)))
  env.amp_discriminator = disc
  alignment_checks = ordinary_reset_checks = 0
  alignment_max_error = 0.

  def check_reset_alignment(reset_mask):
    global alignment_checks, ordinary_reset_checks, alignment_max_error
    if not cfg.amp_reset_command_alignment or env.fixed_command is not None:
      return
    assert not env._amp_reference_command_pending[reset_mask].any()
    reference = reset_mask & env.amp_reference_reset
    state = robot_state(env)
    command_cfg = cfg.task.commands
    expected = torch.stack((
      state[:, 4].clamp(*command_cfg.lin_vel_x),
      state[:, 5].clamp(*command_cfg.lin_vel_y),
      state[:, 9].clamp(*command_cfg.ang_vel_z)), -1)
    if reference.any():
      error = (env.commands[reference] - expected[reference]).abs().max().item()
      alignment_max_error = max(alignment_max_error, error)
      torch.testing.assert_close(env.commands[reference], expected[reference], atol=2e-5, rtol=2e-5)
    alignment_checks += reference.sum().item()
    ordinary_reset_checks += (reset_mask & ~reference).sum().item()

  obs, _ = env.reset(seed=42)
  check_reset_alignment(torch.ones(32, dtype=torch.bool, device=env.device))
  assert obs["policy"].shape == (32, 480)
  frames = env.amp_motion.sample_frames(32)
  root = env.robot.data.root_state_w.clone()
  root[:, :3] = frames[:, :3] + env.scene.env_origins
  root[:, 3:7], root[:, 7:10], root[:, 10:13] = (
    frames[:, [6, 3, 4, 5]], frames[:, 36:39], frames[:, 39:42])
  env.robot.write_root_pose_to_sim(root[:, :7])
  env.robot.write_root_velocity_to_sim(root[:, 7:])
  env.robot.write_joint_state_to_sim(frames[:, 7:36], frames[:, 42:71])
  env.sim.forward()
  env.scene.update(env.step_dt)
  state = robot_state(env)
  expert_error = (g1.state_features(state, env.consts.default_q, args.amp_feature_schema)
                   - g1.frame_features(frames, args.amp_feature_schema)).abs().max().item()
  assert expert_error < 1e-4, expert_error
  native_feet = state[:, g1.FOOT_POS].reshape(-1, 2, 3)
  fk_error = (g1.foot_positions(state[:, g1.Q] + env.consts.default_q)
              - native_feet).abs().max().item()
  assert fk_error < 1e-4, fk_error
  obs, _ = env.reset()
  check_reset_alignment(torch.ones(32, dtype=torch.bool, device=env.device))
  resets = falls = resamples = timeouts = contact_falls = 0
  real_td_max_error = 0.
  native_torque_proxy_difference = native_acceleration_proxy_difference = 0.
  real_anchor = Imagination(ImagineCfg(), cfg.task, env.consts, disc)
  prior_done = torch.ones(32, dtype=torch.bool, device=env.device)

  def context_value(x):
    return (x[:, 0] + x[:, g1.STATE_DIM] + x[:, -9] + x[:, -8]).unsqueeze(-1)

  for step in range(100):
    weight = (0., .5, .17)[step % 3]
    task_weight, style_weight = g1.amp_reward_coefficients(cfg.task, weight)
    for name in cfg.task.rewards.__dataclass_fields__:
      task_term = env.reward_manager.get_term_cfg(name)
      task_term.weight = task_weight * getattr(cfg.task.rewards, name)
      env.reward_manager.set_term_cfg(name, task_term)
    term_cfg = env.reward_manager.get_term_cfg("amp_style")
    term_cfg.weight = style_weight
    env.reward_manager.set_term_cfg("amp_style", term_cfg)
    if step == 10:
      root = env.robot.data.root_state_w[:1].clone()
      root[:, 2] = .1
      env.robot.write_root_pose_to_sim(root[:, :7], env_ids=torch.tensor([0], device=env.device))
    previous, commands, remaining = env.actions.clone(), env.commands.clone(), env.command_time.clone()
    history, gait = obs["policy"].clone(), env.gait.clone()
    action = torch.randn(32, 29, device=env.device) * .05
    obs, actual, term, trunc, extras = env.step(action)
    before, state = env._state_before_action, extras["transition"]["next_state"]
    base, _ = g1.reward(before, state, action, previous, commands, env.consts,
                        cfg.task, env.step_dt, term, gait)
    physical_history = extras["transition"].get("amp_history")
    style = disc.reward(before, state, env.consts.default_q, commands, physical_history)
    torch.testing.assert_close(
      actual, task_weight * base + style_weight * env.step_dt * style, atol=1e-5, rtol=1e-5)
    torch.testing.assert_close(extras["amp_style"], style)
    real_anchor.set_amp_weight(weight)
    batch = {"s": before, "next_s": state, "action": action, "a_prev": previous,
             "commands": commands, "command_time": remaining, "gait": gait,
             "done": term | trunc}
    if physical_history is not None:
      batch["amp_history"] = physical_history
      torch.testing.assert_close(
        physical_history[prior_done], before[prior_done, None].expand(-1, 2, -1))
    real_inputs, targets = real_anchor.real_targets(context_value, batch)
    keep = (remaining > env.step_dt) | term
    next_gait, _ = g1.advance_gait(
      gait, before[:, g1.CONTACT], state[:, g1.CONTACT], env.step_dt)
    following = torch.cat((state, action, commands,
                            (remaining - env.step_dt).clamp(min=0)[:, None], next_gait), -1)
    expected_target = (
      actual + .99 * (~term).float() * context_value(following).squeeze(-1))[keep]
    torch.testing.assert_close(targets, expected_target, atol=1e-5, rtol=1e-5)
    real_td_max_error = max(real_td_max_error, (targets - expected_target).abs().max().item())
    torch.testing.assert_close(real_inputs[:, :g1.STATE_DIM], before[keep])
    done = term | trunc
    check_reset_alignment(done)
    if cfg.task.reward_profile == g1.REWARD_PROFILE and (~done).any():
      valid = ~done
      estimated_torque = g1.motor_torque(state, action, env.consts, cfg.task)
      native_torque_proxy_difference = max(native_torque_proxy_difference, (
        (estimated_torque[valid] - env.robot.data.applied_torque[valid]).abs().max().item()))
      estimated_acceleration = (state[:, g1.QD] - before[:, g1.QD]) / env.step_dt
      native_acceleration_proxy_difference = max(native_acceleration_proxy_difference, (
        (estimated_acceleration[valid] - env.robot.data.joint_acc[valid]).abs().max().item()))
    prior_done = done.clone()
    frame = g1.obs_frame(robot_state(env), env.actions, env.commands)
    expected = g1.push_history(history, frame, cfg.task.history)
    repeated = torch.cat([frame[name].repeat(1, cfg.task.history) for name, _ in g1.OBS_TERMS], -1)
    torch.testing.assert_close(obs["policy"], torch.where(done[:, None], repeated, expected))
    assert not env.gait[done].any()
    if term.any():
      assert g1.terminated(state, cfg.task)[term].all()
    resets += done.sum().item()
    falls += term.sum().item()
    contact_falls += (term & (state[:, g1.BASE_CONTACT].squeeze(-1) > .5)).sum().item()
    timeouts += (trunc & ~term).sum().item()
    resamples += ((remaining <= env.step_dt) & ~done).sum().item()
  assert resets > 0 and falls > 0 and resamples > 0 and timeouts > 0
  assert native_checks > 0 and contact_falls > 0
  if cfg.amp_reset_command_alignment:
    assert alignment_checks > 0 and ordinary_reset_checks > 0
    # A timed resample must not reuse any old reference frame.
    assert not env._amp_reference_command_pending.any()
    env.command_manager.get_term("base_velocity")._resample(
      torch.arange(32, device=env.device))
    assert not torch.equal(env.commands, env._amp_reference_commands)
  env.cfg.amp_reference_reset_fraction = 0.
  env.set_command((.6, 0., 0.))
  obs, _ = env.reset()
  for _ in range(5):
    obs, _, _, _, _ = env.step(torch.zeros(32, 29, device=env.device))
    torch.testing.assert_close(env.commands, env.fixed_command)
  task = replace(cfg.task, observation_noise=False)
  wm = WorldModel((32,), g1.STATE_DIM, 29).to(env.device).requires_grad_(False)
  wm.net[-1].weight.data.mul_(.001)
  actor = Actor(480, (32,), 29).to(env.device)
  critic = Critic(g1.STATE_DIM + g1.GAIT_DIM + 29 + 4, (32,)).to(env.device).requires_grad_(False)
  seed = {"s": robot_state(env).clone(), "a_prev": env.actions.clone(),
          "obs": obs["policy"].clone(), "commands": env.commands.clone(),
          "command_time": torch.full((32,), 10., device=env.device), "gait": env.gait.clone()}
  if args.amp_num_frames > 2:
    seed["amp_history"] = env.amp_history_for_state(seed["s"])
  eager = Imagination(ImagineCfg(horizon=4), task, env.consts, disc)
  compiled = Imagination(ImagineCfg(horizon=4, compile=args.compile), task, env.consts, disc)
  eager.set_amp_weight(.5)
  compiled.set_amp_weight(.5)
  returned, gradients = [], []
  for imagine in (eager, compiled):
    actor.zero_grad(set_to_none=True)
    # Fixed commands do not expire; random resampling is drawn but never selected.
    torch.manual_seed(42)
    obj, _ = imagine.rollout(wm, actor, critic, seed)
    (-obj.mean()).backward()
    returned.append(obj.detach())
    gradients.append(torch.cat([p.grad.flatten() for p in actor.parameters() if p.requires_grad]))
  torch.testing.assert_close(returned[0], returned[1], atol=2e-5, rtol=2e-5)
  torch.testing.assert_close(gradients[0], gradients[1], atol=2e-5, rtol=2e-5)
  assert torch.isfinite(gradients[0]).all() and gradients[0].abs().sum() > 0
  result = {"passed": True, "robot_kind": "g1", "resets": resets, "falls": falls,
            "actuator_model": g1.ACTUATOR_MODEL,
            "state_schema": g1.STATE_SCHEMA,
            "state_dim": g1.STATE_DIM,
            "termination_profile": cfg.task.termination_profile,
            "native_termination_oracle_checks": native_checks,
            "base_contact_falls": contact_falls,
            "amp_reset_command_alignment": cfg.amp_reset_command_alignment,
            "aligned_reference_reset_checks": alignment_checks,
            "ordinary_reset_checks": ordinary_reset_checks,
            "reset_alignment_max_error": alignment_max_error,
            "reward_profile": cfg.task.reward_profile,
            "amp_command_gate": disc.command_gate,
            "final_task_style_coefficients": g1.amp_reward_coefficients(cfg.task, .5),
            "native_last_effort_vs_endpoint_proxy_max_nm": native_torque_proxy_difference,
            "native_joint_acc_vs_control_difference_max_rad_s2": native_acceleration_proxy_difference,
            "proxy_differences_are_diagnostic_not_exact_physics": True,
            "implicit_effort_estimate_max_error": motor_estimate_error,
            "physx_drive_gains_verified": True,
            "amp_feature_schema": args.amp_feature_schema,
            "amp_num_frames": args.amp_num_frames,
            "native_foot_position_max_error_m": fk_error,
            "timeouts": timeouts, "real_td_max_error": real_td_max_error,
            "command_resamples": resamples, "expert_feature_max_error": expert_error,
            "compile": args.compile, "return_max_error": (returned[0]-returned[1]).abs().max().item(),
            "gradient_max_error": (gradients[0]-gradients[1]).abs().max().item(),
            "motion_metadata": env.amp_motion.metadata}
  Path(args.output).parent.mkdir(parents=True, exist_ok=True)
  Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
  print(json.dumps(result, indent=2), flush=True)
except Exception:
  traceback.print_exc()
  raise
finally:
  if env is not None:
    env.close()
  launcher.app.close()
