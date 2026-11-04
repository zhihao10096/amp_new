"""A1 motion data and differentiable AMP, independent of the simulator.

The two-frame LSGAN objective and expert gradient penalty follow rl_amp /
AMP_for_hardware. Policy optimization remains SuperMimic, without PPO.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import torch
from torch import nn

from go2_supermimic import velocity as v
from go2_supermimic.supermimic.world_model import RunningNorm, mlp

AMP_DIM = 43
A1_GEOMETRY = (.1805, .047, .0838, .2, .2)
DEFAULT_A1_MOTIONS = ",".join(
  f"assets/motions/a1/{name}.txt"
  for name in ("trot1", "pace1", "left_turn1", "right_turn1"))


def leg_to_joint_order(values: torch.Tensor) -> torch.Tensor:
  """FL/FR/RL/RR triples -> Isaac Lab hips, thighs, calves."""
  return values.reshape(*values.shape[:-1], 4, 3).transpose(-1, -2).flatten(-2)


def a1_foot_positions(q: torch.Tensor) -> torch.Tensor:
  """Isaac Lab 2.1 A1 USD kinematics, foot-link origins in the root frame.

  Validated against 1280 PhysX states. The reference URDF has hip_x=.183 and
  lateral=.08505; recomputing both expert and policy feet avoids that mismatch.
  """
  hip, thigh, calf = q.unflatten(-1, (3, 4)).unbind(-2)
  side = q.new_tensor((1., -1., 1., -1.))
  front = q.new_tensor((1., 1., -1., -1.))
  hip_x, hip_y, lateral, upper, lower = A1_GEOMETRY
  x = hip_x * front - upper * thigh.sin() - lower * (thigh + calf).sin()
  local_z = -upper * thigh.cos() - lower * (thigh + calf).cos()
  y = hip_y * side + lateral * side * hip.cos() - local_z * hip.sin()
  z = lateral * side * hip.sin() + local_z * hip.cos()
  return torch.stack((x, y, z), -1).flatten(-2)


def state_features(state: torch.Tensor, default_q: torch.Tensor) -> torch.Tensor:
  """Same 43 features for real transitions and differentiable imagined states."""
  q = state[..., v.Q] + default_q
  return torch.cat((q, a1_foot_positions(q), state[..., v.V_B],
                    state[..., v.W_B], state[..., v.QD], state[..., v.Z]), -1)


def frame_features(frames: torch.Tensor) -> torch.Tensor:
  q = leg_to_joint_order(frames[..., 7:19])
  return torch.cat((q, a1_foot_positions(q), frames[..., 31:37],
                    leg_to_joint_order(frames[..., 37:49]), frames[..., 2:3]), -1)


def slerp_xyzw(a: torch.Tensor, b: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
  """Normalized shortest-arc quaternion interpolation, including antipodes."""
  dot = (a * b).sum(-1, keepdim=True)
  b = torch.where(dot < 0, -b, b)
  dot = dot.abs().clamp(max=1 - 1e-7)
  angle = dot.acos()
  curved = ((1 - t) * angle).sin() / angle.sin() * a + (
    t * angle).sin() / angle.sin() * b
  result = torch.where(dot > .9995, torch.lerp(a, b, t), curved)
  return nn.functional.normalize(result, dim=-1)


class MotionLibrary:
  """Vectorized, correctly timed pairs with a disjoint temporal holdout.

  The last 20% of each clip is reserved for evaluation. A pair and its entire
  interpolation support stay inside one split and one clip. No loop-boundary
  translation or quaternion jump becomes an expert transition.
  """

  def __init__(self, files: str, device: str | torch.device, dt: float = .02,
               train_fraction: float = .8):
    if not 0 < train_fraction < 1 or dt <= 0:
      raise ValueError("need positive dt and 0 < train_fraction < 1")
    paths = [Path(x.strip()) for x in files.split(",") if x.strip()]
    if not paths or len(set(paths)) != len(paths):
      raise ValueError("motion files must be a nonempty list of distinct paths")
    self.device, self.dt = device, dt
    frames, durations, sizes, splits, weights, metadata = [], [], [], [], [], []
    for path in paths:
      raw = path.read_bytes()
      data = json.loads(raw)
      x = torch.tensor(data["Frames"], dtype=torch.float32)
      duration, weight = float(data["FrameDuration"]), float(data["MotionWeight"])
      if (x.ndim != 2 or x.shape[1] < 49 or x.shape[0] < 6
          or not torch.isfinite(x).all() or not 0 < duration < float("inf")
          or not 0 < weight < float("inf")):
        raise ValueError(f"invalid AMP motion: {path}")
      length = x.shape[0]
      split = int(length * train_fraction)
      if min((split - 1) * duration, (length - 1 - split) * duration) <= dt:
        raise ValueError(f"motion too short for separate train/holdout pairs: {path}")
      norm = x[:, 3:7].norm(dim=-1, keepdim=True)
      if (norm < 1e-6).any():
        raise ValueError(f"zero motion quaternion: {path}")
      x[:, 3:7] /= norm
      frames.append(x[:, :49])
      durations.append(duration)
      sizes.append(length)
      splits.append(split)
      weights.append(weight)
      metadata.append({"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(),
                       "frames": length, "frame_dt": duration, "split_frame": split,
                       "weight": weight})
    self.frames = torch.cat(frames).to(device)
    self.offsets = torch.tensor([0] + sizes[:-1], device=device).cumsum(0)
    self.durations = torch.tensor(durations, device=device)
    self.sizes = torch.tensor(sizes, device=device)
    self.splits = torch.tensor(splits, device=device)
    self.weights = torch.tensor(weights, device=device)
    self.weights /= self.weights.sum()
    self.metadata = {"schema": "a1_amp_43_v1", "dt": dt, "geometry": list(A1_GEOMETRY),
                     "train_fraction": train_fraction, "motions": metadata}

  def sample_times(self, batch: int, train: bool) -> tuple[torch.Tensor, torch.Tensor]:
    clips = torch.multinomial(self.weights, batch, replacement=True)
    split, size, frame_dt = self.splits[clips], self.sizes[clips], self.durations[clips]
    low = torch.zeros_like(frame_dt) if train else split * frame_dt
    high = ((split - 1) if train else (size - 1)) * frame_dt - self.dt
    return clips, low + torch.rand(batch, device=self.device) * (high - low)

  def at_time(self, clips: torch.Tensor, times: torch.Tensor) -> torch.Tensor:
    position = times / self.durations[clips]
    low = position.floor().long().clamp(min=0)
    low = low.minimum(self.sizes[clips] - 2)
    alpha = (position - low).clamp(0, 1).unsqueeze(-1)
    a, b = self.frames[self.offsets[clips] + low], self.frames[self.offsets[clips] + low + 1]
    blend = torch.lerp(a, b, alpha)
    return torch.cat((blend[:, :3], slerp_xyzw(a[:, 3:7], b[:, 3:7], alpha),
                      blend[:, 7:]), -1)

  def sample_frames(self, batch: int, train: bool = True) -> torch.Tensor:
    clips, times = self.sample_times(batch, train)
    return self.at_time(clips, times)

  def sample_pairs(self, batch: int, train: bool = True) -> tuple[torch.Tensor, torch.Tensor]:
    clips, times = self.sample_times(batch, train)
    return (frame_features(self.at_time(clips, times)),
            frame_features(self.at_time(clips, times + self.dt)))


class AMPDiscriminator(nn.Module):
  features = staticmethod(state_features)

  def __init__(self, hidden: tuple[int, ...] = (512, 256), feature_dim: int = AMP_DIM,
               num_frames: int = 2, command_gate: bool = True):
    super().__init__()
    if num_frames not in (2, 4):
      raise ValueError("AMP num_frames must be 2 or 4")
    self.num_frames = num_frames
    self.command_gate = command_gate
    self.norm = RunningNorm(feature_dim)
    self.net = mlp(num_frames * feature_dim, hidden, 1, act=nn.LeakyReLU)

  def forward(self, before: torch.Tensor, after: torch.Tensor) -> torch.Tensor:
    return self.net(torch.cat((self.norm(before), self.norm(after)), -1)).squeeze(-1)

  def sequence_score(self, features: torch.Tensor) -> torch.Tensor:
    """Chronological B x F x D observations, with shared per-frame statistics."""
    if features.ndim != 3 or features.shape[1] != self.num_frames:
      raise ValueError("AMP sequence length differs from the discriminator")
    return self.net(self.norm(features).flatten(1)).squeeze(-1)

  def reward(self, before: torch.Tensor, after: torch.Tensor, default_q: torch.Tensor,
             commands: torch.Tensor, history: torch.Tensor | None = None) -> torch.Tensor:
    # Deliberately retain state/action gradients; callers freeze only parameters.
    if self.num_frames == 2:
      score = self(self.features(before, default_q), self.features(after, default_q))
    else:
      if history is None or history.shape[1] != self.num_frames - 2:
        raise ValueError("multi-frame AMP requires pre-transition state history")
      states = torch.cat((history, before[:, None], after[:, None]), 1)
      score = self.sequence_score(self.features(states, default_q))
    style = (1 - .25 * (score - 1).square()).clamp(min=0)
    return style * (commands.norm(dim=-1) > .1) if self.command_gate else style

  def loss(self, expert: tuple[torch.Tensor, torch.Tensor] | torch.Tensor,
           policy: tuple[torch.Tensor, torch.Tensor] | torch.Tensor,
           penalty: float = 10.) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    if isinstance(expert, torch.Tensor):
      if (not isinstance(policy, torch.Tensor) or expert.ndim != 3
          or expert.shape[1:] != policy.shape[1:]
          or expert.shape[1] != self.num_frames):
        raise ValueError("invalid AMP expert/policy temporal sequences")
      with torch.no_grad():
        self.norm.update(torch.cat((expert.flatten(0, 1), policy.flatten(0, 1))))
      positive = self.norm(expert).flatten(1).detach().requires_grad_()
      expert_score = self.net(positive).squeeze(-1)
      policy_score = self.sequence_score(policy.detach())
      return self._score_loss(positive, expert_score, policy_score, penalty)
    a, b = expert
    c, d = policy
    with torch.no_grad():
      self.norm.update(torch.cat((a, b, c, d)))
    positive = torch.cat((self.norm(a), self.norm(b)), -1).detach().requires_grad_()
    expert_score = self.net(positive).squeeze(-1)
    policy_score = self(c.detach(), d.detach())
    return self._score_loss(positive, expert_score, policy_score, penalty)

  @staticmethod
  def _score_loss(positive: torch.Tensor, expert_score: torch.Tensor,
                  policy_score: torch.Tensor, penalty: float
                  ) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    classification = .5 * ((expert_score - 1).square().mean()
                            + (policy_score + 1).square().mean())
    grad = torch.autograd.grad(expert_score.sum(), positive, create_graph=True)[0]
    regularizer = penalty * grad.square().sum(-1).mean()
    return classification + regularizer, {
      "amp_classification_loss": classification.detach(),
      "amp_gradient_penalty": regularizer.detach(),
      "amp_expert_score": expert_score.detach().mean(),
      "amp_policy_score": policy_score.detach().mean(),
    }


@torch.no_grad()
def heldout_style_distance(pairs: torch.Tensor, library: MotionLibrary,
                           command_vx: float) -> float:
  """Independent nearest-expert pair distance; never use the learned critic.

  Normalize with training-expert statistics, compare against held-out time
  segments, and condition references on forward speed within 0.35 m/s.
  """
  if pairs.ndim != 2 or pairs.shape[-1] != 2 * AMP_DIM or len(pairs) < 128:
    raise ValueError("style evaluation needs at least 128 real transition pairs")
  train_a, train_b = library.sample_pairs(4096, train=True)
  train = torch.cat((train_a, train_b), -1)
  scale = train.std(0, unbiased=False).clamp(min=.05)
  a, b = library.sample_pairs(8192, train=False)
  keep = ((a[:, 24] + b[:, 24]) * .5 - command_vx).abs() < .35
  reference = torch.cat((a[keep], b[keep]), -1)
  if len(reference) < 128:
    raise ValueError("insufficient held-out expert pairs in the speed band")
  reference = reference[:2048] / scale
  # Chunk queries to bound evaluation memory on the 24 GB development GPU.
  distances = [torch.cdist(query / scale, reference).square().min(-1).values
               for query in pairs.split(256)]
  return (torch.cat(distances).mean() / (2 * AMP_DIM)).item()
