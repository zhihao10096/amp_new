# 进度与恢复入口

先读STATUS/GOAL/PLAN，核实HEAD、队列active_pid、GPU及产物，避免重复实验。

- Manager完成b1f59eb；A1完成37b6b58/7f49486。各自三连续检查点、最终加噪/录像与实际模型审计通过，模型分别checkpoints/go2_manager_converged.pt、a1_amp_converged.pt；无需重训。
- 当前G1平地walk，之后X1 AMP：X1仅下半身12DOF，复制实际动作后.gitignore忽略；部署配置参考reference/AMP，明确跳过RKNN。全程禁PPO，各阶段独立提交，G1/X1未成功前总目标未完成。
- G1参考f33a189/GitHub固定源一致；七份Walk_B及29DOF USD已复制项目assets/motions/g1、assets/robots/g1并保留来源/许可实际状态/SHA256/split/顺序。显式排除run/走跑转换/粗糙地形，适配本机Lab2.1而非直接导入Lab3参考。
- G1接入原生Manager，29act/83state/8gait/480obs、参考RSI、61维相邻帧AMP/LSGAN/GP及真实/想象共享奖励和DC电机；共用训练/回放/想象按维度参数化。正式速度/步态/独立风格与三检查点/加噪/录像/审计标准在训练前锁定G1_CONVERGENCE.md。
- CPU48项通过；GPU验证65reset/13终止/356切换、真实想象奖励/历史/终止快照，专家/PhysX max7.15e-7、编译返回max1.19e-7/actor梯度max1.46e-11。真实四网络四优化器更新/保存通过，CLI恢复20→25步数actor16→21/critic36→46/WM20→25/D18→23且继续更新/有限。A1 GPU回归通过。证据logs/amp_g1/{integration_initial,smoke_initial.audit,smoke_resume.audit,a1_regression}.json。
- G1完整初始步态和留出风格可执行（诊断基线3.5375/3.5631，未收敛）；实现验证队列已退出。4k/8k/12k/16k/18k性能全部通过，选择18432（54114真实转移/s、峰值23108MiB）。实现5c02bf2、训练就绪14b7dcb已提交。正式随机训练队列2577168仍运行，首轮训练已正常结束并保存model_1000；当前阶段formal_r1_velocity1000/active_pid=2582551，目录logs/supermimic/2026-11-04_03-23-40_354760_g1_amp_formal_r1；model_0初始来源/四优化器/锁定任务与数据资产SHA256审计通过，先到1000再完整独立评估。

下一步：核实并继续当前正式G1队列，从1000开始按锁定标准完整独立评估，再决定后续训练/修复，不把短检查称收敛。G1成功提交后再实施X1。

历史事件docs/history/PROGRESS_2026-11-04_g1_implementation.md；原始日志保留路径和结论，不复制到记录。

- G1性能实验结束performance_16384，返回码0，稳定真实吞吐50966.3/s，峰值显存21846MiB，GPU峰值85%。

- G1实现/数据/资产与锁定验收已单独提交5c02bf2（g1-amp-implementation-20261104），正式收敛尚未验证。X1只读部署预查保存logs/amp_x1/reference_prereview.json：源6189ae4、31资产DOF/12策略DOF、.002×5=.01控制周期、10帧历史、动作比例.25、根高1.03及部署配置入口；未实施或复制X1动作，明确排除RKNN。

- 4k/8k/12k/16k性能全部通过并退出，稳定吞吐16132/29009/41393/50966真实转移/s，峰值14382/16212/19218/21846MiB，summary见logs/amp_g1/performance_summary.json。额外串行队列PID2572786启动短benchmark新字段检查及18432规模实测，状态performance_extra_queue.json；完成后选正式配置，从随机初始化保存model_0。

- G1性能实验启动short_velocity，PID2572788，固定完整学习批次，运行状态/命令logs/amp_g1/performance_extra_queue.json，日志short_velocity.log。

