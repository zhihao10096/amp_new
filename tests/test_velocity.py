import math

import pytest
import torch

from go2_supermimic import velocity as v


def standing(n=8):
  s = torch.zeros(n, v.STATE_DIM)
  s[:, 0], s[:, 3] = 0.3, -1.0
  return s


def consts():
  return v.RobotConsts(torch.zeros(12), torch.tensor([[-3.0, 3.0]]).repeat(12, 1),
                        torch.full((12,), 25.0), torch.full((12,), 0.5),
                        torch.full((12,), 23.5), torch.full((12,), 30.0))


def test_velocity_rewards_peak_at_the_command_and_have_useful_gradients():
  s = standing()
  cmd = torch.tensor([[0.8, -0.2, 0.4]]).expand(8, -1)
  action = torch.zeros(8, 12)
  matched = s.clone()
  matched[:, [4, 5, 9]] = cmd
  cfg = v.VelocityTaskCfg()
  _, matched_terms = v.reward(s, matched, action, action, cmd, consts(), cfg, 0.02,
                              torch.zeros(8, dtype=torch.bool))
  assert torch.allclose(matched_terms["track_linear_velocity"], torch.ones(8))
  assert torch.allclose(matched_terms["track_yaw_rate"], torch.ones(8))
  s.requires_grad_()
  reward, _ = v.reward(s.detach(), s, action, action, cmd, consts(), cfg, 0.02,
                       torch.zeros(8, dtype=torch.bool))
  reward.sum().backward()
  assert torch.isfinite(s.grad).all()
  assert (s.grad[:, 4] > 0).all()
  assert (s.grad[:, 5] < 0).all()
  assert (s.grad[:, 9] > 0).all()


def test_commands_cover_all_axes_resample_and_support_standing():
  torch.manual_seed(7)
  cfg = v.CommandCfg(standing_fraction=0)
  commands, time = v.sample_commands(4096, "cpu", cfg)
  for i, bounds in enumerate((cfg.lin_vel_x, cfg.lin_vel_y, cfg.ang_vel_z)):
    assert (commands[:, i] >= bounds[0]).all() and (commands[:, i] <= bounds[1]).all()
    assert commands[:, i].min() < -0.1 and commands[:, i].max() > 0.1
  assert (time >= 6).all() and (time <= 10).all()
  before = commands.clone()
  remaining = torch.full((4096,), 1.0)
  remaining[0] = 0.01
  commands, time = v.advance_commands(commands, remaining, 0.02, cfg)
  torch.testing.assert_close(commands[1:], before[1:])
  assert not torch.equal(commands[0], before[0])
  assert time[0] >= 6
  stopped, _ = v.sample_commands(16, "cpu", v.CommandCfg(standing_fraction=1))
  assert stopped.count_nonzero() == 0
  with pytest.raises(ValueError):
    v.CommandCfg(resampling_time=(0, 1))


def test_history_is_term_major_and_reset_does_not_leak_an_episode():
  cfg = v.VelocityTaskCfg(history=3)
  h = torch.zeros(2, v.FRAME_DIM * cfg.history)
  for step in range(5):
    s = standing(2)
    s[:, 7:10] = step + 1
    h = v.push_history(h, v.obs_frame(s, torch.zeros(2, 12), torch.zeros(2, 3)), cfg.history)
  torch.testing.assert_close(h[:, :9], torch.tensor([[3., 3., 3., 4., 4., 4., 5., 5., 5.]]).repeat(2, 1))
  h[0] = 0
  h = v.push_history(h, v.obs_frame(standing(2), torch.ones(2, 12), torch.zeros(2, 3)), 3)
  assert h[0, :9].count_nonzero() == 0
  torch.testing.assert_close(h[0, -36:-12], torch.zeros(24))
  torch.testing.assert_close(h[0, -12:], torch.ones(12))


def test_hard_and_soft_termination_agree_far_from_boundaries():
  s = standing(3)
  s[1, 0] = 0.05
  s[2, 3] = 0.1
  cfg = v.VelocityTaskCfg()
  assert v.terminated(s, cfg).tolist() == [False, True, True]
  torch.testing.assert_close(v.termination_probability(s, cfg), torch.tensor([0., 1., 1.]), atol=0.001, rtol=0)
  s[:, 3] = -math.cos(math.radians(cfg.fall_angle_deg))
  s[:, 0] = 0.3
  torch.testing.assert_close(v.termination_probability(s, cfg), torch.full((3,), 0.5), atol=0.001, rtol=0)


def test_dc_motor_torque_drops_at_the_speed_limit():
  s = standing(1)
  a = torch.full((1, 12), 4.0)
  torque = v.motor_torque(s, a, consts(), v.VelocityTaskCfg())
  torch.testing.assert_close(torque, torch.full((1, 12), 23.5))
  s[:, v.QD] = 30
  assert (v.motor_torque(s, a, consts(), v.VelocityTaskCfg()) == 0).all()


