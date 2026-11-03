# 当前状态与恢复入口

## 范围、版本与目录
- 权威开发机`/pfs/user/learning/amp_new`，SSH `ssh -p 9205 root@118.196.87.69`；本地镜像`/home/user/Desktop/dream_codex_workspace/amp_new_src`。
- 当前交接commit由标签`a1-amp-handoff-20261104`定位（用`git rev-parse HEAD`核实）；A1完成结果37b6b5804750c661e503154cce0b17af4d37874e，训练源码a909cd2（a1-amp-training-ready-20261104）。A1实现52b35b6、Manager完成b1f59eb。
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
- G1补充只读核对：原始pkl可直接pickle读取（不需joblib依赖），root_rot是WXYZ，dof_pos为29维Lab顺序，6关键体顺序见retarget/config/g1_29dof.yaml；参考代码目前按Lab v3 XYZW适配，不能直接导入本机Lab2.1。README标注MIT，树中未找到独立LICENSE，数据来源/许可须在复制时如实记录并核对。
- RTX4090D24GB；.venv Python3.10.12/Torch2.5.1+cu124/Lab2.1/Sim4.5。仿真清除PYTHONPATH，OMNI_KIT_ACCEPT_EULA=YES、OMNI_KIT_ALLOW_ROOT=1、TORCHINDUCTOR_COMPILE_THREADS=4。开发机无rg/系统python，使用.venv/bin/python。

## 未解决问题与下一条命令
- A1数值/视觉/归档与阶段git提交均完成；G1实现和独立验收尚未完成，不能称总目标完成。G1需核对本地数据及资产、设计原生29DOF状态/观测/AMP与可微想象接口，在正式训练前锁定指令/步态/速度/稳定性标准。
- 下一条命令：`git rev-parse HEAD && nvidia-smi && sed -n "1,180p" reference/legged_lab/scripts/tools/retarget/config/g1_29dof.yaml`。先核实状态，再实施G1数据入库和接口；本次尚未改动G1源码、复制G1动作或启动G1实验。

历史：[A1验收过程](docs/history/STATUS_2026-11-04_a1_final_eval.md)、[A1训练过程](docs/history/STATUS_2026-11-04_a1_training_before_eval.md)、[A1实现](docs/history/PROGRESS_2026-11-04_a1_implementation.md)、[Manager](docs/history/PROGRESS_2026-11-04_manager.md)。

- 当前进入G1实现：七份Walk_B动作及29DOF USD已复制assets/motions/g1、assets/robots/g1（待实现验证后提交），来源/SHA256/许可状态已记录。无G1进程；下一步参数化WM/回放/想象接口并实现G1原生任务，正式训练前锁定指标。

- G1原生接口实验启动：integration_initial，PID 2556134，命令/日志logs/amp_g1/integration_initial.process.json与.log，配置32env/29act/83state/480obs、混合RSI、真实想象奖励/终止历史/编译梯度检查；CPU47项同时运行，日志cpu_initial.log。恢复先核实该PID与输出，不重复启动。

- 用户扩展最终目标：G1成功后参考reference/AMP接入X1 AMP行走，策略只输出下半身12DOF；X1参考动作复制进项目后在.gitignore忽略，来源/SHA256/split清单保留Git。GOAL/PLAN已更新；不改变当前G1验证，X1尚未启动。

- G1接口实验integration_initial已通过并退出：47项CPU、65次reset/13次终止/356次指令切换；实际专家/PhysX特征max7.15e-7，编译返回max1.19e-7/actor梯度max1.46e-11。开始真实四网络更新/保存smoke_initial，PID 2558424，命令与日志logs/amp_g1/smoke_initial.process.json及.log，32env/20迭代，仅链路验证，不作收敛来源。

- 正式G1训练前锁定G1_CONVERGENCE.md：12固定+3随机速度（含无接触≤2%）、7步态、0.6/1.0m/s独立留出风格相对model_0改善≥10%、连续三检查点间隔1000、最终加噪/录像/实际更新与来源审计。当前smoke仅链路验证，无正式训练。新目标还包含成功后的X1下半身12DOF及忽略原始动作。

- G1 smoke_initial已完成并退出，四网络权重/有限性/四优化器更新通过，步数actor16/critic36/WM20/D18；审计smoke_initial.audit.json，模型logs/supermimic/2026-11-04_03-00-37_568059_g1_smoke_initial/model_20.pt。串行验证队列PID2560902启动CLI恢复25→A1回归→G1初始留出步态评估，状态logs/amp_g1/implementation_queue.json。X1后续部署相关配置必须参考reference/AMP实现，已纳入GOAL/PLAN。

- G1验证子任务启动smoke_resume，PID2560903，命令/日志见logs/amp_g1/implementation_queue.json。

- G1验证子任务结束smoke_resume，PID2560903，返回码0。

- G1验证子任务启动a1_regression，PID2561439，命令/日志见logs/amp_g1/implementation_queue.json。

- G1验证子任务结束a1_regression，PID2561439，返回码0。

- G1验证子任务启动smoke_baseline_gait，PID2561968，命令/日志见logs/amp_g1/implementation_queue.json。

- G1验证子任务结束smoke_baseline_gait，PID2561968，返回码0。

- G1验证队列全部返回0并实际退出：CLI恢复20→25继承G1任务/数据/来源及四优化器，计数actor16→21/critic36→46/WM20→25/D18→23，权重继续更新/有限。A1原生接口回归通过；G1完整7指令初始步态/独立留出风格评估可执行（未收敛），证据smoke_resume.audit.json、a1_regression.json、smoke_baseline_gait.json。当前无训练；准备固定学习批次实测4k/8k/12k以上并行规模。

- G1性能串行队列PID2564814启动，4k/8k/12k/16k，每规模80迭代/WM4096×4/imag8192×H32/AMP2048×2/buffer128；只测吞吐/显存及真实全更新，性能模型不作正式来源。状态logs/amp_g1/performance_queue.json；失败即停止更大规模，恢复先核实active_pid。

- G1性能实验启动performance_4096，PID2564816，固定完整学习批次，运行状态/命令logs/amp_g1/performance_queue.json，日志performance_4096.log。

- G1性能实验结束performance_4096，返回码0，稳定真实吞吐16132.3/s，峰值显存14382MiB，GPU峰值98%。

- G1性能实验启动performance_8192，PID2567519，固定完整学习批次，运行状态/命令logs/amp_g1/performance_queue.json，日志performance_8192.log。

- G1性能实验结束performance_8192，返回码0，稳定真实吞吐29008.7/s，峰值显存16212MiB，GPU峰值82%。

- G1性能实验启动performance_12288，PID2568763，固定完整学习批次，运行状态/命令logs/amp_g1/performance_queue.json，日志performance_12288.log。

- 用户明确X1阶段无需处理RKNN相关代码，GOAL/PLAN已同步；其余部署配置仍以reference/AMP为依据。只读预查reference/AMP commit6189ae4，含X1资产/12DOF关节顺序/预处理及导出审计工具；尚未复制X1动作或启动X1实验。

- G1性能实验结束performance_12288，返回码0，稳定真实吞吐41393.0/s，峰值显存19218MiB，GPU峰值82%。

- G1性能实验启动performance_16384，PID2570333，固定完整学习批次，运行状态/命令logs/amp_g1/performance_queue.json，日志performance_16384.log。
