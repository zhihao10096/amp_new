# 当前状态与恢复入口

## 目标、版本和目录
- 开发机权威目录`/pfs/user/learning/amp_new`，SSH `ssh -p 9205 root@118.196.87.69`。恢复先读GOAL/PLAN/STATUS/PROGRESS，再核实HEAD、实际进程和产物，避免重复启动。
- 当前实现/文档版本以`git rev-parse HEAD`核实；当前实验实现commit`fa93cabff98ec9870c971cf155009a29506c022e`；后续仅文档提交以HEAD为准。新增可选真实TD critic目标，源码SHA256及全部验证见real_value_validation.audit.json；正式R3来源仍`9bc7115a082eafc403d5f8fb2947d10e3cac38b2`。原未跟踪reference/、exploration.py、explore_eval.py、dynamics_eval.py、test_exploration.py及R3历史文件保留，勿误提交。
- Manager/A1已独立成功 → 当前G1平地walk → 成功提交后X1下半身12DOF AMP；全程WM可微想象、禁PPO。G1动作Git管理；X1动作复制后.gitignore忽略、清单入Git，部署参考reference/AMP、跳过RKNN。

## 当前进程、配置与目录
- 当前真实TD短程消融driver PID2689332；active_pid/阶段以`logs/amp_g1/real_value_ablation.pipeline.json`及实际ps为准，勿重复启动。运行目录项目根，代码commit`fa93cabff98ec9870c971cf155009a29506c022e`；无新正式训练。
- 两臂control=0/anchor=.5，同源正式R3 model_3000，分别继续500迭代到3500；18432env/collect1/buffer128，WM4096×4/window8、imag8192/H32、critic3×4、D2048×2/interval5/lr1e-5/GP40及其余任务/批次完全相同。仅critic_real_fraction/run_name/stop_file变化，critic总样本预算固定；保存初始3000及3250/3500，初始四网四优化器精确审计。
- 初始源`logs/supermimic/2026-11-04_04-51-38_136861_g1_amp_formal_r3_exploration/model_3000.pt`，新运行目录/最新模型/来源SHA256/实际命令/日志/GPU峰值都写pipeline。两臂各做完整速度和七指令步态/独立风格，报告real_value_ablation_velocity_*.json/gait_*.json。此为诊断续训，不作为正式成功声明；无收益则停止，不自动无限续训。
- 实现验证已全过：CPU55、G1终止/超时/命令与真实TD、编译/四网20→25/CLI继承.5/旧默认/A1、CUDA RNG精确恢复、默认0更新与1be9b27逐位一致；real_value_validation.audit.json。验证driver2683870已退出，短跑步态失败不算收敛。

## 最新/最佳检查点与最近指标
- G1最新正式`logs/supermimic/2026-11-04_04-51-38_136861_g1_amp_formal_r3_exploration/model_3000.pt`；无通过验收的最佳/已收敛G1模型。R3配置18432env、collect1/buffer128、WM4096×4/window8/hidden512×3、imag8192/H32、critic3×4、actor/critic512,256,128、actor_lr_scale.15、WM预热300+critic200/actor_ramp500、FP32 highest/compile；D2048×2/interval5/lr1e-5/GP40/weight.5/ramp1000/RSI.5，25%OU .6/其余Gaussian .1。训练GPU峰值23124MiB、利用率约86%、约5.75万真实转移/s。
- R3完整1000/2000/3000固定RMSE(.963,.299,.410)/(.649,.192,.438)/(.630,.240,.390)，摔倒1460/2/63；0.6m/s每足步频全部0，3000留出风格改善59.2%/59.0%仍原地站立。四网络/四优化器/随机来源审计通过，汇总logs/amp_g1/formal_r3_summary.json及对应assessment/audit；不能把风格改善当行走成功。
- R2同样三点失败，3000固定RMSE(.637,.226,.410)、52摔、步频0，style改善41.8%/46.5%；R1三点也失败。两轮目录/详细失败见历史，均勿作成功或热启动来源。
- A1完成归档checkpoints/a1_amp_converged.pt（3000，SHA256 09a16f5f8bc4bcbf64a1c2dfd80010d3756b5c09224cc706d9a717b155a533ed），三点/加噪/录像/审计通过，固定RMSE .0498/.0524/.0385，风格改善36.3%/40.7%；AMP_CONVERGENCE.md及logs/amp_a1/convergence_report.json。Manager完成checkpoints/go2_manager_converged.pt，证据MANAGER_CONVERGENCE.md。两者勿重训。

