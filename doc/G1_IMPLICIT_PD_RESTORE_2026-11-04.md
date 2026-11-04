# G1 恢复上游隐式 PD

## 问题与决定

用户明确要求G1不用DC模型或转速导致的力矩上限衰减。`reference/legged_lab` f33a189的G1使用`ImplicitActuatorCfg`；本项目最初提交5c02bf2改为`DCMotorCfg`，注释理由仅为真实/想象共用显式公式，没有同条件实验支持该动力学修改。

恢复上游隐式PD，固定分组力矩上限88/139/25/5 Nm；保留上游关节速度上限32/20/37/22 rad/s、Kp/Kd、armature=.01、控制周期和动作尺度。速度上限是PhysX独立关节约束，不再用于计算可用力矩的斜线包络。仅修控制，不同时修改奖励权重、AMP混合、RSI、参考数据或网络。

用户补充允许Isaac Lab `IdealPDActuator`：它显式计算PD力矩并做固定限矩，也满足不用DC的要求。当前优先完成上游隐式PD验证；尚无证据证明隐式PD有缺陷，不因接口便利而再次改动力学。若后续比较IdealPD，使用独立控制类型/新世界模型谱系。

## 实现与边界

- 真实仿真：G1所有驱动改成`ImplicitActuatorCfg`，位置目标交给PhysX PD求解。
- 可微奖励：G1力矩估算为`clip(Kp*(q_target-q)-Kd*qd, -effort, effort)`，不含转速降额。阻尼仍影响PD需求力矩。此公式匹配Isaac Lab同状态的隐式驱动力矩估算；不是PhysX求解器实际力矩，不能把估算精确一致扩大为真实动力学一致。世界模型直接学习新隐式PD下的状态转移。
- 旧模型隔离：新G1 checkpoint及config记录`actuator_model=g1_implicit_pd_v1`；旧G1模型缺标记，历史默认解释为DC。训练CLI/Trainer resume及warm-start、独立评估均拒绝旧类型，避免把已学DC世界模型作为新控制的有效动力学。历史模型和原始证据保留；不新增DC兼容开关。
- Go2/A1已验收结果保留。G1仍只做walk和平地，禁PPO，成功后才进入X1。G1参考动作仍由项目Git管理。

源码依据：`reference/legged_lab/source/legged_lab/legged_lab/assets/unitree.py`；本机Isaac Lab 2.1 `actuators/actuator_pd.py` 的`ImplicitActuator.compute`。GitHub核对记录`logs/amp_g1/implicit_pd_github_evidence_local.json`（开发机直连超时后，本地主机成功读取GitHub v2.1.0源码）。

## 验证计划与结果

全部接口验证完成（2026-11-04），pipeline为complete，driver2858666及子进程均退出：

- CPU75项通过（`logs/amp_g1/implicit_pd_cpu.log`），含高速固定限矩/非饱和梯度/旧DC模型拒绝。
- 真实GPU所有驱动为ImplicitActuator，PhysX Kp/Kd精确对应配置；同状态与Lab自身隐式力矩估算最大误差0。65次reset、11摔倒、54超时、355命令切换均被覆盖；四帧70维下想象编译返回误差1.79e-7、actor梯度误差2.91e-11。报告`logs/amp_g1/implicit_pd_integration.json`。
- 新PD随机velocity8轮→同PD AMP20轮热启动的actor/WM精确继承、四优化器为空；20→25轮CLI恢复后actor16→21、critic36→46、WM20→25、D3→4，模型/优化器有限且持续更新。旧DC CLI resume/warm-start按预期拒绝。证据`logs/amp_g1/implicit_pd_validation.audit.json`，配置和命令见同前缀pipeline.json。
- A1原生GPU回归通过，已有A1三个最终模型完整审计仍converged；最终G1审计新增执行器类型核查，旧DC初始及评估模型按预期拒绝。证据`logs/amp_g1/implicit_pd_a1_regression.json`、`implicit_pd_convergence_audit_regression.json`。
- 新PD model25七指令评估829摔，留出风格距3.7483/3.7296；这是随机短跑的接口测试，**不能证明行走或碎步改善**。最新模型`logs/supermimic/2026-11-04_11-33-30_972624_g1_implicit_pd_smoke_resume/model_25.pt`。

本轮32env用于接口验证，不据此判断18432env容量或训练效率。验证期间有其他项目冻结评估占用约5.9GiB，未终止或干预，pipeline采样的整卡显存不等同本项目净占用。尚未启动新收敛训练；修复接口不代表收敛。上游奖励/AMP组合/关节集合/RSI差异见`doc/G1_AMP_UPSTREAM_AUDIT_2026-11-04.md`；先对齐和验证，再建立新PD训练基线，最终G1/X1标准保持。
