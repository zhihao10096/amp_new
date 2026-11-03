# 进度与恢复入口

恢复先读GOAL/PLAN/STATUS，再核实HEAD、ps、GPU和pipeline；本轮队列均已complete，勿重复启动。

- 总目标不变：Manager/A1独立成功 → G1仅平地walk → 成功提交后X1下半身12DOF AMP；禁PPO、WM可微想象，各阶段独立验收提交。G1/X1未成功前总目标未完成。
- 本轮源码0947e01，生产训练代码未改；当前文档版本用git rev-parse HEAD核实。正式R3源9bc7115，最新仍R3 model_3000，完整路径/配置/先前指标见STATUS；无合格最佳G1模型。原未跟踪文件保留。
- R1/R2/R3三点全部失败，步频0。节流D/加OU改善部分风格或覆盖，未解决步行；几何/映射已核对，严重RSI穿透、普通站立WM爆炸方向无支持。Manager/A1勿重训。
- 动态数据预测改善51.76%未变成控制收益。本轮3200环境成对动作响应后，仅拟合WM的响应约束使独立响应分数.35463→.23847，8步速度RMSE .0767→.0317；但同16初态冷启动控制存活原/普通拟合/响应约束1.3288/1.2813/1.1663s，均15/16摔；统一4步预热后.955/.9725/.9013s，均16/16摔。停止将当前MPC/诊断WM作为正式采样修复，不据离线分数声称成功。
- R3自身策略价值校准：无噪/.6m/s/256env，普通reset32步真实/想象bootstrap 3.038/3.089，参考RSI 1.123/.866；128步RSI生存.2969/.1210。动态状态偏保守是待检验假设，未证明真实价值锚定可改善行走。bootstrap结果不能冒充完整MC价值。
- 全部新队列已退出、GPU无计算进程：directional_response_r3（2665641）、response_fit_r3（2669348）、response_warm_control_r3（2672695）、policy_value_r3（2676135）；命令/脚本SHA256/日志见logs/amp_g1对应pipeline，汇总response_gradient_summary.json。本轮详细结论见docs/experiments/G1_DYNAMICS_RESPONSE_2026-11-04.md。
- G1全部实际动作（含新增/替换）复制assets/motions/g1，文件及清单Git管理，训练前/提交前核验来源/许可/SHA256/split/默认路径。七份现有动作复核通过，g1_motion_tracking_recheck_current.json。X1动作复制后.gitignore忽略、清单Git管理，部署参考reference/AMP、跳过RKNN。

下一条命令：`sed -n '350,415p' go2_supermimic/supermimic/train.py`；先查动态状态价值梯度/真实TD残差，再小型受控验证真实价值锚定；注意终止前状态、摔倒/超时、命令切换和gait，保留WM actor及A1默认行为。不直接盲开新正式轮次，G1成功前不进入X1。
