# 进度与恢复入口

最后核实：2026-11-04T14:44:40+08:00。目录 `/pfs/user/learning/amp_new`，HEAD `707eb41d033ce9f389c67f6b918e63615cbe68ae`。
恢复先读GOAL/PLAN/STATUS，核实实际PID/GPU，不能重复启动。

- Manager/A1已完成，G1 29DOF平地walk未验收，X1未开始。保持SuperMimic/禁PPO；新PD固定限矩，无DC降额。A1/G1动作Git管理，X1按GOAL复制后忽略。
- 上一goal turn新增冷启动决定属progress，但混淆了旧DC与新PD历史，本轮已纠正：旧9000和同源AMP诊断已结束，能移动但碎步；旧WM不能导入新PD。当前新PD/state84/16项奖励此前只有接口smoke，正式无AMP冷启动正在进行。
- 新D组件对齐已提交407b091：profile独立/旧模型legacy/A1不变；CPU95、固定上游oracle、真实GPU编译梯度/四网更新恢复/旧profile/A1回归全部通过。最初过短评估不足style128对样本，仅补足评估，没有重训。
- 进一步量化D interval单位差异：上游每新增物理转移约训练1个policy序列，当前旧AMP为.04444，低22.5倍；仅发现预算差异，未证明根因，不更改当前无AMP队列。
- 当前唯一队列 `logs/amp_g1/implicit_velocity_r1.pipeline.json`，driver3008096/child3010448实际存活。18432完整反传profile约59320转移/s、峰23170MiB，按余量跳过20480；另起新随机1000，不复用profile/旧DC/失败AMP权重。
- 正式run `logs/supermimic/2026-11-04_14-43-09_759735_g1_implicit_velocity_cold_r1`；最新 `logs/supermimic/2026-11-04_14-43-09_759735_g1_implicit_velocity_cold_r1/model_1000.pt`，无已验收最佳。WM300/critic200/actor ramp500，WM4096×4/window8、imag8192/H32、critic3×4，AMP/D/RSI关闭，固定上游任务奖励和命令范围。自动保存0/500/1000并运行0/1000七指令与1000完整速度评估，不自动进入AMP。
- 用户确认后续会结合冷启动与AMP：稳定移动而风格差可做匹配AMP/无AMP诊断。预设入口七组零严格fall/高度≥.65，forward/fast vx RMSE≤.25且非零步频；最终G1完整三点/加噪/录像/审计门槛不变。
- 新D样本预算需在AMP衔接前独立预设/验证；若基础任务仍站立再单独验证Go2式奖励课程。当前无速度范围/奖励渐进，不把网络预热叫速度课程，不做权重网格或盲切PD。

下一条命令见STATUS，只观察已有driver/child/pipeline。日志、配置、指标及旧3000未通过结果均见STATUS。问题思路保存在doc/G1_DISCRIMINATOR_ALIGNMENT_2026-11-04.md、doc/G1_COLD_START_DECISION_2026-11-04.md和doc/G1_DISCRIMINATOR_SAMPLE_BUDGET_2026-11-04.md。

旧记录归档 `docs/history/PROGRESS_2026-11-04_before_implicit_velocity_launch.md`。

- 2026-11-04T14:45:24+08:00：当前driver3008096/child3010448已用ps核实存活，已保存model500；500轮刚结束WM/critic预热，actor尚未更新，不能用该轮摔倒/回报判定冷启动效果。后续1000及独立评估由同一队列执行，不重复启动。衔接规则和D预算记录提交4d5462f。

- 2026-11-04T14:47:42.036228+08:00 隐式PD速度冷启动队列结束implicit_velocity_cold_r1，returncode=0/valid=True；峰值23044MiB/GPU86%，证据logs/amp_g1/implicit_velocity_cold_r1.log。退出码或训练期指标不代表walk成功。

- 2026-11-04T14:47:42.066798+08:00 隐式PD速度冷启动队列启动implicit_velocity_r1_gait，driver3008096/child3015776；命令/配置/状态logs/amp_g1/implicit_velocity_r1.pipeline.json，日志logs/amp_g1/implicit_velocity_r1_gait.log，勿重复启动。

- 2026-11-04T14:48:40+08:00 新PD无AMP1000训练正常结束returncode0，actor/critic/WM更新500/8400/4000、三网/优化器有限性与来源审计通过；最新model1000，无已验收最佳。原队列进入implicit_velocity_r1_gait、child3015776；评估产物可能增量写入，须等待完整两模型/完整速度覆盖后判定，不接入AMP、不重复训练。

- 2026-11-04T14:48:51.772576+08:00 隐式PD速度冷启动队列结束implicit_velocity_r1_gait，returncode=0/valid=True；峰值5614MiB/GPU72%，证据logs/amp_g1/implicit_velocity_r1_gait.log。退出码或训练期指标不代表walk成功。

- 2026-11-04T14:48:51.777099+08:00 隐式PD速度冷启动队列启动implicit_velocity_r1_velocity，driver3008096/child3016937；命令/配置/状态logs/amp_g1/implicit_velocity_r1.pipeline.json，日志logs/amp_g1/implicit_velocity_r1_velocity.log，勿重复启动。

- 2026-11-04T14:50:25+08:00 新PD无AMP1000七指令步态已完整结束：forward/fast vx RMSE1.370/1.444、严格fall/越界采样593/600、步频.044/.033，未达到诊断AMP入口。原队列继续全速度child3016937。先同配置/三网三优化器/计数续1000→3000，补足2500次actor预算并做两点完整评估；不接AMP，不同时改奖励/PD。方案doc/G1_IMPLICIT_VELOCITY_COLD_START_2026-11-04.md。

