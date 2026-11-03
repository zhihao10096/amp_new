# 进度与恢复入口

- 2026-11-04 A1/Go2/G1综合诊断完成：[报告](docs/experiments/A1_GO2_G1_CONVERGENCE_GAP_2026-11-04.md)。Go2从零但使用弱初期平方正则及3000–5000步态课程，A1继承其完整actor/WM，G1从零无对应启动课程。CPU确认G1风格运动区分不足、静止脚离地项满分/高度梯度0，并记录参考覆盖和RSI指令独立采样差异；均不冒充闭环因果结论。脚本/报告/日志`logs/amp_g1/a1_g1_gap_audit.*`，不改生产或原0/.5对照，Manager/A1不重训。control3500仍无迈步，anchor已进入完整评估，以pipeline为准。

- 2026-11-04 A1/G1原因追查：初始评估确认A1 model_0继承Manager actor/WM，七组全部零摔倒，1/1.5m/s实际速度.941/1.434、每足步频3.418/3.489Hz；G1随机model_0七组806次摔倒且步频0。A1快速AMP达标包含既有行走能力，必须先纠正起点不一致，再分析G1站立局部解。原真实TD对照driver2689332继续，未重启实验或修改配置；详见STATUS及后续诊断报告。

恢复先读GOAL/PLAN/STATUS，再核实HEAD、ps/GPU和pipeline；勿重复启动。

- 总目标：Manager/A1已独立成功 → G1仅平地walk → 成功提交后X1下半身12DOF AMP；禁PPO、WM可微想象，各阶段独立验收提交。G1/X1未成功前总目标未完成。
- 当前版本用git rev-parse HEAD核实；本次实现可选critic_real_fraction（默认0），固定critic样本预算混合真实一步TD/想象TD(λ)，actor仍WM更新。使用终止前状态/gait，摔倒不bootstrap、超时bootstrap，跳过非终止命令切换，独立真实采样RNG保存恢复。
- CPU55、G1原生13摔/52超时/356命令切换及真实TD误差1.19e-7、编译梯度/真实四网20→25/CLI继承.5/旧模型默认0/A1回归全部通过。CUDA RNG精确恢复、默认0单次更新与1be9b27逐位一致；real_value_validation.audit.json。短跑步态仍失败，不算成功；验证driver2683870已退出，当前无正式训练。
- 诊断依据：普通/参考真实TD RMSE .03271/.09694，policy_value_r3_td_residual.json；32步参考真实/想象bootstrap 1.123/.866。此前动态拟合/响应约束降低预测/响应误差，但冷启动和统一预热MPC均无稳定性收益；不接入当前MPC，详见docs/experiments/G1_DYNAMICS_RESPONSE_2026-11-04.md。
- 进行0/.5短程消融：同R3 model_3000四网/四优化器初值，18432env、原R3全部批次/任务相同、固定critic样本总量，各续500步到3500，保存3000/3250/3500并完整速度/步态/风格评估。仅诊断续训，无收益停止；状态logs/amp_g1/real_value_ablation.pipeline.json，当前driver PID2689332已启动，代码fa93cab；按pipeline跟进，勿重启。
- 最新正式仍R3 model_3000，完整路径/配置/R1–R3失败指标及Manager/A1完成归档见STATUS；无通过验收的G1最佳模型。Manager/A1勿重训，原未跟踪reference及诊断文件保留。
- G1全部实际动作（含新增/替换）复制assets/motions/g1，文件及清单Git管理，训练前/提交前核验来源/许可/SHA256/split/默认路径。X1动作复制后.gitignore忽略、清单入Git，部署参考reference/AMP，跳过RKNN，待G1独立成功后实施。

下一条命令：cat logs/amp_g1/real_value_ablation.pipeline.json，再核对active_pid实际进程并跟进训练/完整评估，勿重复启动。接口通过不证明迈步收益，G1三点/加噪/录像/审计标准不变。

- 真实TD短程对照启动real_value_ablation_train_control，driver PID2689332、child PID2689497；配置/命令/峰值/log见logs/amp_g1/real_value_ablation.pipeline.json，勿重复启动。

- 真实TD短程对照control初始审计通过：四网/四优化器逐项匹配同一R3模型；任务/数据split不变，仅实验开关不同，属诊断续训，不是正式G1成功来源。

- G1动作归档要求已再次明确写入PLAN第7阶段，训练前及新增/替换后核验；本轮复核七份动作、manifest和来源许可文件均受Git管理、SHA256吻合且默认路径位于项目内，证据logs/amp_g1/g1_motion_plan_recheck_2026-11-04.json。
- 用户关注A1能迈步而人形G1失败：解释须区分已证实的站立局部解与待验证根因，不能只以人形更难作结论；既有诊断排除/负结果见G1_CONVERGENCE和动作响应报告。当前同源真实TD对照继续，不重复启动训练。

- 真实TD短程对照结束real_value_ablation_train_control，返回码0，日志logs/amp_g1/real_value_ablation_train_control.log。

- 真实TD短程对照启动real_value_ablation_velocity_control，driver PID2689332、child PID2692200；配置/命令/峰值/log见logs/amp_g1/real_value_ablation.pipeline.json，勿重复启动。

- A1/G1具体实现差异已核对：A1的43维AMP特征含机身线速度、足端位置和高度，G1的61维仅角速度/关节角/关节速度；G1参考配置四帧而当前两帧。结合静态参考姿态高D分数，列为风格信号偏姿态的待验假设，不能据此宣称根因或修复成功；原0/.5价值对照保持不变。

