# 当前状态与恢复入口

核实时间：2026-11-04T11:40:18+08:00。权威运行目录 `/pfs/user/learning/amp_new`；SSH `ssh -p 9205 root@118.196.87.69`。恢复先读GOAL/PLAN/本文件，核对实际PID/GPU和产物，不重启已完成队列。此前完整状态见 `docs/history/STATUS_2026-11-04_before_implicit_pd.md`。

## 当前版本、范围与决定

- 源码核对基线HEAD `8f63846a6571f7a434c69fd1b81a6afe040c9cd7`；本次已验证控制修复待提交，提交后补准确HEAD。运行 `git rev-parse HEAD; git status --short` 核实，保留既有未跟踪reference/exploration/dynamics诊断和无关文档。
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
