from copy import deepcopy
from dataclasses import asdict
from types import SimpleNamespace

import pytest

from go2_supermimic.supermimic.curriculum import curriculum_fraction, training_task
from go2_supermimic.supermimic.train import TrainCfg, Trainer
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
  assert asdict(trainer.imag.task) == asdict(target)