- 真实TD短程对照结束real_value_ablation_velocity_control，返回码0，日志logs/amp_g1/real_value_ablation_velocity_control.log。

- 真实TD短程对照启动real_value_ablation_gait_control，driver PID2689332、child PID2694072；配置/命令/峰值/log见logs/amp_g1/real_value_ablation.pipeline.json，勿重复启动。

- A1/G1来源差异核实：logs/amp_a1/convergence_report.json的training_origin.kind=warm_start，actor/WM来源checkpoints/go2_manager_converged.pt（SHA256 07fc3f6e0e6801a3e60ab591be25dbeb3071c930809f847dd14284477dbfa9dd）；G1 R1–R3是随机初始化。A1成功不能单独证明当前G1冷启动能形成步态。待当前0/.5对照结束，若无真实迈步收益，优先诊断从零步态启动/动态数据覆盖，再决定分阶段基础行走预训练；维持WM/AMP、禁PPO、正式随机来源及原验收。

- 真实TD短程对照结束real_value_ablation_gait_control，返回码0，日志logs/amp_g1/real_value_ablation_gait_control.log。

- 真实TD短程对照control完整速度/步态评估结束，速度失败19项、步态失败14项；只证明本次诊断结果，不是正式三点验收。

- 真实TD短程对照启动real_value_ablation_train_anchor，driver PID2689332、child PID2694577；配置/命令/峰值/log见logs/amp_g1/real_value_ablation.pipeline.json，勿重复启动。

- 真实TD短程对照anchor初始审计通过：四网/四优化器逐项匹配同一R3模型；任务/数据split不变，仅实验开关不同，属诊断续训，不是正式G1成功来源。

- 进一步核实A1初始model_0已具备迈步：formal_r1_baseline_gait.json在1/1.5m/s指令下实际vx=.94146/1.43389、步频3.4181/3.4889Hz、零摔倒；G1随机model_0约115–116摔且步频0。来源差异比单凭机器人类别更直接。
- 修正旧诊断表述：reference_behavior_diagnostic_r2的hold是固定参考关节目标，不是完全静止状态；其平均vx=.501、2秒128/128摔倒而style=.99978。它证明高风格分数不保证稳定步行，不能单独证明D只看静态姿态。

- 真实TD短程对照结束real_value_ablation_train_anchor，返回码0，日志logs/amp_g1/real_value_ablation_train_anchor.log。

- 真实TD短程对照启动real_value_ablation_velocity_anchor，driver PID2689332、child PID2698057；配置/命令/峰值/log见logs/amp_g1/real_value_ablation.pipeline.json，勿重复启动。

- 真实TD短程对照结束real_value_ablation_velocity_anchor，返回码0，日志logs/amp_g1/real_value_ablation_velocity_anchor.log。

- 真实TD短程对照启动real_value_ablation_gait_anchor，driver PID2689332、child PID2700038；配置/命令/峰值/log见logs/amp_g1/real_value_ablation.pipeline.json，勿重复启动。

- 真实TD短程对照结束real_value_ablation_gait_anchor，返回码0，日志logs/amp_g1/real_value_ablation_gait_anchor.log。

- 真实TD短程对照anchor完整速度/步态评估结束，速度失败20项、步态失败15项；只证明本次诊断结果，不是正式三点验收。

- 真实TD短程0/.5对照全部结束；按real_value_ablation.pipeline.json及velocity/gait报告判断是否有实际迈步收益，无收益则停止此轮，不盲目续训；G1未独立成功前不进入X1。

- 关键决定（2026-11-04）：用户指出Go2可从零收敛，G1应复用其训练过程。已新增`G1-Velocity-Flat`同机器人平地冷启动任务（共享G1奖励/动力学，关闭AMP），计划先从随机初始化验证基础行走，再用同机器人actor/世界模型warm-start G1 AMP；critic/判别器/优化器重新创建。当前真实TD对照仍按pipeline跟进，完成前不重启或叠加正式训练。

- 真实TD=0/.5短程对照已完整结束：同一R3 model_3000续训500步到3500，control固定整体RMSE(.6422,.2238,.3938)、53摔，anchor(.6335,.2406,.3831)、58摔；两臂七指令步态步频均0，style forward/fast分别control 1.2943/1.3792、anchor 1.2683/1.4213。anchor没有真实迈步收益，停止把真实TD锚定作为当前修复方向；证据logs/amp_g1/real_value_ablation.pipeline.json及对应velocity/gait JSON，均为诊断续训，不是G1成功。
- 已按Go2从零收敛流程新增G1冷启动基础任务：`G1-Velocity-Flat`共享G1平地资产、PD、奖励和SuperMimic接口但关闭AMP；修复G1 reward对`joint_deviation_gait_fraction`的忽略，使初期可使用平方关节惩罚并在最终阶段回到现有L1 walk惩罚。新增CPU测试`tests/test_g1_reward.py`与既有课程测试共5项通过，三处源码py_compile及git diff --check通过。
- 下一步：提交冷启动任务与记录后，先运行G1-Velocity-Flat 32env短跑/保存恢复，确认无接口错误；再按Go2课程从G1随机初始化训练基础行走，独立评估有真实步态后warm-start G1 AMP。
