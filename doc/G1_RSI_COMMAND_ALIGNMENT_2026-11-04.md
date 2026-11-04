# G1 RSI同帧命令与独立验收

## 问题和依据

上游legged_lab在参考状态重置时读取相同参考帧并对齐机体系速度。当前参考状态与随机命令独立，A1/G1约55%的速度冲突为双方共有现象，不能单独证明G1失败原因；作为明确实现差异，做可选、独立验证，不盲调AMP权重。

GitHub四份固定f33a189源码与本地一致：logs/amp_g1/g1_boundary_github_evidence.json。执行本机Lab2.1原始CommandTerm.reset/_resample，回调counter在reset/timed实际为1/2，上游counter==0会漏掉重置：g1_rsi_counter_oracle.json。事件在命令管理器reset前执行，因此使用同帧一次性标记适配版本。

## 实现和边界

- amp_reset_command_alignment默认False，仅G1 AMP可开；由reset_robot保存本次同一帧的线/角速度，转换机体系并逐轴裁剪到vx0–1.2/vy±.3/yaw±.8，不引入run命令。只对本次确实用参考状态的环境生效，标记一次消费。
- 普通reset及回合中定时重采样仍均匀随机，固定命令优先；评估强制关闭参考reset和对齐，仍从普通站立开始。CLI/config/checkpoint记录开关，resume自动继承，并识别显式--no-amp-reset-command-alignment。
- 保留50%混合参考重置、不增加height_offset（既有负对照不支持+.1m）。本项目保持直接yaw-rate命令，不移植上游heading控制器及其全局heading状态；因此复现的是同帧速度对齐，不声称完整上游命令MDP等价。
- 训练终止已由eee92bb对齐上游；独立速度/步态评估保留原height<.5或tilt>60°越界为fall，并与原生躯干/低高度终止取并集，零fall门槛不放宽。报告新增fall_definition，验收器拒绝缺此定义的旧报告；单个越界帧即足以使零fall失败，计数不是可比的跌倒事件数量。
- 最终动作审计从正式model_0配置重建实际schema/历史长度，并逐项核对项目内副本metadata；此前固定两帧会误拒四帧，修复不改变独立相邻对风格指标/数据划分/SHA256或验收阈值。

## 验证计划

CPU同帧旋转/裁剪、开关/配置、原验收越界和四帧审计；真实GPU混合reset后的命令对照实际刚写入的机器人速度、标记消费、普通/定时/固定命令、reset/预终止状态/历史、编译回报/actor梯度；四网更新/CLI恢复含显式关闭；默认关闭、历史actor和A1回归；真实七指令及速度评估接口并核对fall_definition。证据结束后补结论，不把短跑当作walk收敛。

## 验证结果

全部结束（2026-11-04T12:38:18+08:00）；pipeline `logs/amp_g1/rsi_alignment_validation.pipeline.json`为complete，driver2907230及所有子进程已退出，audit为passed。

- CPU92通过，rsi_alignment_cpu.log。真实GPU同帧检查59次参考reset/70次普通reset，命令与实际刚写入机器人机体系速度最大误差4.17e-7；one-shot/定时随机/fixed/终止前快照/历史和编译通过，返回误差5.96e-8、actor梯度3.73e-9（rsi_alignment_integration.json）。默认关闭的新profile和旧profile均通过原生GPU/编译。
- 同schema速度→AMP的actor/WM精确继承、优化器重建；CLI20→25自动继承开关True，25→30显式--no保持False，四网络持续更新。optimizer steps 20/25/30分别actor16/21/26、critic36/46/56、WM20/25/30、D3/4/5。模型/配置/计数与所有命令见rsi_alignment_validation.audit.json/pipeline.json。
- 独立七指令及短速度接口报告均带fall_definition=native_or_height05_tilt60_v1；随机25轮模型在20s七指令累计6258个越界/原生终止采样，风格距4.18055/4.20943。只证明严格评估可执行，无walk收益或收敛结论；计数不是独立跌倒事件数，不与历史计数对比。
- 历史83维actor、A1原生GPU回归通过；A1实际三个收敛checkpoint完整审计仍converged，旧DC/83维正式审计被明确拒绝（rsi_alignment_convergence_audit_regression.json）。四帧动作metadata按配置重建且仍核对项目内副本，CPU反例通过；动作Git/SHA256复核通过。

下一阶段先测试完整四网/actor更新的16384与18432环境容量/吞吐，必要且有显存余量才测试20480，OOM/PhysX错误结果作废；使用表现最好的安全规模从全新G1 model_0启动1000轮，再独立评估。只建立对齐后的新基线，不把profile模型或旧DC权重作为来源。

仍有明确实现差异：想象力矩/加速度是端点/控制周期代理、接触计时为控制周期松弛；直接yaw-rate而非全局heading控制。判别器保留本项目512/256 LeakyReLU架构及统一decay1e-4（上游1024/512 ELU、输出层decay.1），本轮不改D以避免叠加变量；lr1e-5/GP40/interval5与上游flat一致。这些是后续候选，不把源码对齐描述为完整上游MDP/优化器复现。
