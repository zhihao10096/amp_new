"""Execute fixed legged_lab reward methods against the project's pure Torch path.

The fixture supplies the same endpoint torque estimate, control-step joint
acceleration and contact timers to both paths. Equality checks reward formulas;
it does not claim those proxies reproduce PhysX's substep quantities.
"""

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
from types import MethodType, SimpleNamespace as NS

import torch

from go2_supermimic import g1


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("--upstream-root", default="reference/legged_lab")
  parser.add_argument("--output", default="logs/amp_g1/upstream_reward_oracle.json")
  args = parser.parse_args()
  torch.set_num_threads(2)
  torch.manual_seed(1701)
  n, dt, dtype = 512, .02, torch.float64
  upstream = Path(args.upstream_root) / "source/legged_lab/legged_lab"
  host = Path(".venv/lib/python3.10/site-packages/isaaclab/source/isaaclab/isaaclab/envs/mdp/rewards.py")
  manifest = json.loads(g1.MANIFEST.read_text())
  joints = manifest["joint_names"]
  bodies = ["left_ankle_roll_link", "right_ankle_roll_link", "left_elbow_link",
            "right_elbow_link", "left_wrist_roll_link", "right_wrist_roll_link",
            "left_wrist_pitch_link", "right_wrist_pitch_link", "left_wrist_yaw_link",
            "right_wrist_yaw_link"]
  source_hashes = {}

  def entity(name, joint_names=None, body_names=None, **kwargs):
    def resolve(patterns, names):
      if patterns is None:
        return slice(None)
      patterns = [patterns] if isinstance(patterns, str) else patterns
      return [i for i, value in enumerate(names) if any(re.fullmatch(p, value) for p in patterns)]
    return NS(name=name, joint_ids=resolve(joint_names, joints),
              body_ids=resolve(body_names, bodies))

  def yaw_quat(q):
    w, x, y, z = q.unbind(-1)
    yaw = torch.atan2(2 * (w * z + x * y), 1 - 2 * (y.square() + z.square()))
    zero = torch.zeros_like(yaw)
    return torch.stack(((yaw / 2).cos(), zero, zero, (yaw / 2).sin()), -1)

  loss_type = NS(GAN="GAN", LSGAN="LSGAN", WGAN="WGAN")
  namespace = dict(torch=torch, SceneEntityCfg=entity, LossType=loss_type,
                   quat_apply_inverse=g1.quat_inverse_apply, yaw_quat=yaw_quat)

  def load_methods(path, names):
    source_hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    nodes = [node for node in ast.walk(ast.parse(path.read_text()))
             if isinstance(node, ast.FunctionDef) and node.name in names]
    assert len(nodes) == len(names), (path, names)
    module = ast.Module(body=[
      ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
      *nodes], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(path), "exec"), namespace)

  load_methods(host, [
    "is_terminated", "lin_vel_z_l2", "ang_vel_xy_l2", "flat_orientation_l2",
    "joint_torques_l2", "joint_acc_l2", "joint_deviation_l1", "action_rate_l2",
    "joint_pos_limits", "undesired_contacts"])
  namespace["mdp"] = NS(joint_deviation_l1=namespace["joint_deviation_l1"])
  load_methods(upstream / "tasks/locomotion/amp/mdp/rewards.py",
               ["stand_still_joint_deviation_l1"])
  load_methods(upstream / "tasks/locomotion/velocity/mdp/rewards.py", [
    "feet_air_time_positive_biped", "feet_slide", "track_lin_vel_xy_yaw_frame_exp",
    "track_ang_vel_z_world_exp"])
  load_methods(upstream / "rsl_rl/amp/discriminator.py",
               ["predict_style_reward", "lerp_reward"])
  config = upstream / "tasks/locomotion/amp/config/g1/g1_amp_rough_env_cfg.py"
  source_hashes[str(config)] = hashlib.sha256(config.read_bytes()).hexdigest()
  reward_class = next(node for node in ast.parse(config.read_text()).body
                      if isinstance(node, ast.ClassDef) and node.name == "G1AmpRewards")
  specifications = []
  for node in reward_class.body:
    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
      keywords = {kw.arg: kw.value for kw in node.value.keywords}
      params = (eval(compile(ast.Expression(keywords["params"]), str(config), "eval"), namespace)
                if "params" in keywords else {})
      specifications.append((node.targets[0].id, ast.unparse(keywords["func"]).split(".")[-1],
                             ast.literal_eval(keywords["weight"]), params))
  assert len(specifications) == 16

  roll, pitch, yaw = [torch.rand(n, dtype=dtype) * width - width / 2
                       for width in (1., 1., 6.)]
  cr, sr, cp, sp, cy, sy = [(x / 2).cos() if kind == "cos" else (x / 2).sin()
                           for x, kind in [(roll, "cos"), (roll, "sin"), (pitch, "cos"),
                                           (pitch, "sin"), (yaw, "cos"), (yaw, "sin")]]
  quaternion = torch.stack((cr * cp * cy + sr * sp * sy, sr * cp * cy - cr * sp * sy,
                             cr * sp * cy + sr * cp * sy, cr * cp * sy - sr * sp * cy), -1)
  default = torch.randn(29, dtype=dtype) * .1
  consts = g1.RobotConsts(
    default, torch.tensor([[-1., 1.]] * 29, dtype=dtype),
    torch.full((29,), 100., dtype=dtype), torch.full((29,), 2., dtype=dtype),
    torch.full((29,), 88., dtype=dtype), torch.full((29,), 32., dtype=dtype))
  before, after = [torch.randn(n, g1.STATE_DIM, dtype=dtype) * .4 for _ in range(2)]
  after[:, g1.Z] = .78
  after[:, g1.GRAV] = g1.quat_inverse_apply(
    quaternion, torch.tensor([0., 0., -1.], dtype=dtype).expand(n, -1))
  after[:, g1.CONTACT] = torch.randint(0, 2, (n, 2)).to(dtype)
  before[:, g1.CONTACT] = torch.randint(0, 2, (n, 2)).to(dtype)
  counts = torch.randint(0, 9, (n,))
  after[:, g1.UNDESIRED_CONTACT] = counts[:, None]
  action, previous = [torch.randn(n, 29, dtype=dtype) for _ in range(2)]
  commands = torch.randn(n, 3, dtype=dtype) * .3
  commands[:6] = torch.tensor(
    [[0., 0., 0.], [0., 0., .5], [.059, 0., 0.], [.06, 0., 0.],
     [.1, 0., 0.], [.101, 0., 0.]], dtype=dtype)
  gait = torch.rand(n, g1.GAIT_DIM, dtype=dtype) * .5
  following, _ = g1.advance_gait(gait, before[:, g1.CONTACT], after[:, g1.CONTACT], dt)
  done = torch.rand(n) < .1
  task = g1.walk_task()
  actual, terms = g1.reward(before, after, action, previous, commands,
                            consts, task, dt, done, gait)
  force = torch.zeros(n, 4, len(bodies), 3, dtype=dtype)
  force[:, :, :2, 2] = 2 * after[:, None, g1.CONTACT]
  force[:, :, 2:, 2] = 2 * (torch.arange(8)[None, None] < counts[:, None, None])
  sensor = NS(data=NS(
    current_air_time=following[:, g1.AIR], current_contact_time=following[:, g1.STANCE],
    net_forces_w_history=force))
  foot_velocity = after[:, g1.FOOT_VEL].reshape(n, 2, 3)
  world_feet = g1.quat_apply(quaternion[:, None].expand(-1, 2, -1), foot_velocity)
  data = NS(
    joint_pos=after[:, g1.Q] + default, default_joint_pos=default.expand(n, -1),
    joint_acc=(after[:, g1.QD] - before[:, g1.QD]) / dt,
    applied_torque=g1.motor_torque(after, action, consts, task),
    soft_joint_pos_limits=consts.soft_limits.expand(n, -1, -1),
    root_lin_vel_b=after[:, g1.V_B], root_ang_vel_b=after[:, g1.W_B],
    projected_gravity_b=after[:, g1.GRAV], root_quat_w=NS(torch=quaternion),
    root_lin_vel_w=NS(torch=g1.quat_apply(quaternion, after[:, g1.V_B])),
    root_ang_vel_w=g1.quat_apply(quaternion, after[:, g1.W_B]),
    body_lin_vel_w=torch.cat((world_feet, torch.zeros(n, 8, 3, dtype=dtype)), 1))

  class Scene(dict):
    sensors = {"contact_forces": sensor}

  env = NS(
    scene=Scene(robot=NS(data=data)), command_manager=NS(get_command=lambda _: commands),
    termination_manager=NS(terminated=done),
    action_manager=NS(action=action, prev_action=previous))
  mapping = dict(
    track_lin_vel_xy_exp="track_linear_velocity", track_ang_vel_z_exp="track_yaw_rate",
    flat_orientation_l2="orientation", lin_vel_z_l2="vertical_velocity",
    ang_vel_xy_l2="roll_pitch_rate", dof_torques_l2="joint_torque",
    dof_acc_l2="joint_acceleration", action_rate_l2="action_rate",
    dof_pos_limits="joint_limits", undesired_arm_contacts="undesired_contacts",
    termination_penalty="terminated")
  weighted = torch.zeros(n, dtype=dtype)
  errors, native_dtypes = {}, {}
  for name, function, weight, params in specifications:
    expected = namespace[function](env, **params)
    own_name = mapping.get(name, name)
    assert getattr(task.rewards, own_name) == weight
    native_dtypes[name] = str(expected.dtype)
    expected = expected.to(terms[own_name].dtype)
    torch.testing.assert_close(terms[own_name], expected, atol=1e-10, rtol=1e-10)
    errors[name] = (terms[own_name] - expected).abs().max().item()
    weighted += weight * expected
  torch.testing.assert_close(actual, weighted * dt, atol=1e-10, rtol=1e-10)

  scores = torch.linspace(-1.2, 1.2, n, dtype=dtype)

  class Dummy(torch.nn.Module):
    def __init__(self):
      super().__init__()
      self.disc_obs_steps, self.disc_obs_dim = 4, 61
      self.disc_obs_normalizer = torch.nn.Identity()
      self.loss_type, self.style_reward_scale = "LSGAN", 2.
      self.task_style_lerp = .5

    def forward(self, values):
      return scores[:, None]

  Dummy.predict_style_reward = namespace["predict_style_reward"]
  Dummy.lerp_reward = namespace["lerp_reward"]
  reference = Dummy()
  disc = g1.AMPDiscriminator((8,), command_gate=False).double()
  disc.forward = MethodType(lambda self, a, b: scores, disc)
  raw_style = disc.reward(before, after, default, commands)
  mix_errors = {}
  for period in (.005, .02, .04):
    style, _ = reference.predict_style_reward(torch.zeros(n, 4, 61, dtype=dtype), period)
    for fraction in (0., .17, .5):
      reference.task_style_lerp = 1 - fraction
      expected = reference.lerp_reward(weighted * period, style)
      task_scale, style_scale = g1.amp_reward_coefficients(task, fraction)
      mixed = task_scale * (actual / dt * period) + style_scale * period * raw_style
      torch.testing.assert_close(mixed, expected, atol=1e-10, rtol=1e-10)
      mix_errors[f"dt{period}/mix{fraction}"] = (mixed - expected).abs().max().item()
  report = dict(
    passed=True, batch=n, dtype=str(dtype), reward_profile=task.reward_profile,
    source_commit=subprocess.check_output(
      ["git", "-C", args.upstream_root, "rev-parse", "HEAD"], text=True).strip(),
    source_sha256=source_hashes, original_upstream_methods_executed=True,
    upstream_term_count=16, term_max_absolute_error=errors,
    native_term_dtypes=native_dtypes,
    task_reward_max_absolute_error=(actual - weighted * dt).abs().max().item(),
    mix_max_absolute_error=mix_errors, standing_style_is_enabled=True,
    joint_ids=dict(legs=g1.LEG_JOINT_IDS, acceleration=g1.HIP_KNEE_IDS,
                   ankles=g1.ANKLE_IDS, hip_deviation=g1.HIP_DEVIATION_IDS,
                   arms=g1.ARM_IDS, waist=g1.WAIST_IDS),
    limitation="Formula oracle uses matching endpoint PD effort, control-step acceleration "
               "and timer inputs. It does not prove solver substep equivalence or gait convergence.")
  path = Path(args.output)
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text(json.dumps(report, indent=2) + "\n")
  print(json.dumps(report, indent=2))


if __name__ == "__main__":
  main()
