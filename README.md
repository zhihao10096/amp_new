# SuperMimic：Go2 Manager 与 A1 AMP 平地行走

当前目标、计划和开发机实际状态见 [GOAL.md](GOAL.md)、[PLAN.md](PLAN.md)、[STATUS.md](STATUS.md)。
新Manager环境已通过预先记录的独立验收：7000/8000/9000三个相隔1000迭代检查点完整速度和步态全部达标，最终加噪、录像及来源/更新审计通过。
最终模型 `checkpoints/go2_manager_converged.pt`，报告 [Manager验收记录](MANAGER_CONVERGENCE.md)，侧面对比 `videos/manager_gait_comparison.mp4`。旧训练产物仍保留于logs/videos。

当前推进 `A1-AMP-Flat`：Isaac Lab 原生 A1、平地、A1 动作数据和 AMP 风格奖励，
沿用 SuperMimic 世界模型与可微想象更新 actor，全程不用 PPO。数据、时间留出与独立收敛
标准见 [A1 AMP 验收](AMP_CONVERGENCE.md)；实现验证与实际训练状态见 STATUS.md。
后续为 G1 平地 walk。

使用 **Isaac Lab / Isaac Sim / PhysX** 实现 Unitree Go2 平地速度跟踪。任务为
`Go2-Velocity-Flat`，输入机体系前进速度 `vx`、侧向速度 `vy`（m/s）与转向角速度
`yaw_rate`（rad/s），输出 12 个关节位置偏移。指令每 6–10 秒重采样，10% 为站立。

训练保留 SuperMimic 的模型学习方法：在 PhysX 中收集真实转移，拟合多步世界模型，
再通过冻结的世界模型进行想象滚动，反向传播更新 actor，并用 TD(λ) 更新 critic。

环境现使用 **ManagerBasedRLEnv**，由原生动作、观测、指令、奖励、终止和事件
managers 执行任务。新实现已从随机初始化训练并通过收敛验收，结果及独立验收标准见
[Manager based 验证记录](MANAGER_CONVERGENCE.md)。可收敛历史版本的差异及修正依据见
[基线对照](MANAGER_BASELINE.md)。

以下为迁移前 Direct 环境的历史基线。速度收敛模型：
`checkpoints/go2_velocity_converged.pt`。第 3000、4000、
5000 次检查点连续通过完整指令评估；第 5000 次模型随机指令稳态 RMSE 为
vx / vy / yaw-rate = **0.048 / 0.032 / 0.039**，独立标准/带噪声评估均零摔倒。
模型和录像保留在本地，详见 [收敛验证记录](CONVERGENCE.md)。

步态改进模型为 `checkpoints/go2_velocity_gait.pt`：1 m/s 的每足步频从 6.04 降到
2.63 Hz，1.5 m/s 从 8.71 降到 2.75 Hz，抬脚和滑移均改善；
标准/带噪声完整评估合计 640 机器人分钟零摔倒。奖励、验收和训练参数见
[步态验证记录](GAIT.md)，本地对比视频为 `videos/go2_gait_comparison.mp4`。

## 环境与安装

验证版本：Python 3.10、Isaac Lab 2.1.0、Isaac Sim 4.5.0、Torch 2.5.1，CUDA GPU。
已配置 Isaac Lab 的环境只需安装项目；单元测试本身不需要模拟器。

```bash
source .venv/bin/activate
python -m pip install -e '.[dev]'

# 尚未安装 Isaac Lab / Sim 时，使用与本项目验证版本一致的可选依赖：
python -m pip install -e '.[isaac,dev]' --extra-index-url https://pypi.nvidia.com
```

首次使用 Isaac Sim 需接受其 EULA；无人值守运行可在接受协议后设置
`export OMNI_KIT_ACCEPT_EULA=YES`。默认使用 Isaac Lab 官方的 Go2 USD 资产，首次
加载需联网；已有完整本地 USD 资产时，训练和评估都可传 `--robot-usd /path/to/go2.usd`。

如果终端自动加载 ROS，先运行 `unset PYTHONPATH`，防止 ROS 插件污染虚拟环境。

## 训练

运行 A1 AMP：

```bash
python -m pytest tests
python tests/check_amp_isaaclab.py --headless
python scripts/train.py --headless --task A1-AMP-Flat \
  --warm-start checkpoints/go2_manager_converged.pt \
  --matmul-precision highest --compile-imagination --run-name a1_amp
```

