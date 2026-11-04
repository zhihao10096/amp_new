# 当前状态与恢复入口

核实时间：2026-11-04T09:58:41+08:00。本文件为当前事实；旧实验流水见[历史快照](docs/history/STATUS_2026-11-04_before_velocity64_result.md)与[PROGRESS.md](PROGRESS.md)，不得按历史PID重复启动。

## 目标与版本
- 开发机权威目录`/pfs/user/learning/amp_new`，SSH `ssh -p 9205 root@118.196.87.69`；HEAD `e83583505586738d3587bda9575cdd86cc633222`（70维FK特征已实现、CPU/GPU验证并提交；默认61维兼容）。本轮更新全程问题报告及交接记录；其他既有未提交修改以git status为准。
- Manager与A1 AMP已独立完成；当前G1平地walk未成功，成功后才进入X1下半身12DOF。全部使用SuperMimic WM可微想象，禁止PPO；最终验收阈值不变。
- G1实际参考动作位于Git管理的`assets/motions/g1/`，七份Walk_B及manifest；训练/留出80%/20%。新增/替换数据先复制、记录来源/许可/SHA256/split并核对Git状态，再训练。X1遵循GOAL中独立的数据忽略规则。
- 保留原未跟踪`reference/`及exploration/dynamics诊断文件；本轮没有修改生产代码，不误提交这些文件。

## 当前运行状态与配置
- 70维单变量1000轮诊断及model_0/1000独立评估已全部完成，pipeline stage=complete（09:56:13 +0800）。原driver2802496/训练2802600/评估2807823均退出；09:57实际核实无GPU计算进程，显存1MiB、利用率0%。目录`logs/supermimic/2026-11-04_09-49-14_815830_g1_amp_warm9000_feet70_diag`，勿重复启动。完整GPU验证证据feet70_r2_validation.audit.json通过。
- 上轮64维对照目录`logs/supermimic/2026-11-04_09-09-01_259556_g1_amp_warm9000_velocity64_diag`；最新有效70维目录见上项。最新70维失败验证目录`logs/supermimic/2026-11-04_09-33-42_200537_g1_feet70_smoke_initial`仅model_0，不作为有效训练结果；完整验证命令/配置见`logs/amp_g1/feet70_validation.pipeline.json`。
- seed0、18432env、1000迭代，collect1/buffer128、WM4096×4/window8/hidden512×3、imag8192/H32、critic3×4、actor/critic512,256,128、actor_lr_scale=.15、WM预热300/critic200/actor_ramp500，FP32 highest/compile；OU .6占25%，其余Gaussian .1。
- schema=`g1_amp_70_feet_v1`，D2048×2/interval5/lr1e-5/GP40/weight.5/ramp1000/RSI.5；真实/专家/想象统一机体系根线速度。默认61维、旧模型metadata兼容；此前CPU61及完整GPU更新/恢复均通过，本轮文档汇总未重跑训练/测试。
- 四臂来源均为下方同一速度9000模型：继承actor/WM及归一化，重建critic/优化器，AMP臂另建D；无AMP臂同时无参考重置，不能将所有差异仅归因于D。

## 最新与最佳checkpoint
- 最新诊断：`logs/supermimic/2026-11-04_09-49-14_815830_g1_amp_warm9000_feet70_diag/model_1000.pt`，另保留独立`model_0.pt`，四网更新/匹配来源审计及独立七指令评估已完成；这不是正式成功模型。
- 稳定运动诊断来源：`logs/supermimic/2026-11-04_08-00-37_784295_g1_velocity_cold_start18432_to9000/model_9000.pt`。该谱系来自G1随机初始化及3000→5000奖励课程；9000七指令零摔倒，vx=.601/.999m/s，但步频3.672/4.258Hz、腾空.087/.093s、离地7.20/14.10mm，尚未达walk验收。
- 最新正式随机来源仍`logs/supermimic/2026-11-04_04-51-38_136861_g1_amp_formal_r3_exploration/model_3000.pt`；R1/R2/R3均未通过。不存在已通过验收的G1最佳/已收敛checkpoint。
- 已完成阶段归档：`checkpoints/go2_manager_converged.pt`、`checkpoints/a1_amp_converged.pt`，不要重训。

