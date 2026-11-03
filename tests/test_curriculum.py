from copy import deepcopy
from dataclasses import asdict, replace
from types import SimpleNamespace

import pytest
import torch

from go2_supermimic.supermimic.curriculum import (
  curriculum_fraction, restore_curriculum_options, training_task,
)
from go2_supermimic.supermimic.train import TrainCfg, Trainer
from go2_supermimic import velocity as v
from go2_supermimic.velocity import VelocityTaskCfg


def test_curriculum_has_stable_endpoints_and_preserves_target_configuration():
  target = VelocityTaskCfg()
  original = asdict(target)
  assert curriculum_fraction(50, 0, 0) == 1
  assert curriculum_fraction(1000, 2000, 6000) == 0
  assert curriculum_fraction(4000, 2000, 6000) == .5
  assert curriculum_fraction(9000, 2000, 6000) == 1
  initial = training_task(target, 0)
  assert initial.rewards.gait_duration == initial.rewards.feet_slide == 0
  assert initial.rewards.joint_deviation == -.05
  assert asdict(training_task(target, 1)) == original
  assert asdict(target) == original
  with pytest.raises(ValueError, match="curriculum"):
    TrainCfg(reward_curriculum_start=100, reward_curriculum_end=0)


def test_simulator_managers_and_imagination_use_the_same_scheduled_weights():
  target = VelocityTaskCfg()
  terms = {name: SimpleNamespace(weight=value)
           for name, value in asdict(target.rewards).items()}

  class Manager:
    def get_term_cfg(self, name):
      return deepcopy(terms[name])

    def set_term_cfg(self, name, term):
      terms[name] = term

  trainer = Trainer.__new__(Trainer)
  trainer.cfg = TrainCfg(reward_curriculum_start=100, reward_curriculum_end=300)
  trainer.env = SimpleNamespace(cfg=SimpleNamespace(task=target), reward_manager=Manager())
  trainer.imag = SimpleNamespace(task=target)
  for iteration in (0, 100, 200, 300, 500):
    trainer.set_training_rewards(iteration)
    for name, value in asdict(trainer.imag.task.rewards).items():
      assert terms[name].weight == value
    assert target.rewards.gait_duration == -8
    assert trainer.env.training_task is trainer.imag.task
  assert asdict(trainer.imag.task) == asdict(target)


def test_initial_curriculum_matches_convergent_squared_reward_and_gradients():
  """Initial rewards must reproduce the speed baseline, including small motions."""
  task = training_task(VelocityTaskCfg(), 0)
  consts = v.RobotConsts(
    default_q=torch.zeros(12), soft_limits=torch.tensor([[-2., 2.]]).expand(12, 2),
    kp=torch.ones(12) * 20, kd=torch.ones(12), effort=torch.ones(12) * 30,
    velocity=torch.ones(12) * 30)
  state = torch.zeros(3, v.STATE_DIM)
  state[:, 0], state[:, 3] = .3, -1
  state[:, v.Q] = .01
  state.requires_grad_()
  action = torch.zeros(3, 12)
  commands = torch.tensor([[0., 0., 0.], [1., 0., 0.], [-1., .3, .5]])
  reward_args = (state.detach(), state, action, action, commands, consts)
  tail = (.02, torch.zeros(3), torch.zeros(3, v.GAIT_DIM))
  actual, terms = v.reward(*reward_args, task, *tail)
  legacy, _ = v.reward(*reward_args, replace(task, reward_profile="legacy"), *tail)
  torch.testing.assert_close(actual, legacy)
  torch.testing.assert_close(terms["joint_deviation"], torch.full((3,), .0012))
  actual_grad = torch.autograd.grad(actual.sum(), state, retain_graph=True)[0]
  legacy_grad = torch.autograd.grad(legacy.sum(), state)[0]
  torch.testing.assert_close(actual_grad, legacy_grad)
  assert task.rewards.undesired_contacts == 0
  assert training_task(VelocityTaskCfg(), .5).joint_deviation_gait_fraction == .5


def test_resume_inherits_schedule_and_respects_explicit_zero_or_partial_overrides():
  values = asdict(TrainCfg())
  saved = {"reward_curriculum_start": 3000, "reward_curriculum_end": 5000}
  inherited = TrainCfg(**restore_curriculum_options(values, saved, []))
  assert (inherited.reward_curriculum_start, inherited.reward_curriculum_end) == (3000, 5000)
  values["reward_curriculum_start"] = 3500
  partial = TrainCfg(**restore_curriculum_options(
    values, saved, ["--reward-curriculum-start=3500"]))
  assert (partial.reward_curriculum_start, partial.reward_curriculum_end) == (3500, 5000)
  values["reward_curriculum_start"] = 0
  disabled = TrainCfg(**restore_curriculum_options(
    values, saved, ["--reward-curriculum-start", "0", "--reward-curriculum-end", "0"]))
  assert disabled.reward_curriculum_start == disabled.reward_curriculum_end == 0
  assert restore_curriculum_options(values, {}, []) == values
