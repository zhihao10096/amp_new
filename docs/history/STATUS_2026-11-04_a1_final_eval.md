# 当前状态与恢复入口

## 范围、commit与目录
- 完整目标：已完成Go2 Manager收敛 → 当前A1 AMP平地行走 → 后续G1 AMP平地walk；全程禁PPO。原Go2 AMP已替换为A1，GOAL/PLAN和AMP_CONVERGENCE.md保留锁定指标、预算及阶段提交条件。
- 权威目录开发机`/pfs/user/learning/amp_new`，SSH `ssh -p 9205 root@118.196.87.69`；本地镜像`/home/user/Desktop/dream_codex_workspace/amp_new_src`。
- 当前训练代码/HEAD：a909cd2bd935a0df9ee45a0bf5d7bbfdb6312351（标签a1-amp-training-ready-20261104）。A1实现/动作已提交52b35b6；Manager完成提交b1f59eb。当前文档/交接记录有未提交更新，训练源码未变。
- 保留未跟踪reference/和早期诊断exploration.py、explore_eval.py、dynamics_eval.py、test_exploration.py；未用于正式训练，勿误提交。

## 当前实验、进程与配置
- 正式A1已从1000恢复到3000并保存；训练2528767已退出，串行验收队列2531693运行中，当前formal_r1_velocity2000_3000、active_pid=2538622。即时核实存活：{2528767: True, 2528768: True, 2531693: True}；队列状态waiting_for_training。恢复必须先核对/proc、队列JSON和GPU，避免重复启动。
- 当前运行目录`logs/supermimic/2026-11-04_02-21-44_764493_a1_amp_formal_r1_to3000`；完整命令/版本/源SHA：logs/amp_a1/formal_r1_to3000.process.json，训练日志formal_r1_to3000.log，显存formal_r1_to3000.process.gpu.json。
- 队列脚本logs/amp_a1/eval_r1_to3000.py；状态formal_r1_to3000.eval_pipeline.json，日志formal_r1_to3000.eval_pipeline.log。等待训练实际退出，依次完整速度2000/3000→步态/留出风格→3000加噪→三模型审计；数值通过才录制3段视频并抽帧。没有自动启动G1；最终仍需人工看图、归档及阶段git提交。
- 正式初始目录`logs/supermimic/2026-11-04_02-10-55_869146_a1_amp_formal_r1`；model_0独立保存，actor/WM从已验收Manager跨机器人热启动，critic/D/四优化器新建。初始训练2520598与1000评估/队列已全部退出；正式来源从未使用性能模型。
- 配置：32768env/collect1/buffer128，WM4096×4/window8/hidden512×3，imag8192/H32，critic3×4；actor_hidden/critic_hidden512,256,128，actor_scale=.15，warmup300+200/actor_ramp500；AMP2048×2/hidden512,256/lr1e-4/GP10/weight.5/ramp1000/RSI.5；seed0，FP32 highest/compile。1000以后保持最终奖励与原训练配置，CLI continue-run恢复四优化器和计数。

