# 进度与恢复入口

最后核实：2026-11-04T13:54:29+08:00；权威目录 `/pfs/user/learning/amp_new`，当前HEAD `cddcbde66235e12d1a0ac33c477ab11485745768`。恢复先读GOAL/PLAN/STATUS并核实实际进程，避免重复实验。

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

- 2026-11-04T13:55:49+08:00 随机分支/完整Adam诊断、当前课程说明及交接记录已提交 `cddcbde66235e12d1a0ac33c477ab11485745768`；最终CPU92通过，GPU四任务正常结束、无本项目活动作业。提交后仅回填HEAD，不改变正式训练内核/模型。

- 2026-11-04T14:00:24+08:00 上一轮为progress(cddcbde，两seed真实首动作/完整Adam验证改变下一步)，当前已核实旧作业结束/GPU空闲。新假设：当前D实现偏离已验证legged_lab（ELU1024/512、policy-only归一化/eps.01/无clip/1e8冻结、优化后更新统计、输出decay.1）。已核对GitHub固定f33a189及RSL-RL v5.4.1；本机旧rsl normalizer.forward会自动更新，而5.4.1不会，不能据本机旧模块推断上游统计。决定实现独立legged_lab_v1 D profile，旧模型按legacy加载，A1保持兼容；先CPU/oracle/真实GPU编译四网恢复验证，再新随机来源容量profiling及受控训练，不改PD、16项奖励、混合/RSI或做奖励网格。D样本预算先量化，不与组件对齐同时改变。

- 2026-11-04：确认 G1 AMP 仍需参考 Go2 的速度/步态冷启动；当前正式 AMP 3000 轮固定速度范围、无有效奖励课程且只站立，不能跳过前置阶段。该表述限于当前隐式PD/state84；历史DC冷启动9000已完成并移动但碎步，旧WM不能复用。下一步新PD无AMP独立冷启动，成功后再warm-start AMP。

- 2026-11-04T14:28:59+08:00：纠正上一轮“G1速度冷启动从未运行”的错误：旧DC 0→9000及AMP对照已结束并有碎步证据；当前新PD/state84仅8轮smoke。核实旧config与拒绝旧WM的GPU审计，决定新PD先关闭AMP/D/RSI、固定16项奖励独立训练1000及0/1000评估，不重复旧DC或启用无效奖励课程参数。

- 2026-11-04T14:31:43.206186+08:00 新D独立GPU验证启动 driver 3000701；状态 logs/amp_g1/discriminator_alignment_validation.pipeline.json，日志 logs/amp_g1/discriminator_alignment_validation.driver.log。CPU95通过。先验证再提交，不是收敛训练，不重复启动。

- 2026-11-04T14:31:44.550472+08:00 判别器接口验证启动discriminator_alignment_integration，driver PID3000701、child PID3000870；命令/配置/日志见logs/amp_g1/discriminator_alignment_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T14:32:57.256628+08:00 判别器接口验证结束discriminator_alignment_integration，返回码0，预期拒绝=False，证据logs/amp_g1/discriminator_alignment_integration.log。

- 2026-11-04T14:32:57.263470+08:00 判别器接口验证启动discriminator_alignment_velocity_smoke，driver PID3000701、child PID3002099；命令/配置/日志见logs/amp_g1/discriminator_alignment_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T14:33:18.466968+08:00 判别器接口验证结束discriminator_alignment_velocity_smoke，返回码0，预期拒绝=False，证据logs/amp_g1/discriminator_alignment_velocity_smoke.log。

- 2026-11-04T14:33:18.476210+08:00 判别器接口验证启动discriminator_alignment_smoke_initial，driver PID3000701、child PID3002525；命令/配置/日志见logs/amp_g1/discriminator_alignment_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T14:34:00.891300+08:00 判别器接口验证结束discriminator_alignment_smoke_initial，返回码0，预期拒绝=False，证据logs/amp_g1/discriminator_alignment_smoke_initial.log。

- 2026-11-04T14:34:00.905248+08:00 判别器接口验证启动discriminator_alignment_smoke_resume，driver PID3000701、child PID3003219；命令/配置/日志见logs/amp_g1/discriminator_alignment_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T14:34:25.141254+08:00 判别器接口验证结束discriminator_alignment_smoke_resume，返回码0，预期拒绝=False，证据logs/amp_g1/discriminator_alignment_smoke_resume.log。

- 2026-11-04T14:34:27.046914+08:00 判别器接口验证启动discriminator_alignment_smoke_gait，driver PID3000701、child PID3003758；命令/配置/日志见logs/amp_g1/discriminator_alignment_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T14:34:42.191764+08:00 新D接口验证失败AssertionError(PosixPath('logs/amp_g1/discriminator_alignment_smoke_gait.log'))，检查logs/amp_g1/discriminator_alignment_validation.pipeline.json及实际进程，不自动重复启动。

- 2026-11-04T14:36:49.331270+08:00 新D四网20→25/编译已通过；过短2s×2评估不足128对style样本而退出，原训练不重跑。失败记录discriminator_alignment_validation.failed.json保留，仅评估恢复driver3005309，状态仍discriminator_alignment_validation.pipeline.json。

- 2026-11-04T14:36:50.642204+08:00 判别器接口验证启动discriminator_alignment_smoke_gait_r2，driver PID3005309、child PID3005466；命令/配置/日志见logs/amp_g1/discriminator_alignment_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T14:37:30.021583+08:00 判别器接口验证结束discriminator_alignment_smoke_gait_r2，返回码0，预期拒绝=False，证据logs/amp_g1/discriminator_alignment_smoke_gait_r2.log。

- 2026-11-04T14:37:30.040495+08:00 判别器接口验证启动discriminator_alignment_legacy_checkpoint_gait，driver PID3005309、child PID3006136；命令/配置/日志见logs/amp_g1/discriminator_alignment_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T14:38:12.456197+08:00 判别器接口验证结束discriminator_alignment_legacy_checkpoint_gait，返回码0，预期拒绝=False，证据logs/amp_g1/discriminator_alignment_legacy_checkpoint_gait.log。

- 2026-11-04T14:38:12.466404+08:00 判别器接口验证启动discriminator_alignment_a1_regression，driver PID3005309、child PID3006928；命令/配置/日志见logs/amp_g1/discriminator_alignment_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T14:38:36.730545+08:00 判别器接口验证结束discriminator_alignment_a1_regression，返回码0，预期拒绝=False，证据logs/amp_g1/discriminator_alignment_a1_regression.log。

- 2026-11-04T14:38:36.731360+08:00 新D profile CPU95/真实GPU编译梯度/四网更新与CLI恢复/旧checkpoint/A1回归完成；仅补足评估样本，训练未重跑。

- 2026-11-04T14:39:27+08:00 新D组件对齐CPU95+独立上游oracle+GPU编译梯度+四网20→25/CLI恢复/旧模型/A1回归全部通过；首次评估样本不足仅补足评估未重训。待提交D后启动新PD无AMP1000冷启动，详细入口见STATUS和doc/G1_DISCRIMINATOR_ALIGNMENT_2026-11-04.md。
