# 目标、范围与完成条件

- 总目标：先实现Manager based收敛，再参考`reference/rl_amp`实现A1 AMP平地行走；禁止使用PPO，沿用/扩展SuperMimic模型学习路线。
- Manager阶段已完成：随机来源7000/8000/9000连续通过完整速度/步态，最终加噪、录像和实际checkpoint来源/更新审计通过；证据MANAGER_CONVERGENCE.md。A1 AMP已独立通过1000/2000/3000三检查点、最终加噪/录像及审计，证据AMP_CONVERGENCE.md；下一阶段G1平地walk；两者均禁止PPO，不能以Manager完成代替总目标完成。
- 用户已上传logs/videos并明确继续，撤销此前暂停约束；可以修复代码/依赖、运行实验和直接git commit。保留reference原状。
- 维持MANAGER_CONVERGENCE.md预先记录的全部标准：三个相隔1000迭代的检查点同时通过20固定+3随机种子的速度及7指令步态评估，最终加噪复测及录像；正式训练来源必须为Manager随机初始化。
- 训练实测并行数/batch/吞吐/显存，以策略质量为约束尽量提高RTX4090D 24GB利用率。用户未指定硬性时间/费用上限；按阶段评估，停止无效实验，不降低验收标准。
- 完成条件：真实采样及WM/actor/critic更新（AMP阶段还需discriminator及其优化器）、保存恢复和接口检查通过，模型/报告/视频保留，完整审计通过，代码及交接记录提交。短跑或旧Direct策略兼容不算收敛。

## AMP后续阶段
已完成`A1-AMP-Flat`，使用Isaac Lab原生A1和plane；参考reference/rl_amp的A1 walk数据、
相邻帧判别器及参考重置，AMP奖励接入SuperMimic世界模型和可微想象，不使用PPO。
训练指令vx=[0,1.5]、vy=[-.3,.3]、yaw=[-1,1]，10%站立，仅平地行走。
实际使用的A1参考动作复制至受本项目Git管理的`assets/motions/a1/`并默认从此加载；
保留来源、许可及SHA256，训练/评估无需依赖未跟踪reference目录。

正式训练前锁定的独立标准见[AMP_CONVERGENCE.md](AMP_CONVERGENCE.md)：
12固定指令与3随机种子的速度评估全部零摔倒；7指令步态评估；
1/1.5m/s的留出专家风格距离相对A1初始模型均改善至少10%；
连续三个相隔1000迭代的A1检查点全部通过，最终加噪复测和侧面录像。
各项RMSE、步频、腾空、离地及足滑阈值、数据split/SHA256与来源审计以该文档为准。
Manager模型可用于明确记录的跨机器人热启动，不能替代A1独立结果。

## G1后续阶段（用户明确新增）
A1 AMP行走实现并独立评估后，参考`reference/legged_lab`实现G1 AMP平地walk。
只训练walk，不训练run、其他动作或粗糙地形；继续SuperMimic世界模型/可微想象路线，
全阶段禁止PPO。先核对本地G1资产和walk运动数据，再在训练前记录指令范围、步行/
速度/稳定性指标及完成条件。实际使用的G1参考动作同样复制到本项目Git管理的目录，
保留来源/许可/SHA256及划分，训练/评估默认读取项目内副本并随实现提交。
Manager、A1 AMP、G1 AMP各阶段完成时分别git commit。
预算无新增硬上限，继续按阶段评估，停止无效实验，保留模型、报告和视频。

## 范围变更（2026-11-04）
用户明确将Go2 AMP改为A1 AMP，并要求更新goal。当前完整目标为：已完成Manager收敛 → 已完成A1 AMP平地行走 → 参考reference/legged_lab实现G1 AMP平地walk；全部禁用PPO，各阶段git提交。Go2 AMP不再属于目标。