## 关键结论、排除方案与未解决问题
- 首要未解决：真实闭环仍不能walk。动态补数据让8步预测误差改善51.76%，成对响应约束另让独立响应分数.35463→.23847、8步速度RMSE .0767→.0317；仍未转化控制收益。冷启动原/普通拟合/响应约束存活1.3288/1.2813/1.1663s、均15/16摔；统一预热后.9550/.9725/.9013s、均16/16摔。不接入MPC或诊断WM，不盲目继续此方向。
- 正式策略32步校准：普通reset初始V3.399、真实/想象bootstrap 3.038/3.089；参考RSI V1.001、真实/想象1.123/.866。128步RSI真实/想象生存.2969/.1210，未支持整体收益过度乐观；动态状态价值尾项偏保守仅为下一假设，未证明真实价值锚定能改善控制。细节/限制见docs/experiments/G1_DYNAMICS_RESPONSE_2026-11-04.md。
- 骨架/映射已核对：原型与PhysX足端位置max6.03e-6m、link速度max2.71e-5m/s；WM32步足端/关节几何差3.74mm，直接FK收益小，暂不投影。原型link与runtime COM速度语义已区分；kinematics_r3.json。站立复制状态的有限差分受接触噪声干扰；本轮预热后零对照明显小于动作信号。
- 已排除：R1/R2/R3同配置盲续训、继续仅加OU、严重RSI穿透/直接加.1m高度、普通站立WM整体爆炸、原样参考PD/前馈或当前MPC作为可靠采样行为。D姿态捷径和风格改善不能代替真实步行；响应/预测分数下降也不能替代闭环稳定性。
- 真实TD可选实现验证完成：CPU55；原生13摔倒/52超时/356命令切换，TD目标与实际奖励最大误差1.19e-7；编译返回/actor梯度一致。四网20→25继续更新，CLI继承.5、独立CUDA RNG精确恢复/后续随机数一致；旧模型缺字段默认0恢复及A1 GPU回归通过。默认0的一次actor/critic/优化器更新与1be9b27逐位一致。短跑步态未通过，不能称G1成功；审计logs/amp_g1/real_value_validation.audit.json。
- G1七份Walk_B与manifest在assets/motions/g1，USD在assets/robots/g1；前80%训练/RSI、后20%独立专家时间留出，不跨clip/split差分或插值。新增/替换动作必须复制并Git提交；本次manifest/SHA256/HEAD/追踪与默认路径复核通过，g1_motion_tracking_recheck_current.json。源f33a189的README MIT与LICENCE Apache-2.0冲突原文已保留，动作独立授权未明示。
- RTX4090D24GB；.venv Python3.10/Torch2.5.1+cu124/Lab2.1/Sim4.5。仿真清PYTHONPATH，OMNI_KIT_ACCEPT_EULA=YES、OMNI_KIT_ALLOW_ROOT=1、TORCHINDUCTOR_COMPILE_THREADS=4；Kit后中文文件显式UTF-8。无rg/系统python，用.venv/bin/python。

## 下一条命令
`cat logs/amp_g1/real_value_ablation.pipeline.json`，然后用active_pid核对ps及对应job.log；跟进同一driver训练/评估，勿重启。当前0/.5同源短程消融尚未得到闭环结论，不把接口通过当行走成功。G1三点/加噪/录像/审计全部通过前不进入X1。

本轮证据：[动作响应/控制/价值校准报告](docs/experiments/G1_DYNAMICS_RESPONSE_2026-11-04.md)。历史R1/R2/R3见G1_CONVERGENCE.md及docs/history。X1只读预查logs/amp_x1/reference_prereview.json（6189ae4），尚未实施，待G1独立成功提交。

- 用户再次明确G1实际参考动作须复制至项目Git管理目录，已在PLAN第7阶段列为训练前必要任务。七份动作、manifest及来源许可文件均已提交且SHA256吻合，默认路径为assets/motions/g1；本轮复核证据logs/amp_g1/g1_motion_plan_recheck_2026-11-04.json。
- A1能迈步而G1失败的差异仍待因果定位：G1当前是站立局部解，独立风格改善不等于动态步态；骨架映射/严重RSI穿透等假设未获支持。当前真实TD对照仅检验动态价值保守这一假设，未证明修复成功，继续跟进原driver。

- 真实TD短程对照结束real_value_ablation_train_control，返回码0，日志logs/amp_g1/real_value_ablation_train_control.log。

- 真实TD短程对照启动real_value_ablation_velocity_control，driver PID2689332、child PID2692200；配置/命令/峰值/log见logs/amp_g1/real_value_ablation.pipeline.json，勿重复启动。

- A1/G1具体实现差异已核对：A1的43维AMP特征含机身线速度、足端位置和高度，G1的61维仅角速度/关节角/关节速度；G1参考配置四帧而当前两帧。结合静态参考姿态高D分数，列为风格信号偏姿态的待验假设，不能据此宣称根因或修复成功；原0/.5价值对照保持不变。
- 本轮恢复核实：driver PID2689332，阶段`real_value_ablation_velocity_control`，child PID2692200；当前诊断运行目录`logs/supermimic/2026-11-04_06-23-45_439174_g1_real_value_ablation_control`，最新诊断checkpoint`logs/supermimic/2026-11-04_06-23-45_439174_g1_real_value_ablation_control/model_3500.pt`。正式来源与最佳模型结论不变；动态更新以pipeline及实际ps为准。
