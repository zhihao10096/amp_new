"""GPU integration check: run explicitly after installing Isaac Lab.

python tests/check_isaaclab.py --headless
"""

import argparse
import traceback

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description=__doc__)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()
launcher = AppLauncher(args)
env = None
try:
  import gymnasium as gym
  import torch

  import go2_supermimic.env
  from isaaclab.envs import ManagerBasedRLEnv
  from go2_supermimic import velocity as v
  from go2_supermimic.env.env_cfg import Go2VelocityEnvCfg
  from go2_supermimic.supermimic.state import robot_state

  cfg = Go2VelocityEnvCfg()
  cfg.scene.num_envs = 16
  cfg.sim.device = args.device
  cfg.seed = 13
  cfg.episode_length_s = 0.12
  cfg.task.observation_noise = False
  cfg.task.commands.resampling_time = (0.04, 0.06)
  env = gym.make("Go2-Velocity-Flat", cfg=cfg).unwrapped
  assert isinstance(env, ManagerBasedRLEnv)
  assert type(env).step is ManagerBasedRLEnv.step
  assert type(env)._reset_idx is ManagerBasedRLEnv._reset_idx
  assert env.observation_manager.active_terms["policy"] == [name for name, _ in v.OBS_TERMS]
  assert env.action_manager.active_terms == ["joint_position"]
  assert set(env.termination_manager.active_terms) == {"fall", "time_out"}
  assert env.event_manager.active_terms["reset"] == ["reset_robot"]
  obs, _ = env.reset()
  assert obs["policy"].shape == (16, 225)
  assert len(env.robot.joint_names) == 12
  resets = falls = resamples = 0
  for step in range(30):
    if step == 8:
      # Force one upside-down robot to verify the terminal next-state path.
      root = env.robot.data.root_state_w[:1].clone()
      root[:, 3:7] = torch.tensor([[0., 1., 0., 0.]], device=env.device)
      env.robot.write_root_pose_to_sim(root[:, :7], env_ids=torch.tensor([0], device=env.device))
    before = robot_state(env).clone()
    previous = env.actions.clone()
    command, time = env.commands.clone(), env.command_time.clone()
    history = obs["policy"].clone()
    gait = env.gait.clone()
    action = torch.randn(16, 12, device=env.device) * 0.1
    obs, actual, terminated, truncated, extras = env.step(action)
    state = extras["transition"]["next_state"]
    torch.testing.assert_close(extras["transition"]["commands"], command)
    expected, terms = v.reward(before, state, action, previous, command,
                                env.consts, cfg.task, env.step_dt, terminated, gait)
    torch.testing.assert_close(actual, expected)
    independent_tracking = torch.exp(-((state[:, 4:6] - command[:, :2])**2).sum(-1) / 0.25)
    torch.testing.assert_close(terms["track_linear_velocity"], independent_tracking)
    done = terminated | truncated
    expected_gait, _ = v.advance_gait(gait, before[:, v.CONTACT], state[:, v.CONTACT], env.step_dt)
    expected_gait[done] = 0
    torch.testing.assert_close(env.gait, expected_gait)
    # Native manager histories repeat the first frame on reset. Between resets,
    # the same term-major push used in imagination must match exactly.
    frame = v.obs_frame(robot_state(env), env.actions, env.commands)
    expected_obs = v.push_history(history, frame, 5)
    repeated = torch.cat([frame[name].repeat(1, 5) for name, _ in v.OBS_TERMS], -1)
    expected_obs[done] = repeated[done]
    torch.testing.assert_close(obs["policy"], expected_obs)
    assert torch.equal(v.terminated(state, cfg.task), terminated)
    if terminated.any():
      assert not v.terminated(robot_state(env)[terminated], cfg.task).any()
    expired = (time <= env.step_dt) & ~done
    resamples += expired.sum().item()
    resets += done.sum().item()
    falls += terminated.sum().item()
  assert resets > 0 and falls > 0 and resamples > 0
  env.set_command((0.7, -0.2, 0.4))
  for _ in range(15):
    obs, _, _, _, extras = env.step(torch.zeros(16, 12, device=env.device))
    torch.testing.assert_close(env.commands, env.fixed_command.expand(16, -1))
  batch = torch.zeros(16, 3, device=env.device)
  batch[:, 0] = torch.linspace(-1, 1.5, 16, device=env.device)
  env.set_command(batch)
  for _ in range(15):
    env.step(torch.zeros(16, 12, device=env.device))
    torch.testing.assert_close(env.commands, batch)
  env.set_command(None)
  env.reset()
  assert env.fixed_command is None
  assert not torch.equal(env.commands, batch)
  action = torch.full((16, 12), 8.0, device=env.device)
  env.step(action)
  torch.testing.assert_close(action, torch.full_like(action, 8.0))
  torch.testing.assert_close(env.action_manager.action, torch.full_like(action, 4.0))
  term = env.action_manager.get_term("joint_position")
  torch.testing.assert_close(term.processed_actions, env.robot.data.default_joint_pos + 1.0)
  # A manager weight edit must affect the actual step reward, not a parallel
  # reward calculation hidden in an overridden environment step.
  track = env.reward_manager.get_term_cfg("track_linear_velocity")
  track.weight = 0.0
  env.reward_manager.set_term_cfg("track_linear_velocity", track)
  before, previous, command, gait = robot_state(env).clone(), env.actions.clone(), env.commands.clone(), env.gait.clone()
  action.zero_()
  _, actual, term, _, extras = env.step(action)
  expected, terms = v.reward(before, extras["transition"]["next_state"], action, previous,
                             command, env.consts, cfg.task, env.step_dt, term, gait)
  expected -= cfg.task.rewards.track_linear_velocity * terms["track_linear_velocity"] * env.step_dt
  torch.testing.assert_close(actual, expected)
  print(f"PASS: native manager step/reset, observation/reward parity, {resets} resets, {falls} falls, "
        f"{resamples} command resamples, single/batched commands survive resets", flush=True)
except Exception:
  traceback.print_exc()
  raise
finally:
  if env is not None:
    env.close()
  launcher.app.close()
