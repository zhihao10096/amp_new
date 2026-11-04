# 进度与恢复入口

最后核实：2026-11-04T14:44:40+08:00。目录 `/pfs/user/learning/amp_new`，HEAD `407b09140883d507a128a0081b7e9c92e4caa2cb`。
恢复先读GOAL/PLAN/STATUS，核实实际PID/GPU，不能重复启动。

- Manager/A1已完成，G1 29DOF平地walk未验收，X1未开始。保持SuperMimic/禁PPO；新PD固定限矩，无DC降额。A1/G1动作Git管理，X1按GOAL复制后忽略。
- 上一goal turn新增冷启动决定属progress，但混淆了旧DC与新PD历史，本轮已纠正：旧9000和同源AMP诊断已结束，能移动但碎步；旧WM不能导入新PD。当前新PD/state84/16项奖励此前只有接口smoke，正式无AMP冷启动正在进行。
- 新D组件对齐已提交407b091：profile独立/旧模型legacy/A1不变；CPU95、固定上游oracle、真实GPU编译梯度/四网更新恢复/旧profile/A1回归全部通过。最初过短评估不足style128对样本，仅补足评估，没有重训。
- 进一步量化D interval单位差异：上游每新增物理转移约训练1个policy序列，当前旧AMP为.04444，低22.5倍；仅发现预算差异，未证明根因，不更改当前无AMP队列。
- 当前唯一队列 `logs/amp_g1/implicit_velocity_r1.pipeline.json`，driver3008096/child3010448实际存活。18432完整反传profile约59320转移/s、峰23170MiB，按余量跳过20480；另起新随机1000，不复用profile/旧DC/失败AMP权重。
- 正式run `logs/supermimic/2026-11-04_14-43-09_759735_g1_implicit_velocity_cold_r1`；最新 `logs/supermimic/2026-11-04_14-43-09_759735_g1_implicit_velocity_cold_r1/model_0.pt`，无已验收最佳。WM300/critic200/actor ramp500，WM4096×4/window8、imag8192/H32、critic3×4，AMP/D/RSI关闭，固定上游任务奖励和命令范围。自动保存0/500/1000并运行0/1000七指令与1000完整速度评估，不自动进入AMP。
- 用户确认后续会结合冷启动与AMP：稳定移动而风格差可做匹配AMP/无AMP诊断。预设入口七组零严格fall/高度≥.65，forward/fast vx RMSE≤.25且非零步频；最终G1完整三点/加噪/录像/审计门槛不变。
- 新D样本预算需在AMP衔接前独立预设/验证；若基础任务仍站立再单独验证Go2式奖励课程。当前无速度范围/奖励渐进，不把网络预热叫速度课程，不做权重网格或盲切PD。

下一条命令见STATUS，只观察已有driver/child/pipeline。日志、配置、指标及旧3000未通过结果均见STATUS。问题思路保存在doc/G1_DISCRIMINATOR_ALIGNMENT_2026-11-04.md、doc/G1_COLD_START_DECISION_2026-11-04.md和doc/G1_DISCRIMINATOR_SAMPLE_BUDGET_2026-11-04.md。

旧记录归档 `docs/history/PROGRESS_2026-11-04_before_implicit_velocity_launch.md`。
