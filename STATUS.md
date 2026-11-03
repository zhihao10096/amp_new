# 当前状态与恢复入口

## 目标/版本
- 总目标：先Manager完整收敛，再参考reference/rl_amp实现Go2 AMP行走；禁止PPO。当前专注Manager静止策略。
- 开发机目录/pfs/user/learning/amp_new；HEAD8029aaa。训练代码已提交奖励调度、PhysX扩容及调度恢复；当前未提交诊断脚本dynamics_eval.py/explore_eval.py、纯Torch探索生成器exploration.py及测试test_exploration.py。
- reference/为用户未跟踪目录，保持原状。CPU28项通过；当前Actor接口仍225维，无phase输入。

## 当前实验
- PID2378486，32env实际更新保存烟测，配置reward-curriculum4/12；日志logs/manager_4090/baseline_reward_smoke.log，命令见baseline_reward_smoke.process.json。
- GPU接口回归PASS：80reset/1强制翻倒/144指令切换，真实/想象奖励初中末一致。CPU29项通过。
- 旧周期探索扫描已结束，112组结果存trot_phase_scan.json，未用于训练。当前优先修正初期奖励与可收敛基线的数学差异。
- 下一条命令：`tail -n 5 logs/manager_4090/baseline_reward_smoke.log`；完成后验证恢复/评估，提交修复，再从Manager随机初始化启动受控训练。

## 最新/最佳checkpoint与最近结果
- 最新有效：logs/supermimic/2026-11-03_22-28-23_077303_manager4090_curriculum_fixed/model_2500.pt；运行代码917072e，24576env/collect1/buffer128/WM4096×4/imag4096/horizon32，初期弱正则未开始增加最终约束（start3000/end5000）。
- 从原Manager model1000（actor与model0相同、随机来源）继续至2500结束，用时648秒，actor更新阶段约2.2迭代/s、真实采样5.5万/s，显存约16.1GB；全日志零PhysX/CUDA错误。日志curriculum_fixed.log/.gpu.csv。
- 7指令×4env×8秒诊断：model1500/2000前进几乎0；model2500前进1m/s实际vx约.00075，转弯yaw约.104/目标.5（curriculum_gait2500.json）。最佳Manager尚无，尚未证明收敛。
- 原始Manager初始/恢复证据：logs/supermimic/2026-11-03_20-51-11_991689_manager_from_scratch/model_0.pt、model_1000.pt；原model2000/2025同目录仍在。
- 旧Direct最佳步态：logs/supermimic/2026-11-03_20-07-39_561455_gait_slip_refinement/model_1500.pt；logs/videos均已上传，旧结果只作历史基线。

## 已完成验证与已排除
- CPU28项；16env和24576env GPU接口/奖励调度一致，32env实际WM/actor/critic更新、保存/恢复/评估、默认继承调度CLI均PASS。报告均在logs/manager_4090/。
- 已修复PhysX patch默认163840不足，现至少32×envs（24576为786432）；大规模回归122880reset/221184指令切换零物理错误。原16k/24k吞吐测试和首次curriculum_train.log因初始化溢出作废，不复用模型/吞吐结论。
- 弱正则训练至2500仍未解决前进，排除“仅调低步态惩罚已成功”判断；不盲目增加最终权重或宣称收敛。
- dynamics2000.json：低速轨迹线速度RMSE单步.0032、32步.0132m/s；这不足以检验运动区间模型，接触归一化误差约1。下一关注运动覆盖、闭环预测及探索。
- 初始周期探索扫描（trot_exploration_scan.json）可产生-.3～-.65m/s后退，但零可用前进组；尚未用于训练。实际足端Jacobian（kinematics.json）确认thigh对x为负、calf对z为负，几何符号基本符合，下一检验执行器/接触导致的抬腿相位偏差。
- 独立SuperMimic实现通常由参考重置获得运动状态；仅作为数据覆盖启发，不移植PPO。检索结果supermimic_research.json。

## 环境/后续
- RTX4090D 24564MiB，Python3.10.12/Torch2.5.1+cu124/Lab2.1/Sim4.5，项目editable/pytest/mediapy已安装；仿真设OMNI_KIT_ACCEPT_EULA=YES/OMNI_KIT_ALLOW_ROOT=1并清除PYTHONPATH。无rg。
- 当前剩余：验证运动探索，改善世界模型训练分布，再测随机actor的真实速度学习；完成最终步态奖励及三个1000间隔完整验收/加噪/录像后，再实现AMP。
- AMP预研：reference/rl_amp有A1的61维motion、43维AMP特征和LSGAN判别器；后续需要Go2关节排序、足端几何适配并接入SuperMimic可微奖励，禁止PPO。

验收标准MANAGER_CONVERGENCE.md；阶段计划PLAN.md；关键事件同步PROGRESS.md。

## 用户提供可收敛基线（最新优先级）
- 用户明确d9eee9b3f248e5300e636c433255db2c1c3e086a可收敛；立即转为对照该版本与Manager/后续改动的因果差异，优先复用已验证方法。
- 当前无正式训练；周期探索及其Trainer接入尚未用于正式训练。训练接入修改只在本地/tmp/amp_new_edit，远端仍为已提交核心训练器；远端新增诊断/探索生成器未提交。
- 下一条命令：git show d9eee9b3:README.md，检查该提交源码树及训练/状态/奖励实现。保留当前checkpoint，不回滚用户文件。

- 烟测完成，model20=logs/supermimic/2026-11-03_23-10-31_076350_baseline_reward_smoke/model_20.pt，真实WM/actor/critic更新及保存成功；恢复CLI验证PID2379347（20→24，省略调度参数），日志logs/manager_4090/baseline_reward_resume.log。

- 恢复验证PASS：model24三网络/优化器均更新且有限，CLI继承4/12调度和最终公式；开始32env/2秒评估PID2380247，日志logs/manager_4090/baseline_reward_eval.log；证据baseline_reward_regression.json。
