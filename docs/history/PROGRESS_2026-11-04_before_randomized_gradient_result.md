# 进度与恢复入口

最后核实：2026-11-04T13:36:55+08:00。权威目录 `/pfs/user/learning/amp_new`，HEAD `8e1a29e70dd91bb54e6ae64ac6a4ae48a8130834`；完整配置、checkpoint、进程及下一条命令见 [STATUS.md](STATUS.md)。恢复必须先核实进程，避免重复启动。

- Manager / A1 已完成，G1 仍未通过；X1 未开始。仅平地walk、SuperMimic世界模型 / 可微想象、禁PPO。参考动作与控制要求见 GOAL。
- 已恢复上游隐式PD及固定限矩，无DC转速降额；用户允许IdealPD候选，未实施该对照，也无隐式PD故障证据。切换须独立控制类型 / 新WM谱系。
- 奖励16项与混合、state84原生终止、RSI同帧命令、严格评估及四帧metadata已修复。CPU92、真实GPU / 编译梯度 / 四网恢复 / A1回归通过；训练内核仍20ad0d3。
- 18432完整更新 profiling 比16384吞吐高9.7%，正式新随机AMP1000后四网完整恢复到3000；训练无OOM/PhysX错误，峰值24134MiB，actor实际更新由500增到2500。
- 2000 / 3000四网及配置审计passed；旧list/tuple误报只恢复审计和评估，未重训。完整速度失败30/19、七指令步态失败22/15。3000前进vx约.004m/s，步频 / 腾空 / 净空为0；六组零严格fall、转弯16，仍未迈步。不能用风格距改善代替行走。
- 3000冻结模型普通 / 参考H32 bootstrap真实-想象差异扩大；配对首动作方向模型高估普通起点收益，参考样本间一致性弱。但正方向相对零对照收益很小，物理配对有噪声，缺成对置信区间，且bootstrap共用critic，尚无根因证明。
- 2026-11-04T13:36:55+08:00 已核实续训 / 完整评估 / 冻结模型 / 方向审计全部complete，旧PID退出，GPU0%/1MiB。本次CPU92passed，证据 logs/amp_g1/aligned_extension_cpu.log；未新增训练或IdealPD实验。
- 下一项先改进配对审计方法并验证；不盲续、不改奖励网格、不切PD。报告 [doc/G1_ALIGNED_3000_AND_PD_DECISION_2026-11-04.md](doc/G1_ALIGNED_3000_AND_PD_DECISION_2026-11-04.md) 保存结果、证据和方法局限；历史在 [PROGRESS归档](docs/history/PROGRESS_2026-11-04_before_aligned_3000_handover.md)。

下一条工作命令：`sed -n '1,260p' scripts/g1_return_direction_audit.py`，执行前按STATUS核实HEAD和进程。

- 2026-11-04T13:38:19+08:00 本轮完整评估、PD选择与配对审计方法限制已提交 `8e1a29e70dd91bb54e6ae64ac6a4ae48a8130834`；STATUS/PROGRESS提交后仅回填准确HEAD，不改训练配置。文档链接、23份训练源码SHA256及model3000 SHA256复核通过。

- 2026-11-04T13:43:13+08:00 上一轮为progress（3000完整评估/方法限制归档提交8e1a29e）；已核实旧PID退出/GPU空闲。启动随机分支冻结方向审计，driver2967297，状态logs/amp_g1/randomized_return3000.pipeline.json；不训练、不改PD/奖励。

- 2026-11-04T13:43:13+08:00 冻结方向审计启动randomized_return3000_seed1701，driver2967297/child2967299；状态logs/amp_g1/randomized_return3000.pipeline.json。

- 2026-11-04T13:43:13+08:00 冻结方向审计失败AssertionError({'name': 'randomized_return3000_seed1701', 'command': ['.venv/bin/python', 'scripts/g1_return_direction_audit.py', '--headless', '--checkpoint', 'logs/supermimic/2026-11-04_13-09-39_985939_g1_aligned_formal_r1_to3000/model_3000.pt', '--output', 'logs/amp_g1/randomized_return3000_seed1701.json', '--samples', '128', '--warmup', '8', '--steps', '128', '--seed', '1701'], 'log': 'logs/amp_g1/randomized_return3000_seed1701.log', 'output': 'logs/amp_g1/randomized_return3000_seed1701.json', 'pid': 2967299, 'returncode': 1})；先核实进程/日志，不自动重复启动。

