# Go2 Isaac Lab 速度跟踪：当前进度

## 当前目标与结果
- 用户最初授权迁移到 Isaac Lab、删除追球/避障任务、可 Git 提交及启动训练；迁移已提交 `4ca881b`。
- 用户随后要求“继续训练直到任务收敛”。已完成：第 3000、4000、5000 次检查点连续通过预先记录的完整指令验收；第 5000 次模型的带训练噪声复测也通过。
- 收敛模型已复制至 `checkpoints/go2_velocity_converged.pt`，与原始 model_5000.pt SHA-256 一致。训练在评估期间继续至 6200 次附近，确认达标后发送 SIGINT 正常关闭；所有训练、评估和录像进程已退出。
- 最后工作：提交新增 benchmark、批量指令接口和收敛记录；不提交模型/录像/日志。

## 当前实现
- `Go2-Velocity-Flat`，Isaac Lab DirectRLEnv、官方 Go2 USD、PhysX 平地、200 Hz 物理 / 50 Hz 控制。
- 保留 SuperMimic：真实采样 → 多步世界模型拟合 → 想象 BPTT 更新 actor / TD(λ) 更新 critic。
- 机体系指令范围 vx [-1,1.5] m/s、vy [-0.6,0.6] m/s、yaw [-1,1] rad/s，每 6–10 秒切换，10% 站立。actor 225 维历史观测，模型 34 维状态。
- 共享纯 Torch 观测/奖励/指令/终止，回放显式保存重置前 next_state、屏蔽跨 episode 步；旧追球/避障、MuJoCo 模型和策略已移除。
- 新增 `scripts/benchmark.py`：20 种固定指令（含混合和边界），以及 42/123/2026 三随机种子；支持训练传感器噪声。

## 收敛依据
- 查看后续检查点前已记录标准：随机稳态 vx/vy/yaw RMSE <= (0.20,0.15,0.15)，摔倒率 <=0.1 次/机器人/分钟；每个固定用例 RMSE <=(0.30,0.25,0.25)，站立 <=(0.10,0.10,0.10)，固定组总摔倒率 <=0.1，单用例 <=0.5。
- 每检查点评估 20 指令 × 8 环境 × 30 秒，加 160 环境 × 3 随机种子 × 30 秒；每轮 320 机器人分钟。稳态剔除切换/重置后 1 秒，完整 RMSE 和摔倒仍覆盖全部步骤。
- 3000：随机稳态 RMSE (0.065,0.049,0.063)，随机种子各自摔倒率 0.0375/0.05/0，固定组零摔倒，全部用例达标。
- 4000：随机稳态 RMSE (0.067,0.040,0.049)，随机/固定全部零摔倒，全部用例达标。
- 5000：随机稳态 RMSE **(0.048,0.032,0.039)**，完整 **(0.155,0.073,0.076)**；固定/随机共 320 机器人分钟零摔倒。
- 5000 带噪声：随机稳态 RMSE **(0.052,0.035,0.061)**，完整 **(0.163,0.075,0.090)**；另 320 机器人分钟零摔倒，各固定用例达标。
- 三检查点误差范围 (0.0193,0.0168,0.0237)，无性能退化；最终完整标准见 `CONVERGENCE.md` 和机器可读报告。
- 最终录像 10 秒、960×540、25 fps、250 帧，指令 (1,0,0.5)，平均实测 (0.964,0.028,0.502)，零摔倒；已抽帧检查运动和目标/实际速度读数。

## 验证与本机环境
- Python 3.10、Isaac Lab 2.1.0、Isaac Sim 4.5.0、Torch 2.5.1、NumPy 1.26.4；RTX 4070 Ti SUPER 16 GB。
- 10 项 CPU 单测通过；PhysX 集成测试含 80 次 reset、1 次强制翻倒、80 次指令切换及单/批量指令跨 reset 保持。
- `pip check`、compileall、Git whitespace 检查通过。最新检查点模型张量全部有限，模型、归一化器、优化器状态齐全。
- shell 的 PYTHONPATH 注入 ROS 导致原始 pytest 缺少无关 lark；使用 `env -u PYTHONPATH` 隔离解决，无需改动 ROS。
- 首次 RTX 初始化/着色器编译较慢，已等到输出正常；未误判为训练阻塞。

## 本地生成物（均不提交）
- 模型：`checkpoints/go2_velocity_converged.pt`，元数据 `checkpoints/go2_velocity_converged.json`；迭代 5000，累计 14,348,288 真实转移。
- 原始运行：`logs/supermimic/2026-11-03_18-48-14_562457_velocity_convergence/`，含 model_3000/4000/5000/6000.pt。
- 训练日志：`logs/convergence/train.log`。
- 原始评估：`logs/convergence/benchmark_3000.json`、`benchmark_4000.json`、`benchmark_5000.json`、`benchmark_5000_noisy.json`。
- 审核报告：`logs/convergence/convergence_report.json`；生成脚本 `logs/convergence/report.py`；曲线 `logs/convergence/convergence.png`。
- 演示：`videos/go2_velocity_converged.mp4`，指标 `logs/convergence/video_metrics.json`。
