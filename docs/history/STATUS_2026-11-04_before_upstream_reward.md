# 当前状态与恢复入口

核实时间：2026-11-04T11:40:18+08:00。权威运行目录 `/pfs/user/learning/amp_new`；SSH `ssh -p 9205 root@118.196.87.69`。恢复先读GOAL/PLAN/本文件，核对实际PID/GPU和产物，不重启已完成队列。此前完整状态见 `docs/history/STATUS_2026-11-04_before_implicit_pd.md`。

## 当前工作

- 2026-11-04T11:50:47+08:00 恢复核实HEAD f32755e，隐式PD验证已complete/全部进程退出，无本项目训练；其他项目约5895MiB使用保留。上一轮属于进展：控制实现、四网恢复及上游公式差异证据均已完成。
- 本轮实现明确的g1_legged_lab_walk_v1奖励配置：上游16项/关节范围/坐标与AMP混合；旧G1 profile保留，新配置不使用旧四足奖励课程。不同时更改RSI/终止或WM状态；原生子步力矩/加速度及控制周期计时近似写入doc，oracle不得夸大验证范围。尚未启动新训练。

## 当前版本、范围与决定

- 当前HEAD `f32755ead857a35a9b8041a0a4e7fcfad9c1cd2e`（隐式PD控制修复，完整验证通过）；源码审计历史基线8f63846。运行 `git rev-parse HEAD; git status --short` 核实，保留既有未跟踪reference/exploration/dynamics诊断和无关文档。
- Manager与A1 AMP已独立完成。G1只做平地walk/29DOF，SuperMimic世界模型与可微想象，全程禁PPO；G1完整验收后才进入X1下半身12DOF，跳过RKNN，其他部署配置参考reference/AMP。
- 用户明确禁用G1 DC模型及转速降额。已恢复上游PhysX隐式PD/固定限矩，各组Kp/Kd、速度上限、armature和动作尺度不变。IdealPD是用户允许的备选，目前没有其优于隐式PD的证据，未切换。
- 新模型/config标记 `actuator_model=g1_implicit_pd_v1`。旧DC世界模型不能直接resume/warm-start或作为新控制评估；CLI、Trainer、评估入口及最终验收均有类型检查。真实物理由PhysX解PD，想象奖励用可微PD力矩估算，不能声称是求解器的实际力矩。
- 七份G1参考动作仍在Git管理的assets/motions/g1；验证前逐一Git/SHA256通过。A1/G1后续新增动作继续追踪；X1动作另按用户要求复制后忽略。

## 当前进程与配置

- 无本项目训练/验证进程。隐式PD driver `2858666`、所有子进程均已退出，`logs/amp_g1/implicit_pd_validation.pipeline.json` 为complete，audit为passed。禁止重复启动同名队列。
- GPU仍有其他项目的冻结评估（`python -u logs/foot_impact_evaluation_20261104/evaluate_frozen.py`，此前观测PID2852429、显存约5895MiB）；其状态需恢复时重查，不终止未知进程。未把其他进程的占用记作本项目性能。
- 本轮仅接口短跑，不是收敛训练：32env，G1-Velocity随机8轮→同控制G1 AMP warm-start20轮→CLI resume到25轮；WM64×2、actor/critic64,32、WM/imag batch32、H4、buffer32/window4、collect2，D64,32/batch64/interval5/lr1e-5→2e-5/GP40；AMP70维两帧。实际命令/日志/作业PID见pipeline各jobs及每个run/config.json。
- 原生边界验证覆盖70维四帧、编译、混合RSI、普通reset、终止/超时、指令及历史；A1真实GPU接口回归完成。未改任务奖励/AMP混合/RSI配置，未启动权重网格或新正式训练。

## 最新与最佳checkpoint

- 最新：`logs/supermimic/2026-11-04_11-33-30_972624_g1_implicit_pd_smoke_resume/model_25.pt`。仅25轮恢复/评估接口模型，**不能作为行走候选**；初始20轮和model_0保留于对应smoke_initial目录。
- 新控制随机速度接口模型：`logs/supermimic/2026-11-04_11-31-57_568801_g1_implicit_pd_velocity_smoke/model_8.pt`；只验证同PD velocity→AMP模型转移。
- 新隐式PD下无已验收最佳/已收敛checkpoint。历史DC稳定运动来源 `logs/supermimic/2026-11-04_08-00-37_784295_g1_velocity_cold_start18432_to9000/model_9000.pt`（不能导入新PD世界模型）。
- 历史DC最新四帧70维 `logs/supermimic/2026-11-04_10-24-56_796290_g1_amp_warm9000_feet70_history4_diag/model_1000.pt`，七指令零摔但碎步，未通过walk。其数据仅作历史负结果。
- 已完成阶段归档 `checkpoints/go2_manager_converged.pt`、`checkpoints/a1_amp_converged.pt`；无需重训。

