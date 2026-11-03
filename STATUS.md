# 当前状态与恢复入口

更新时间：2026-11-03 21:56:01 CST。本页是当前开发机的事实来源；历史训练结果未经本轮复现。

## 当前任务与版本
- 当前任务：熟悉项目并整理持久记录；未启动新实验。此前训练被用户要求停止，新 Manager 环境尚未证明收敛。
- 主机/目录：开发机，`/pfs/user/learning/amp_new`。
- 当前交接 commit：`HEAD`（本状态文件所在的文档提交，恢复时用 `git rev-parse HEAD` 获取完整哈希）。
- 当前代码基线 commit：`24046e2fef54b438e400a8bc8da1809aefbebcd7`（`dev`，切换训练环境）。本次提交仅整理文档。
- 整理前源码工作树干净；用户未跟踪的 `reference/` 包含 `rl_amp/`、`unitree_rl_lab/`，保持原状。

## 已核实的机器与进程
- GPU：NVIDIA RTX4090D，24564MiB；检查时1MiB/0%利用率。
- 活动实验：无；训练/评估/仿真 PID、作业 ID：无。本轮运行目录、实验配置：无。
- Python：`.venv/bin/python` 3.10.12；Torch2.5.1+cu124、IsaacLab2.1.0、IsaacSim4.5.0.0、Gymnasium1.2.3、TensorBoard2.20.0。
- 缺少 `pytest`、`mediapy` 和 `go2-supermimic` 安装元数据；仓库根目录下纯 Torch 模块导入通过。`PYTHONPATH` 当前未设置。
- 尝试 `env -u PYTHONPATH .venv/bin/python -m pytest -q tests`：报 `No module named pytest`，本轮没有测试通过结论。
- 直接导入 Isaac Lab 触发 Isaac Sim EULA 交互，在非交互会话以 EOF 结束；未代用户接受许可，也未启动仿真。之后按包元数据核对版本。
- 远端没有 `rg`，搜索可用 Python/pathlib 或 find。

## 实现与入口
- `velocity.py`：真实/想象共用的观测、奖励、终止、电机及足端计时；状态63维、计时16维、actor观测45×5=225维，动作12维。
- `env/`：原生六类 managers；环境不覆盖 step/reset；自动reset前捕获 next-state。仿真200Hz、控制50Hz。
- `supermimic/`：回放显式保留终止状态，多步世界模型拟合状态增量，冻结世界模型/critic进行可微想象更新actor，再以TD(λ)更新critic。
- 默认训练1024环境、WM batch1024×2、imag batch2048、horizon32；CLI由 `TrainCfg` 自动生成，入口 `scripts/train.py`。
- 评估入口：`scripts/eval.py`、`benchmark.py`（20固定+3随机种子）、`gait_eval.py`（7指令）、`check_convergence.py`（报告+实际checkpoint审计）。

## Checkpoint、运行目录与最近指标
- 当前项目目录下 `logs/`、`checkpoints/`、`videos/` 均不存在。当前可用最新/最佳 checkpoint：无。
- 历史最新 Manager：`logs/supermimic/2026-11-03_20-51-11_991689_manager_from_scratch/model_2025.pt`；主要诊断使用 `model_2000.pt`。仅见历史文档引用，本机不存在。
- 历史最佳旧Direct步态策略：`checkpoints/go2_velocity_gait.pt`；历史标准/加噪完整评估合计640机器人分钟零摔倒，随机稳态RMSE约(0.046,0.044,0.043)/(0.051,0.047,0.055)。本机模型/报告均不存在，未复验。
- 历史 Manager 从零配置：8192 env、WM4096×4、imag8192、800轮WM+200轮critic预热、actor_lr_scale0.3、action/explore noise0.1/0.5。
- 历史最近失败：model2000 固定前进平均vx约0.0006m/s，步频/离地为0；报告原路径 `logs/manager/diagnostic_2000.json`（缺失）。没有当前机器的学习指标。
- 历史旧步态模型在Manager环境5秒评估零摔倒、平均vx0.902m/s；只说明短时兼容，不能证明Manager从零训练收敛。

## 已排除方案与未解决问题
- 旧Direct收敛证据、短跑、仅GPU利用率不能代替新Manager训练收敛验收。
- 历史16GB GPU恢复训练在想象阶段OOM；拟减imag batch至4096（另一次WM3072）后被用户中止，未形成成功长跑。当前24GB机器需重新测量，不能据此宣称8192环境是上限。
- 不重复旧记录中的已停止PID/会话，不假定历史产物仍在；先确认恢复来源或选择随机初始化。
- 待处理：依赖与项目安装、许可状态/仿真可运行性、缺失产物来源、静止策略根因、当前GPU最佳吞吐配置，以及新Manager完整收敛验证。
- 本轮文档整理完成，全部文档链接及 `git diff --check` 通过；源码未改，纯Torch导入通过，pytest因缺依赖未执行。已将用户的commit和GPU效率偏好写入AGENTS。

## 下一条执行命令
恢复后先在本地执行以下只读命令，核对记录、HEAD和进程；没有新的训练指示时不要启动实验：

```bash
ssh -p 9205 root@118.196.87.69 'cd /pfs/user/learning/amp_new && cat GOAL.md PLAN.md STATUS.md && git log -1 --oneline && git status --short && ps -eo pid,stat,etime,args | grep -E "[p]ython.*scripts/(train|eval|benchmark|gait_eval)\.py|[i]saacsim" || true'
```

下一实验启动前，再根据用户指示补充运行目录、完整命令/配置、PID、预算和停止条件。历史细节见 [归档](docs/history/PROGRESS_2026-11-03.md)、[Manager验收](MANAGER_CONVERGENCE.md)。
