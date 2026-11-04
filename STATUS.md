# 当前状态与恢复入口

核实时间：2026-11-04T14:56:32+08:00。权威目录 `/pfs/user/learning/amp_new`，SSH `ssh -p 9205 root@118.196.87.69`。
恢复先读GOAL/PLAN/本文件，核实实际PID、GPU和pipeline；勿重复启动实验。

## 版本与范围

- 当前HEAD `4d5462f0ef776eed247dadae346ed01b569e6d37`。已提交新G1 D组件profile和冷启动历史纠正；当前训练相关源码SHA256保存在 `logs/amp_g1/implicit_velocity_r1.pipeline.json`，其受测D/GPU源码记录为 `discriminator_alignment_validation.pipeline.json`。文档改动不改变训练内核。
- Manager/A1已独立完成，checkpoint为 `checkpoints/go2_manager_converged.pt`、`checkpoints/a1_amp_converged.pt`。G1当前仅29DOF、平地walk、SuperMimic/可微想象、禁PPO，未通过最终验收。G1成功提交后才做X1下半身12DOF，部署参考reference/AMP，跳过RKNN。
- G1 `g1_implicit_pd_v1`：PhysX隐式PD、固定限矩88/139/25/5Nm，无DC降额。用户允许IdealPD候选但无切换证据。`g1_state84_base_contact_v1`：WM84/critic125/actor480；旧DC/83维WM禁止直接导入。
- 上游16项reward `g1_legged_lab_walk_v1`，最终AMP `R=.5task+dt*style`。训练终止height<.2或torso/pelvis接触；独立评估仍 `native_or_height05_tilt60_v1`。严格越界采样不等同独立摔倒回合数。
- A1/G1实际动作在assets/motions中由Git管理，7份G1动作Git/SHA256已复核。X1动作复制后忽略、清单入Git，按GOAL执行。

## 当前唯一队列与配置

- 原 `logs/amp_g1/implicit_velocity_r1.pipeline.json` 已complete，原driver3008096及全部child已退出，0/1000步态和1000完整速度结束，无重复训练。
- 当前 `logs/amp_g1/implicit_velocity_extension_r1.pipeline.json`，driver `3020615`、child `3020789` 已用ps核实存活，阶段 `implicit_velocity_extension_train3000`；完整命令、实时checkpoint/显存及PID以pipeline.jobs为准。驱动日志 `logs/amp_g1/implicit_velocity_extension_r1.driver.log`。
- 当前运行目录 `logs/supermimic/2026-11-04_14-53-53_184959_g1_implicit_velocity_cold_r1_to3000`；配置同目录config.json；日志 `logs/amp_g1/implicit_velocity_extension_train3000.log`。来源 `logs/supermimic/2026-11-04_14-43-09_759735_g1_implicit_velocity_cold_r1/model_1000.pt`，三网/三优化器 `--resume --continue-run`，从1000计数到3000，保持同一随机来源；保存2000/3000后两点完整速度与步态评估，不自动进入AMP。
- 当前隐式PD/state84，上游16项任务奖励固定，AMP/D/RSI均关闭；没有速度范围课程或奖励渐进。vx[0,1.2]、vy±.3、yaw±.8、10%站立、6–10秒重采样。
- 18432env/collect1/buffer128；WM512×3/window8/batch4096×4；actor及critic512,256,128；imag8192/H32/critic3×4；actor_lr_scale.15、OU.3占25%/Gaussian.1；原WM300/critic200预热已完成，不重计数，actor ramp500已达到最终值，FP32 highest/编译。其他学习参数未改。
- 无AMP完整反传profiling18432约59320转移/s、峰23170MiB，按余量跳过20480（不是OOM）。当前续训最近后段约59676/s，峰23698MiB；勿与其他GPU任务并发。profile模型不作来源。

## 最新/最佳checkpoint与最近指标

- 当前新PD无AMP最新 `logs/supermimic/2026-11-04_14-43-09_759735_g1_implicit_velocity_cold_r1/model_1000.pt`；1000已完整评估失败，无已验收最佳。1000包含300轮WM与200轮critic预热，actor有效更新500次；正在补足3000预算至2500次actor更新。
- 1000三网/三优化器审计通过，更新500/8400/4000。七指令物理步态失败22项；forward/fast vx RMSE1.370/1.444、严格fall/越界采样593/600、步频.044/.033Hz。完整速度失败30项，固定整体RMSE1.329/.337/.539，三随机vx RMSE1.313/1.294/1.330，均未达AMP入口。结论 `logs/amp_g1/implicit_velocity_r1_assessment1000.json`，报告及思路 `doc/G1_IMPLICIT_VELOCITY_COLD_START_2026-11-04.md`。
- 最近旧新PD AMP模型 `logs/supermimic/2026-11-04_13-09-39_985939_g1_aligned_formal_r1_to3000/model_3000.pt`，SHA256 `426459ba148ddff2e907d7c74336d02b09dbaf5c8593d501f26e3fd7db846ce0`。它不是当前训练来源，也不是已验收最佳。
- 旧AMP2000/3000完整速度失败30/19项、步态22/15项；3000固定整体RMSE(vx/vy/yaw)=.646/.204/.461，forward/fast实际vx≈.004/.004m/s，步频/腾空/净空0；六组零严格fall、转弯16。证据 `aligned_extension_velocity2000_3000.json`、`aligned_extension_gait2000_3000.json`（均logs/amp_g1下）。稳定站立不算walk。