## 本轮验证与最近指标

- CPU75项通过：`logs/amp_g1/implicit_pd_cpu.log`；检查高速固定限矩、非饱和梯度、旧DC模型拒绝及原有回归。
- 原生GPU所有驱动为ImplicitActuator，PhysX Kp/Kd与配置一致；同状态Lab隐式力矩估算最大误差0。65reset/11摔倒/54超时/355指令切换；FK误差1.73e-6m、专家特征7.15e-7；编译返回max1.79e-7、actor梯度max2.91e-11；`logs/amp_g1/implicit_pd_integration.json`。
- 四网络四优化器20→25持续更新：actor16→21、critic36→46、WM20→25、D3→4；同PD速度到AMP热启动继承actor/WM、四优化器新建；旧DC CLI resume/warm-start按预期拒绝；`logs/amp_g1/implicit_pd_validation.audit.json`。
- 新PD短跑model25七指令829摔，风格距3.7483/3.7296；仅证明评估能运行，不能算收敛或控制修复改善碎步。`logs/amp_g1/implicit_pd_smoke_gait.json`。
- A1原生GPU回归passed，既有A1三个模型完整审计仍converged；旧G1 DC审计新增执行器类型拒绝通过。`logs/amp_g1/implicit_pd_a1_regression.json`、`implicit_pd_convergence_audit_regression.json`。

## 上游对照结论、已排除方案与待办

- 四方源码/实际checkpoint审计PID2851914结束、passed：固定legged_lab f33a189。上游 `R=.5*task+dt*style`，当前 `R=task+.5*dt*style`，同task下相对风格系数少4倍；当前全29DOF运动L1惩罚，上游仅指定关节且在平移命令<.06时生效。相同D score=1时当前stand/walk style=0/1，上游=1/1；CPU原方法探针已验证。
- 上述属于公式偏差证据，尚未证明哪项导致碎步。报告 `doc/G1_AMP_UPSTREAM_AUDIT_2026-11-04.md`，原始JSON `logs/amp_g1/go2_a1_g1_legged_lab_source_audit.json`（8f63846修复前）、`upstream_amp_command_gate_probe.json`。
- 历史DC严重RSI穿透/骨架映射错误未获支持；增加OU/节流D/真实TD/MPC/补动态拟合/特征61→64→70/四帧均未通过最终walk，不原样加码。Go2课程只使G1稳定移动；A1/G1同1m/s摆动约.175/.093s、净空20.77/12.36mm，RSI随机命令冲突约55%双方共有。
- AMP权重网格取消，RSI对齐尚未实现；上游counter==0不能直接照搬，本机Lab2.1回调看见1。下一阶段按上游奖励公式/关节范围/AMP混合补齐明确G1配置，做数值oracle与真实GPU验证后再建立新PD训练基线；不叠加盲调，不复用DC世界模型。
- 新PD正式规模须重新核查GPU容量/吞吐。历史18432env完整反传约23GiB，24576 OOM/32768 PhysX错误作废；不得将32env接口或预热吞吐当作大规模容量。
- G1完整速度、三连续点、加噪、录像与实际模型审计仍未通过；总目标保持进行中，X1未开始。

## 文档和下一条命令

本项思路/结果：`doc/G1_IMPLICIT_PD_RESTORE_2026-11-04.md`。长期范围GOAL、阶段PLAN、事件PROGRESS；最终门槛G1_CONVERGENCE，未降低。

```bash
cd /pfs/user/learning/amp_new
nvidia-smi
git rev-parse HEAD
cat logs/amp_g1/implicit_pd_validation.audit.json
sed -n '1,180p' doc/G1_AMP_UPSTREAM_AUDIT_2026-11-04.md
sed -n '35,137p' reference/legged_lab/source/legged_lab/legged_lab/tasks/locomotion/amp/config/g1/g1_amp_rough_env_cfg.py
```

下一开发步骤是按上游逐项列出G1奖励/AMP混合的配置与可微实现对照；先完成oracle验证，暂不启动新长训或RSI实验。

- 2026-11-04T11:59:18.721074+08:00 新G1奖励CPU82通过。上游原函数oracle首跑因undesired_contacts整数计数与浮点状态dtype检查停下，尚无数值不符证据；现保留原日志并在oracle记录原始dtype、转为对应状态dtype后重查，生产公式不改。新训练未启动。

