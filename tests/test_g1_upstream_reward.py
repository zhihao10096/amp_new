"""Behavioral checks for the upstream G1 reward, mixing and legacy isolation."""

from copy import deepcopy
from dataclasses import asdict
from types import SimpleNamespace

import pytest
import torch

from go2_supermimic import g1
from go2_supermimic.supermimic.curriculum import training_task
from go2_supermimic.supermimic.imagine import ImagineCfg, Imagination
from go2_supermimic.supermimic.train import TrainCfg, Trainer, task_from_dict


def constants():
  return g1.RobotConsts(
    torch.zeros(29), torch.tensor([[-3., 3.]] * 29),
    torch.full((29,), 100.), torch.full((29,), 2.),
    torch.full((29,), 88.), torch.full((29,), 32.))


def state(n=4):
  s = torch.zeros(n, g1.STATE_DIM)
  s[:, 0], s[:, 3], s[:, g1.CONTACT] = .78, -1., 1.
  return s


def evaluate(s, commands, previous=None):
  zero = torch.zeros(len(s), 29)
  return g1.reward(s.detach() if previous is None else previous, s, zero, zero,
                   commands, constants(), g1.walk_task(), .02, torch.zeros(len(s)),
                   torch.zeros(len(s), g1.GAIT_DIM))


def test_upstream_profile_uses_sixteen_terms_and_never_invents_a_gait_curriculum():
  task = g1.walk_task()
  assert task.reward_profile == g1.REWARD_PROFILE
  active = {k: v for k, v in asdict(task.rewards).items() if v}
  assert active == {
    "track_linear_velocity": 1., "track_yaw_rate": 2.,
    "vertical_velocity": -.2, "roll_pitch_rate": -.05, "orientation": -1.,
    "action_rate": -.005, "joint_torque": -2e-6,
    "joint_acceleration": -1.25e-7, "joint_limits": -1.,
    "feet_air_time": .75, "feet_slide": -.1, "undesired_contacts": -1.,
    "terminated": -200., "joint_deviation_hip": -.1,
    "joint_deviation_arms": -.05, "joint_deviation_waist": -.1}
  for fraction in (0., .5, 1.):
    assert asdict(training_task(task, fraction)) == asdict(task)
  for original in (task, g1.legacy_walk_task()):
    assert asdict(task_from_dict(asdict(original))) == asdict(original)


def test_walking_does_not_penalize_leg_pose_and_stationary_yaw_keeps_pose_penalty():
  s = state(5)
  s[:, g1.Q][:, 0] = .3  # hip pitch and knee are never default-pose penalties
  s[:, g1.Q][:, 9] = .4
  s[:, g1.Q][:, 3] = .2  # hip roll is penalized only with small translation
  s[:, g1.Q][:, 2] = .1  # waist
  commands = torch.tensor([[.6, 0., 0.], [0., 0., .5], [.059, 0., 0.],
                           [.06, 0., 0.], [0., .1, 0.]])
  _, terms = evaluate(s, commands)
  torch.testing.assert_close(
    terms["joint_deviation_hip"], torch.tensor([0., .2, .2, 0., 0.]))
  torch.testing.assert_close(
    terms["joint_deviation_waist"], torch.tensor([0., .1, .1, 0., 0.]))
  assert not terms["joint_deviation"].any()


def test_upper_body_motion_is_not_charged_as_leg_torque_acceleration_or_ankle_limit():
  s = state(3)
  arm, ankle, knee = g1.ARM_IDS[0], g1.ANKLE_IDS[0], g1.LEG_INDICES[3][0]
  s[0, 10 + arm] = 4.
  s[0, 39 + arm] = 10.
  s[1, 10 + ankle] = 4.
  s[1, 39 + ankle] = 10.
  s[2, 39 + knee] = 10.
  _, terms = evaluate(s, torch.tensor([[.6, 0., 0.]] * 3), state(3))
  assert terms["joint_torque"][0] == terms["joint_acceleration"][0] == 0
  assert terms["joint_limits"][0] == 0
  assert terms["joint_torque"][1] > 0 and terms["joint_limits"][1] > 0
  assert terms["joint_acceleration"][1] == 0  # upstream acceleration excludes ankles
  assert terms["joint_acceleration"][2] > 0