- 2026-11-04T14:51:53.658468+08:00 隐式PD速度冷启动队列结束implicit_velocity_r1_velocity，returncode=0/valid=True；峰值5612MiB/GPU46%，证据logs/amp_g1/implicit_velocity_r1_velocity.log。退出码或训练期指标不代表walk成功。

- 2026-11-04T14:51:53.659253+08:00 新PD无AMP1000及独立评估结束：物理步态失败22项，速度失败30项。此为基础速度诊断，不能代替最终AMP验收；无自动AMP热启动。

- 2026-11-04T14:52:43+08:00 新PD无AMP1000全速度结束，原driver/全部child已退出、GPU空闲；物理步态失败22、速度失败30，固定整体RMSE=[1.3285375833511353, 0.33740633726119995, 0.5387760996818542]，不满足AMP入口。按预定预算唯一续训队列启动driver3020615，状态logs/amp_g1/implicit_velocity_extension_r1.pipeline.json；同model1000/三网三优化器/continue-run到3000，保存2000/3000后两点完整评估，无PD/奖励/探索/学习率修改。

- 2026-11-04T14:52:44.579164+08:00 隐式PD速度冷启动队列启动implicit_velocity_extension_train3000，driver3020615/child3020789；命令/配置/状态logs/amp_g1/implicit_velocity_extension_r1.pipeline.json，日志logs/amp_g1/implicit_velocity_extension_train3000.log，勿重复启动。

- 2026-11-04T14:56:32+08:00：当前唯一活跃队列已切换implicit_velocity_extension_r1，driver3020615/child3020789，run=logs/supermimic/2026-11-04_14-53-53_184959_g1_implicit_velocity_cold_r1_to3000。1000完整评估失败22物理步态/30速度项；三网三优化器及计数续至3000，不改奖励/PD/探索。原队列已complete且PID退出。最新仍来源model1000，无已验收最佳。

- 2026-11-04T14:59:49+08:00 同谱系2000已保存并完成CPU实际checkpoint审计：actor/critic/WM更新1500/20400/8000、三网有限且较1000变化、原随机来源和任务保持，AMP关闭；证据logs/amp_g1/implicit_velocity_interim2000_audit.json。原driver3020615/child3020789继续到3000，未做2000物理验收，不提前接AMP。

- 2026-11-04T15:04:37.038679+08:00 隐式PD速度冷启动队列结束implicit_velocity_extension_train3000，returncode=0/valid=True；峰值23698MiB/GPU88%，证据logs/amp_g1/implicit_velocity_extension_train3000.log。退出码或训练期指标不代表walk成功。

- 2026-11-04T15:04:37.055787+08:00 新PD速度续训队列失败AssertionError('wm_hidden')，核实logs/amp_g1/implicit_velocity_extension_r1.pipeline.json、PID和日志；不自动重复训练。

- 2026-11-04T15:06:02+08:00 新PD无AMP3000训练returncode0/validTrue并保存2000/3000。审计脚本重现wm_hidden list/tuple误判，原failed.json/failed.pipeline.py保留；仅将同值序列按JSON规范化比较，其他数值差异仍拒绝。启动仅审计/评估恢复driver3032041，状态仍implicit_velocity_extension_r1.pipeline.json；没有重训或修改训练源码/配置。

- 2026-11-04T15:06:04.316110+08:00 隐式PD速度冷启动队列启动implicit_velocity_extension_gait，driver3032041/child3032214；命令/配置/状态logs/amp_g1/implicit_velocity_extension_r1.pipeline.json，日志logs/amp_g1/implicit_velocity_extension_gait.log，勿重复启动。

- 2026-11-04T15:07:03+08:00：新PD无AMP3000训练结束。审计序列list/tuple误判已仅规范化表示后恢复，2000/3000三网/优化器实际更新、数值配置、原随机来源验证通过；当前恢复driver3032041/child3032214正在两点物理评估。原失败记录保留，训练不重跑，最新model3000，无已验收最佳；仍按“稳定真实迈步即可诊断AMP，风格问题留到AMP改善”衔接。

- 2026-11-04T15:07:07.961682+08:00 隐式PD速度冷启动队列结束implicit_velocity_extension_gait，returncode=0/valid=True；峰值5634MiB/GPU45%，证据logs/amp_g1/implicit_velocity_extension_gait.log。退出码或训练期指标不代表walk成功。

- 2026-11-04T15:07:07.964564+08:00 隐式PD速度冷启动队列启动implicit_velocity_extension_velocity，driver3032041/child3033193；命令/配置/状态logs/amp_g1/implicit_velocity_extension_r1.pipeline.json，日志logs/amp_g1/implicit_velocity_extension_velocity.log，勿重复启动。

- 2026-11-04T15:09:09+08:00：2000/3000七指令独立步态完整结束：forward/fast步频/腾空/净空均0，vx RMSE约.595/.995，主要站立；七组严格fall总采样7/23。两点均不满足诊断AMP入口，暂不引入AMP。原恢复driver3032041/child3033193继续完整速度评估。下一独立方向为让当前新PD G1速度任务真正接入Go2弱初期正则→最终奖励课程，先CPU/GPU验证；不把当前被跳过的schedule当已有课程，不盲续固定奖励或调AMP权重。证据doc/G1_IMPLICIT_VELOCITY_COLD_START_2026-11-04.md。
