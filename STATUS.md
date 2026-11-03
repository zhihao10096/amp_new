# 当前状态与恢复入口

## 目标、版本和目录
- 开发机权威目录`/pfs/user/learning/amp_new`，SSH `ssh -p 9205 root@118.196.87.69`。恢复先读GOAL/PLAN/STATUS/PROGRESS，再核实HEAD、实际进程和产物，避免重复启动。
- 当前文档版本以`git rev-parse HEAD`核实；本轮复核/诊断源码HEAD `0947e012b36eda2efe3bb1af063600547c888809`，其后仅文档变更。训练实现仍754e1fd，正式R3来源`9bc7115a082eafc403d5f8fb2947d10e3cac38b2`；未跟踪reference/、exploration.py、explore_eval.py、dynamics_eval.py、test_exploration.py及原R3历史文件保留，勿误提交。
- Manager/A1已独立成功 → 当前G1平地walk → 成功提交后X1下半身12DOF AMP；全程WM可微想象、禁PPO。G1动作Git管理；X1动作复制后.gitignore忽略、清单入Git，部署参考reference/AMP、跳过RKNN。

## 当前进程、配置与目录
- 2026-11-04T06:00:58.509893+08:00核实：无实验进程，GPU显存1MiB、利用率0%、无计算进程；本轮所有队列complete/active_pid=null，driver均已退出，无新正式训练，不重复启动。
- 已结束driver：directional_response_r3 PID2665641、response_fit_r3 PID2669348、response_warm_control_r3 PID2672695、policy_value_r3 PID2676135。运行目录均项目根；对应`logs/amp_g1/<name>.pipeline.json`保存命令/日志/源码SHA256及返回码；汇总`logs/amp_g1/response_gradient_summary.json`。
- 响应采集64参考初态×50分支=3200env，共用4步真实PD后做腿部±.2/±.6动作及零对照，16步；仅初态写PhysX。WM消融48初态训练/原ID%4==3的16初态留出、统计冻结、window8/batch256/lr1e-5、最多750更新；普通拟合300步选50、响应约束750选750。专家时间留出未参与。
- 冷启动/匹配预热各三组真实MPC：同16留出初态，H16/每步8次Adam/2秒。诊断模型`logs/amp_g1/response_fit_r3.*.world_model.pt`均为diagnostic_world_model_only，不含新策略；不作为正式恢复来源。
- 策略价值校准：冻结正式R3四网，256env分别普通reset/100%训练参考RSI，固定.6m/s、无噪、128步；真实与想象使用同初态、自身策略与旧critic bootstrap。配置/报告`policy_value_r3.pipeline.json`/`.json`，真实轨迹`.transitions.pt`；不是完整MC价值或收敛证据。

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
- 原接口/真实想象/RSI/终止历史/编译/四网更新恢复/A1回归已通过，CPU50项及GPU计数/兼容证据discriminator_throttle_validation.audit.json；本轮未修改这些生产代码，未重训Manager/A1。
- G1七份Walk_B与manifest在assets/motions/g1，USD在assets/robots/g1；前80%训练/RSI、后20%独立专家时间留出，不跨clip/split差分或插值。新增/替换动作必须复制并Git提交；本次manifest/SHA256/HEAD/追踪与默认路径复核通过，g1_motion_tracking_recheck_current.json。源f33a189的README MIT与LICENCE Apache-2.0冲突原文已保留，动作独立授权未明示。
- RTX4090D24GB；.venv Python3.10/Torch2.5.1+cu124/Lab2.1/Sim4.5。仿真清PYTHONPATH，OMNI_KIT_ACCEPT_EULA=YES、OMNI_KIT_ALLOW_ROOT=1、TORCHINDUCTOR_COMPILE_THREADS=4；Kit后中文文件显式UTF-8。无rg/系统python，用.venv/bin/python。

## 下一条命令
`sed -n '350,415p' go2_supermimic/supermimic/train.py`：核对当前critic仅想象TD(λ)的路径，结合`policy_value_r3.transitions.pt`先检查动态状态价值梯度和真实TD残差，再设计真实价值锚定的小型受控消融。若增加真实目标，必须使用终止前状态、区分摔倒/超时、处理命令切换与gait上下文；actor继续WM可微想象，旧A1默认行为保留。先验证闭环收益与四网/恢复，不能直接新开3000轮。恢复仍核实ps/GPU，所有本轮队列已结束，勿重启。

本轮证据：[动作响应/控制/价值校准报告](docs/experiments/G1_DYNAMICS_RESPONSE_2026-11-04.md)。历史R1/R2/R3见G1_CONVERGENCE.md及docs/history。X1只读预查logs/amp_x1/reference_prereview.json（6189ae4），尚未实施，待G1独立成功提交。
