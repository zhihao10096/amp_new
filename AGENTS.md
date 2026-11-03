# Repository Guidelines

## Project Structure

The Python package is `go2_supermimic/`. Shared simulator-independent commands,
observations, rewards and terminations live in `velocity.py`; Isaac Lab task
configuration and DirectRLEnv live in `env/`; the SuperMimic state adapter, replay
buffer, world model, imagined rollouts and learner live in `supermimic/`.
Use `scripts/train.py` and `scripts/eval.py` as entry points. Tests are in `tests/`.
The robot is Isaac Lab's Unitree Go2 USD asset.

## Build, Test, and Development Commands

Run from the repository root in the configured Isaac Lab Python environment:

```bash
python -m pip install -e '.[dev]'
python -m pytest tests
python scripts/train.py --headless --task Go2-Velocity-Flat --run-name velocity
python scripts/eval.py Go2-Velocity-Flat --headless --checkpoint <model.pt> \
  --num-envs 1 --seconds 10 --command 0.8 0 0 --video videos/velocity.mp4
```

Training and evaluation require Isaac Lab / Isaac Sim and a CUDA GPU. Start
AppLauncher before importing simulator-dependent packages. The CPU tests need no
simulator. If the shell injects ROS packages, unset PYTHONPATH before running.

## Coding Style & Naming

Match the existing two-space indentation and type hints where useful. Use batched
Torch operations that preserve device and dtype, snake_case for modules/functions,
PascalCase for classes and UPPER_SNAKE_CASE for constants. Keep pure Torch helpers
free of Isaac Lab imports so they can be tested and reused by imagination.

## Testing Guidelines

Run `python -m pytest tests` before submitting. Seed sampled behavior and assert
numerical invariants with explicit tolerances. For simulation-facing changes,
also run a short GPU training with actual actor/critic updates, save/reload a
checkpoint and evaluate it. Check simulator and imagination observation/reward
parity, terminal next states and reset masking when touching those interfaces.
Do not treat a short smoke run as evidence of policy convergence.

## Progress and Commits

Maintain PROGRESS.md during long work: update after completed subtasks, key findings,
failed approaches and stage transitions. On resuming, read it and verify actual state.
Use concise imperative commit subjects. Do not commit generated logs, videos,
checkpoints, caches or virtual environments. Describe behavior changes and validation
results, and include a local video for simulation-facing changes when feasible.
