# 当前状态与恢复入口

## 目标、版本和目录
- 开发机权威目录`/pfs/user/learning/amp_new`，SSH `ssh -p 9205 root@118.196.87.69`。恢复先读GOAL/PLAN/本文件/PROGRESS，再核实HEAD、进程/GPU和实际产物，避免重复启动。
- 当前文档版本为本次提交HEAD（`git rev-parse HEAD`核实），复核起点`b44f9e087c9a624a5c2dbcb52b369ae304ba03a5`；本次仅文档变更，训练实现仍754e1fd。R3正式训练来源commit `9bc7115a082eafc403d5f8fb2947d10e3cac38b2`，动态诊断来源b44f9e0。原未跟踪reference/、exploration.py、explore_eval.py、dynamics_eval.py、test_exploration.py保留勿误提交。
- Manager/A1已独立成功 → 当前G1平地walk → 成功提交后X1下半身12DOF AMP；全程WM可微想象、禁PPO。X1部署参考reference/AMP、跳过RKNN，动作复制项目后.gitignore忽略，清单入Git；G1动作始终Git管理。

## 当前进程、配置与目录
- 2026-11-03T21:35:36+00:00重新核实：无项目实验进程，GPU显存1MiB、利用率0%、无计算进程。R3正式队列/训练/三点评估及动态覆盖诊断均已退出；不重复启动、不继续原配置。
- 动态覆盖队列`logs/amp_g1/dynamic_coverage_r3.pipeline.json`为`stage=complete`、`active_pid=null`，2026-11-04T05:27:29结束，四个子任务返回码均0。原driver PID2658191、采集2658193、拟合2658914、控制baseline2659119/refit2659811均已退出；运行目录项目根目录。
- 已完成诊断配置：冻结R3 model_3000 WM，同128个训练参考初态分别PD/速度前馈和MPC/H16/每步8次Adam，2s；仅初态写PhysX，其余只用真实action。WM拟合window8/batch128/lr1e-5/1000更新，统计冻结，初态75%/25%成对拟合/留出，不跨reset，专家留出未用于拟合。完整命令/日志/脚本SHA256见pipeline JSON的jobs。
- 产物均在`logs/amp_g1/`：`dynamic_coverage_r3_collect.json`、`dynamic_coverage_r3.transitions.pt`、`dynamic_coverage_r3_fit.json`、`dynamic_coverage_r3.world_model.pt`及`dynamic_coverage_r3_control_baseline.json`/`dynamic_coverage_r3_control_refit.json`。world_model.pt为`diagnostic_world_model_only`，不是正式四网/策略检查点。本次未启动新训练。

## 最新/最佳检查点与最近指标
- G1最新正式`logs/supermimic/2026-11-04_04-51-38_136861_g1_amp_formal_r3_exploration/model_3000.pt`；无通过验收的最佳/已收敛G1模型。R3配置18432env、collect1/buffer128、WM4096×4/window8/hidden512×3、imag8192/H32、critic3×4、actor/critic512,256,128、actor_lr_scale.15、WM预热300+critic200/actor_ramp500、FP32 highest/compile；D2048×2/interval5/lr1e-5/GP40/weight.5/ramp1000/RSI.5，25%OU .6/其余Gaussian .1。训练GPU峰值23124MiB、利用率约86%、约5.75万真实转移/s。
- R3完整1000/2000/3000固定RMSE(.963,.299,.410)/(.649,.192,.438)/(.630,.240,.390)，摔倒1460/2/63；0.6m/s每足步频全部0，3000留出风格改善59.2%/59.0%仍原地站立。四网络/四优化器/随机来源审计通过，汇总logs/amp_g1/formal_r3_summary.json及对应assessment/audit；不能把风格改善当行走成功。
- R2同样三点失败，3000固定RMSE(.637,.226,.410)、52摔、步频0，style改善41.8%/46.5%；R1三点也失败。两轮目录/详细失败见历史，均勿作成功或热启动来源。
- A1完成归档checkpoints/a1_amp_converged.pt（3000，SHA256 09a16f5f8bc4bcbf64a1c2dfd80010d3756b5c09224cc706d9a717b155a533ed），三点/加噪/录像/审计通过，固定RMSE .0498/.0524/.0385，风格改善36.3%/40.7%；AMP_CONVERGENCE.md及logs/amp_a1/convergence_report.json。Manager完成checkpoints/go2_manager_converged.pt，证据MANAGER_CONVERGENCE.md。两者勿重训。

