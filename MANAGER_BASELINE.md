# Manager 与可收敛基线的对照

用户确认 `d9eee9b3f248e5300e636c433255db2c1c3e086a` 可收敛。
该版本使用 mjlab/MuJoCo 追逐任务；中间的 `4ca881b`/`a446d02` 则有
Isaac Lab Direct 速度跟踪收敛记录，因此同时比较两条基线。

| 项目 | 原始 d9eee9b3 | Direct 速度阶段 | 当前 Manager |
| --- | --- | --- | --- |
| 学习路线 | 多步世界模型、可微想象、TD(λ) | 相同 | 相同，无 PPO |
| 关节偏移惩罚 | 平方和 | 平方和，权重 -0.05 | 最终范数，权重 -0.7，站立乘 5 |
| 世界模型 | 机身、关节、足端、环境上下文 | 初期 34 维 | 63 维，含足端和接触 |
| 数据覆盖 | OU、接触优先采样、稀有事件存档 | 高斯和 OU | 高斯和 OU |
| 奖励 | 追逐方向速度等 | 速度指令跟踪 | 跟踪加步态约束 |
| 初始化/阶段 | 多阶段任务训练 | 先速度，后步态 | 要求随机来源及完整独立验收 |

Manager 迁移 `b6a1b7a..24046e2` 没有改动世界模型损失或 actor 目标；
原生历史填充、动作裁剪、终止前状态和真实/想象接口均有 GPU 回归覆盖。
这不等于证明 Manager 已收敛。

## 已定位的奖励差异与修正

此前奖励课程只插值权重，未插值关节惩罚公式，初期也保留了非足接触惩罚。
在每关节偏移 0.01 rad 时，平方和为 0.0012，原范数为 0.03464，
站立时为 0.1732；相同权重下相差约 29/144 倍。
因此此前“弱正则”没有还原可收敛速度任务，不能据其失败排除初期奖励问题。

现使初期关节项使用平方和，随课程平滑过渡至最终范数，并将初期非足接触权重置零。
真实 reward manager 和想象共享当期公式及权重；checkpoint 保留最终任务配置，
已有检查点缺省使用最终公式，最终奖励及验收阈值沿用原定标准。
CPU 检查覆盖小偏移、站立/运动命令及状态梯度与 legacy 公式的一致性。

这是一处已确认的实现差异；是否足以解决静止策略，需要新实验回答。
新的正式来源从 Manager 随机初始化，不使用 Direct 策略或周期探索。
按检查点真实速度跟踪决定是否继续，再进入最终步态阶段。

## 证据与恢复

- 原始代码：`git show d9eee9b3:go2_supermimic/supermimic/imagine.py`。
- Direct 配置：`logs/supermimic/2026-11-03_18-48-14_562457_velocity_convergence/config.json`。
- 原始课程结果：`logs/manager_4090/curriculum_gait2500.json`。
- 本轮 GPU 回归：`logs/manager_4090/baseline_reward_integration.log`。
- 更新/恢复验证：`logs/manager_4090/baseline_reward_{smoke,resume}.log`。
- 尝试检索官方 GitHub 奖励源码遇开发机网络超时；记录
  `logs/manager_4090/baseline_reward_research.json`。当前修正依据仓库内可核对的历史源码。
- 最新训练、checkpoint、PID 和下一条命令始终见 [STATUS.md](STATUS.md)。

## 想象执行效率

原始d9eee9b3支持编译想象单步；现增加可选 `--compile-imagination`，默认关闭，
通过 `--matmul-precision highest` 使用FP32。CPU30项及CUDA返回/梯度一致性通过，
真实32env更新、课程切换、保存及恢复20→24通过。TF32严格对比未通过，
FP32 actor梯度最大绝对差4.84e-8。128batch/H8微基准暖运行.0753→.0147秒，
这不是完整训练加速比，完整吞吐及更大并行数仍须实测。
证据 `logs/manager_4090/compiled_imagination_{fp32.json,smoke.log,resume.log}`。

## 当前验证结论

新Manager随机来源的model3000已通过完整速度覆盖：20固定指令及42/123/2026
三个随机种子，随机稳态平均RMSE(.0566,.0701,.0561)，各组阈值全部通过。
7指令速度均达标且零摔倒，但1m/s步频6.087Hz、腾空.0422秒、足滑.2857m/s，
尚未满足最终步态要求。报告 `logs/manager_4090/baseline_squared_{velocity,gait}3000.json`。
该结果来自还原初期奖励、随机初始化和已记录的训练/执行配置；没有做单因素消融，
不把改善全部归因于某一项改动。正式训练从未使用周期探索、外部策略或优先采样。

新增编译路径将课程系数保存在GPU张量中，课程期间复用编译图；
CPU31项验证5种比例的返回/梯度及编译图复用，CUDA中间比例梯度最大差2.98e-8。
真实更新/保存恢复证据为 `logs/manager_4090/dynamic_reward_*.log`。
3000→5000完成最终任务课程，6000仅快走足滑未过后保持相同任务继续；7000/8000/9000均完整通过速度/步态，9000加噪也通过，数值来源审计converged=true。完整结果与视觉检查状态见MANAGER_CONVERGENCE.md、STATUS.md。
