# Go2 速度跟踪收敛验证

2026-11-03，`Go2-Velocity-Flat` 在预先记录的验收标准下达到收敛要求。
第 3000、4000、5000 次迭代的连续三个检查点通过完整评估；保留第 5000 次模型。
评估期间训练继续到 6200 次附近，确认结果后停止训练，保留额外的第 6000 次检查点。

## 模型与本地产物

- 可直接使用：`checkpoints/go2_velocity_converged.pt`。
- 原始检查点：`logs/supermimic/2026-11-03_18-48-14_562457_velocity_convergence/model_5000.pt`。
- 训练迭代：5000；累计真实转移：14,348,288。模型、归一化器和优化器状态完整。
- SHA-256：`29df88a65975af8509fcfccfabf179aefe7704b9a26ef513135eec4b847ce148`。
- 机器可读报告：`logs/convergence/convergence_report.json`。
- 各检查点评估：`logs/convergence/benchmark_{3000,4000,5000}.json`。
- 噪声评估：`logs/convergence/benchmark_5000_noisy.json`。
- 曲线：`logs/convergence/convergence.png`。
- 演示录像：`videos/go2_velocity_converged.mp4`，10 秒、960×540、25 fps。

上述生成物保留在当前机器，按仓库约定不提交 Git。

## 验收标准与覆盖

在查看后续检查点结果前，将以下标准记录到 PROGRESS.md：

- 随机指令稳态 RMSE：vx ≤ 0.20 m/s，vy ≤ 0.15 m/s，yaw-rate ≤ 0.15 rad/s；
  每个种子的摔倒率 ≤ 0.1 次/机器人/分钟。
- 固定指令每个用例的稳态 RMSE：vx ≤ 0.30、vy ≤ 0.25、yaw-rate ≤ 0.25；
  站立三轴均 ≤ 0.10。固定组总摔倒率 ≤ 0.1，每个用例 ≤ 0.5 次/机器人/分钟。
- 连续三个相邻已保存检查点通过，并复测训练时的传感器噪声。

每个检查点测试 20 种固定指令，每种 8 个环境、30 秒；另用 160 个环境分别运行
42、123、2026 三个随机种子，每个 30 秒。每次完整评估共 320 机器人分钟。
固定指令包括站立、慢/快前进、后退、双向侧移、双向转向、混合运动以及范围边界
`(1.5, 0.6, 1)` / `(-1, -0.6, -1)`。训练的指令范围、奖励和任务难度保持原配置。

完整 RMSE 包括起步、指令变化和重置后的全部采样。稳态 RMSE 去除每次重置或指令
变化后的 1 秒；摔倒始终覆盖完整时段，正常 20 秒超时单独处理。

## 测量结果

下表为三个随机种子的算术平均 RMSE：

| 检查点 | 观测噪声 | 稳态 vx / vy / yaw-rate | 完整 vx / vy / yaw-rate | 随机组摔倒 | 固定组摔倒 |
|---|---|---|---|---:|---:|
| 3000 | 关闭 | 0.065 / 0.049 / 0.063 | 0.188 / 0.088 / 0.101 | 7 | 0 |
| 4000 | 关闭 | 0.067 / 0.040 / 0.049 | 0.170 / 0.078 / 0.085 | 0 | 0 |
| 5000 | 关闭 | 0.048 / 0.032 / 0.039 | 0.155 / 0.073 / 0.076 | 0 | 0 |
| 5000 | 训练噪声 | 0.052 / 0.035 / 0.061 | 0.163 / 0.075 / 0.090 | 0 | 0 |

三个检查点的各用例、各随机种子均达到标准。第 5000 次模型的 20 个固定用例中，
各轴最差稳态 RMSE 分别为 0.078 / 0.095 / 0.089；加噪后为 0.095 / 0.090 / 0.105。
第 3000 次模型随机组的 7 次摔倒分布为 3 / 4 / 0，各种子摔倒率 0.0375 / 0.05 / 0，
均在标准内；后续检查点的独立评估均零摔倒。

最终录像使用指令 `(1, 0, 0.5)`，10 秒全程零摔倒，平均实测速度
`(0.964, 0.028, 0.502)`；全程 RMSE 为 `(0.161, 0.040, 0.055)`。
已抽帧检查机器人运动和目标/实际速度读数。

## 复现评估

在项目 .venv 中运行；若 shell 自动注入 ROS，先 `unset PYTHONPATH`。

```bash
export OMNI_KIT_ACCEPT_EULA=YES
python scripts/benchmark.py --headless \
  --checkpoints checkpoints/go2_velocity_converged.pt \
  --output logs/convergence/recheck.json --seconds 30 --repeats 8 \
  --seeds 42 123 2026

python scripts/benchmark.py --headless \
  --checkpoints checkpoints/go2_velocity_converged.pt \
  --output logs/convergence/recheck_noisy.json --seconds 30 --repeats 8 \
  --seeds 42 123 2026 --observation-noise

python scripts/eval.py --headless --checkpoint checkpoints/go2_velocity_converged.pt \
  --command 1 0 0.5 --num-envs 1 --seconds 10 --video videos/go2_velocity_converged.mp4
```

训练从第 2000 次检查点恢复，1024 个环境、每迭代 4 步真实采样，
world-model batch / imagination batch 均为 1024，其余使用 TrainCfg 配置，
每 1000 次保存。完整运行参数见原始运行目录的 `config.json`。

新增批量固定指令接口已通过 PhysX 集成测试；CPU 单元测试 10 项通过。
