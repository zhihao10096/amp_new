# Go2 SuperMimic：Isaac Lab 速度跟踪

使用 **Isaac Lab / Isaac Sim / PhysX** 实现 Unitree Go2 平地速度跟踪。任务为
`Go2-Velocity-Flat`，输入机体系前进速度 `vx`、侧向速度 `vy`（m/s）与转向角速度
`yaw_rate`（rad/s），输出 12 个关节位置偏移。指令每 6–10 秒重采样，10% 为站立。

训练保留 SuperMimic 的模型学习方法：在 PhysX 中收集真实转移，拟合多步世界模型，
再通过冻结的世界模型进行想象滚动，反向传播更新 actor，并用 TD(λ) 更新 critic。

本机已训练并验证收敛模型：`checkpoints/go2_velocity_converged.pt`。第 3000、4000、
5000 次检查点连续通过完整指令评估；第 5000 次模型随机指令稳态 RMSE 为
vx / vy / yaw-rate = **0.048 / 0.032 / 0.039**，独立标准/带噪声评估均零摔倒。
模型和录像保留在本地，详见 [收敛验证记录](CONVERGENCE.md)。

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

`TrainCfg` 的字段均可用同名短横线参数设置，完整列表见 `--help`。默认 1024 个环境、
每迭代采样 4 步，前 300 次迭代只拟合世界模型，随后逐步提升 actor 学习率。
恢复时自动使用检查点中的网络尺寸和任务设置，并重新收集回放数据。
短跑用于检查执行链路，运动策略需要持续训练后按下面的实际速度误差评估。

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
```

不带 `--headless` 可打开 Isaac Sim 窗口。评估关闭观测噪声，随机种子默认 42；固定
指令在 episode 重置后继续生效。计时截断和摔倒分别统计，RMSE 覆盖全部采样步骤。

## 接口

- 仿真 200 Hz，控制 50 Hz；关节目标为 `default_joint_pos + 0.25 * action`。
  使用 Isaac Lab Go2 的 DC motor PD 与转速相关力矩限制，动作限幅到 `[-4, 4]`。
- actor 每帧 45 维：角速度 3、重力投影 3、速度指令 3、关节位置偏移 12、
  关节速度 12、上一动作 12；按观测项保存 5 帧历史，共 **225 维**。
  reset 清空历史，随后填入首帧。actor 不输入真实线速度。
- 世界模型状态 34 维：机身高度 1、重力投影 3、机体系线速度 3、角速度 3、
  关节位置偏移 12、关节速度 12。模型以当前状态、当前动作、上一动作预测状态增量。
- 奖励包含 XY 速度与 yaw-rate 指数跟踪、姿态/高度、动作变化、力矩、关节加速度和
  关节限位项。高度低于 0.16 m 或倾角超过 60° 终止，episode 最长 20 秒。
- 真实环境和想象使用相同的 Torch 观测及奖励函数；想象将相同终止边界平滑为生存概率。
  回放显式保存自动重置前的终止状态，多步损失不跨 episode 传播。

检查点包含 actor、critic、world model、归一化统计、优化器、任务配置和迭代计数，
使用 `isaaclab_velocity_v1` 格式。旧小球/避障任务、MuJoCo 模型、演示和旧策略已删除；
旧检查点的观测与动力学接口不适用于新任务。

## 目录

```text
go2_supermimic/
  velocity.py       共用的纯 Torch 指令、观测、奖励、终止及电机模型
  env/              Isaac Lab 配置、任务注册和 DirectRLEnv
  supermimic/       状态适配、回放、世界模型、想象滚动和训练器
scripts/            train.py、eval.py、benchmark.py
tests/              数值/梯度回归测试及显式 GPU 集成检查
PROGRESS.md         迁移进度及实际验证记录
CONVERGENCE.md      收敛标准、测量结果及本地模型位置
```

采用 MIT 许可证（见 [LICENSE](LICENSE)）。训练方法参考
[SuperMimic](https://arxiv.org/abs/2610.28480)，机器人资产使用
[Isaac Lab](https://github.com/isaac-sim/IsaacLab) 提供的 Unitree Go2 配置与 USD。
