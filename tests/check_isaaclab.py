"""GPU integration check: run explicitly after installing Isaac Lab.

python tests/check_isaaclab.py --headless
"""

import argparse

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
    action = torch.randn(16, 12, device=env.device) * 0.1
    obs, actual, terminated, truncated, extras = env.step(action)
    state = extras["transition"]["next_state"]
    torch.testing.assert_close(extras["transition"]["commands"], command)
    expected, terms = v.reward(before, state, action, previous, command,
                                env.consts, cfg.task, env.step_dt, terminated)
    torch.testing.assert_close(actual, expected)
    independent_tracking = torch.exp(-((state[:, 4:6] - command[:, :2])**2).sum(-1) / 0.25)
    torch.testing.assert_close(terms["track_linear_velocity"], independent_tracking)
    done = terminated | truncated
    # Rebuild the complete next observation as imagination would, including reset.
    history[done] = 0
    expected_obs = v.push_history(history, v.obs_frame(robot_state(env), env.actions, env.commands), 5)
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
  print(f"PASS: observation/reward parity, {resets} resets, {falls} falls, "
        f"{resamples} command resamples, single/batched commands survive resets", flush=True)
finally:
  if env is not None:
    env.close()
  launcher.app.close()
