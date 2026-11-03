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

## 本轮数值验收结果（2026-11-04）

新Manager随机来源的7000、8000、9000三个相隔1000迭代检查点，均通过上方全部完整速度和步态标准；
9000另通过训练观测噪声下的完整速度复测。四轮完整速度评估共1280机器人分钟，均零摔倒；
三个7指令步态评估也均零摔倒。最终侧面正常走/快走及站立录像已完成，抽帧检查通过；所有项目训练、评估和录像进程已结束，见 [STATUS.md](STATUS.md)。

| 检查点 | 随机稳态vx / vy / yaw RMSE | 站立步频Hz | 1m/s足滑m/s | 1.5m/s足滑m/s | 完整速度/步态 |
| --- | --- | ---: | ---: | ---: | --- |
| 7000 | .05065 / .04618 / .04593 | 0 | .07259 | .11017 | 全部通过 |
| 8000 | .04603 / .04378 / .04109 | .00988 | .07737 | .11334 | 全部通过 |
| 9000 | .04054 / .04416 / .03648 | 0 | .07295 | .11357 | 全部通过 |
| 9000加噪 | .04285 / .04726 / .05306 | — | — | — | 完整速度通过 |

9000在1/1.5m/s时每足步频均3.530Hz、平均腾空均约.1312s、
平均摆动离地.01697/.01893m、短摆动比例均0，七指令速度均达标。
保留原定阈值；未使用PPO、外部策略、周期探索或优先采样。

## 模型、来源和证据

- 最终模型 `checkpoints/go2_manager_converged.pt`，元数据同名.json。
- 源模型 `logs/supermimic/2026-11-04_00-32-55_866984_manager_final9000/model_9000.pt`；8000同目录。
- 7000 `logs/supermimic/2026-11-04_00-24-18_384210_manager_final7000/model_7000.pt`。
- 随机初始 `logs/supermimic/2026-11-03_23-14-56_505712_manager_baseline_squared/model_0.pt`，无resume/warm-start。
  后续续训始终保留Manager random_initialization来源；a3ea68e修正初期平方惩罚，8cb89bb/a86c036优化编译执行。
- 审计 `logs/manager_4090/convergence_report.json`：converged=true、failures=[]；核实task一致、最终课程比例1、
  三网络及优化器真实更新、数值有限性、来源与实际文件SHA256。
- 速度/步态 `logs/manager_4090/manager_{velocity,gait}7000.json`、`manager_{velocity,gait}8000_9000.json`；
  最终噪声 `manager_noisy9000.json`，完整指标和曲线 `manager_evaluation_summary.{json,png}`。
- 最终SHA256 `07fc3f6e0e6801a3e60ab591be25dbeb3071c930809f847dd14284477dbfa9dd`。
- 侧面对比 `videos/manager_gait_comparison.mp4`（左3000/右9000），快走 `manager_fast_side.mp4`，站立 `manager_stand.mp4`；所有录像指标零摔倒。
  2/2.08/5/8秒抽帧 `logs/manager_4090/manager_side_contact_sheet.jpg` 已检查，四足完整入镜，未见翻倒或明显穿地。接触时序的定量结论来自独立评估。
- 首批录像 `videos/manager_{before,after,fast,stand}.mp4` 及近景调试产物保留。
  首次远景偏小，近景lookat正z导致下沿偏紧；依据IsaacLab跟随原点定义补录eye=(1.2,-1.8,.6)、lookat=(0,0,-.1)，不修改训练代码或模型。

## 验证与效率

此前CPU31项、原生manager观测/奖励/reset/终止/指令切换、三网络真实更新、保存恢复及课程编译数值/梯度一致性已通过。
PhysX patch按32×env扩容后32768环境完整回归零物理错误；相同每轮32768真实转移下，
32k编译约12.5万转移/s、21728MiB，16k约11.9万/s、8k约10.4万/s。
旧16k/24k初始化溢出的性能数字作废，不计入证据。
最终训练配置32k/collect1/buffer128（每env回放2.56s）、WM4096×4/window8/hidden512×3、imag8192/H32、
FP32 highest编译、actor_scale=.15、seed0；3000→5000最终奖励课程后保持最终任务。
真实manager和想象共享同一奖励数学定义。6000→9000各训练日志均零物理/CUDA错误，末段约12.2–12.6万转移/s、显存21792MiB。

## 复核命令

```bash
.venv/bin/python scripts/check_convergence.py \
  --benchmarks logs/manager_4090/manager_velocity7000.json logs/manager_4090/manager_velocity8000_9000.json \
  --gaits logs/manager_4090/manager_gait7000.json logs/manager_4090/manager_gait8000_9000.json \
  --noisy logs/manager_4090/manager_noisy9000.json \
  --initial-checkpoint logs/supermimic/2026-11-03_23-14-56_505712_manager_baseline_squared/model_0.pt \
  --output logs/manager_4090/convergence_report.json
```

初期静止、奖励差异及已排除方案详见 [MANAGER_BASELINE.md](MANAGER_BASELINE.md) 与PROGRESS历史归档。
这不是单因素消融，不把改善全部归因于某一项改动；结论适用于上述平地任务和预先记录的评估覆盖。
