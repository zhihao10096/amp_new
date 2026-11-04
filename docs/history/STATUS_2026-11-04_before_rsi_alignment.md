# 当前状态与恢复入口

核实时间：2026-11-04T12:25:38+08:00。权威目录`/pfs/user/learning/amp_new`；SSH `ssh -p 9205 root@118.196.87.69`。先读GOAL/PLAN/本文件，再核对HEAD、PID、GPU和产物，避免重启已完成队列。上一状态快照`docs/history/STATUS_2026-11-04_before_upstream_reward.md`。

## 当前工作

终止接口84维已提交eee92bb；RSI可选实现/严格评估及四帧审计修复CPU92通过，正在真实GPU验证；未启动正式训练。下一步独立RSI/评估门槛核对后建立新隐式PD基线。

## 当前版本与决定

- 当前HEAD `eee92bbc9b6fdbbbea5dc9e6d82b09133b18cdbe`（84维终止接口；上游奖励29b1875、隐式PD f32755e）。恢复执行`git rev-parse HEAD; git status --short`；保留其他既有改动和未跟踪reference/exploration/dynamics诊断文件。
- Manager与A1已独立完成；G1只做平地walk/29DOF，SuperMimic世界模型与可微想象，禁止PPO；G1验收后进入X1下半身12DOF、跳过RKNN，其他部署配置参考reference/AMP。
- G1继续`actuator_model=g1_implicit_pd_v1`，PhysX隐式PD和固定限矩，不使用DC/转速降额；旧DC世界模型不可resume/warm-start/作为新控制评估。IdealPD是用户允许的备选，无对照证据要求切换；若比较须记录独立模型类型和训练来源。
- 新默认`reward_profile=g1_legged_lab_walk_v1`：固定上游legged_lab f33a189的16项奖励/权重/关节范围/坐标；最终`R=.5*task+dt*style`，站立style开启，AMP ramp同步真实/想象task与style比例，不套旧四足步态课程。旧`g1_walk`保留以恢复历史隐式PD短跑，Go2/A1回归通过。
- 七份实际G1动作在assets/motions/g1由Git管理，SHA256本轮全部通过；新增A1/G1动作仍须提交，X1另按GOAL要求复制后忽略。

## 当前进程、目录与配置

- 当前RSI验证driver2907230正在运行，权威阶段/child PID见logs/amp_g1/rsi_alignment_validation.pipeline.json；勿重复启动。此前终止队列已结束。`logs/amp_g1/contact_termination_validation.pipeline.json`为complete、audit为passed；driver2896882和所有子进程均退出。此前driver2896001仅在源码清单阶段失败，没有启动GPU子进程，不重复已完成队列。
- 本轮32env，G1随机velocity8轮→同schema AMP20轮→CLI续到25；WM64×2、actor/critic64,32、WM/imag batch32/H4、buffer32/window4、collect2、FP32编译；D64,32/batch64/interval5/lr1e-5→2e-5/GP40、AMP61维四帧。全部命令/实际run目录/PID见pipeline.jobs和各run/config.json。
- G1状态84维/critic125维，state_schema=g1_state84_base_contact_v1，新增独立torso/pelvis接触；上游walk的termination_profile=g1_legged_lab_contact_v1，高度<.2或躯干接触，不用倾角终止。actor480维及AMP特征不变。旧83维WM禁止resume/warm-start；旧隐式PDactor仍可评估。

## 最新与最佳checkpoint