默认读取项目内受 Git 管理的 `assets/motions/a1/` 中的 trot1、pace1、left_turn1、
right_turn1，无需 reference 目录即可运行 A1 AMP；[数据来源及许可](assets/motions/a1/README.md)
和 manifest 保存来源 commit 与 SHA256。专家与策略共用原生 A1 FK，
判别器使用相邻两帧 43 维状态及 LSGAN/专家梯度惩罚；真实与想象共享可微风格奖励。
`--amp-weight` 为每秒奖励权重，`--amp-ramp-iterations` 控制初期渐进，
`--amp-reference-reset-fraction` 控制参考重置比例，评估始终普通站立起步。
跨机器人热启动保留 actor/世界模型，其余网络及优化器新建；也可移除 warm-start 随机初始化。
保存包含判别器、优化器、机器人类型及运动数据 SHA256/split。
CLI 恢复自动继承 A1 任务与 AMP 配置；评估脚本也按 checkpoint 选择 A1，
gait_eval 额外输出与时间留出专家的独立风格距离。GPU 并行数仍需按实测吞吐和质量选择，
以上命令不代表已经收敛。

Go2 Manager 的历史训练入口：

```bash
python -m pytest tests
python tests/check_isaaclab.py --headless  # 仿真/想象接口、重置和指令切换
python scripts/train.py --headless --task Go2-Velocity-Flat --run-name velocity

# 小规模检查真实采样、世界模型、actor/critic 更新及保存：
python scripts/train.py --headless --num-envs 32 --iterations 10 \
  --warmup-iterations 2 --collect-steps 2 --buffer-len 32 \
  --wm-window 4 --wm-batch 32 --imag-batch 32 --horizon 4 \
  --wm-hidden 64 64 --actor-hidden 64 32 --critic-hidden 64 32 \
  --critic-epochs 1 --critic-minibatches 2 --log-interval 1 --save-interval 10 \
  --run-name smoke

# 恢复网络、归一化器及优化器；--iterations 为继续训练后的总迭代数。
python scripts/train.py --headless --resume logs/supermimic/<run>/model_1000.pt \
  --continue-run --iterations 5000 --run-name continued

tensorboard --logdir logs/supermimic
```

从随机初始化学习完整步态奖励时，可先使用弱运动惩罚，再逐步恢复最终权重：

```bash
python scripts/train.py --headless --reward-curriculum-start 3000 \
  --reward-curriculum-end 5000 --run-name manager_curriculum
```

初期关节偏移使用已收敛速度阶段的平方惩罚，再平滑过渡至最终步态范数；
调度在真实RewardManager与想象中使用相同公式和权重；checkpoint保留最终任务配置并记录实际
调度比例；恢复默认继承checkpoint中的调度参数，显式传参可覆盖，并按总迭代数继续。评估始终使用最终任务，完整验收拒绝尚未到最终权重的
checkpoint。默认不启用调度；本轮Manager随机来源已通过最终权重下的完整三检查点验收，证据见MANAGER_CONVERGENCE.md。

`TrainCfg` 的字段均可用同名短横线参数设置，完整列表见 `--help`。默认 1024 个环境、
每迭代采样 4 步，前 300 次迭代只拟合世界模型，随后逐步提升 actor 学习率。
恢复时自动使用检查点中的网络尺寸和任务设置，并重新收集回放数据。
短跑用于检查执行链路，运动策略需要持续训练后按下面的实际速度误差评估。

新版默认奖励参考 Unitree Go2 的速度任务，增加足端接触、腾空时序、滑移和摆脚高度约束。
已有速度策略可用 `--warm-start <model.pt>` 保留 actor 和动力学，重新拟合新增状态并训练
critic。`--resume` 会恢复检查点的原奖励；修改奖励后继续训练应使用 `--warm-start`。

本机 RTX 4070 Ti SUPER 16 GB 的吞吐测试中，8192 环境、世界模型批次 4096、
想象批次 8192 约采集 9.4 万条真实转移/秒，显存峰值 14,419 MiB；
1024 环境约 1.8 万条/秒。可用以下参数运行，显存较少时相应缩小：

```bash
python scripts/train.py --headless --num-envs 8192 --wm-batch 4096 \
  --wm-updates 4 --imag-batch 8192 --buffer-len 256 --run-name gait
```

可用 `--compile-imagination --matmul-precision highest` 编译想象单步，减少 Python
启动 GPU kernel 的开销；沿用原始基线的做法。奖励系数和公式混合比例使用设备张量，
课程权重插值时也复用编译图。首次编译耗时应与后续稳定吞吐分开统计。
FP32 返回和 actor 梯度已实测一致；TF32 的累计舍入不同，因此本轮编译训练使用 highest。

