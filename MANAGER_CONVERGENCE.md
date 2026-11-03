# Manager based 迁移与收敛验证

目标是将 `Go2-Velocity-Flat` 改为 Isaac Lab `ManagerBasedRLEnv`，保留
SuperMimic 学习流程，并在新环境中训练、验证速度跟踪和步态收敛。
旧 Direct 环境的收敛模型与数据仅作为历史基线。

## 实现与接口

- 场景由 `InteractiveSceneCfg` 创建，机器人、平地、接触传感器与灯光均为 scene 配置。
- 动作、六项观测、机体系速度指令、各奖励项、终止和重置由原生 managers 执行。
  环境不覆盖 `step` 或 `_reset_idx`。
- `JointPositionAction` 扩展仅捕获动作前状态并统一裁剪动作，关节目标仍为
  `default_q + 0.25 * action`。
- 奖励 term 与想象调用同一纯 Torch 数学定义；manager 负责权重及 dt。
  termination term 在自动 reset 前缓存终止 next-state，防止回放学习重置跳变。
- 原生 ObservationManager 保存六项各五帧的历史，共225维；reset重复首帧。
  与旧 Direct 的零填充不同，已单独检查原生 reset 行为；稳态历史排列保持一致。
- 世界模型63维、足端计时16维，保留v1/v2检查点评估/迁移接口。
  新检查点和训练配置记录 `environment_backend=isaaclab_manager_based_v1`。

## 预先记录的验收标准

在查看新环境训练结果前，沿用既有速度和步态验收要求：

1. 完整指令评估：20种固定指令×8环境×30秒，另160环境分别使用
   42/123/2026三个随机种子各30秒；稳态剔除指令切换/reset后首秒。
   每随机种子稳态 vx/vy/yaw RMSE不超过(0.20,0.15,0.15)，
   各固定用例不超过(0.30,0.25,0.25)，站立不超过(0.10,0.10,0.10)。
   固定总组/各随机组摔倒率不超过0.1次/机器人/分钟，单固定用例不超过0.5。
2. 步态评估：7种固定指令×8环境×20秒。1/1.5m/s每足步频分别不超过
   原模型6.0409/8.7131Hz的70%，平均腾空至少0.10秒，平均摆动离地至少
   0.012m，短摆动(<0.08s)占比低于50%，接触足滑低于0.15m/s。
   站立步频低于0.3Hz，7指令零摔倒；各轴稳态RMSE不超过(0.20,0.15,0.15)。
3. 收敛需要连续三个、相隔1000次训练迭代的检查点均通过上述速度和步态要求，
   最终模型另做训练观测噪声下的完整指令复测，并录像检查。
4. 必须有新manager环境中的真实采样、世界模型和actor/critic更新、保存/恢复证据。
   正式训练从随机初始化开始，配置不使用resume或warm-start。

## 已完成的验证

- CPU23项测试通过，含空报告/覆盖缺失、非有限指标、旧backend、
  检查点配对/间隔、噪声配置错误的拒绝测试。
- GPU集成通过：原生manager step/reset、观测/共享奖励一致性、80次reset、
  强制翻倒、144次指令切换、计时器清空、跨reset固定指令。
- 检查动作裁剪不会修改调用者输入，manager.action、观测与关节目标使用相同裁剪值。
- 实际修改RewardManager权重后，step返回奖励按预期改变。
- 原始日志 `logs/manager/integration_fixed.log`。

## 当前训练状态

用户已上传logs/videos并授权继续，当前开发机RTX4090D 24GB。最新运行目录、进程和配置见 [STATUS.md](STATUS.md)，恢复前核实进程。

已复验CPU25项、原生manager GPU接口，以及奖励渐进初始/中间/最终权重与想象的一致性。32环境实际actor/critic/世界模型更新、保存恢复和短评估通过，报告 `logs/manager_4090/curriculum_smoke_report.json`。

8192/16384/24576环境的实际采样约5.8/9.9/13.4万转移每秒，24576环境峰值显存22506MiB。原model2025在最终奖励下续训仍未改善静止策略。当前验证弱正则速度学习后逐步引入最终步态奖励，目标任务和预定验收阈值不变；审计新增拒绝调度未完成的checkpoint。

正式训练仍只接受Manager随机初始化来源；本轮拟从原model1000未更新的随机actor与已预热世界模型继续，初始证据仍为原model0。原始目录 `logs/supermimic/2026-11-03_20-51-11_991689_manager_from_scratch/`。
**新Manager环境尚无收敛证据。** 历史Direct结果不能代替新环境验收。

完整审计命令：

```bash
python scripts/check_convergence.py \
  --benchmarks <three-checkpoint-velocity.json> \
  --gaits <three-checkpoint-gait.json> --noisy <final-noisy.json> \
  --initial-checkpoint <run>/model_0.pt --output logs/manager/convergence_report.json
```

审计同时读取实际检查点，核对manager backend、随机初始化来源、任务配置、
网络/优化器更新、数值有限性和文件校验和；缺少任何一项不宣布收敛。