def test_contact_event_timers_and_unitree_foot_rewards():
  gait = torch.zeros(1, v.GAIT_DIM)
  c0 = torch.tensor([[0., 1., 1., 0.]])
  gait[:, v.AIR] = torch.tensor([[.2, 0, 0, .3]])
  gait[:, v.STANCE] = torch.tensor([[0, .4, .5, 0]])
  c1 = torch.tensor([[1., 0., 1., 0.]])
  next_gait, touch = v.advance_gait(gait, c0, c1, .02)
  torch.testing.assert_close(touch, torch.tensor([[1., 0., 0., 0.]]))
  torch.testing.assert_close(next_gait[:, v.AIR], torch.tensor([[0., .02, 0., .32]]))
  torch.testing.assert_close(next_gait[:, v.LAST_AIR], torch.tensor([[.22, 0., 0., 0.]]))
  torch.testing.assert_close(next_gait[:, v.LAST_STANCE], torch.tensor([[0., .42, 0., 0.]]))
  before, after = standing(1), standing(1)
  before[:, v.CONTACT], after[:, v.CONTACT] = c0, c1
  after[:, v.FOOT_VEL] = torch.tensor([[1., 0., 2.]]).repeat(1, 4)
  _, terms = v.reward(before, after, torch.zeros(1, 12), torch.zeros(1, 12),
                      torch.tensor([[1., 0., 0.]]), consts(), v.VelocityTaskCfg(),
                      .02, torch.zeros(1), gait)
  torch.testing.assert_close(terms["feet_air_time"], torch.tensor([-.28]))
  torch.testing.assert_close(terms["feet_slide"], torch.tensor([2.]))
  expected = next_gait[:, v.LAST_AIR].var(-1) + next_gait[:, v.LAST_STANCE].var(-1)
  torch.testing.assert_close(terms["air_time_variance"], expected)


def test_reference_standing_penalty_energy_and_soft_contact_gradients():
  s = standing(2)
  s[:, v.Q] = .1
  s[:, v.QD] = 2
  commands = torch.tensor([[0., 0., 0.], [1., 0., 0.]])
  cfg = v.VelocityTaskCfg()
  _, terms = v.reward(s, s, torch.ones(2, 12), torch.zeros(2, 12), commands,
                      consts(), cfg, .02, torch.zeros(2), torch.zeros(2, v.GAIT_DIM))
  torch.testing.assert_close(terms["joint_deviation"][0], 5 * terms["joint_deviation"][1])
  torch.testing.assert_close(terms["joint_velocity"], torch.full((2,), 48.))
  assert (terms["energy"] > 0).all()
  soft = torch.full((2, 4), .5, requires_grad=True)
  gait, touchdown = v.advance_gait(torch.ones(2, v.GAIT_DIM) * .1,
                                  torch.zeros(2, 4), soft, .02)
  (gait.square().sum() + touchdown.sum()).backward()
  assert torch.isfinite(soft.grad).all() and soft.grad.abs().sum() > 0


def test_gait_shaping_rewards_clear_swing_diagonals_and_quiet_standing():
  s = standing(2)
  s[:, v.FOOT_POS] = torch.tensor([[0., 0., -.27]]).repeat(2, 4)
  s[1, v.FOOT_POS] = torch.tensor([[0., 0., -.24]]).repeat(1, 4)
  s[:, v.FOOT_VEL] = torch.tensor([[1., 0., 0.]]).repeat(2, 4)
  s[:, v.CONTACT] = torch.tensor([[1., 0., 0., 1.], [1., 1., 1., 1.]])
  cfg = v.VelocityTaskCfg()
  action = torch.zeros(2, 12)
  cmd = torch.tensor([[1., 0., 0.]]).repeat(2, 1)
  gait = torch.full((2, v.GAIT_DIM), .18)
  _, terms = v.reward(s, s, action, action, cmd, consts(), cfg, .02, torch.zeros(2), gait)
  assert terms["feet_clearance"][1] > terms["feet_clearance"][0]
  torch.testing.assert_close(terms["gait_duration"], torch.zeros(2))
  torch.testing.assert_close(terms["diagonal_gait"], torch.tensor([1., .5]))
  _, stationary = v.reward(s, s, action, action, torch.zeros_like(cmd),
                           consts(), cfg, .02, torch.zeros(2), gait)
  torch.testing.assert_close(stationary["feet_contact_without_command"], torch.tensor([2., 4.]))
  torch.testing.assert_close(stationary["feet_clearance"], torch.zeros(2))