训练日志包含真实/想象转移吞吐。`--stop-file <path>` 可在该文件出现时保存并在迭代边界
停止；恢复前需移走该文件。更大的 batch 应以吞吐和策略质量评估，本机世界模型批次
8192 的吞吐约 7.3 万条/秒，低于批次 4096。

## 评估与录像

```bash
# 随机速度指令；报告 vx/vy/yaw-rate RMSE、平均速度、奖励和摔倒频率。
python scripts/eval.py Go2-Velocity-Flat --headless \
  --checkpoint logs/supermimic/<run>/model_1000.pt --num-envs 64 --seconds 30 \
  --metrics-json logs/eval/random.json

# 固定指令：前进 0.8 m/s，侧向 0，转向 0.3 rad/s。记录环境 0，25 fps。
python scripts/eval.py --headless --checkpoint logs/supermimic/<run>/model_1000.pt \
  --command 0.8 0 0.3 --num-envs 1 --seconds 10 --video videos/velocity.mp4
```

完整指令覆盖评估（20 种固定指令，加 3 个随机种子；同时输出完整误差与去除切换/重置后
1 秒过渡的稳态误差）：

```bash
python scripts/benchmark.py --headless --checkpoints <model.pt> \
  --output logs/convergence/benchmark.json --seconds 30 --repeats 8 \
  --seeds 42 123 2026
# 加 --observation-noise 可评估训练时的传感器噪声。

# 7 种固定指令的步频、腾空时长、抬脚高度、足滑和能耗对比。
python scripts/gait_eval.py --headless --checkpoints <old.pt> <new.pt> \
  --output logs/gait/comparison.json --seconds 20 --repeats 8
```

不带 `--headless` 可打开 Isaac Sim 窗口。评估关闭观测噪声，随机种子默认 42；固定
指令在 episode 重置后继续生效。计时截断和摔倒分别统计，RMSE 覆盖全部采样步骤。

## 接口

- 仿真 200 Hz，控制 50 Hz；关节目标为 `default_joint_pos + 0.25 * action`。
  使用 Isaac Lab Go2 的 DC motor PD 与转速相关力矩限制，动作限幅到 `[-4, 4]`。
- actor 每帧 45 维：角速度 3、重力投影 3、速度指令 3、关节位置偏移 12、
  关节速度 12、上一动作 12；按观测项保存 5 帧历史，共 **225 维**。
  原生 ObservationManager 在 reset 后用首帧填满历史。actor 不输入真实线速度。
- 世界模型状态 63 维：原有机身/关节状态 34 维，加足端位置 12、足端速度 12、
  足端接触 4、非足端接触数量 1。模型以当前状态、当前动作、上一动作预测状态增量。
  回放另外保存 16 维足端腾空/支撑计时，由仿真和想象共用的可微计时器更新。
- 奖励包含速度跟踪、姿态、关节偏差/速度、动作变化、力矩、能耗、关节加速度、
  关节限位，以及腾空时长、时长方差、足滑、非足接触、摆脚高度、站立足接触和
  对角配合约束。高度低于 0.16 m 或倾角超过 60° 终止，episode 最长 20 秒。
- 真实环境和想象使用相同的 Torch 观测及奖励函数；想象将相同终止边界平滑为生存概率。
  回放显式保存自动重置前的终止状态，多步损失不跨 episode 传播。

检查点包含 actor、critic、world model、归一化统计、优化器、任务配置和迭代计数，
使用 `isaaclab_velocity_v2` 格式；原速度任务的 v1 检查点可评估或通过 `--warm-start`
迁移，actor 的 225 维观测接口保持兼容。旧小球/避障任务的检查点不适用于速度任务。

## 目录

```text
go2_supermimic/
  velocity.py       共用的纯 Torch 指令、观测、奖励、终止及电机模型
  env/              ManagerBasedRLEnv 配置、manager terms、状态适配及任务注册
  supermimic/       状态适配、回放、世界模型、想象滚动和训练器
scripts/            train.py、eval.py、benchmark.py、gait_eval.py
tests/              数值/梯度回归测试及显式 GPU 集成检查
AMP_CONVERGENCE.md  A1 AMP动作数据、独立留出指标及验收标准
PROGRESS.md         迁移进度及实际验证记录
CONVERGENCE.md      收敛标准、测量结果及本地模型位置
MANAGER_CONVERGENCE.md  Manager based 迁移、随机初始化训练及新收敛验收
```

采用 MIT 许可证（见 [LICENSE](LICENSE)）。训练方法参考
[SuperMimic](https://arxiv.org/abs/2610.28480)，机器人资产使用
[Isaac Lab](https://github.com/isaac-sim/IsaacLab) 提供的 Unitree Go2 配置与 USD。