## 关键结论、排除方案与未解决问题
- 首要未解决：真实闭环步行仍失败，预测误差与控制收益不一致。动态数据补充后8步留出线速度RMSE .29988→.14465（改善51.76%），同32个独立初态MPC平均存活1.2669→.9331s，两组2s内均32/32摔倒；PD对照均.7119s。证据fit及control_baseline/control_refit.json。暂不将MPC或诊断WM接入正式采样；先核查控制目标、想象优化与真实闭环误差，再设计新对照。不能据此声称已解决动态覆盖或已收敛。
- 骨架/映射未见不匹配：USD几何与7份训练动作足端RMSE<3.2e-7m，PhysX位置max6.03e-6m、link速度max2.71e-5m/s；CPU JVP max1.55e-15。WM足端/关节几何32步差3.74mm，直接FK替换实际足端误差仅12.71→12.59mm，收益小，暂不加投影；kinematics_r3.json。runtime根/足速度通道是COM，原型速度验证是link，已区分。原型仅在logs，未接入训练。
- 已排除：三轮同配置盲目续训/继续只加OU噪声、普通站立WM整体爆炸、严重RSI穿透（+.1m反增自由落体）、直接参考PD/前馈采样、普通站立复制状态的有限差分误差可直接证明梯度错误，以及run/走跑转换/粗糙地形。D存在姿态捷径，风格分不能替代速度/稳定性/步态。
- 接口/真实想象奖励/终止历史/RSI/编译/四网更新恢复/A1回归通过；节流CPU50项及GPU计数/旧模型兼容通过，discriminator_throttle_validation.audit.json。R3 model0与R2四网逐位一致，cfg仅explore_noise/run_name/stop_file变化，formal_r3_initial_audit.json。
- G1七份Walk_B和manifest在assets/motions/g1、USD在assets/robots/g1；前80%训练/RSI、后20%专家独立留出，不跨split/clip差分/插值；新增/替换动作也须复制并Git提交。本次逐文件核对manifest/SHA256/HEAD与Git追踪通过，证据logs/amp_g1/g1_motion_tracking_recheck_current.json；默认go2_supermimic/g1.py从项目内manifest加载。源f33a189 README声明MIT、LICENCE为Apache-2.0，冲突原文/SHA256已保留，动作独立授权未明示。
- RTX4090D24GB；.venv Python3.10/Torch2.5.1+cu124/Lab2.1/Sim4.5。仿真清PYTHONPATH，OMNI_KIT_ACCEPT_EULA=YES、OMNI_KIT_ALLOW_ROOT=1、TORCHINDUCTOR_COMPILE_THREADS=4；Kit后中文文档显式UTF-8。开发机无rg/系统python，用.venv/bin/python。

## 下一条命令
`sed -n '1,240p' logs/amp_g1/g1_reference_mpc_diagnostic.py`：先核查MPC控制目标、action映射与想象优化；结合已完成fit和成对真实control报告提出可验证闭环假设，再核对相关现成方案并决定新实验。恢复时仍须核对HEAD、pipeline和实际进程，禁止重新启动已结束队列。G1独立三点/最终加噪/录像/审计成功后才X1。

历史：[R3](docs/history/STATUS_2026-11-04_g1_r3_diagnosis.md)、[R2](docs/history/STATUS_2026-11-04_g1_r2_diagnosis.md)、[R1](docs/history/STATUS_2026-11-04_g1_r1_diagnosis.md)。X1只读预查logs/amp_x1/reference_prereview.json（6189ae4），尚未实施。
