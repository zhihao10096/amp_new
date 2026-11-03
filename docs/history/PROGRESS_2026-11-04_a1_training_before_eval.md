# 进度与恢复入口

恢复先读[STATUS.md](STATUS.md)，核实Git、进程、产物；范围与预算见[GOAL.md](GOAL.md)，阶段见[PLAN.md](PLAN.md)。

## 已完成：Go2 Manager收敛
- 随机来源7000/8000/9000连续通过完整速度/步态，最终加噪、录像和来源/更新审计通过；四轮完整速度合计1280机器人分钟零摔倒。模型checkpoints/go2_manager_converged.pt；证据MANAGER_CONVERGENCE.md。
- 已提交b1f59eb；可收敛d9eee9b3对照和平方关节惩罚差异、PhysX容量/编译结论见MANAGER_BASELINE.md。无需重训Manager。

## 当前：A1 AMP正式训练与独立评估
- Go2 AMP按用户要求替换为A1 AMP平地行走；后续G1只做平地walk，全程禁PPO。GOAL已更新指令范围/独立指标/预算/完成条件，AMP_CONVERGENCE.md在正式训练前锁定完整标准。
- 接入原生A1 Manager配置、接触pattern、运动库/时间留出、参考重置、43维相邻帧LSGAN、冻结判别器可微想象奖励、真实判别器更新及checkpoint保存/恢复。actor继续沿SuperMimic世界模型反传。
- 定位A1构造失败为Go2的Head_.*正则；A1改用trunk。1280真实状态拟合原生FK，误差max2.11e-6m，专家/策略统一重算，排除USD/URDF形态差异判别标签（geometry_fit.json）。
- 编译首轮比较失败为测试夹具随机切换指令；固定相同窗口后原阈值通过。首次训练因零权重term被RewardManager跳过而缺style日志；GitHub v2.1.0源码核对后移到转移快照采集，GPU0/.123/.5权重与训练复测通过，未改奖励尺度。
- 按用户要求，实际四份动作原样复制到Git管理的assets/motions/a1，附来源commit/许可/manifest/SHA256，默认从项目内读取，reference原状保留。PLAN第7阶段及GOAL明确G1动作同样入本项目Git并默认本地加载。
- 最终CPU39项通过（cpu_bundled.log）；GPU原生reset/翻倒/指令/终止历史/奖励/FK/编译梯度通过（integration_bundled.json），FK max2.29e-6m，返回与actor梯度max5.96e-8。
- 项目内数据32env×12迭代真实四网络/四优化器更新与有限性审计通过；不传task/amp参数CLI自动恢复A1续至16迭代，四网络继续更新且配置/数据/来源一致（training_bundled_audit.json、resume_bundled_audit.json）。均明确从Manager actor/WM跨机器人热启动；不是正式训练来源。
- 短速度12固定+seed42两组零摔倒；7指令短步态model_0/16均零摔倒，独立留出指标生成（velocity_smoke.json、gait_smoke.json）。forward风格距离.73435→.71775，fast1.08452→1.16614，尚未达到独立收敛标准，不夸大短跑结果。
- 全部验证作业已退出；当前版本标识a1-amp-implementation-20261104，A1实现/动作/文档已纳入本阶段提交。完整配置/PID/checkpoint/指标和准确SHA入口见STATUS及logs/amp_a1/implementation_validation.json。日志、模型、录像和未用于正式训练的诊断候选不提交。

## 下一步
- 先核实无运行进程，再测8k/16k/32k吞吐/显存/学习质量，尽量提高GPU利用率；然后启动有独立model_0的正式A1训练，按锁定标准完整评估/录像/审计。通过并提交后进入G1。下一条可执行命令见STATUS。
- 历史：[A1实现排查](docs/history/PROGRESS_2026-11-04_a1_implementation.md)、[Manager过程](docs/history/PROGRESS_2026-11-04_manager.md)、[更早记录](docs/history/PROGRESS_2026-11-03.md)。

- A1 8k吞吐实验已启动PID2508085（基于52b35b6，无源码改动）；100迭代/collect1/buffer128，WM4096×4/window8，imag8192/H32，AMP2048×2；日志logs/amp_a1/perf8k.log，命令perf8k.process.json。正式训练尚未开始；下一命令tail -n 3 logs/amp_a1/perf8k.log并核实PID。

