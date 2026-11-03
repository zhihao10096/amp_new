# 进度与恢复入口

恢复先读 [STATUS.md](STATUS.md) 并核实Git、进程和产物；目标见 [GOAL.md](GOAL.md)，阶段计划见 [PLAN.md](PLAN.md)。

## 已完成：Manager随机来源收敛（2026-11-04）
- 7000/8000/9000相隔1000迭代，完整速度和7指令步态全部通过；最终9000训练观测噪声复测通过。四轮完整速度评估合计1280机器人分钟零摔倒，三轮步态也零摔倒。
- 实际checkpoint来源/任务/最终奖励/三网络与优化器更新/有限性/SHA256审计通过，converged=true、failures=[]；证据 [MANAGER_CONVERGENCE.md](MANAGER_CONVERGENCE.md)。
- 最终模型checkpoints/go2_manager_converged.pt；9000随机稳态RMSE .04054/.04416/.03648，加噪 .04285/.04726/.05306；1/1.5m/s足滑 .07295/.11357，腾空均.1312s，站立步频0。
- videos/manager_gait_comparison.mp4为左3000/右9000的侧面对照，manager_fast_side.mp4快走、manager_stand.mp4站立；录像均零摔倒，侧面抽帧检查通过。相机副本和命令保存在logs/manager_4090，不改变训练代码。
- 所有项目训练/评估/录像进程结束，监控2381346停止，核实记录logs/manager_4090/final_process_check.json。当前阶段结果提交并建立本地标签manager-converged-20261104；AMP未启动。

## 保留的关键结论
- 用户确认d9eee9b3可收敛；对照该版本和Direct中间基线，发现初期弱正则没有还原平方关节惩罚。修正并随机重训后学会运动，再渐进最终奖励；未经单因素消融，不把改善全部归因于单项。见 [MANAGER_BASELINE.md](MANAGER_BASELINE.md)。
- 初期静止、单纯弱权重和无效溢出轮已排除；周期探索、外部策略、PPO和优先采样未用于正式训练。reference/保持用户原状。
- PhysX patch按32×env扩容；旧16k/24k溢出性能作废。真实完整更新对照后采用32k/collect1，FP32编译约12.5万真实转移/s、显存约21.8GB，TF32严格比较未过故不用。
- CPU31项及原生GPU接口、三网络更新、保存恢复、动态课程/编译梯度一致性此前通过；后续没有训练源码改动。AGENTS保持长期规则和文档入口。

## 下一阶段
- 按GOAL/PLAN，Manager后参考reference/rl_amp接入A1 AMP平地行走，再参考reference/legged_lab做G1平地walk，全程不用PPO。当前任务已完成，尚未启动AMP实验。
- 下一条恢复命令及最新/最佳checkpoint、版本、运行目录和配置见STATUS，避免重复启动。

历史事件及日志依据：[本轮完整过程](docs/history/PROGRESS_2026-11-04_manager.md)、[更早归档](docs/history/PROGRESS_2026-11-03.md)。

## 进入Go2 AMP平地阶段
- 恢复核实HEAD b1f59eb，前阶段记录的训练/评估/监控均已退出，GPU空闲；Manager验收和模型保留，不重复训练。
- 用户明确Go2 AMP也仅平地；G1后续仅平地walk，禁run和其它动作。全程禁止PPO，按阶段提交，总目标仍未完成。
- 已核对reference/rl_amp：43维状态（绝对关节角、局部足端、机体系线/角速度、关节速度、高度）相邻帧LSGAN与专家零中心梯度惩罚。现有63维WM状态足够，拟接入同一纯Torch特征和冻结判别器可微奖励，actor继续世界模型反传，不使用参考PPO训练器。
- A1运动数据为FL/FR/RL/RR逐腿顺序，当前IsaacLab关节顺序及Go2几何必须实测；拟用Go2 FK重算足端和高度，避免A1/Go2几何混入判别标签。先GPU探测，再锁定数据/验收，尚未启动AMP训练。

## 用户范围变更：A1替代Go2 AMP
- 按用户最新要求，将后续Go2 AMP改为A1 AMP平地行走，G1仅平地walk和全程禁PPO保持；已更新GOAL.md和PLAN.md，不能把A1阶段省略或以Go2结果代替。
- 尚未启动Go2几何探测或AMP实验，只有日志目录中的探测脚本草稿；无需停止运行作业。当前HEAD仍b1f59eb，GPU空闲，无最新/最佳AMP checkpoint。
- A1原生IsaacLab资产与reference/rl_amp的mocap_motions_a1对应，优先验证A1 Manager环境、关节顺序和FK，而非继续Go2几何适配。AMP判别器/纯Torch特征与世界模型可微想象方案继续适用。
- 下一条命令：核对UNITREE_A1_CFG、参考A1 URDF与运动库，随后建立A1-AMP-Flat配置和GPU接口验证。