## 最新/最佳checkpoint与评估
- 最新正式checkpoint：`logs/supermimic/2026-11-04_02-21-44_764493_a1_amp_formal_r1_to3000/model_3000.pt`；**最佳已评估为初始正式目录model_1000.pt**。1000通过仅为1/3候选，2000/3000尚待完整评估，不得宣称A1阶段已收敛。
- 正式1000完整速度/步态/独立风格全部通过：formal_r1_assessment1000.json为velocity_failures=[]、gait_failures=[]。12固定+3随机的30秒速度及7指令×20秒步态均零摔倒。
- 1000固定总体RMSE=.08454/.05249/.07327；随机seed42/123/2026各组约(.075,.030,.067)，全部原阈值通过。报告formal_r1_velocity1000.json。
- 初始风格forward=.73862、fast=1.06638；1000=.52284/.68874，分别改善29.2%/35.4%。1/1.5m/s每足步频2.445/2.870Hz，腾空.1611/.1461s，平均离地.01979/.02239m，足滑.06961/.13077m/s；其余指令、站立和短摆动也通过。报告formal_r1_baseline_gait.json、formal_r1_gait1000.json。
- 正式1000实际模型审计formal_r1_checkpoint1000_audit.json通过：数据/来源/最终权重/有限性和四网络更新，优化器步数actor500/critic8400/WM4000/D1400。正式恢复2000审计formal_r1_resume2000_audit.json通过，步数→1500/20400/8000/3400且四网络继续更新，数据与来源一致。
- GPU接口/编译/参考与站立reset/翻倒/指令/终止历史/奖励一致见integration_bundled.json（FK max2.29e-6m，返回/actor梯度max5.96e-8）；最终CPU43项通过cpu_warmup_memory.log，短跑负例在audit_negative.json被完整验收器拒绝。
- 已完成Manager模型checkpoints/go2_manager_converged.pt（9000），7000/8000/9000完整速度/步态、最终加噪/录像/审计通过；源SHA07fc3f6e0e6801a3e60ab591be25dbeb3071c930809f847dd14284477dbfa9dd。证据MANAGER_CONVERGENCE.md、logs/manager_4090/convergence_report.json；无需重训。

## 数据、重要定位与已排除方向
- A1四份实际动作已纳入Git：assets/motions/a1/{trot1,pace1,left_turn1,right_turn1}.txt，默认从项目内加载；manifest记录来源b4666fa/许可/SHA256，前80%训练/参考重置、后20%独立时间留出，dt=.02，不跨split/loop。正式独立评估一律普通站立reset。
- 8k/16k/32k稳定吞吐3.46万/6.22万/11.04万真实转移/s，选择32k，峰值约20262MiB；performance_summary.json。原32k OOM来自critic预热无actor更新仍保留完整想象图，在gae_targets峰值耗尽显存；torch.set_grad_enabled(update_actor)修复后原batch/回放全部不变，完整真实更新通过。不是显存碎片主因，未盲目缩减并行数或学习批次。
- A1构造失败根因为Go2专属Head_.*正则，现使用trunk/hip/thigh/calf；不是资产缺失/CUDA故障。原生USD与参考URDF毫米差异已统一原生FK（1280状态拟合max2.11e-6m，geometry_fit.json）。
- 编译首轮失败为测试夹具随机重采样，固定同一窗口后原阈值通过。初始AMP权重0会被原生RewardManager跳过，分数采集已移至转移快照，每步可用且仍只乘一次权重/dt。此前引用reference路径/早期失败的smoke与溢出性能模型均不作正式来源。
- G1只读审计：参考commit f33a189，29DOF本地USD/Walk_B*数据可用；样例252帧、fps29.910979，root_pos/rot、29关节位置和6关键体位置，无直接速度字段，四元数约定/关节顺序仍待原生GPU验证。默认flat配置混有run/走跑转换，必须显式walk白名单、plane和不使用PPO。实际所用G1动作必须复制进项目Git（如assets/motions/g1），附来源/许可/SHA256/划分并默认本地加载；尚无G1实验。
- RTX4090D24GB；.venv Python3.10.12/Torch2.5.1+cu124/Lab2.1/Sim4.5。仿真清除PYTHONPATH，OMNI_KIT_ACCEPT_EULA=YES、OMNI_KIT_ALLOW_ROOT=1、TORCHINDUCTOR_COMPILE_THREADS=4。开发机无rg和系统python，使用.venv/bin/python。

## 未解决问题与下一条命令
- A1还需2000/3000完整速度/步态/独立风格、最终加噪、实际三模型审计和3段录像人工检查；数值或视觉失败须定位后继续，不能降低阈值。通过后归档模型/报告/视频并提交A1阶段，再实施G1 walk。
- 下一条命令（开发机项目目录）：`tail -n 2 logs/amp_a1/formal_r1_to3000.log; cat logs/amp_a1/formal_r1_to3000.eval_pipeline.json; nvidia-smi`，核实2528767/队列当前active_pid，勿重复启动训练/评估。
- 队列通过后查看logs/amp_a1/convergence_report.json、a1_video_contact_sheet.jpg及a1_amp_video_{stand,walk,fast}.json，视频videos/a1_amp_{stand,walk,fast}.mp4；人工确认后才复制最终checkpoint并git提交。若队列失败先读具体报告failures和子任务日志，保留已通过1000的原始证据。

