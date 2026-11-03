# 当前状态与恢复入口

## 目标、版本和目录
- 开发机权威目录`/pfs/user/learning/amp_new`，SSH `ssh -p 9205 root@118.196.87.69`。恢复先读GOAL/PLAN/STATUS/PROGRESS，再核实HEAD、实际进程和产物，避免重复启动。
- 当前实现/文档版本以`git rev-parse HEAD`核实；本次实现提交前HEAD1be9b27。新增可选真实TD critic目标，源码SHA256及全部验证见real_value_validation.audit.json；正式R3来源仍`9bc7115a082eafc403d5f8fb2947d10e3cac38b2`。原未跟踪reference/、exploration.py、explore_eval.py、dynamics_eval.py、test_exploration.py及R3历史文件保留，勿误提交。
- Manager/A1已独立成功 → 当前G1平地walk → 成功提交后X1下半身12DOF AMP；全程WM可微想象、禁PPO。G1动作Git管理；X1动作复制后.gitignore忽略、清单入Git，部署参考reference/AMP、跳过RKNN。

## 当前进程、配置与目录
- GPU验证driver2683870及所有子进程已结束，pipeline为complete/active_pid=null；当前无正式训练。验证根目录项目根，完整命令/配置/log/源码SHA256见logs/amp_g1/real_value_validation.pipeline.json，审计real_value_validation.audit.json。
- 可选critic_real_fraction默认0；.5按固定critic样本预算混合真实一步TD与想象TD(λ)，actor仍WM可微更新。真实目标使用终止前状态/预重置gait，重算当前奖励+AMP；摔倒不bootstrap、超时bootstrap，跳过非终止命令切换，从非OU环境采样并保存/恢复独立RNG。
- CPU55项通过；首次未限定目录误收集reference/logs旧测试，保留cpu_real_value_initial_collection.log，正确命令`.venv/bin/python -m pytest -q tests`及成功日志cpu_real_value.log。G1真实TD/编译/四网20→25恢复、默认旧模型、A1回归及短跑评估均执行；默认0更新与旧版逐位一致，CUDA RNG恢复已逐项核对。短跑仍不满足步态，非收敛模型。
- 准备短程0/.5对照：同R3 model_3000分别继续500迭代到3500，18432env/collect1/buffer128/原R3全部批次与任务不变，保存初始3000和3250/3500、审计四网四优化器初值，随后两臂完整速度/七指令步态/风格。仅诊断续训，无收益停止，不自动新正式轮次；尚未启动，启动后看real_value_ablation.pipeline.json的active_pid。

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
提交已验证的真实TD实现后，启动`logs/amp_g1/real_value_ablation.pipeline.py`，先核对无同名存活driver/子进程；状态`logs/amp_g1/real_value_ablation.pipeline.json`保存配置、PID、目录、最新模型和日志。0/.5两臂同R3随机来源模型，仅诊断续训500步并各做完整评估。G1三点/加噪/录像/审计标准不变；本轮未证明真实价值锚定能促进迈步，勿把接口通过当成功。

本轮证据：[动作响应/控制/价值校准报告](docs/experiments/G1_DYNAMICS_RESPONSE_2026-11-04.md)。历史R1/R2/R3见G1_CONVERGENCE.md及docs/history。X1只读预查logs/amp_x1/reference_prereview.json（6189ae4），尚未实施，待G1独立成功提交。

- 决定验证可选真实TD锚定：policy_value_r3_td_residual.json中普通/参考自身策略TD RMSE .03271/.09694。新增critic_real_fraction默认0，试验.5；按相同critic样本预算混合真实一步TD和想象TD(λ)，actor始终只通过WM可微想象更新。真实目标重算当前任务+AMP奖励，使用终止前next_state/gait；摔倒不bootstrap、超时保留bootstrap；跳过命令恰好重采样的非终止转移。只从非OU环境采样（全OU时回退全部），独立采样RNG；先CPU/真实GPU更新恢复/A1兼容，再从同一R3模型做短程0/.5对照，不直接启动新正式3000轮。此为待检验假设，未证明能改善步行。GitHub SVG真实转移critic仅作为路线核对，其Q/SAC与本V/PhysX不同，不移植代码。

- 真实TD GPU验证启动real_value_integration，driver PID2683870、child PID2684018；配置/命令/log见logs/amp_g1/real_value_validation.pipeline.json，勿重复启动。

- 真实TD GPU验证结束real_value_integration，返回码0，日志logs/amp_g1/real_value_integration.log。

- 真实TD GPU验证启动real_value_smoke_initial，driver PID2683870、child PID2684334；配置/命令/log见logs/amp_g1/real_value_validation.pipeline.json，勿重复启动。

- 真实TD GPU验证结束real_value_smoke_initial，返回码0，日志logs/amp_g1/real_value_smoke_initial.log。

- 真实TD GPU验证启动real_value_smoke_resume，driver PID2683870、child PID2684665；配置/命令/log见logs/amp_g1/real_value_validation.pipeline.json，勿重复启动。

- 真实TD GPU验证结束real_value_smoke_resume，返回码0，日志logs/amp_g1/real_value_smoke_resume.log。

- 真实TD GPU验证启动real_value_default_resume，driver PID2683870、child PID2684968；配置/命令/log见logs/amp_g1/real_value_validation.pipeline.json，勿重复启动。

- 真实TD GPU验证结束real_value_default_resume，返回码0，日志logs/amp_g1/real_value_default_resume.log。

- 真实TD GPU验证启动real_value_a1_regression，driver PID2683870、child PID2685258；配置/命令/log见logs/amp_g1/real_value_validation.pipeline.json，勿重复启动。

- 真实TD GPU验证结束real_value_a1_regression，返回码0，日志logs/amp_g1/real_value_a1_regression.log。

- 真实TD GPU验证启动real_value_smoke_gait，driver PID2683870、child PID2685569；配置/命令/log见logs/amp_g1/real_value_validation.pipeline.json，勿重复启动。

- 真实TD GPU验证结束real_value_smoke_gait，返回码0，日志logs/amp_g1/real_value_smoke_gait.log。

- 真实TD GPU更新/CLI恢复/默认旧模型/A1/原生终止超时命令及短跑评估验证全部结束；证据logs/amp_g1/real_value_validation.audit.json。仅接口验证，不是G1收敛。