- 2026-11-04T12:00:42.291681+08:00 上游16项奖励oracle passed，512样本/float64原方法最大项误差9.76e-13，task误差1.95e-14；9组dt/混合组合通过。CPU82通过，真实GPU验证driver PID2883115已启动，状态logs/amp_g1/upstream_reward_validation.pipeline.json；将覆盖新61维四帧及legacy、四网保存恢复/A1回归，非收敛训练。

- 2026-11-04T12:00:43.509499+08:00 上游奖励验证启动upstream_reward_integration，driver PID2883115、child PID2883231；命令/配置/日志见logs/amp_g1/upstream_reward_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:01:31.994041+08:00 上游奖励验证结束upstream_reward_integration，返回码0，预期拒绝=False，证据logs/amp_g1/upstream_reward_integration.log。

- 2026-11-04T12:01:31.999277+08:00 上游奖励验证启动upstream_reward_legacy_integration，driver PID2883115、child PID2884393；命令/配置/日志见logs/amp_g1/upstream_reward_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:02:08.351162+08:00 上游奖励验证结束upstream_reward_legacy_integration，返回码0，预期拒绝=False，证据logs/amp_g1/upstream_reward_legacy_integration.log。

- 2026-11-04T12:02:08.352958+08:00 上游奖励验证启动upstream_reward_velocity_smoke，driver PID2883115、child PID2885161；命令/配置/日志见logs/amp_g1/upstream_reward_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:02:47.730651+08:00 上游奖励验证结束upstream_reward_velocity_smoke，返回码0，预期拒绝=False，证据logs/amp_g1/upstream_reward_velocity_smoke.log。

- 2026-11-04T12:02:47.736142+08:00 上游奖励验证启动upstream_reward_smoke_initial，driver PID2883115、child PID2885969；命令/配置/日志见logs/amp_g1/upstream_reward_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:03:12.786376+08:00 新上游奖励原生GPU/编译已passed：8个手臂接触体映射、真实/想象混合与真实TD/reset/终止/命令/4帧均通过；原生PD末子步估算与端点代理、原生加速度与控制周期差分存在预期差异，已量化于upstream_reward_integration.json，不能宣称原生MDP完全等价。旧profile原生编译也passed；原driver继续四网短跑/恢复/A1与旧checkpoint回归，不启动新长训。

- 2026-11-04T12:03:30.178002+08:00 上游奖励验证结束upstream_reward_smoke_initial，返回码0，预期拒绝=False，证据logs/amp_g1/upstream_reward_smoke_initial.log。

- 2026-11-04T12:03:30.187934+08:00 上游奖励验证启动upstream_reward_smoke_resume，driver PID2883115、child PID2886721；命令/配置/日志见logs/amp_g1/upstream_reward_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:03:51.400153+08:00 上游奖励验证结束upstream_reward_smoke_resume，返回码0，预期拒绝=False，证据logs/amp_g1/upstream_reward_smoke_resume.log。

- 2026-11-04T12:03:51.407940+08:00 上游奖励验证启动upstream_reward_legacy_checkpoint_gait，driver PID2883115、child PID2887134；命令/配置/日志见logs/amp_g1/upstream_reward_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:04:33.819643+08:00 上游奖励验证结束upstream_reward_legacy_checkpoint_gait，返回码0，预期拒绝=False，证据logs/amp_g1/upstream_reward_legacy_checkpoint_gait.log。

- 2026-11-04T12:04:33.825163+08:00 上游奖励验证启动upstream_reward_a1_regression，driver PID2883115、child PID2887834；命令/配置/日志见logs/amp_g1/upstream_reward_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:05:16.229500+08:00 上游奖励验证结束upstream_reward_a1_regression，返回码0，预期拒绝=False，证据logs/amp_g1/upstream_reward_a1_regression.log。

- 2026-11-04T12:05:16.231357+08:00 上游奖励验证启动upstream_reward_smoke_gait，driver PID2883115、child PID2888712；命令/配置/日志见logs/amp_g1/upstream_reward_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T12:05:55.626008+08:00 上游奖励验证结束upstream_reward_smoke_gait，返回码0，预期拒绝=False，证据logs/amp_g1/upstream_reward_smoke_gait.log。

- 2026-11-04T12:05:55.626945+08:00 上游16项奖励/AMP混合CPU82/oracle/原生GPU/想象编译梯度/同控制velocity→AMP热启动/四网20→25/旧profile及checkpoint/A1回归/七指令评估接口均完成。短跑不证明walk收敛。