def test_tilted_velocity_matches_independently_constructed_yaw_frame():
  roll = torch.tensor([-.4, 0., .5, .2])
  pitch = torch.tensor([.3, -.2, .4, 0.])
  velocity = torch.tensor([[.7, -.2, .3], [.5, .1, -.2], [.1, .3, .7], [0., 1., 0.]])
  # First Rx, then Ry, constructed independently of projected gravity.
  rx_y = roll.cos() * velocity[:, 1] - roll.sin() * velocity[:, 2]
  rx_z = roll.sin() * velocity[:, 1] + roll.cos() * velocity[:, 2]
  expected = torch.stack((pitch.cos() * velocity[:, 0] + pitch.sin() * rx_z,
                          rx_y, -pitch.sin() * velocity[:, 0] + pitch.cos() * rx_z), -1)
  s = state(4)
  s[:, g1.V_B] = velocity
  s[:, g1.GRAV] = torch.stack((pitch.sin(), -roll.sin() * pitch.cos(),
                               -roll.cos() * pitch.cos()), -1)
  torch.testing.assert_close(g1.yaw_frame_velocity(s), expected)


def test_standing_style_and_final_reward_match_upstream_mix_and_td_target():
  task, c = g1.walk_task(), constants()
  disc = g1.AMPDiscriminator((8,), command_gate=False)
  for p in disc.parameters():
    p.data.zero_()
  disc.net[-1].bias.data.fill_(1.)  # raw style=1 for both standing and walking
  disc.requires_grad_(False)
  s, action, commands = state(2), torch.zeros(2, 29), torch.zeros(2, 3)
  style = disc.reward(s, s, c.default_q, commands)
  torch.testing.assert_close(style, torch.ones(2))
  imagine = Imagination(ImagineCfg(), task, c, disc)
  assert imagine.set_amp_weight(.5) == (.5, 1.)
  batch = {"s": s, "next_s": s, "action": action, "a_prev": action,
           "commands": commands, "command_time": torch.full((2,), 10.),
           "gait": torch.zeros(2, 8)}
  _, target = imagine.real_targets(lambda x: x.new_zeros(len(x), 1), batch)
  torch.testing.assert_close(target, torch.full((2,), .05))
  with pytest.raises(ValueError, match="mixing fraction"):
    imagine.set_amp_weight(1.1)
  assert g1.amp_reward_coefficients(g1.legacy_walk_task(), .5) == (1., .5)


def test_reward_manager_and_imagination_share_ramped_task_and_style_coefficients():
  task = g1.walk_task()
  terms = {k: SimpleNamespace(weight=v) for k, v in asdict(task.rewards).items()}
  terms["amp_style"] = SimpleNamespace(weight=0.)

  class Manager:
    def get_term_cfg(self, name):
      return deepcopy(terms[name])

    def set_term_cfg(self, name, cfg):
      terms[name] = cfg

  trainer = Trainer.__new__(Trainer)
  trainer.cfg = TrainCfg(task="G1-AMP-Flat", amp_ramp_iterations=10)
  trainer.env = SimpleNamespace(cfg=SimpleNamespace(task=task), reward_manager=Manager())
  trainer.amp = g1.AMPDiscriminator((8,), command_gate=False)
  trainer.imag = Imagination(ImagineCfg(), task, constants(), trainer.amp)
  for iteration, task_weight, style_weight in ((0, 1., 0.), (5, .75, .5), (10, .5, 1.)):
    trainer.set_training_rewards(iteration)
    assert terms["amp_style"].weight == style_weight
    assert trainer.imag.task_weight == task_weight
    assert trainer.imag.amp_weight == style_weight
    for name, value in asdict(task.rewards).items():
      assert terms[name].weight == task_weight * value


def test_reward_has_finite_gradients_at_normal_and_invalid_imagined_gravity():
  s = state(4)
  s[0, g1.GRAV] = 0.  # world model has no hard unit-gravity constraint
  s[:, g1.V_B] = .2
  s[:, g1.W_B] = .1
  s[:, g1.Q] = .1
  s.requires_grad_()
  total, _ = evaluate(s, torch.tensor([[.6, .1, .2]] * 4))
  total.sum().backward()
  assert torch.isfinite(s.grad).all() and s.grad.abs().sum() > 0
