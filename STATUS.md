# 当前状态与恢复入口

## 目标、版本与目录
- 开发机权威目录`/pfs/user/learning/amp_new`，SSH `ssh -p 9205 root@118.196.87.69`；本地镜像`/home/user/Desktop/dream_codex_workspace/amp_new_src`。
- 实现交接commit由标签`g1-amp-implementation-20261104`定位（提交前基线7f49486，恢复用git rev-parse HEAD核实）；A1完成37b6b58/7f49486，Manager完成b1f59eb。
- 总目标：Manager/A1已完成 → 当前G1 AMP平地walk → G1成功后X1 AMP行走。全程无PPO，SuperMimic WM/可微想象，各阶段独立验收/提交。GOAL/PLAN及G1_CONVERGENCE.md保留范围、预算及锁定标准。
- X1参考reference/AMP，只策略控制下半身12DOF；实际动作复制进项目后.gitignore忽略（来源/SHA256/split清单纳入Git），部署配置参照参考实现；用户明确无需处理RKNN。X1尚未开始。
- 保留未跟踪reference/和原有exploration.py、explore_eval.py、dynamics_eval.py、test_exploration.py，勿误提交。

## 当前进程与配置
- G1性能队列PID2564814，记录时阶段performance_16384、active_pid=2570333；已实际ps核实子进程。状态/完整命令`logs/amp_g1/performance_queue.json`，队列日志performance_queue.log，各子任务performance_N.log。恢复先看JSON、/proc和GPU，不能重复启动。
- 固定4k/8k/12k/16k并行环境串行比较，每规模80迭代；collect1/buffer128，WM4096×4/window8/hidden512×3，imag8192/H32，actor/critic512,256,128，critic3×4，AMP2048×2/hidden512,256/weight.5/RSI.5，FP32 highest/compile。性能模型不作正式训练来源；尚无正式G1训练。
- 4k已通过实际全更新/保存，稳定真实吞吐16132/s、峰值14382MiB/GPU98%；其余规模结果以performance_queue.json为准。选择规模后从随机初始化正式训练，保留独立model_0及最终原始配置，不能从性能模型热启动。
- G1初始接口2556134、smoke2558424、验证队列2560902及其所有子进程已实际退出。验证队列implementation_queue.json为complete，三个子任务均返回0。

## 最新/最佳checkpoint与证据
- G1无正式或已收敛模型。最新链路诊断`logs/supermimic/2026-11-04_03-04-30_578700_g1_smoke_resume/model_25.pt`；初始诊断目录`logs/supermimic/2026-11-04_03-00-37_568059_g1_smoke_initial/`，不能作正式成绩。性能模型目录logs/supermimic/*_g1_perf_N。
- CPU最终48项通过logs/amp_g1/cpu_implementation.log。GPUintegration_initial.json覆盖65reset/13终止/356指令切换/终止前状态和历史/普通与RSI reset/真实想象奖励一次dt；专家与PhysX特征max7.15e-7，编译返回max1.19e-7、actor梯度max1.46e-11。
- 实际四网络/四优化器更新及保存通过smoke_initial.audit.json；CLI恢复20→25继承任务/数据/来源，四网络继续更新且有限，步数actor16→21/critic36→46/WM20→25/D18→23；smoke_resume.audit.json。
- A1原生GPU接口回归a1_regression.json通过；G1完整七指令初始步态/独立留出评估可执行，smoke_baseline_gait.json风格距3.5375/3.5631（初始策略未收敛，仅验证评估链路）。完整评估入口benchmark.py/gait_eval.py/check_amp_convergence.py --robot g1。
- 已完成A1：checkpoints/a1_amp_converged.pt，源3000，SHA256 09a16f5f8bc4bcbf64a1c2dfd80010d3756b5c09224cc706d9a717b155a533ed；1000/2000/3000、最终加噪/录像/审计全部通过，证据AMP_CONVERGENCE.md及logs/amp_a1/convergence_report.json。3000固定RMSE .0498/.0524/.0385、随机约.045/.035/.026，风格改善36.3%/40.7%；视频videos/a1_amp_{stand,walk,fast}.mp4。
- Manager已完成：checkpoints/go2_manager_converged.pt，7000/8000/9000与最终加噪/录像/审计通过，证据MANAGER_CONVERGENCE.md。无需重训Manager/A1。

## 数据、关键决定与已排除方向
- G1七份Walk_B原样复制assets/motions/g1并纳入Git，源legged_lab f33a189（已核对GitHub固定源与本地一致）；本地29DOF USD复制assets/robots/g1。来源README标MIT但无独立LICENSE/运动许可文本，已如实记录，不套用本项目许可。
- manifest保存WXYZ、Lab 29关节和6关键体顺序及SHA256；前80%训练/RSI、后20%时间留出，速度分split差分，插值与对采样不跨边界。专家/PhysX顺序和特征已原生GPU验证；评估始终普通站立reset。
- 参考flat默认混有run/走跑转换且实现面向Lab3，不直接导入；采用七份walk白名单和本机Lab2.1原生plane。只用参考的角速度/绝对关节位置/速度61维AMP特征，沿本项目两帧LSGAN，不使用PPO。
- G1动作29、历史480、WM状态83、双足计时8；共用WM/回放/想象已按机器人维度参数化，Go2/A1默认接口不变且CPU/A1GPU回归通过。多电机组常量逐关节组装，原生DC PD/限幅与想象同公式。
- A1此前critic预热保留无用actor图导致OOM已修复；G1保留无actor更新时关闭梯度的路径。后续OOM按峰值来源定位，不盲目减学习batch。
- RTX4090D24GB；.venv Python3.10.12/Torch2.5.1+cu124/Lab2.1/Sim4.5。仿真清除PYTHONPATH，OMNI_KIT_ACCEPT_EULA=YES、OMNI_KIT_ALLOW_ROOT=1、TORCHINDUCTOR_COMPILE_THREADS=4。开发机无rg/系统python，使用.venv/bin/python。

## 未解决问题及下一条命令
- 当前G1实现/接口/更新/恢复已通过，正式收敛尚未验证。完成并行数/显存实测后选择规模，检查短benchmark新字段与完整验收器负例；正式从随机初始化保存model_0，持续训练并做锁定的连续三检查点/加噪/录像/实际审计。失败须定位，不能降低阈值。
- 下一条命令：`cat logs/amp_g1/performance_queue.json && nvidia-smi`；据active_pid运行`ps -p PID -o pid,stat,etime,args`并读对应日志尾部，继续同一队列，勿重复启动。全部性能任务结束后整理summary，选择正式规模/配置并更新记录。
- X1仅只读核对参考commit6189ae4，含资产、关节顺序、预处理和导出审计；待G1独立成功/提交后才接入，不处理RKNN。

历史：[G1实现/验证事件](docs/history/STATUS_2026-11-04_g1_implementation.md)、[A1](docs/history/STATUS_2026-11-04_a1_final_eval.md)、[Manager](docs/history/PROGRESS_2026-11-04_manager.md)。
