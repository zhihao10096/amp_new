# 目标、范围与完成条件

- 总目标：先实现Manager based收敛，再参考`reference/rl_amp`实现Go2 AMP行走；禁止使用PPO，沿用/扩展SuperMimic模型学习路线。
- Manager阶段已完成：随机来源7000/8000/9000连续通过完整速度/步态，最终加噪、录像和实际checkpoint来源/更新审计通过；证据MANAGER_CONVERGENCE.md。后续目标为Go2 AMP，再G1平地walk，本轮尚未启动AMP训练。
- 用户已上传logs/videos并明确继续，撤销此前暂停约束；可以修复代码/依赖、运行实验和直接git commit。保留reference原状。
- 维持MANAGER_CONVERGENCE.md预先记录的全部标准：三个相隔1000迭代的检查点同时通过20固定+3随机种子的速度及7指令步态评估，最终加噪复测及录像；正式训练来源必须为Manager随机初始化。
- 训练实测并行数/batch/吞吐/显存，以策略质量为约束尽量提高RTX4090D 24GB利用率。用户未指定硬性时间/费用上限；按阶段评估，停止无效实验，不降低验收标准。
- 完成条件：真实采样及WM/actor/critic更新、保存恢复和接口检查通过，模型/报告/视频保留，完整审计通过，代码及交接记录提交。短跑或旧Direct策略兼容不算收敛。

## AMP后续阶段
Manager验收完成后核对reference/rl_amp的判别器、运动库、重置和AMP奖励接口；明确Go2动作数据，接入可微奖励/世界模型训练路线，并独立评估行走质量。保持不用PPO。

## G1后续阶段（用户明确新增）
Go2 AMP行走实现并独立评估后，参考`reference/legged_lab`实现G1 AMP平地walk。
只训练walk，不训练run、其他动作或粗糙地形；继续SuperMimic世界模型/可微想象路线，
全阶段禁止PPO。先核对本地G1资产和walk运动数据，再在训练前记录指令范围、步行/
速度/稳定性指标及完成条件。Manager、Go2 AMP、G1 AMP各阶段完成时分别git commit。
预算无新增硬上限，继续按阶段评估，停止无效实验，保留模型、报告和视频。
