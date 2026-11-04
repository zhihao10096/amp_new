# G1 平地walk终止接口对齐

## 问题和假设

固定上游legged_lab f33a189的flat配置使用height<.2或torso_link/pelvis接触（历史力范数>1N）终止，不用倾角阈值。本项目仍height<.5或60°，且83维世界模型状态只有手臂接触计数，不能直接表达躯干碰地。接触终止必须在真实采样、终止前状态、想象软终止、真实TD和独立评估使用一致输入。

这属于已确认的接口差异，尚无它导致碎步的因果证据。不改变已对齐的16项奖励、AMP参数、数据、RSI、控制或训练算法。

## 实现决定

G1状态追加独立躯干接触标量，原83维字段顺序保留，新增state_schema元数据；actor观测和AMP61/64/70特征不变，WM84维/critic125维。上游walk使用height<.2或独立躯干接触，想象使用相同字段的连续松弛；历史profile保留高度/倾角判定。旧83维WM不自动补零迁移或warm-start，新schema同机器人速度→AMP可继承。历史隐式PDactor仍可通过旧profile独立评估；DC仍拒绝。

## 验证计划

CPU边界/手臂与躯干隔离/软判定有限梯度/旧schema拒绝/roundtrip；真实GPU与上游illegal_contact及height原方法对照、实际碰地/预reset终止状态、超时/指令/历史、编译回报和actor梯度；四网更新/保存CLI恢复、同schema速度→AMP、旧checkpointactor评估/A1回归。动作Git/SHA256和固定GitHub源码逐一核验。

证据入口：logs/amp_g1/g1_boundary_github_evidence.json。验证结束后补结论及日志路径，不复制原始日志。G1/X1总体目标和正式验收不变，短跑不能证明walk收敛。

## 验证结果

全部完成，`logs/amp_g1/contact_termination_validation.pipeline.json`为complete，driver2896882和全部子进程已退出，汇总`contact_termination_validation.audit.json`为passed。CPU88项通过（contact_termination_cpu_r2.log）；新原生GPU1851次与Lab原始height/illegal_contact方法一致，65reset/6摔倒/59超时、含1次实际躯干碰地；真实TD和编译返回/actor梯度通过（返回5.96e-8/梯度3.73e-9）。证据contact_termination_integration.json。

新schema四网20→25持续更新：actor16→21、critic36→46、WM20→25、D3→4；同schema速度8轮→AMP的actor/WM精确继承、四优化器重建，CLI继承84维/profile/61维四帧；旧83维resume和warm-start在启动仿真前均按预期拒绝。旧profile、旧83维actor评估、A1真实GPU回归均通过，见pipeline各job日志/JSON及audit。

新25轮随机接口模型七指令737摔，留出风格距4.18733/4.21171；仅证明评估可运行，终止定义变化后的计数不能与旧模型比较为收益。最新模型logs/supermimic/2026-11-04_12-21-14_719010_g1_contact_termination_smoke_resume/model_25.pt，不是行走候选。

首轮CPU86过2失败源于测试夹具83/124维未迁移及0.3m软高度尾部断言过严，修正后全88通过；首driver2896001在hash清单错误路径处退出，未启动任何GPU子作业，修正路径后原状态文件不存在且PID已退出才启动2896882。失败证据均保留，未修改生产公式来迎合测试。

下一阶段：RSI对齐默认关闭并独立验证；完善独立评估的原高度/倾角越界记录，确保训练终止对齐不放宽既有验收。新PD容量/吞吐和正式随机训练尚未开始，G1/X1目标仍未完成。