- 最新：`logs/supermimic/2026-11-04_12-21-14_719010_g1_contact_termination_smoke_resume/model_25.pt`，25轮随机接口模型，**不是行走候选**；初始20轮`logs/supermimic/2026-11-04_12-20-31_799666_g1_contact_termination_smoke_initial/model_20.pt`。
- 同控制速度接口模型`logs/supermimic/2026-11-04_12-19-52_684131_g1_contact_termination_velocity_smoke/model_8.pt`。
- 新隐式PD/新上游奖励下没有已验收最佳模型或已收敛checkpoint。
- 历史DC稳定移动来源`logs/supermimic/2026-11-04_08-00-37_784295_g1_velocity_cold_start18432_to9000/model_9000.pt`；历史四帧AMP`logs/supermimic/2026-11-04_10-24-56_796290_g1_amp_warm9000_feet70_history4_diag/model_1000.pt`仍碎步；都不能导入新PD世界模型。
- 已完成阶段归档`checkpoints/go2_manager_converged.pt`、`checkpoints/a1_amp_converged.pt`，无需重训。

## 最近验证与指标

- CPU88通过，`logs/amp_g1/contact_termination_cpu_r2.log`。原生GPU1851次与Lab原始height/illegal_contact方法一致，65reset/6摔倒/59超时、含1次实际躯干碰地；编译返回5.96e-8/actor梯度3.73e-9。`contact_termination_integration.json`。
- 四网20→25持续更新actor16→21/critic36→46/WM20→25/D3→4；同schema velocity→AMP精确继承actor/WM且四优化器重建；CLI继承schema/终止profile/61维四帧，旧83维训练在仿真前拒绝。旧profile/checkpoint actor评估及A1 GPU回归passed。`contact_termination_validation.audit.json`。
- 新25轮随机接口模型七指令737摔，风格距4.18733/4.21171，`contact_termination_smoke_gait.json`；无行走/碎步收益结论，不将不同终止定义的摔倒数作因果比较。
- 上一轮16项原函数oracle单项max9.76e-13/task1.95e-14，9组dt/混合组合通过；7份动作Git/SHA256和GitHub固定源码均通过，本轮未改奖励公式。历史证据upstream_reward_oracle.json/upstream_reward_validation.audit.json。

## 已定位差异、排除方案与未解决问题

- 已修复上游相对style权重少4倍、全部29DOF运动L1姿态惩罚、额外自定义步态奖励、奖励关节范围及站立style门控等实现差异；这是公式对齐，尚未证明闭环收益。
- 终止接口已对齐并验证；独立验收仍须保留原高度/倾角越界门槛，下一阶段在评估记录中明确核对，不能以修改终止规则降低零摔倒标准。RSI命令对齐尚未落地；原始Lab2.1回调counter实际reset=1/timed=2（g1_rsi_counter_oracle.json），须使用同帧pending标记，默认关闭并独立验证。
- 原生末子步PD估算与共享端点代理最大差52.21Nm、末子步关节加速度与控制差分最大差2443.33rad/s²；接触计时也有控制周期量化/想象松弛。oracle只证明相同输入下公式一致，不能声称完整MDP或PhysX实际力矩一致；因果影响待验证。
- 历史负结果：严重RSI穿透/骨架映射错误未获支持；增加OU/节流D/真实TD/MPC/补动态拟合/特征61→64→70/四帧均未通过walk；Go2课程仅使G1稳定移动，不原样加码。A1/G1 RSI随机命令冲突约55%是共有现象。
- 新控制正式规模仍须重新测完整actor更新峰值/吞吐；历史18432约23GiB、24576完整更新OOM、32768PhysX错误，不能用32env接口或预热吞吐替代容量结论。尽量用满GPU须兼顾学习质量。
- G1完整速度、三个连续点、加噪、录像与实际模型审计仍未通过；总目标未完成，X1未开始。下一阶段独立处理终止/RSI接口后确定新PD训练基线，不把旧DC世界模型导入。

## 文档与下一条命令

思路/证据/限制：`doc/G1_LEGGED_LAB_REWARD_ALIGNMENT_2026-11-04.md`、`doc/G1_IMPLICIT_PD_RESTORE_2026-11-04.md`；最终门槛`G1_CONVERGENCE.md`不变。

