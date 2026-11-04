"""Pure Torch normalization matching the legged_lab / RSL-RL 5.4.1 contract."""

import torch

from go2_supermimic.supermimic.world_model import RunningNorm


class LeggedLabNorm(RunningNorm):
  """Policy-only moments, explicit updates, epsilon .01, no input clipping.

  Uses this project's pooled-moment implementation. RSL-RL 5.4.1's forward
  never updates moments; its older installed version has different semantics.
  """

  def __init__(self, dim: int):
    super().__init__(dim, eps=0., clip=float("inf"))
    self.count = torch.zeros((), dtype=torch.long)

  @torch.no_grad()
  def update(self, x: torch.Tensor) -> None:
    if self.training and self.count < 100_000_000:
      super().update(x)

  def forward(self, x: torch.Tensor) -> torch.Tensor:
    return (x - self.mean) / (self.var.sqrt() + .01)
