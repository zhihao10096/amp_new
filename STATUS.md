# 当前状态与恢复入口

核实时间：2026-11-04T14:44:40+08:00。权威目录 `/pfs/user/learning/amp_new`，SSH `ssh -p 9205 root@118.196.87.69`。
恢复先读GOAL/PLAN/本文件，核实实际PID、GPU和pipeline；勿重复启动实验。

## 版本与范围

- 当前HEAD `407b09140883d507a128a0081b7e9c92e4caa2cb`。已提交新G1 D组件profile和冷启动历史纠正；当前训练相关源码SHA256保存在 `logs/amp_g1/implicit_velocity_r1.pipeline.json`，其受测D/GPU源码记录为 `discriminator_alignment_validation.pipeline.json`。文档改动不改变训练内核。
- Manager/A1已独立完成，checkpoint为 `checkpoints/go2_manager_converged.pt`、`checkpoints/a1_amp_converged.pt`。G1当前仅29DOF、平地walk、SuperMimic/可微想象、禁PPO，未通过最终验收。G1成功提交后才做X1下半身12DOF，部署参考reference/AMP，跳过RKNN。
- G1 `g1_implicit_pd_v1`：PhysX隐式PD、固定限矩88/139/25/5Nm，无DC降额。用户允许IdealPD候选但无切换证据。`g1_state84_base_contact_v1`：WM84/critic125/actor480；旧DC/83维WM禁止直接导入。
- 上游16项reward `g1_legged_lab_walk_v1`，最终AMP `R=.5task+dt*style`。训练终止height<.2或torso/pelvis接触；独立评估仍 `native_or_height05_tilt60_v1`。严格越界采样不等同独立摔倒回合数。
- A1/G1实际动作在assets/motions中由Git管理，7份G1动作Git/SHA256已复核。X1动作复制后忽略、清单入Git，按GOAL执行。

## 当前唯一队列与配置

- `logs/amp_g1/implicit_velocity_r1.pipeline.json`，driver `3008096`、当前child `3010448`，阶段 `implicit_velocity_cold_r1`；已用ps核实存活。驱动日志 `logs/amp_g1/implicit_velocity_r1.driver.log`，完整命令及每job PID/日志/显存以pipeline.jobs为准。
- 当前运行目录 `logs/supermimic/2026-11-04_14-43-09_759735_g1_implicit_velocity_cold_r1`；配置同目录 `config.json`；训练日志 `logs/amp_g1/implicit_velocity_cold_r1.log`。
- 全新随机seed0，task `G1-Velocity-Flat`，无resume/warm-start、AMP/D/RSI均关闭；固定上游16项任务奖励，没有速度范围课程或奖励渐进。vx[0,1.2]、vy±.3、yaw±.8、10%站立、6–10秒重采样。
- 18432env/collect1/buffer128；WM512×3/window8/batch4096×4；actor及critic512,256,128；imag8192/H32/critic3×4；actor_lr_scale.15、OU.3占25%/Gaussian.1；WM300/critic200预热、actor ramp500、FP32 highest/编译。目标1000轮，保存0/500/1000后自动独立0/1000步态20s×8、1000全速度30s/96env/三随机seed。
- 完整反传profiling18432通过：actor25/critic360/WM160更新，后段约59320真实转移/s、峰23170MiB。按余量阈值跳过20480（不是OOM）；profile模型不用于正式训练来源。当前进程GPU最近77%/18176MiB，仍在预热/编译，正式吞吐待日志。

## 最新/最佳checkpoint与最近指标

- 当前新PD无AMP最新 `logs/supermimic/2026-11-04_14-43-09_759735_g1_implicit_velocity_cold_r1/model_0.pt`；尚未产生独立评估指标，无已验收最佳。1000包含300轮WM与200轮critic预热，actor有效更新500次；不能用这一点宣称充分收敛预算。
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

- 等当前1000及自动评估完成后，读取真实速度/步态决定继续同谱系或修基础课程。若仍站立，单独检验Go2式基础速度→最终奖励课程；当前profile明确忽略该schedule，不用无效参数冒充课程。
- 稳定移动但风格差可进入诊断AMP；预设入口：七组20s×8严格fall为0、高度≥.65m，forward/fast vx RMSE≤.25m/s且有非零步频。其他未通过指标保留，不称正式成功。AMP与无AMP臂同初值/预算、同样重建critic/优化器，AMP另建D；仅继承当前同G1 actor/WM。
- AMP衔接前先按物理采样量预设D预算并GPU验证，再渐进style；不与奖励课程同时实验。最终G1三连续点/全速度步态/留出风格/加噪/录像/审计仍未完成，X1未开始。

下一条命令只观察已有队列，**不要再次启动pipeline**：

```bash
cd /pfs/user/learning/amp_new
cat logs/amp_g1/implicit_velocity_r1.pipeline.json
ps -p 3008096,3010448 -o pid,ppid,etime,stat,args
nvidia-smi
tail -n 8 logs/amp_g1/implicit_velocity_cold_r1.log
```

阶段思路：`doc/G1_DISCRIMINATOR_ALIGNMENT_2026-11-04.md`、`doc/G1_COLD_START_DECISION_2026-11-04.md`；此前记录归档 `docs/history/STATUS_2026-11-04_before_implicit_velocity_launch.md`。
