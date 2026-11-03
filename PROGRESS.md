# 进度与恢复入口

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
