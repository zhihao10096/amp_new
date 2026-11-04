# 当前状态与恢复入口

核实时间：2026-11-04T12:08:44+08:00。权威目录`/pfs/user/learning/amp_new`；SSH `ssh -p 9205 root@118.196.87.69`。先读GOAL/PLAN/本文件，再核对HEAD、PID、GPU和产物，避免重启已完成队列。上一状态快照`docs/history/STATUS_2026-11-04_before_upstream_reward.md`。

## 当前版本与决定

- 当前HEAD `29b18758e16f33b31f071bcb0f55c347e50f7640`（本轮上游奖励对齐实现与验证记录已提交；隐式PD控制父提交f32755e）。恢复执行`git rev-parse HEAD; git status --short`；保留其他既有改动和未跟踪reference/exploration/dynamics诊断文件。
- Manager与A1已独立完成；G1只做平地walk/29DOF，SuperMimic世界模型与可微想象，禁止PPO；G1验收后进入X1下半身12DOF、跳过RKNN，其他部署配置参考reference/AMP。
- G1继续`actuator_model=g1_implicit_pd_v1`，PhysX隐式PD和固定限矩，不使用DC/转速降额；旧DC世界模型不可resume/warm-start/作为新控制评估。IdealPD是用户允许的备选，无对照证据要求切换；若比较须记录独立模型类型和训练来源。
- 新默认`reward_profile=g1_legged_lab_walk_v1`：固定上游legged_lab f33a189的16项奖励/权重/关节范围/坐标；最终`R=.5*task+dt*style`，站立style开启，AMP ramp同步真实/想象task与style比例，不套旧四足步态课程。旧`g1_walk`保留以恢复历史隐式PD短跑，Go2/A1回归通过。
- 七份实际G1动作在assets/motions/g1由Git管理，SHA256本轮全部通过；新增A1/G1动作仍须提交，X1另按GOAL要求复制后忽略。

## 当前进程、目录与配置

- 无本项目训练/验证进程，GPU无计算进程。`logs/amp_g1/upstream_reward_validation.pipeline.json`为complete、audit为passed；driver2883115及8个子作业全部退出，勿重复启动。此前隐式PDdriver2858666也已完成。
- 本轮只做接口短跑：32env，随机G1-Velocity8轮→同控制AMP20轮→CLI恢复25轮；WM64×2、actor/critic64,32、WM/imag batch32、H4、buffer32/window4、collect2、FP32编译；D64,32/batch64/update interval5/lr1e-5→2e-5/GP40，AMP61维四帧。命令/PID/日志见pipeline.jobs，run/config.json保存实际配置。
- 新真实GPU原生边界覆盖reset/终止/超时/指令/历史、混合RSI、真实TD、想象编译；旧profile及旧checkpoint、A1原生GPU回归均结束。没有新收敛训练或权重网格。

## 最新与最佳checkpoint

- 最新：`logs/supermimic/2026-11-04_12-03-38_812189_g1_upstream_reward_smoke_resume/model_25.pt`，25轮随机接口模型，**不是行走候选**；初始20轮`logs/supermimic/2026-11-04_12-02-56_338155_g1_upstream_reward_smoke_initial/model_20.pt`。
- 同控制速度接口模型`logs/supermimic/2026-11-04_12-02-17_174191_g1_upstream_reward_velocity_smoke/model_8.pt`。
- 新隐式PD/新上游奖励下没有已验收最佳模型或已收敛checkpoint。
- 历史DC稳定移动来源`logs/supermimic/2026-11-04_08-00-37_784295_g1_velocity_cold_start18432_to9000/model_9000.pt`；历史四帧AMP`logs/supermimic/2026-11-04_10-24-56_796290_g1_amp_warm9000_feet70_history4_diag/model_1000.pt`仍碎步；都不能导入新PD世界模型。
- 已完成阶段归档`checkpoints/go2_manager_converged.pt`、`checkpoints/a1_amp_converged.pt`，无需重训。

## 最近验证与指标

