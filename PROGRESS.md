# 进度与恢复入口

最后核实：2026-11-04T13:36:55+08:00。权威目录 `/pfs/user/learning/amp_new`，HEAD `9fb00b305aea39a71944361b78d0a20cc8a81133`；完整配置、checkpoint、进程及下一条命令见 [STATUS.md](STATUS.md)。恢复必须先核实进程，避免重复启动。

- Manager / A1 已完成，G1 仍未通过；X1 未开始。仅平地walk、SuperMimic世界模型 / 可微想象、禁PPO。参考动作与控制要求见 GOAL。
- 已恢复上游隐式PD及固定限矩，无DC转速降额；用户允许IdealPD候选，未实施该对照，也无隐式PD故障证据。切换须独立控制类型 / 新WM谱系。
- 奖励16项与混合、state84原生终止、RSI同帧命令、严格评估及四帧metadata已修复。CPU92、真实GPU / 编译梯度 / 四网恢复 / A1回归通过；训练内核仍20ad0d3。
- 18432完整更新 profiling 比16384吞吐高9.7%，正式新随机AMP1000后四网完整恢复到3000；训练无OOM/PhysX错误，峰值24134MiB，actor实际更新由500增到2500。
- 2000 / 3000四网及配置审计passed；旧list/tuple误报只恢复审计和评估，未重训。完整速度失败30/19、七指令步态失败22/15。3000前进vx约.004m/s，步频 / 腾空 / 净空为0；六组零严格fall、转弯16，仍未迈步。不能用风格距改善代替行走。
- 3000冻结模型普通 / 参考H32 bootstrap真实-想象差异扩大；配对首动作方向模型高估普通起点收益，参考样本间一致性弱。但正方向相对零对照收益很小，物理配对有噪声，缺成对置信区间，且bootstrap共用critic，尚无根因证明。
- 2026-11-04T13:36:55+08:00 已核实续训 / 完整评估 / 冻结模型 / 方向审计全部complete，旧PID退出，GPU0%/1MiB。本次CPU92passed，证据 logs/amp_g1/aligned_extension_cpu.log；未新增训练或IdealPD实验。
- 下一项先改进配对审计方法并验证；不盲续、不改奖励网格、不切PD。报告 [doc/G1_ALIGNED_3000_AND_PD_DECISION_2026-11-04.md](doc/G1_ALIGNED_3000_AND_PD_DECISION_2026-11-04.md) 保存结果、证据和方法局限；历史在 [PROGRESS归档](docs/history/PROGRESS_2026-11-04_before_aligned_3000_handover.md)。

下一条工作命令：`sed -n '1,260p' scripts/g1_return_direction_audit.py`，执行前按STATUS核实HEAD和进程。