```bash
cd /pfs/user/learning/amp_new
git rev-parse HEAD
git status --short
nvidia-smi
cat logs/amp_g1/rsi_alignment_validation.pipeline.json
sed -n '1,180p' doc/G1_LEGGED_LAB_REWARD_ALIGNMENT_2026-11-04.md
```

下一执行步骤：独立RSI默认关闭实现/原验收fall门槛保持/四帧metadata审计，然后测新PD完整actor更新容量并开始新随机训练。先核对contact_termination_validation.audit.json，不重启已完成队列。

- 2026-11-04T12:28:20+08:00 终止提交eee92bb后进入独立RSI：amp_reset_command_alignment默认False，仅G1 AMP可启用；同帧机体系速度裁剪到walk范围，由reset事件写pending并由下一command回调消费，普通reset/回合中仍随机、fixed优先、评估关闭。补充保留验收原height<.5/tilt>60任一越界即fall的计数，新增fall_definition元数据；训练上游终止不变。另修最终审计按实际AMP历史长度重建项目内动作metadata（此前硬编码两帧会错误拒绝四帧）。不改奖励/控制/数据/D参数，不启动新长训。

- 2026-11-04T12:30:20+08:00 RSI接口CPU92通过；真实GPU验证driver PID2907230已启动，状态logs/amp_g1/rsi_alignment_validation.pipeline.json。覆盖同帧速度/one-shot/混合reset/定时和fixed、默认关闭/CLI20→25继承/25→30显式关闭、四网恢复、严格七指令及速度评估、旧actor/A1回归；仅接口短跑，不是收敛。终止工作doc已同步本机并确认中央弹窗显示（eee92bb）。

- 2026-11-04T12:30:21.692179+08:00 RSI接口验证启动rsi_alignment_reject83_resume，driver PID2907230、child PID2907333；命令/配置/日志见logs/amp_g1/rsi_alignment_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:30:24.725942+08:00 RSI接口验证结束rsi_alignment_reject83_resume，返回码1，预期拒绝=True，证据logs/amp_g1/rsi_alignment_reject83_resume.log。

- 2026-11-04T12:30:24.729883+08:00 RSI接口验证启动rsi_alignment_reject83_warm-start，driver PID2907230、child PID2907375；命令/配置/日志见logs/amp_g1/rsi_alignment_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:30:27.764147+08:00 RSI接口验证结束rsi_alignment_reject83_warm-start，返回码1，预期拒绝=True，证据logs/amp_g1/rsi_alignment_reject83_warm-start.log。

- 2026-11-04T12:30:27.766957+08:00 RSI接口验证启动rsi_alignment_integration，driver PID2907230、child PID2907426；命令/配置/日志见logs/amp_g1/rsi_alignment_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:30:55.058048+08:00 RSI接口验证结束rsi_alignment_integration，返回码0，预期拒绝=False，证据logs/amp_g1/rsi_alignment_integration.log。

- 2026-11-04T12:30:55.065793+08:00 RSI接口验证启动rsi_alignment_default_off_integration，driver PID2907230、child PID2907938；命令/配置/日志见logs/amp_g1/rsi_alignment_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:31:22.322656+08:00 RSI接口验证结束rsi_alignment_default_off_integration，返回码0，预期拒绝=False，证据logs/amp_g1/rsi_alignment_default_off_integration.log。

- 2026-11-04T12:31:22.324217+08:00 RSI接口验证启动rsi_alignment_legacy_integration，driver PID2907230、child PID2908464；命令/配置/日志见logs/amp_g1/rsi_alignment_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:31:49.607508+08:00 RSI接口验证结束rsi_alignment_legacy_integration，返回码0，预期拒绝=False，证据logs/amp_g1/rsi_alignment_legacy_integration.log。

