# 当前状态与恢复入口

## 范围、版本与目录
- 权威开发机`/pfs/user/learning/amp_new`，SSH `ssh -p 9205 root@118.196.87.69`；本地镜像`/home/user/Desktop/dream_codex_workspace/amp_new_src`。
- 当前代码HEAD a909cd2bd935a0df9ee45a0bf5d7bbfdb6312351（a1-amp-training-ready-20261104）；本次补充A1完成文档，准备单独提交。A1实现52b35b6、Manager完成b1f59eb。
- 完整目标：Manager已完成 → A1 AMP已完成 → 下一阶段G1 AMP平地walk；全部禁PPO，沿SuperMimic世界模型/可微想象。GOAL/PLAN保留范围、预算、数据入库与各阶段提交要求。
- 保留未跟踪reference/及早期诊断exploration.py、explore_eval.py、dynamics_eval.py、test_exploration.py，勿误提交。

## 进程与运行配置
- 已实际核实：A1训练2528767、串行队列2531693及所有评估/录像子进程均退出；GPU无计算进程、显存1MiB。G1尚无实验，勿重复启动A1。
- 队列`logs/amp_a1/formal_r1_to3000.eval_pipeline.json`现为complete；全部7个子任务返回0，数值与人工视觉审查均通过。命令/PID/日志见该JSON及各process.json。
- A1最终目录`logs/supermimic/2026-11-04_02-21-44_764493_a1_amp_formal_r1_to3000`；初始与1000目录`logs/supermimic/2026-11-04_02-10-55_869146_a1_amp_formal_r1`。
- 正式配置：32768env/collect1/buffer128，WM4096×4/window8/hidden512×3，imag8192/H32，critic3×4；actor/critic512,256,128，actor_scale=.15，warmup300+200/ramp500；AMP2048×2/hidden512,256/lr1e-4/GP10/weight.5/ramp1000/RSI.5；seed0，FP32 highest/compile。1000恢复后保持最终奖励及四优化器/计数。

## 最新/最佳checkpoint与关键证据
- A1最新/最佳为正式model_3000.pt，归档`checkpoints/a1_amp_converged.pt`，SHA256 `09a16f5f8bc4bcbf64a1c2dfd80010d3756b5c09224cc706d9a717b155a533ed`。
- 1000/2000/3000三检查点完整12固定+3随机速度、7指令步态、独立留出风格全部通过；最终3000完整加噪速度和实际来源/更新审计通过，全部零摔倒。`logs/amp_a1/convergence_report.json`为converged=true/failures=[]。
- 3000固定总体RMSE=.04982/.05242/.03852；随机三组约.045/.035/.026；加噪固定总体=.05178/.05494/.05499。留出风格距离forward=.47081、fast=.63290，相对本次A1初始改善36.3%/40.7%；不以训练判别器分数作结论。
- 3000的1/1.5m/s步态全部通过锁定阈值，具体表见AMP_CONVERGENCE.md和formal_r1_gait2000_3000.json。四优化器步数actor2500/critic32400/WM12000/D5400，四网络/有限性/数据/来源通过实际模型审计。
- 3段10秒视频`videos/a1_amp_{stand,walk,fast}.mp4`均零摔倒；人工检查2秒连续步态及6/7/8/9秒后段，未见明显异常。证据`logs/amp_a1/visual_review.json`及两张contact_sheet.jpg。
- CPU43项、GPU原生接口/编译梯度/参考reset/站立reset/翻倒/指令/终止历史/真实想象奖励一致通过，详见integration_bundled.json、cpu_warmup_memory.log。短跑负例被完整验收器拒绝。
- Manager已完成并提交，模型`checkpoints/go2_manager_converged.pt`，7000/8000/9000及最终加噪/录像/审计通过；证据MANAGER_CONVERGENCE.md。无需重训。

## 数据、排除方向与环境
- A1四份实际动作纳入Git的assets/motions/a1，记录来源b4666fa/许可/SHA256，前80%训练/RSI、后20%独立时间留出，dt=.02，不跨split/loop。正式评估均普通站立reset。
- 8k/16k/32k吞吐3.46万/6.22万/11.04万真实转移/s，选择32k，峰值约20GB。critic预热保留无用actor图导致OOM已修复；不是显存碎片主因，未缩减并行数/batch。
- A1接触Head正则和原生USD/URDF几何差异已修复，专家/策略统一原生FK；编译测试随机重采样、零AMP权重日志缺失均已排除。早期失败smoke/性能模型不作正式训练来源。
- G1预查：reference/legged_lab commit f33a189，29DOF本地USD/Walk_B*可用；样例252帧、fps29.910979，root_pos/rot、29关节位置和6关键体位置，无直接速度，四元数/关节顺序待GPU核对。默认flat混有run/转换，须显式walk白名单/plane，禁止PPO。
- **G1实际使用的参考动作必须复制进assets/motions/g1等项目Git目录，记录来源commit/许可/SHA256/划分并随代码提交，训练/评估默认读取项目内副本。**
- RTX4090D24GB；.venv Python3.10.12/Torch2.5.1+cu124/Lab2.1/Sim4.5。仿真清除PYTHONPATH，OMNI_KIT_ACCEPT_EULA=YES、OMNI_KIT_ALLOW_ROOT=1、TORCHINDUCTOR_COMPILE_THREADS=4。开发机无rg/系统python，使用.venv/bin/python。

## 未解决问题与下一条命令
- A1数值/视觉/归档均完成，待本次阶段git提交；G1实现和独立验收尚未完成，不能称总目标完成。G1需核对本地数据及资产、设计原生29DOF状态/观测/AMP与可微想象接口，在正式训练前锁定指令/步态/速度/稳定性标准。
- 下一条命令：`git diff --stat`，审查本次A1完成文档并只提交指定文件，保留reference及诊断文件。提交后读取reference/legged_lab的G1 flat/robot/motion实现及许可证，实施G1数据入库和接口。

历史：[A1验收过程](docs/history/STATUS_2026-11-04_a1_final_eval.md)、[A1训练过程](docs/history/STATUS_2026-11-04_a1_training_before_eval.md)、[A1实现](docs/history/PROGRESS_2026-11-04_a1_implementation.md)、[Manager](docs/history/PROGRESS_2026-11-04_manager.md)。