## 已完成验证与重要结论

- 新D `legged_lab_v1`：G1新CLI默认1024/512 ELU、policy-only统计、eps.01/无clip/1e8冻结、优化后更新统计、输出decay.1；旧checkpoint缺profile按legacy，A1不变。新旧D不能直接resume。
- CPU95通过（含2项既有未跟踪exploration）；固定上游/RSL5.4.1源码oracle的两/四帧loss/梯度/Adam/归一化/style一致，最大参数误差3.73e-9。日志及审计 `discriminator_alignment_cpu.log`、`discriminator_alignment_oracle.json`。
- 新D原生GPU/编译梯度/速度8轮→AMP20轮→恢复25轮/旧profile/A1回归通过；四网更新16/36/20/3→21/46/25/4。审计 `logs/amp_g1/discriminator_alignment_validation.audit.json`。随机smoke不能证明walk。
- 初次2s×2 gait smoke不足style128对转移，日志异常虽返回0被runner拒绝。失败记录 `discriminator_alignment_validation.failed.json` 保留，只补20s×8评估，训练未重复。该验证队列已complete/active_pid=null，旧driver3000701及恢复driver3005309均退出。
- D预算审计：上游interval=5按mini-batch计、实际policy序列/新增物理转移约1；当前旧AMP为2048×2/(5×18432)=.04444，低22.5倍。只是计数单位/样本预算差异，尚未证明因果；当前无AMP队列不受影响。见 `doc/G1_DISCRIMINATOR_SAMPLE_BUDGET_2026-11-04.md`。
- 历史DC冷启动0→9000确已完成并能移动，但高频低抬脚；后续无AMP/61/64/70维/四帧匹配对照均未通过walk。不能说“从未冷启动”；旧WM不能复用到当前PD。当前新PD/state84/16项奖励下，除接口smoke外首次正式无AMP冷启动正在进行。详见 `doc/G1_COLD_START_DECISION_2026-11-04.md`。
- 既有真实TD、MPC/动态拟合、增加OU/节流D等未解决walk；普通局部actor真实Adam一步回报有小幅条件增益，参考128步存活仅23–31%。不重复梯度审计、不盲切PD、不做奖励权重网格。完整历史与证据见 `doc/G1_RANDOMIZED_GRADIENT_AUDIT_2026-11-04.md`。

## 未解决问题与下一步

- 当前1000完整结果已失败，正在同谱系续到3000并独立评估2000/3000，补足早期actor预算后再决定基础课程。若仍站立，单独检验Go2式基础速度→最终奖励课程；当前profile明确忽略该schedule，不用无效参数冒充课程。
- 稳定移动但风格差可进入诊断AMP；预设入口：七组20s×8严格fall为0、高度≥.65m，forward/fast vx RMSE≤.25m/s且有非零步频。其他未通过指标保留，不称正式成功。AMP与无AMP臂同初值/预算、同样重建critic/优化器，AMP另建D；仅继承当前同G1 actor/WM。
- AMP衔接前先按物理采样量预设D预算并GPU验证，再渐进style；不与奖励课程同时实验。最终G1三连续点/全速度步态/留出风格/加噪/录像/审计仍未完成，X1未开始。

下一条命令只观察已有队列，**不要再次启动pipeline**：

```bash
cd /pfs/user/learning/amp_new
cat logs/amp_g1/implicit_velocity_extension_r1.pipeline.json
ps -p 3020615,3020789 -o pid,ppid,etime,stat,args
nvidia-smi
tail -n 8 logs/amp_g1/implicit_velocity_extension_train3000.log
```

阶段思路：`doc/G1_DISCRIMINATOR_ALIGNMENT_2026-11-04.md`、`doc/G1_COLD_START_DECISION_2026-11-04.md`；此前记录归档 `docs/history/STATUS_2026-11-04_before_implicit_velocity_launch.md`。

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

- 2026-11-04T14:56:32+08:00：已按上游默认4096环境/24步/4D更新/每批24576换算后续唯一D预算候选24576×3/interval4（18432env），匹配全局新增转移的样本与优化步比。仅预设、尚未GPU验证，未改变当前无AMP续训；见D_SAMPLE_BUDGET文档。