- 2026-11-04T12:31:49.609344+08:00 RSI接口验证启动rsi_alignment_velocity_smoke，driver PID2907230、child PID2908953；命令/配置/日志见logs/amp_g1/rsi_alignment_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:32:03+08:00 RSI原生GPU/编译passed：59参考reset同实际机器人机体系速度一致，最大误差4.17e-7；70普通reset覆盖，pending已一次性消费，定时随机/fixed/历史/终止接口通过，编译返回5.96e-8/actor梯度3.73e-9。默认关闭新profile也通过；driver2907230继续CLI恢复/显式关闭、评估及A1，未启动正式训练。证据logs/amp_g1/rsi_alignment_integration.json。

- 2026-11-04T12:32:10.888835+08:00 RSI接口验证结束rsi_alignment_velocity_smoke，返回码0，预期拒绝=False，证据logs/amp_g1/rsi_alignment_velocity_smoke.log。

- 2026-11-04T12:32:10.898769+08:00 RSI接口验证启动rsi_alignment_smoke_initial，driver PID2907230、child PID2909368；命令/配置/日志见logs/amp_g1/rsi_alignment_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:32:38.212425+08:00 RSI接口验证结束rsi_alignment_smoke_initial，返回码0，预期拒绝=False，证据logs/amp_g1/rsi_alignment_smoke_initial.log。

- 2026-11-04T12:32:38.237026+08:00 RSI接口验证启动rsi_alignment_smoke_resume，driver PID2907230、child PID2910140；命令/配置/日志见logs/amp_g1/rsi_alignment_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:33:02.475973+08:00 RSI接口验证结束rsi_alignment_smoke_resume，返回码0，预期拒绝=False，证据logs/amp_g1/rsi_alignment_smoke_resume.log。

- 2026-11-04T12:33:02.489972+08:00 RSI接口验证启动rsi_alignment_smoke_disabled，driver PID2907230、child PID2910587；命令/配置/日志见logs/amp_g1/rsi_alignment_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:33:26.764250+08:00 RSI接口验证结束rsi_alignment_smoke_disabled，返回码0，预期拒绝=False，证据logs/amp_g1/rsi_alignment_smoke_disabled.log。

- 2026-11-04T12:33:26.773822+08:00 RSI接口验证启动rsi_alignment_legacy_checkpoint_gait，driver PID2907230、child PID2911019；命令/配置/日志见logs/amp_g1/rsi_alignment_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:34:12.201688+08:00 RSI接口验证结束rsi_alignment_legacy_checkpoint_gait，返回码0，预期拒绝=False，证据logs/amp_g1/rsi_alignment_legacy_checkpoint_gait.log。

- 2026-11-04T12:34:12.203552+08:00 RSI接口验证启动rsi_alignment_a1_regression，driver PID2907230、child PID2911777；命令/配置/日志见logs/amp_g1/rsi_alignment_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:34:36.443955+08:00 RSI接口验证结束rsi_alignment_a1_regression，返回码0，预期拒绝=False，证据logs/amp_g1/rsi_alignment_a1_regression.log。

- 2026-11-04T12:34:36.448586+08:00 RSI接口验证启动rsi_alignment_smoke_gait，driver PID2907230、child PID2912224；命令/配置/日志见logs/amp_g1/rsi_alignment_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:35:18.862050+08:00 RSI接口验证结束rsi_alignment_smoke_gait，返回码0，预期拒绝=False，证据logs/amp_g1/rsi_alignment_smoke_gait.log。

- 2026-11-04T12:35:18.864031+08:00 RSI接口验证启动rsi_alignment_smoke_velocity，driver PID2907230、child PID2912908；命令/配置/日志见logs/amp_g1/rsi_alignment_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:35:34.014722+08:00 RSI接口验证结束rsi_alignment_smoke_velocity，返回码0，预期拒绝=False，证据logs/amp_g1/rsi_alignment_smoke_velocity.log。

- 2026-11-04T12:35:34.015736+08:00 RSI同帧命令CPU92/真实GPU/默认关闭/显式关闭/严格评估/想象编译梯度/同控制velocity→AMP热启动/四网20→25/旧profile及checkpoint/A1回归/七指令评估接口均完成。短跑不证明walk收敛。
