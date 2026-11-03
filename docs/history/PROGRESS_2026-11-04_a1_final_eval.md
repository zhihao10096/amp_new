# 进度与恢复入口

恢复先读STATUS.md，核实HEAD/进程/队列/产物；目标与预算见GOAL.md，阶段见PLAN.md。全程禁PPO。

## 已完成的阶段与实现
- Go2 Manager随机来源7000/8000/9000完整速度/步态、最终加噪/录像/实际模型审计通过，已提交b1f59eb；模型checkpoints/go2_manager_converged.pt，证据MANAGER_CONVERGENCE.md。无需重训。
- A1替代Go2 AMP，原生Manager/运动库/RSI/相邻帧LSGAN/可微想象奖励/四网络更新/保存恢复/独立评估已接入；四份实际动作及来源/许可/SHA256已纳入assets/motions/a1，提交52b35b6。G1所用动作也必须复制进本项目Git，已写GOAL/PLAN。
- 原生A1接触正则和USD/URDF几何差异均定位修复；专家/策略共用拟合原生FK。零权重日志缺失改为转移快照采集，真实/想象只乘一次dt；编译夹具随机指令问题固定窗口后原阈值通过。证据logs/amp_a1/integration_bundled.json，CPU最终43项通过。
- 8k/16k/32k性能实测后选择32k；原32k critic预热保留无用actor图导致OOM，改为无actor更新时关闭梯度，不缩减batch/回放，稳定约11万真实转移/s、峰值约20GB。完整A1三模型/初始基线/加噪与实际checkpoint审计已补齐，短跑负例被拒绝；提交a909cd2。

## 当前A1正式训练
- 从Manager actor/WM明确跨机器人热启动，独立A1 model_0，其余网络/四优化器新建；首轮0→1000已完成并独立通过完整速度/步态/留出风格。12固定+3随机30秒速度和7指令20秒步态全部零摔倒；随机RMSE约.075/.030/.067；风格forward/fast分别改善29.2%/35.4%，并非使用训练判别器分数作风格结论。
- 1000的1/1.5m/s步频2.445/2.870Hz，腾空.1611/.1461s，离地.01979/.02239m，足滑.06961/.13077m/s，均通过原阈值。formal_r1_assessment1000.json记录两类failures=[]，但仅1/3候选，尚未宣称A1阶段收敛。
- 从正式model_1000恢复到3000正在进行，训练2528767/监控2528768；已保存2000，四网络/四优化器继续更新及来源/数据继承审计通过（formal_r1_resume2000_audit.json）。最新/最佳路径、配置、指标见STATUS。
- 验收队列2531693等待训练实际退出，随后2000/3000完整速度→步态/留出风格→最终3000加噪→三模型实际审计；数值通过才录制站立/正常/快走与抽帧，最终需要人工看图、归档及阶段git提交。进程/命令/报告均在logs/amp_a1，队列状态formal_r1_to3000.eval_pipeline.json；勿重复启动。
- G1只读预查发现默认flat的motion白名单混run/转换；后续仅walk白名单，29DOF和四元数/速度插值须原生GPU核对，实际动作必须复制入项目Git。尚无G1实验，等A1验收/提交后进入。

## 下一步
- 持续核实当前训练/队列并维护事件记录，完整评估若失败按实际报告排查，不降低标准。数值/视觉全部通过后归档A1模型和证据、git提交，再实施G1平地walk。
- 原始过程与恢复命令见STATUS及docs/history/PROGRESS_2026-11-04_a1_training_before_eval.md；日志只记录路径和结论，不复制原始日志。

- A1恢复训练2528767到3000完成并退出；2000/3000位于logs/supermimic/2026-11-04_02-21-44_764493_a1_amp_formal_r1_to3000。开始两模型完整速度、步态、最终加噪和三模型实际来源/更新审计，尚无阶段收敛结论。

- A1任务启动formal_r1_velocity2000_3000，PID2538622，命令logs/amp_a1/formal_r1_velocity2000_3000.process.json，日志formal_r1_velocity2000_3000.log；不重复启动。

- 正式恢复训练到3000完成，训练2528767退出，2000/3000保留；末段约10.65万真实转移/s。串行验收队列2531693已进入2000/3000完整速度，当前子进程2538622；等待实际完整速度/步态/风格/最终加噪及模型审计，再录制/看图，不能提前判定阶段完成。

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
