"""CPU checks for the G1 cold-start reward curriculum."""

import torch

from go2_supermimic import g1
from go2_supermimic.velocity import RobotConsts


def _consts():
  return RobotConsts(
    default_q=torch.zeros(29),
    soft_limits=torch.tensor([[-3., 3.]] * 29),
    kp=torch.ones(29), kd=torch.ones(29),
    effort=torch.ones(29), velocity=torch.ones(29) * 10.)


def _params(task, fraction):
  return torch.tensor([getattr(task.rewards, name) for name in g1.REWARD_NAMES]
                      + [fraction])


def test_g1_joint_deviation_curriculum_matches_final_reward():
  task = g1.walk_task()
  state = torch.zeros(2, g1.STATE_DIM)
  state[:, g1.Z] = task.nominal_height
  state[:, g1.GRAV] = torch.tensor([[0., 0., 1.], [0., 0., 1.]])
  state[:, g1.Q] = torch.tensor([[.1, -.2] + [0.] * 27, [.3, -.4] + [0.] * 27])
  action = torch.zeros(2, g1.NUM_JOINTS)
  commands = torch.tensor([[.6, 0., 0.], [.6, 0., 0.]])
  kwargs = dict(s0=state.clone(), s1=state, action=action,
                previous_action=action, commands=commands, c=_consts(),
                cfg=task, dt=.02, done=torch.zeros(2, dtype=torch.bool))
  _, initial = g1.reward(**kwargs, parameters=_params(task, 0.))
  _, final = g1.reward(**kwargs, parameters=_params(task, 1.))
  q = state[:, g1.Q]
  torch.testing.assert_close(initial["joint_deviation"], q.square().sum(-1))
  torch.testing.assert_close(final["joint_deviation"], q.abs().sum(-1))
