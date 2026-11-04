# 进度与恢复入口

最后核实：2026-11-04T13:54:29+08:00；权威目录 `/pfs/user/learning/amp_new`，当前HEAD `8e1a29e70dd91bb54e6ae64ac6a4ae48a8130834`。恢复先读GOAL/PLAN/STATUS并核实实际进程，避免重复实验。

- Manager/A1已完成；G1仍仅29DOF平地walk、SuperMimic/禁PPO，未通过；X1未开始。A1/G1动作Git管理，X1按GOAL复制后忽略。
- 隐式PD固定限矩/无DC降额；用户允许IdealPD独立候选，无切换证据。训练内核20ad0d3，上游16项奖励/state84/RSI命令/严格评估已修复，CPU92/真实GPU/四网恢复/A1回归通过。
- 新PD随机AMP0→1000→3000结束，18432env完整更新无OOM/PhysX错误；2000/3000速度失败30/19、步态22/15。3000主要稳定站立、前进vx约.004m/s、步频/腾空/净空0，无已验收最佳，最新模型完整路径见STATUS。
- 上一轮为progress：完整3000评估和配对方法限制已归档提交8e1a29e。本轮实现共同预热动作、随机分支、配对误差、零对照和95%bootstrapCI，分离物理奖励与critic尾项，观察128步真实后果。
- 首动作两seed：普通+.03干预128步纯物理回报均小幅提高、CI大于0；参考同项CI跨0。随后直接测完整actor参数一步：恢复原Adam动量/实际lr/grad_clip，普通真实增益+.00784/+.00742，参考+.00548/+.00496，四组条件CI均大于0；临时actor候选不写checkpoint，不改正式四网。
- 不再支持普通局部梯度完全无效/完整参数一步必然有害；WM幅度仍高估，参考128步存活仅30.9%/23.0%，不等于walk改善。临时候选用当前起点批次，不能代表生产replay/长期四网交互。
- 用户询问课程：当前无速度范围课程、无渐进任务奖励；WM300/critic200后501起actor，D305起每5轮2步；w=.5*min(iter/1000,1)，最终R=.5task+dt*style；RSI.5且命令对齐。仅核对解释，未改配置。
- 新两队列均complete、PID退出/GPU空闲；首轮后台缺README既有EULA环境在导入前EOF已修复并留证；无新长训。工具/命令/原始JSON/源码副本详见 [doc/G1_RANDOMIZED_GRADIENT_AUDIT_2026-11-04.md](doc/G1_RANDOMIZED_GRADIENT_AUDIT_2026-11-04.md)；CPU最终日志 logs/amp_g1/randomized_return_cpu_final.log。
- 下一项核对参考动态训练覆盖/存活，以及上游D结构、归一化、decay及每物理样本更新预算；不再重复当前梯度实验，不盲续、调奖励网格或切PD。

历史事件见 [PROGRESS归档](docs/history/PROGRESS_2026-11-04_before_randomized_gradient_result.md)；下一条执行命令见STATUS（上游D源码与本地fit_amp核对）。