- 2026-11-04T13:44:02+08:00 新审计首轮在AppLauncher导入前因后台进程缺README既有OMNI_KIT_ACCEPT_EULA=YES而EOF退出，未进入仿真。原driver/child退出、GPU空闲。按项目既有启动环境修正，原失败证据保留，新r2队列独立路径，不改模型/算法。

- 2026-11-04T13:44:02+08:00 上一轮为progress（3000完整评估/方法限制归档提交8e1a29e）；已核实旧PID退出/GPU空闲。启动随机分支冻结方向审计，driver2968029，状态logs/amp_g1/randomized_return3000_r2.pipeline.json；不训练、不改PD/奖励。

- 2026-11-04T13:44:02+08:00 冻结方向审计启动randomized_return3000_r2_seed1701，driver2968029/child2968031；状态logs/amp_g1/randomized_return3000_r2.pipeline.json。

- 2026-11-04T13:44:29+08:00 冻结方向审计结束randomized_return3000_r2_seed1701，returncode0，证据logs/amp_g1/randomized_return3000_r2_seed1701.json；尚非行走验收。

- 2026-11-04T13:44:29+08:00 冻结方向审计启动randomized_return3000_r2_seed2026，driver2968029/child2968781；状态logs/amp_g1/randomized_return3000_r2.pipeline.json。

- 2026-11-04T13:44:59+08:00 冻结方向审计结束randomized_return3000_r2_seed2026，returncode0，证据logs/amp_g1/randomized_return3000_r2_seed2026.json；尚非行走验收。

- 2026-11-04T13:46:30+08:00 随机分支v2两seed(1701/2026)均complete，128组×14分支、共同动作预热8步/首动作扰动/真实128步。普通起点全关节+.03的128步纯物理奖励增益+.01056[.00369,.02144]、+.00500[.00426,.00575]；参考起点同项CI均跨0。前动作/命令严格配对，状态/观测接触差仍在。证据不支持普通局部梯度完全无效，也不支持切PD，下一项检验完整actor参数更新/生产Adam而非继续首动作审计；未训练或改奖励。证据logs/amp_g1/randomized_return3000_r2.pipeline.json及两seed.json。

- 2026-11-04T13:48:45+08:00 上一轮为progress（3000完整评估/方法限制归档提交8e1a29e）；已核实旧PID退出/GPU空闲。启动完整actor临时Adam单步审计，driver2972307，状态logs/amp_g1/policy_step3000.pipeline.json；仅临时actor候选一步，不写checkpoint，不改PD/奖励/WM/critic/D。

- 2026-11-04T13:48:45+08:00 冻结方向审计启动policy_step3000_seed1701，driver2972307/child2972312；状态logs/amp_g1/policy_step3000.pipeline.json。

- 2026-11-04T13:49:11+08:00 冻结方向审计结束policy_step3000_seed1701，returncode0，证据logs/amp_g1/policy_step3000_seed1701.json；尚非行走验收。

- 2026-11-04T13:49:11+08:00 冻结方向审计启动policy_step3000_seed2026，driver2972307/child2972955；状态logs/amp_g1/policy_step3000.pipeline.json。

- 2026-11-04T13:49:40+08:00 冻结方向审计结束policy_step3000_seed2026，returncode0，证据logs/amp_g1/policy_step3000_seed2026.json；尚非行走验收。

- 2026-11-04T13:51:45+08:00 完整actor临时Adam单步审计两seed均complete：恢复原Adam动量/实际3001轮lr=2.92874e-5/grad_clip1，仅候选actor一步，四正式网络/checkpoint未改。256组×6随机分支。普通起点128步纯物理奖励增益+.00784[.00721,.00848]、+.00742[.00676,.00806]；参考+.00548[.00038,.01287]、+.00496[.00038,.01029]。模型H32改进幅度仍偏大，但不支持整体参数更新必然损害真实回报或优先切PD。参考128步原生存活仅30.9%/23.0%，仍是重要分布/稳定性问题，不能当walk改善。当前无作业，下一步优先核对参考动态学习与上游D实现/采样差异，不再重复当前梯度方向审计。证据logs/amp_g1/policy_step3000.pipeline.json及两seed.json。
