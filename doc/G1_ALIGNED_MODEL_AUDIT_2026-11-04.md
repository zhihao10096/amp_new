# G1 新 PD 基线的冻结模型审计与训练预算验证

## 问题和假设

新隐式 PD / 上游奖励 / state84 / 四帧 AMP 的 1000 点未通过独立行走。总迭代不等于策略更新：300 轮 WM 预热及 200 轮 critic 预热，actor 只更新 500 次，且学习率逐渐抬升。需区分训练预算不足与新动力学的想象失真；不能沿用历史 DC 模型的诊断结论，也不能据单个早期点认定隐式 PD 错误。

## 方法与边界

新增 `scripts/g1_model_audit.py`，冻结 actor / WM / critic / D，不训练。128 环境、固定 0.6 m/s，普通与参考起点分别运行 64 步；使用当前隐式 PD、state84、61 维四帧 AMP、`.5task+dtstyle` 混合和物理 AMP 历史。开环使用真实动作检验 1/4/8/16/32/64 步预测，保留终止前 next state，排除跨 reset 窗口；闭环对比首回合折扣回报与 critic bootstrap，并检查 32 步 actor 梯度、动作及 WM 输入裁剪。

原生训练终止与严格行走评估门槛不同，本工具不能替代正式验收。Bootstrap 不是完整回合 Monte Carlo；模型终止后的外推高度不能直接解释为存活机器人的高度。有限梯度不证明物理方向正确，均值接近不保证逐样本准确。

## 结果

| 指标 | 普通起点 | 参考起点 |
|---|---:|---:|
| 32 步 actor 梯度 norm | 10.1304 | 4.2610 |
| 动作触及 ±4 比例 | 0 | 0 |
| 实际 WM 输入裁剪比例 | .000006 | .000380 |
| 32 步实际 bootstrap 均值 | 1.09807 | -.32111 |
| 32 步想象 bootstrap 均值 | 1.09826 | -.28897 |
| 32 步 bootstrap 差异 RMSE | .31946 | .17388 |
| 32 步线速度开环 RMSE | .04120 | .20875 |
| 64 步线速度开环 RMSE | .13758 | .70328 |

动作未饱和，未发现断梯度或大面积输入裁剪；32 步均值回报没有明显虚高。参考状态多步预测仍有误差，物理回报梯度方向尚未检验，不能断言 WM 已排除。64 步误差较大，当前策略优化使用 32 步。

原始结果 `logs/amp_g1/aligned_model_audit1000.json`；真实进程生命周期、命令见同前缀 `.pipeline.json`，日志为 `.log`。受测 run 为 `logs/supermimic/2026-11-04_12-45-04_890456_g1_aligned_formal_r1`。审计 returncode=0 / complete，原 driver2934344 及 child 已退出。

## 依据与下一项验证

本项目 Manager 的随机来源曾在 3000 才通过完整速度，最终完整步态在 7000/8000/9000 通过，见 `MANAGER_BASELINE.md`。新的 G1 控制与奖励不能只凭 500 次 actor 更新排除。

GitHub 检索找到独立实现 [SuperMimic-Reproduced](https://github.com/CuboiLeo/SuperMimic-Reproduced)，其 README 采用 H32 / BPTT / 生存加权 / TD(λ)，报告的训练预算远高于 1000 次。它是 MuJoCo 上的参考跟踪任务，不是本项目的 Isaac Lab AMP 速度任务；其成绩未在本机复验，不直接移植参数或作为本项目收敛证据。检索与 README 副本保留在 `logs/amp_g1/aligned_model_audit_github_*`。

下一项保持执行器、16 项奖励与 AMP 混合、网络、RSI、探索、学习批次及学习率日程不变，以四网络 / 四优化器从 1000 继续到 3000，保存 2000/3000。必须使用 `--continue-run`，不重新计数或重做预热，不导入 profile / 历史 DC 权重。独立评估与原 model0 比较；若没有收益，再审计物理梯度方向及训练分布，不直接调权重或换 IdealPD。继续使用实测有效的 18432 环境，监控 OOM / PhysX 错误。

## 验证

真实 GPU 审计执行成功、数据有限，覆盖两种 reset、真实与想象接口。CPU 项目测试 `pytest -q tests`：**92 passed**，日志 `logs/amp_g1/aligned_model_audit_cpu.log`。最初不限定目录的 pytest 误收集 logs / reference 中第三方测试，在收集阶段失败；不把该失败当作项目回归，也不为它安装无关依赖。