- 8k性能实验2508085已结束，末段34570真实转移/s，峰值15772MiB（监控从中途开始），无物理/CUDA报错；16k同配置100迭代对照启动PID2510222，监控PID2510223，命令/日志logs/amp_a1/perf16k.process.json和perf16k.log。尚无正式训练；下一命令tail -n 2 logs/amp_a1/perf16k.log。

- 16k性能实验2510222结束，末段62514真实转移/s、峰值18888MiB，末段0摔倒且无物理/CUDA错误；32k同配置100迭代对照启动PID2511912，监控PID2511913，命令/日志logs/amp_a1/perf32k.process.json和perf32k.log。正式训练仍未开始；下一命令tail -n 2 logs/amp_a1/perf32k.log。

- A1三检查点/初始风格基线/最终加噪及实际模型审计已补齐，CPU回归PID2513785（cpu_convergence.log）；此改动仅涉及验收工具，不改变运行中的训练算法或数据。

- 32k/8192imag首轮OOM退出，峰值24206MiB；traceback定位critic warmup第一个gae_targets对全部8192×33状态求值时，未执行actor更新的想象仍保留完整反传图。PyTorch分配13.14GiB且仅155MiB缓存空闲，不是碎片主因；优先避免critic warmup无用的actor计算图，再实测32k，暂不缩减并行数/batch/回放。CPU验收工具42项通过（cpu_convergence.log）。

- 已修复critic warmup无actor更新时仍保留想象图：torch.set_grad_enabled(update_actor)，actor正式更新保留完整反传。CPU43项通过（cpu_warmup_memory.log），含预热只更新critic且不建actor图的回归。原32k/buffer128/imag8192/H32完整配置重试PID2516078，监控2516079，日志perf32k_nograd.log，配置未缩减；尚无正式训练。

- 32k no-grad修复复测2516078已结束；原始全部batch/回放未缩减，稳定约11万真实转移/s、峰值20258MiB、GPU峰值97%，四网络/四优化器真实更新和有限性通过，无物理/CUDA错误。性能汇总performance_summary.json：选择32768env/collect1/buffer128/WM4096×4/window8/imag8192/H32作为正式A1配置，actor_lr_scale=.15，预热300+200/ramp500，AMP.5/ramp1000/RSI.5。正式训练将从Manager跨机器人热启动并新建A1 model_0，不复用性能模型；先跑1000再完整评估。

- 训练准备版本a1-amp-training-ready-20261104纳入critic预热关闭无用actor图、完整A1三检查点/初始基线/加噪/实际模型审计。CPU43项通过；32k全部batch/回放不变，真实100次四网络更新/保存/有限性通过，峰值20258MiB；短跑负例被审计明确拒绝。下一步提交后正式训练1000迭代，并独立评估。

- 正式A1首轮启动PID2520598，GPU监控2520599，代码a909cd2bd935a0df9ee45a0bf5d7bbfdb6312351；新运行a1_amp_formal_r1，32768env/collect1/buffer128/WM4096×4/window8/imag8192/H32，warmup300+200/actor_ramp500/actor_scale.15，AMP.5/ramp1000/RSI.5，FP32编译；从Manager actor/WM跨机器人热启动，独立model_0，其余新建，先到1000再完整评估。命令与源SHA logs/amp_a1/formal_r1.process.json，日志formal_r1.log；运行目录待Log directory行生成。无A1最佳模型/收敛结论，G1未启动；下一命令tail -n 3 logs/amp_a1/formal_r1.log并核实PID。

- 已安排正式首轮结束后的串行完整评估，队列PID2522060，脚本logs/amp_a1/eval_formal_r1.py，状态formal_r1.eval_pipeline.json、日志formal_r1.eval_pipeline.log；先等待训练2520598实际退出且model_1000存在，随后model_0完整步态基线→1000完整速度→1000完整步态/留出风格。勿重复启动评估；队列仅评估，不自动续训。

- 正式首轮运行目录已生成logs/supermimic/2026-11-04_02-10-55_869146_a1_amp_formal_r1，已保存独立model_0.pt；当前训练PID2520598及评估队列2522060存活，尚无正式最佳模型。最近100迭代WM loss .24244（仅WM预热），actor/D未开始更新；后续不得把预热统计当作最终质量。

- 正式A1首轮2520598完成1000迭代并退出，model_0/model_500/model_1000位于logs/supermimic/2026-11-04_02-10-55_869146_a1_amp_formal_r1，尚无收敛结论；开始锁定标准的初始基线和1000完整评估。

