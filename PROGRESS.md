# Isaac Lab 速度跟踪迁移

## 目标与当前状态
用户授权在当前仓库迁移到 Isaac Lab，改为 Go2 速度跟踪，删除小球追踪与避障任务，可提交 Git 和启动训练验证。
代码迁移、CPU/GPU 集成检查、2000 次训练及恢复、独立速度评估和带速度读数的录像均完成，已完成提交前审查。

## 实现与依据
- 唯一任务 `Go2-Velocity-Flat`，使用 Isaac Lab DirectRLEnv、官方 Go2 USD、PhysX 平地、DC motor 位置控制；200 Hz 物理、50 Hz 控制。
- 保留 SuperMimic：真实采样 → 多步世界模型拟合 → 想象 BPTT 更新 actor / TD(λ) 更新 critic。
- 机体系 `(vx, vy, yaw_rate)` 指令每 6–10 秒重采样，10% 站立；actor 225 维历史观测，模型 34 维状态。
- `velocity.py` 是纯 Torch 的共用观测/奖励/指令/终止实现。已核对 Isaac Lab v2.1.0 官方 GitHub 示例与本机源码：自动重置在 rewards 与 observations 之间，因此在 rewards 阶段保存终止 next_state；回放保留终止转移并屏蔽后续跨 episode 步。
- 已删除旧 target、避障/地形任务、MuJoCo 模型、旧策略、旧演示、旧 driver/viz 和相关测试；依赖及 README/AGENTS.md 同步更新。检查点格式 `isaaclab_velocity_v1`，明确拒绝旧格式。

## 本机环境及排查
- RTX 4070 Ti SUPER 16 GB。项目初始 .venv 只有 Python 3.10 / Torch 2.7，无 Isaac Lab/Sim；已在该 .venv 安装 Isaac Lab 2.1.0 + Isaac Sim 4.5.0，按其约束使用 Torch 2.5.1 / NumPy 1.26.4，其他项目未修改。
- 安装复用了本机缓存，`pip check` 无依赖问题。
- shell 的 PYTHONPATH 注入 ROS pytest 插件，导致无关 `lark` 缺失；验证使用 `env -u PYTHONPATH` 隔离，无需改动 ROS。
- 首次 RTX 录像初始化/着色器编译较慢；已确认不是训练阻塞。运行模拟器时设置 `OMNI_KIT_ACCEPT_EULA=YES`。

## 验证结果
- `env -u PYTHONPATH .venv/bin/python -m pytest tests -q`：**10 passed**。
- `python -m compileall -q go2_supermimic scripts tests` 和 `git diff --check` 通过。
- `tests/check_isaaclab.py --headless`：16 环境、80 次重置、1 次强制翻倒、80 次指令切换；完整观测/奖励与共用实现一致，终止状态和固定指令跨重置行为正确。
- 32 环境 3 次迭代冒烟训练：世界模型及 actor/critic 更新、保存均通过。
- 256 环境先训练 400 次，再 `--continue-run` 恢复至 **2000 次**，累计 **2,052,096** 次真实转移，全部完成、无非有限数值。验证恢复后 actor/critic/world model 参数均继续变化，计数和优化器状态正确。
- 最终检查点所有模型张量有限、三组优化器状态齐全，迭代/观测尺寸正确。
- 64 环境 × 30 秒独立随机指令评估：vx / vy / yaw-rate RMSE 为 **0.652 m/s / 0.292 m/s / 0.165 rad/s**，6 次摔倒，**0.1875 次/机器人/分钟**。早期策略仍需更长训练，不能视为收敛。
- 最终录像已完成并抽帧检查：960×540、25 fps、125 帧、5 秒，目标/实际速度读数与 Go2/平地画面正常。固定指令 (0.8, 0, 0.3) 下零摔倒，yaw RMSE 0.0694 rad/s、vx RMSE 0.760 m/s；已学到转向响应，前进跟踪仍需训练。

## 本地生成物（均不提交）
- 检查点：`logs/supermimic/2026-11-03_18-28-09_678706_velocity_resume_validation/model_2000.pt`
- 训练日志：`/tmp/go2_velocity_training.log`、`/tmp/go2_velocity_resume.log`
- 随机评估：`logs/validation/random_eval_2000.json`
- 最终录像：`videos/velocity_validation.mp4`；指标 `logs/validation/video_eval_2000.json`。训练和评估进程均已正常结束。

## 后续使用
迁移及执行链路验证已完成。可从 model_2000.pt 使用 README 的 --resume / --continue-run 命令继续正式训练；当前策略尚未收敛。日志、视频、检查点和 .venv 不纳入 Git。