历史事件：[本轮训练过程](docs/history/PROGRESS_2026-11-04_a1_training_before_eval.md)、[整理前状态](docs/history/STATUS_2026-11-04_a1_training_before_eval.md)、[A1实现排查](docs/history/PROGRESS_2026-11-04_a1_implementation.md)、[Manager过程](docs/history/PROGRESS_2026-11-04_manager.md)。

- A1恢复训练2528767到3000完成并退出；2000/3000位于logs/supermimic/2026-11-04_02-21-44_764493_a1_amp_formal_r1_to3000。开始两模型完整速度、步态、最终加噪和三模型实际来源/更新审计，尚无阶段收敛结论。

- A1任务启动formal_r1_velocity2000_3000，PID2538622，命令logs/amp_a1/formal_r1_velocity2000_3000.process.json，日志formal_r1_velocity2000_3000.log；不重复启动。

- 正式训练3000结束，完整原始配置保持，末段真实吞吐10.65万/s；已保存2000/3000，最佳已评估仍为1000。验收队列已实际开始两个模型完整速度（PID2538622）；不再有训练进程，勿重复启动。全部后续评估/录像仍依次由队列执行，数值未完成前不宣称收敛。

- A1任务结束formal_r1_velocity2000_3000，PID2538622，返回码0。

- A1任务启动formal_r1_gait2000_3000，PID2540607，命令logs/amp_a1/formal_r1_gait2000_3000.process.json，日志formal_r1_gait2000_3000.log；不重复启动。

- A1任务结束formal_r1_gait2000_3000，PID2540607，返回码0。

- A1任务启动formal_r1_noisy3000，PID2542023，命令logs/amp_a1/formal_r1_noisy3000.process.json，日志formal_r1_noisy3000.log；不重复启动。

- A1任务结束formal_r1_noisy3000，PID2542023，返回码0。

- A1任务启动formal_r1_convergence_audit，PID2543271，命令logs/amp_a1/formal_r1_convergence_audit.process.json，日志formal_r1_convergence_audit.log；不重复启动。

- A1任务结束formal_r1_convergence_audit，PID2543271，返回码0。

- A1三检查点1000/2000/3000完整速度/步态/留出风格与最终加噪、实际模型审计通过；convergence_report.json为converged=true。继续录制站立/正常走/快走，待人工抽帧检查及阶段提交，G1尚未启动。

- A1任务启动formal_r1_video_stand，PID2543490，命令logs/amp_a1/formal_r1_video_stand.process.json，日志formal_r1_video_stand.log；不重复启动。

- A1任务结束formal_r1_video_stand，PID2543490，返回码0。

- A1任务启动formal_r1_video_walk，PID2544259，命令logs/amp_a1/formal_r1_video_walk.process.json，日志formal_r1_video_walk.log；不重复启动。

- A1任务结束formal_r1_video_walk，PID2544259，返回码0。

- A1任务启动formal_r1_video_fast，PID2544931，命令logs/amp_a1/formal_r1_video_fast.process.json，日志formal_r1_video_fast.log；不重复启动。

- A1任务结束formal_r1_video_fast，PID2544931，返回码0。

- A1最终3段录像与抽帧完成：videos/a1_amp_{stand,walk,fast}.mp4，logs/amp_a1/a1_video_contact_sheet.jpg；数值审计通过，等待人工视觉检查、归档模型及阶段git提交。队列没有启动G1。下一命令cat logs/amp_a1/convergence_report.json，并读取队列状态/录像指标、查看抽帧。