- CPU82通过（`logs/amp_g1/upstream_reward_cpu.log`）。上游16项原函数oracle：512样本/float64，单项max9.76e-13、task max1.95e-14，9组dt/混合通过；GitHub固定源码与本地SHA256一致。证据`upstream_reward_oracle.json`、`upstream_reward_github_evidence.json`。
- 新profile真实GPU/编译passed：65reset/11摔倒/54超时/355命令切换，8个手臂接触体正确；真实TD max4.77e-7，编译返回max3.58e-7、actor梯度max1.46e-11。`logs/amp_g1/upstream_reward_integration.json`。
- 四网四优化器20→25持续更新actor16→21/critic36→46/WM20→25/D3→4；同PD velocity→AMP精确继承actor/WM、优化器重建；CLI自动恢复profile/61维四帧/奖励。`logs/amp_g1/upstream_reward_validation.audit.json`。
- 25轮随机接口模型七指令829摔，风格距3.81350/3.80468（`upstream_reward_smoke_gait.json`）；无行走/碎步改善结论。旧profile/checkpoint及A1 GPU回归passed。

## 已定位差异、排除方案与未解决问题

- 已修复上游相对style权重少4倍、全部29DOF运动L1姿态惩罚、额外自定义步态奖励、奖励关节范围及站立style门控等实现差异；这是公式对齐，尚未证明闭环收益。
- 未对齐：上游height=.2且无60°倾角终止，依赖torso/pelvis接触；当前仍height=.5/倾角终止。RSI命令对齐未实现，上游counter==0与本机Lab2.1回调计数不同，不可照搬。
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
cat logs/amp_g1/upstream_reward_validation.audit.json
sed -n '1,180p' doc/G1_LEGGED_LAB_REWARD_ALIGNMENT_2026-11-04.md
```

下一执行步骤：核对上游终止/RSI回调的实际输入及计数，形成独立改动/验证计划，之后再启动新隐式PD基线训练；不要重复本轮验证。

- 2026-11-04T12:12:20+08:00 继续主目标，核实HEAD29b1875、上一轮完整验证complete且GPU无进程。新问题：83维状态只有手臂接触计数，缺少上游torso/pelvis接触终止输入；真实单改height/tilt会与想象不一致。决定增加独立base-contact标量（G1状态84维、critic125维、actor/AMP不变），新walk终止用height<.2或躯干接触，不再倾角终止；旧profile判定和actor评估保留，旧83维WM拒绝继续训练。先仅做终止接口并验证/提交，再独立RSI，不启动权重网格。GitHub四份固定源码与本地逐字一致：logs/amp_g1/g1_boundary_github_evidence.json。

- 2026-11-04T12:16:03+08:00 终止接口CPU首轮86过2失败：四帧编译测试夹具仍用83/124维，新增软终止断言漏算0.3m高度sigmoid尾部；均为测试输入/断言问题，已按84/125维与既定.015m软宽修正，不改生产公式。原日志contact_termination_cpu.log保留，r2日志contact_termination_cpu_r2.log（logs/amp_g1），无GPU作业/训练启动。

- 2026-11-04T12:16:52+08:00 终止接口CPU88全部通过；真实GPU验证driver PID2896001已启动，状态logs/amp_g1/contact_termination_validation.pipeline.json。覆盖84维/上游终止oracle/真实碰地/想象编译、旧83维训练拒绝、四网保存恢复、历史actor及A1回归；仅接口验证，勿重复启动，未启动正式训练。

- 2026-11-04T12:18:12+08:00 验证driver2896001在源码hash清单阶段因脚本模板错误文件名退出，已核实PID不存在/无pipeline状态文件/未启动GPU子作业；修复清单并逐路径检查后启动driver2896882，使用同队列contact_termination_validation.pipeline.json，旧driver日志保留.driver.log，新driver_r2.log。CPU88证据仍有效，生产代码未改。

- 2026-11-04T12:18:13.408423+08:00 终止接口验证启动contact_termination_reject83_resume，driver PID2896882、child PID2897005；命令/配置/日志见logs/amp_g1/contact_termination_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:18:16.441768+08:00 终止接口验证结束contact_termination_reject83_resume，返回码1，预期拒绝=True，证据logs/amp_g1/contact_termination_reject83_resume.log。

- 2026-11-04T12:18:16.448824+08:00 终止接口验证启动contact_termination_reject83_warm-start，driver PID2896882、child PID2897032；命令/配置/日志见logs/amp_g1/contact_termination_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:18:19.483249+08:00 终止接口验证结束contact_termination_reject83_warm-start，返回码1，预期拒绝=True，证据logs/amp_g1/contact_termination_reject83_warm-start.log。

- 2026-11-04T12:18:19.487175+08:00 终止接口验证启动contact_termination_integration，driver PID2896882、child PID2897093；命令/配置/日志见logs/amp_g1/contact_termination_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:19:04.949554+08:00 终止接口验证结束contact_termination_integration，返回码0，预期拒绝=False，证据logs/amp_g1/contact_termination_integration.log。

- 2026-11-04T12:19:04.957795+08:00 终止接口验证启动contact_termination_legacy_integration，driver PID2896882、child PID2898199；命令/配置/日志见logs/amp_g1/contact_termination_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:19:44.342787+08:00 终止接口验证结束contact_termination_legacy_integration，返回码0，预期拒绝=False，证据logs/amp_g1/contact_termination_legacy_integration.log。

- 2026-11-04T12:19:44.344486+08:00 终止接口验证启动contact_termination_velocity_smoke，driver PID2896882、child PID2899088；命令/配置/日志见logs/amp_g1/contact_termination_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:19:47+08:00 84维终止原生GPU/编译passed：1851次与Lab原生height/illegal_contact判定一致，1次实际躯干碰地终止、65reset/6摔倒/59超时；编译返回max5.96e-8/actor梯度3.73e-9。driver2896882继续旧profile/四网保存恢复/历史actor及A1回归；未启动正式训练。证据logs/amp_g1/contact_termination_integration.json。

- 2026-11-04T12:20:20.688944+08:00 终止接口验证结束contact_termination_velocity_smoke，返回码0，预期拒绝=False，证据logs/amp_g1/contact_termination_velocity_smoke.log。

- 2026-11-04T12:20:20.694825+08:00 终止接口验证启动contact_termination_smoke_initial，driver PID2896882、child PID2899857；命令/配置/日志见logs/amp_g1/contact_termination_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:21:06.137164+08:00 终止接口验证结束contact_termination_smoke_initial，返回码0，预期拒绝=False，证据logs/amp_g1/contact_termination_smoke_initial.log。

- 2026-11-04T12:21:06.161532+08:00 终止接口验证启动contact_termination_smoke_resume，driver PID2896882、child PID2900695；命令/配置/日志见logs/amp_g1/contact_termination_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:21:27.366242+08:00 终止接口验证结束contact_termination_smoke_resume，返回码0，预期拒绝=False，证据logs/amp_g1/contact_termination_smoke_resume.log。

- 2026-11-04T12:21:27.374565+08:00 终止接口验证启动contact_termination_legacy_checkpoint_gait，driver PID2896882、child PID2901105；命令/配置/日志见logs/amp_g1/contact_termination_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:22:09.805059+08:00 终止接口验证结束contact_termination_legacy_checkpoint_gait，返回码0，预期拒绝=False，证据logs/amp_g1/contact_termination_legacy_checkpoint_gait.log。

- 2026-11-04T12:22:09.810339+08:00 终止接口验证启动contact_termination_a1_regression，driver PID2896882、child PID2901780；命令/配置/日志见logs/amp_g1/contact_termination_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:22:31.051481+08:00 终止接口验证结束contact_termination_a1_regression，返回码0，预期拒绝=False，证据logs/amp_g1/contact_termination_a1_regression.log。

- 2026-11-04T12:22:31.053374+08:00 终止接口验证启动contact_termination_smoke_gait，driver PID2896882、child PID2902177；命令/配置/日志见logs/amp_g1/contact_termination_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:23:13.469970+08:00 终止接口验证结束contact_termination_smoke_gait，返回码0，预期拒绝=False，证据logs/amp_g1/contact_termination_smoke_gait.log。

- 2026-11-04T12:23:13.472272+08:00 终止84维CPU88/上游原生终止/想象编译梯度/同控制velocity→AMP热启动/四网20→25/旧profile及checkpoint/A1回归/七指令评估接口均完成。短跑不证明walk收敛。
