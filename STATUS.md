# 当前状态与恢复入口

核实时间：2026-11-04T12:07:53+08:00。权威目录`/pfs/user/learning/amp_new`；SSH `ssh -p 9205 root@118.196.87.69`。先读GOAL/PLAN/本文件，再核对HEAD、PID、GPU和产物，避免重启已完成队列。上一状态快照`docs/history/STATUS_2026-11-04_before_upstream_reward.md`。

## 当前版本与决定

- 当前HEAD `f32755ead857a35a9b8041a0a4e7fcfad9c1cd2e`；本轮上游奖励对齐实现/文档待提交，提交后更新准确HEAD。恢复执行`git rev-parse HEAD; git status --short`；保留其他既有改动和未跟踪reference/exploration/dynamics诊断文件。
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

下一执行步骤：提交本轮已验证奖励对齐；核对上游终止/RSI回调的实际输入及计数，形成独立改动/验证计划，之后再启动新隐式PD基线训练。