## 最新评估与结论
- 无AMP/61维/64维/70维四臂同源1000轮独立步态已完成，均为七指令×8环境×20秒、seed42，全部零摔倒；不等同完整正式验收。
- 70维在0.6/1.0m/s下实际vx=.5932/1.0199、每足步频3.533/3.800Hz、腾空.0815/.0913s、离地7.13/14.18mm、足滑.1072/.2087m/s；左侧移vy=.1074（指令.3）。仍未通过walk标准，不能把快走步频下降写成整体步态修复。
- 70维schema内部留出风格距forward 6.58430→5.00757（改善23.95%）、fast 9.56222→7.74379（19.02%）；风格改善未带来合格摆动/离地，跨schema绝对距离不直接比较。
- 0.6m/s下，无AMP/61维AMP/64维AMP的每足步频4.044/3.754/3.477Hz，腾空.0878/.0872/.0836s，摆动离地9.20/6.79/6.05mm；1m/s下步频4.287/4.031/4.350Hz。正式要求步频≤2.5Hz、腾空≥.15s、离地≥15mm，三臂均未通过。
- 64维内部风格距forward 7.13088→5.02951、fast 10.39874→7.80138，但低抬脚未改善；不同schema的绝对风格距离不可直接比较。新增根线速度不是已验证的碎步修复。
- 左侧移三臂均退化，无AMP实际vy=.0326、61维=.1030、64维=.0976（指令.3）；网络重建/分布改变仍为混杂，不能只归因于AMP。
- 完整对照与下一步依据：[诊断报告](docs/experiments/G1_AMP_WARM9000_COMPARISON_2026-11-04.md)。原始报告：`logs/amp_g1/g1_velocity_warm9000_control1000_assessment.json`、`g1_amp_warm9000_diag_assessment.json`、`g1_amp_warm9000_velocity64_diag_assessment.json`（后两者同目录）；日志与报告同前缀。

## 已排除/停止的方向与未解决问题
- 单独加大探索、节流D、真实TD0/.5短程对照均未使旧随机AMP来源迈步；动态拟合/局部响应改善与MPC也未形成稳定闭环收益，不把它们继续默认加码。几何/关节映射、严重RSI穿透假设未获证据支持，详见历史和G1_CONVERGENCE。
- Go2启动流程已迁移并让G1稳定移动，但高频碎步、低抬脚、较短摆动仍未解决；61/64/70维AMP1000轮均未显示足够步态收益，暂不按原配置盲目延长。
- GPU配置：24576完整actor更新OOM，32768 PhysX allocator故障，二者结果作废；18432完整更新通过，后续保持学习批次并以有效吞吐决定并行数。
- 70维FK常量广播编译问题已修复并提交e835835：CPU61、CUDA fullgraph位置/梯度、原生/终止/reset、四网四优化器20→25/CLI schema恢复、61/64维兼容及A1 GPU回归全部通过。1000轮训练与独立评估也已完成；工程验证通过不代表物理步态达标，历史/参考条件/奖励仍须分开消融。

## 问题与方案总览
- 用户要求的[G1 AMP全程问题、方案与效果报告](docs/experiments/G1_AMP_ISSUES_AND_SOLUTIONS_2026-11-04.md)原版提交`b2343e1`；本轮已补齐70维编译修复、完整验证和最终独立评估，本地交付副本位于工作区artifacts同名文件。

## 下一条执行命令
恢复先复核已结束pipeline和GPU状态，再读取四臂对照报告，不重复启动旧队列：

```bash
cd /pfs/user/learning/amp_new
nvidia-smi
cat logs/amp_g1/g1_amp_warm9000_feet70_diag.pipeline.json
cat docs/experiments/G1_AMP_WARM9000_COMPARISON_2026-11-04.md
```

全程问题/方案/效果Markdown报告已完成，主要数据和证据路径已核验，准备提交；本轮不启动新实验。后续按建议文档单变量验证时序历史、参考条件或辅助步态项；完整速度/连续三点/加噪/录像/实际模型审计尚未通过，G1保持未完成，X1未开始。