- 正式A1评估启动formal_r1_baseline_gait，PID2525389，配置/命令logs/amp_a1/formal_r1_baseline_gait.process.json，日志formal_r1_baseline_gait.log；训练2520598已退出，不重复启动。

- 正式首轮到800迭代，已保存model_500，AMP尚在渐进(.8)，真实吞吐约10.3万/s、峰值20262MiB；无物理/OOM错误。先等1000完整评估，不把训练平均指标当收敛。另只读核对G1参考f33a189：29DOF本地USD及Walk_B*数据可用，walk_and_run目录混有run/转换片段，G1阶段必须显式白名单筛选walk并复制入项目Git，不能整目录混用；尚无G1实验。

- 正式A1评估结束formal_r1_baseline_gait，PID2525389，返回码0；原始日志formal_r1_baseline_gait.log。

- 正式A1评估启动formal_r1_velocity1000，PID2525940，配置/命令logs/amp_a1/formal_r1_velocity1000.process.json，日志formal_r1_velocity1000.log；训练2520598已退出，不重复启动。

- 正式A1评估结束formal_r1_velocity1000，PID2525940，返回码0；原始日志formal_r1_velocity1000.log。

- 正式A1评估启动formal_r1_gait1000，PID2527354，配置/命令logs/amp_a1/formal_r1_gait1000.process.json，日志formal_r1_gait1000.log；训练2520598已退出，不重复启动。

- 正式A1评估结束formal_r1_gait1000，PID2527354，返回码0；原始日志formal_r1_gait1000.log。

- 正式A1首轮1000完整评估结束，结论logs/amp_a1/formal_r1_assessment1000.json；没有自动续训。下一条命令cat logs/amp_a1/formal_r1_assessment1000.json，按未达标项定位后推进，三检查点/加噪/录像尚未完成。

- 正式A1 model_1000完整速度/步态/风格全部通过，velocity_failures=[]、gait_failures=[]；1/1.5m/s独立留出风格距离.73862→.52284（改善29.2%）、1.06638→.68874（改善35.4%）。12固定+3随机完整速度及7指令步态全部零摔倒，结论formal_r1_assessment1000.json。仅1/3检查点通过，最终加噪/录像尚未完成。
- 从正式model_1000恢复继续至3000启动PID2528767，监控2528768；全部训练配置保持，保存2000/3000，不使用性能模型。命令formal_r1_to3000.process.json，日志formal_r1_to3000.log，新运行目录待Log directory行；当前最佳已评估为原始目录model_1000，最新随保存更新；下一命令tail -n 2 logs/amp_a1/formal_r1_to3000.log并核实PID。

- 已安排到3000后的完整串行验收队列PID2531693：状态logs/amp_a1/formal_r1_to3000.eval_pipeline.json、日志formal_r1_to3000.eval_pipeline.log。等待训练2528767实际退出且2000/3000存在，再完整速度→步态/风格→3000加噪→三模型实际审计；只有数值审计通过才录制站立/正常/快走及抽帧。最终必须人工看图、归档模型与阶段git提交后才能进入G1，队列不自动启动G1。勿重复启动。

- G1只读数据审计：reference/legged_lab commit f33a18904e5209d9aceb95ef78ed82412c5f2072；Walk_B10样例为252帧、fps29.910979、root_pos[T,3]、root_rot[T,4]、dof_pos[T,29]、key_body_pos[T,6,3]；无直接速度字段，后续需按原fps/四元数约定计算速度并以控制dt重采样。29DOF原始/Isaac Lab顺序见scripts/tools/retarget/config/g1_29dof.yaml，仍需原生GPU核对。参考flat继承rough并关闭terrain_generator/height_scan/curriculum，但motion白名单含run/C4/C5转换，不能直接复用其默认配置；G1仅walk白名单，实际用到的数据必须复制进项目Git。尚未启动G1。

- 正式恢复运行目录logs/supermimic/2026-11-04_02-21-44_764493_a1_amp_formal_r1_to3000，已保存model_2000.pt；当前训练到2100/3000，尚未独立评估2000（完整队列2531693等待训练结束）。正式CLI恢复审计formal_r1_resume2000_audit.json通过，四网络继续更新且优化器{'actor': [500, 1500], 'critic': [8400, 20400], 'world_model': [4000, 8000], 'amp': [1400, 3400]}、来源/数据元信息保留；最新正式checkpoint为此model_2000，最佳已评估仍为初始正式目录model_1000。