- G1性能实验结束short_velocity，返回码0，稳定真实吞吐0.0/s，峰值显存5590MiB，GPU峰值43%。

- G1性能实验启动performance_18432，PID2573272，固定完整学习批次，运行状态/命令logs/amp_g1/performance_extra_queue.json，日志performance_18432.log。

- 短G1速度benchmark新机器人/12指令/flight字段已实际运行成功；完整验收器负例audit_negative.json正确拒绝短跑（require_three_velocity_and_gait_checkpoints）。同一更新后的验收器重读实际A1三个模型及原始报告仍converged=true，a1_final_audit_regression.json；此回归未重训或改动A1产物。18k性能实验仍按原队列运行。

- G1性能实验结束performance_18432，返回码0，稳定真实吞吐54114.3/s，峰值显存23108MiB，GPU峰值85%。

- G1并行性能已全部完成/退出：18432稳定54114真实转移/s、峰值23108MiB/GPU85%，选择此规模且学习批次不变，summary已归档。正式首轮决定已写G1_CONVERGENCE.md：随机初始化seed0、WM预热300+critic200、actor_ramp500、AMP_ramp1000，先到1000完整独立评估；无热启动或PPO，所有性能模型排除。准备提交训练就绪记录并启动正式队列。

- G1正式队列已实际启动，PID2577168，训练代码/HEAD 14b7dcbaf7257b8b32dce1d8db467b16225595be（14b7dcb），启动记录formal_r1.launch.json；状态logs/amp_g1/formal_r1.pipeline.json包含active_pid/配置/运行目录/检查点。18432环境、随机初始化，无PPO/热启动，先1000再完整基线/速度/步态/风格。下一条命令cat logs/amp_g1/formal_r1.pipeline.json并核实active_pid/GPU，禁止重复启动。

- G1正式任务启动formal_r1_train，PID2577268，命令/配置/日志logs/amp_g1/formal_r1_train.process.json及.log，队列formal_r1.pipeline.json；不重复启动。

- 正式G1已保存独立model_0，运行目录logs/supermimic/2026-11-04_03-23-40_354760_g1_amp_formal_r1；训练PID2577268/队列2577168实际存活。初始四优化器为空、随机来源、无resume/warm-start、锁定任务/数据及本地USD SHA256全部核对通过formal_r1_initial_audit.json。当前WM预热阶段，不能以早期奖励/吞吐宣称收敛。X1部署预查另发现旧31DOF审计/可视化工具与当前12DOF策略接口不一致，后续须按实际源代码/数据验证，审计logs/amp_x1/reference_prereview.json；尚未开始X1实现。

- G1正式任务结束formal_r1_train，PID2577268，返回码0，证据logs/amp_g1/formal_r1_train.log。

- G1正式1000训练及实际四网络四优化器/随机来源审计通过，开始初始基线及完整独立速度/步态/留出风格；不代表已收敛。

- G1正式任务启动formal_r1_baseline_gait，PID2581898，命令/配置/日志logs/amp_g1/formal_r1_baseline_gait.process.json及.log，队列formal_r1.pipeline.json；不重复启动。

- G1正式任务结束formal_r1_baseline_gait，PID2581898，返回码0，证据logs/amp_g1/formal_r1_baseline_gait.log。

- G1正式任务启动formal_r1_velocity1000，PID2582551，命令/配置/日志logs/amp_g1/formal_r1_velocity1000.process.json及.log，队列formal_r1.pipeline.json；不重复启动。

- 2026-11-04 03:30:45 CST：落实用户G1数据要求，PLAN明确`assets/motions/g1/`及后续新增/替换同规则；七份实际动作均已在HEAD纳入Git，SHA256全匹配，默认加载入口go2_supermimic/g1.py:31。正式model_0基线留出风格距离forward=3.538978/fast=3.586489（仅初始基线）；1000独立评估未结束。无新启动实验。
