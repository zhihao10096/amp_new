# 进度与恢复入口

恢复先读STATUS/GOAL/PLAN并核实HEAD、进程、GPU与产物；全程禁PPO。

- Manager随机来源7000/8000/9000完整速度/步态及最终加噪/录像/实际模型审计通过，完成提交b1f59eb；模型checkpoints/go2_manager_converged.pt，无需重训。
- A1原生Manager/运动库/参考重置/相邻帧LSGAN/可微想象奖励/四网络优化器更新及保存恢复完成；四份动作与来源/许可/SHA256已纳入assets/motions/a1，提交52b35b6。CPU43项和真实GPU/编译梯度一致通过。
- A1接触正则、USD/URDF几何差异、零权重日志、编译夹具重采样均已修复。32k critic预热OOM根因是无actor更新仍保留完整想象图；关闭对应梯度后不减batch，约11万真实转移/s、峰值20GB，训练就绪提交a909cd2。
- 正式A1由已验收Manager actor/WM明确跨机器人热启动，critic/D/四优化器新建并保存model_0。1000/2000/3000三个检查点全部通过锁定的完整速度/步态/独立留出风格，最终3000加噪及实际来源/四网络四优化器更新审计通过，全部零摔倒。证据logs/amp_a1/convergence_report.json。
- 3000固定总体RMSE=.04982/.05242/.03852，随机约.045/.035/.026，加噪=.05178/.05494/.05499。1/1.5m/s风格距=.47081/.63290，相对初始改善36.3%/40.7%。各步态指标见AMP_CONVERGENCE.md。
- 三段站立/正常走/快走10秒录像生成并人工查看2秒连续步态及6–9秒后段，未见明显异常。证据logs/amp_a1/visual_review.json；模型已归档checkpoints/a1_amp_converged.pt并核对SHA256，已单独提交37b6b58。A1训练/验收/录像进程已全部退出，GPU空闲，禁止重复启动。
- G1所用参考动作同样必须复制进项目Git管理的assets/motions/g1等目录，随代码提交来源commit/许可/SHA256/划分，默认读取项目内副本，GOAL/PLAN已明确。G1预查默认flat包含run/转换，后续显式walk白名单/plane；29DOF、四元数及速度待原生GPU验证，尚无G1实验。

下一步：实现G1平地walk；先数据/资产与许可证核对、原生状态和AMP接口设计，正式训练前锁定独立验收标准。详细配置、进程、产物和下一条命令见STATUS。历史过程见docs/history/；仅保留日志路径与结论。

- 阶段切换交接：A1结果提交37b6b58；G1只读核对确认pkl可pickle读取、四元数WXYZ、29维关节为Lab顺序，参考实现面向Lab v3而本机为2.1，后续须原生验证。未启动新实验；当前任务的数据入库要求已在PLAN第7阶段和GOAL同步明确。恢复commit使用标签a1-amp-handoff-20261104核实。

- G1关键决定及数据入库：固定GitHub源f33a189与本地一致，明确仅七份Walk_B文件（无run/转换），已原样复制assets/motions/g1并生成来源/许可实际状态/SHA256/split及顺序manifest；本地29DOF USD一并复制assets/robots/g1。参考判别器实际为角速度+29关节位置/速度61维。计划沿用相邻帧AMP，适配Lab2.1并参数化共用WM/回放维度；尚无G1实验。审计logs/amp_g1/reference_audit.json。

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
