# 当前状态与恢复入口

核实时间：2026-11-04 09:40:07 +0800。本文件为当前事实；旧实验流水见[历史快照](docs/history/STATUS_2026-11-04_before_velocity64_result.md)与[PROGRESS.md](PROGRESS.md)，不得按历史PID重复启动。

## 目标与版本
- 开发机权威目录`/pfs/user/learning/amp_new`，SSH `ssh -p 9205 root@118.196.87.69`；HEAD `b2343e10d004258f5b05405ca0f1accfc6892369`（问题/方案/效果报告已提交；生产源码基线e375093）。70维足端特征实现及交接记录仍有未提交改动，GPU验证已通过，准备提交代码。
- Manager与A1 AMP已独立完成；当前G1平地walk未成功，成功后才进入X1下半身12DOF。全部使用SuperMimic WM可微想象，禁止PPO；最终验收阈值不变。
- G1实际参考动作位于Git管理的`assets/motions/g1/`，七份Walk_B及manifest；训练/留出80%/20%。新增/替换数据先复制、记录来源/许可/SHA256/split并核对Git状态，再训练。X1遵循GOAL中独立的数据忽略规则。
- 保留原未跟踪`reference/`及exploration/dynamics诊断文件；本轮没有修改生产代码，不误提交这些文件。

## 当前运行状态与配置
- 70维完整验证driver PID2797838已complete，所有子进程完成；CPU61、CUDA FK、原生/编译、四网更新恢复、旧模型兼容与A1回归全过。证据`logs/amp_g1/feet70_r2_validation.audit.json`。即将提交后启动单变量1000轮，实际PID以随后pipeline及ps为准。
- 最新有效诊断目录`logs/supermimic/2026-11-04_09-09-01_259556_g1_amp_warm9000_velocity64_diag`。最新70维失败验证目录`logs/supermimic/2026-11-04_09-33-42_200537_g1_feet70_smoke_initial`仅model_0，不作为有效训练结果；完整验证命令/配置见`logs/amp_g1/feet70_validation.pipeline.json`。
- seed0、18432env、1000迭代，collect1/buffer128、WM4096×4/window8/hidden512×3、imag8192/H32、critic3×4、actor/critic512,256,128、actor_lr_scale=.15、WM预热300/critic200/actor_ramp500，FP32 highest/compile；OU .6占25%，其余Gaussian .1。
- schema=`g1_amp_64_velocity_v1`，D2048×2/interval5/lr1e-5/GP40/weight.5/ramp1000/RSI.5；真实/专家/想象统一机体系根线速度。默认61维、旧模型metadata兼容；既有CPU58项通过，本轮未重新测试。
- 三臂来源均为下方同一速度9000模型：继承actor/WM及归一化，重建critic/优化器，AMP臂另建D；无AMP臂同时无参考重置，不能将所有差异仅归因于D。

## 最新与最佳checkpoint
- 最新诊断：上述64维目录`model_1000.pt`，另保留独立`model_0.pt`。这不是正式成功模型。
- 稳定运动诊断来源：`logs/supermimic/2026-11-04_08-00-37_784295_g1_velocity_cold_start18432_to9000/model_9000.pt`。该谱系来自G1随机初始化及3000→5000奖励课程；9000七指令零摔倒，vx=.601/.999m/s，但步频3.672/4.258Hz、腾空.087/.093s、离地7.20/14.10mm，尚未达walk验收。
- 最新正式随机来源仍`logs/supermimic/2026-11-04_04-51-38_136861_g1_amp_formal_r3_exploration/model_3000.pt`；R1/R2/R3均未通过。不存在已通过验收的G1最佳/已收敛checkpoint。
- 已完成阶段归档：`checkpoints/go2_manager_converged.pt`、`checkpoints/a1_amp_converged.pt`，不要重训。

## 最新评估与结论
- 三臂同源1000轮独立步态已完成，均为七指令×8环境×20秒、seed42，全部零摔倒；不等同完整正式验收。
- 0.6m/s下，无AMP/61维AMP/64维AMP的每足步频4.044/3.754/3.477Hz，腾空.0878/.0872/.0836s，摆动离地9.20/6.79/6.05mm；1m/s下步频4.287/4.031/4.350Hz。正式要求步频≤2.5Hz、腾空≥.15s、离地≥15mm，三臂均未通过。
- 64维内部风格距forward 7.13088→5.02951、fast 10.39874→7.80138，但低抬脚未改善；不同schema的绝对风格距离不可直接比较。新增根线速度不是已验证的碎步修复。
- 左侧移三臂均退化，无AMP实际vy=.0326、61维=.1030、64维=.0976（指令.3）；网络重建/分布改变仍为混杂，不能只归因于AMP。
- 完整对照与下一步依据：[诊断报告](docs/experiments/G1_AMP_WARM9000_COMPARISON_2026-11-04.md)。原始报告：`logs/amp_g1/g1_velocity_warm9000_control1000_assessment.json`、`g1_amp_warm9000_diag_assessment.json`、`g1_amp_warm9000_velocity64_diag_assessment.json`（后两者同目录）；日志与报告同前缀。

## 已排除/停止的方向与未解决问题
- 单独加大探索、节流D、真实TD0/.5短程对照均未使旧随机AMP来源迈步；动态拟合/局部响应改善与MPC也未形成稳定闭环收益，不把它们继续默认加码。几何/关节映射、严重RSI穿透假设未获证据支持，详见历史和G1_CONVERGENCE。
- Go2启动流程已迁移并让G1稳定移动，但高频碎步、低抬脚、较短摆动仍未解决；仅61/64维现有AMP1000轮均未显示足够步态收益，暂不按原配置盲目延长。
- GPU配置：24576完整actor更新OOM，32768 PhysX allocator故障，二者结果作废；18432完整更新通过，后续保持学习批次并以有效吞吐决定并行数。
- 70维方案追加左右足端相对骨盆位置，三条路径统一USD FK；新CPU61项通过（`feet70_cpu.log`），GPU编译遇constexpr/broadcast_to异常（`feet70_integration.log`及`feet70_smoke_initial.log`）。下一步先改写FK常量/广播表达并独立验证GPU编译及梯度，随后重新完成原生/四网更新/CLI恢复。通过且提交后才启动同源1000轮；历史、参考条件和奖励均不同时改。

## 问题与方案总览
- 用户要求的[G1 AMP全程问题、方案与效果报告](docs/experiments/G1_AMP_ISSUES_AND_SOLUTIONS_2026-11-04.md)已完成并提交`b2343e1`，本地副本位于工作区artifacts同名文件。报告截止70维首次GPU验证失败，未宣称收敛。

## 下一条执行命令
先核实无新进程，随后定位70维FK的Inductor常量广播问题；旧验证已终止，修复后使用新验证ID并保留失败日志，勿重复评估已完成的64维队列：

```bash
cd /pfs/user/learning/amp_new
nvidia-smi
tail -n 80 logs/amp_g1/feet70_integration.log
sed -n '1,200p' go2_supermimic/g1_kinematics.py
```

恢复时一起读GOAL/PLAN/PROGRESS及上述对照报告；完整速度/连续三点/加噪/录像/实际模型审计通过后才可宣告G1成功。

- 70维足端特征验证启动feet70_integration，driver PID2790233、child PID2790320；配置/命令/log见logs/amp_g1/feet70_validation.pipeline.json，勿重复启动。

- 70维足端特征验证结束feet70_integration，返回码0，日志logs/amp_g1/feet70_integration.log。

- 70维足端特征验证启动feet70_smoke_initial，driver PID2790233、child PID2791858；配置/命令/log见logs/amp_g1/feet70_validation.pipeline.json，勿重复启动。

- 70维足端特征验证结束feet70_smoke_initial，返回码0，日志logs/amp_g1/feet70_smoke_initial.log。

- 70维足端验证失败FileNotFoundError(2, 'No such file or directory')，核对原pipeline及日志后修复，不启动训练。

- 2026-11-04T09:35:24 重要问题定位：70维CPU61项通过，但原生/短跑编译均遇PyTorch2.5.1/Inductor生成Triton的constexpr broadcast_to错误。Kit退出返回0不能代表验证通过：缺feet70_integration.json与model_20.pt，driver2790233已failed，正式1000轮未启动。原始日志logs/amp_g1/feet70_integration.log、feet70_smoke_initial.log，完整状态feet70_validation.pipeline.json；先修复FK编译表达并要求产物/通过标志，不能用退出码声称成功。

- 2026-11-04T09:42:23 70维FK编译修复：原验证driver2790233已退出、GPU空闲。原日志表明常量轴表广播生成tl.broadcast_to(constexpr,...)；GitHub检索存github_fk_inductor_broadcast_2026-11-04.json，未将不同版本Issue当作直接修复。FK现改为旋转基向量和Python标量几何常量，保留坐标/单位/关节顺序；正在CPU61及32/8192样本CUDA fullgraph值/梯度检查（会话12949，日志feet70_r2_cpu.log与feet70_fk_compile_r2.log）。新GPU验证使用r2 ID，要求报告passed、模型产物及无异常，保留原失败日志；1000轮训练尚未启动。

- 70维FK改写后CPU61及独立CUDA fullgraph通过：32/8192批量位置max1.79e-7m、梯度max4.77e-7；feet70_fk_compile_r2.json。完整原生/编译/四网更新恢复验证driver PID2797838已启动，状态logs/amp_g1/feet70_r2_validation.pipeline.json；原失败r1保留，勿重复启动。

- 70维足端特征验证启动feet70_r2_integration，driver PID2797838、child PID2797944；配置/命令/log见logs/amp_g1/feet70_r2_validation.pipeline.json，勿重复启动。

- 70维足端特征验证结束feet70_r2_integration，返回码0，日志logs/amp_g1/feet70_r2_integration.log。

- 70维足端特征验证启动feet70_r2_smoke_initial，driver PID2797838、child PID2799145；配置/命令/log见logs/amp_g1/feet70_r2_validation.pipeline.json，勿重复启动。

- 2026-11-04T09:45:10 70维完整原生/想象编译验证通过：65reset/13摔倒/52超时/356命令切换，专家特征max7.15e-7、原生足端位置max1.73e-6m、返回max1.79e-7、actor梯度max7.28e-12；feet70_r2_integration.json。当前driver2797838，阶段feet70_r2_smoke_initial，child2799145；继续四网更新/CLI恢复/A1回归，未启动1000轮。

- 70维足端特征验证结束feet70_r2_smoke_initial，返回码0，日志logs/amp_g1/feet70_r2_smoke_initial.log。

- 70维足端特征验证启动feet70_r2_smoke_resume，driver PID2797838、child PID2799919；配置/命令/log见logs/amp_g1/feet70_r2_validation.pipeline.json，勿重复启动。

- 70维足端特征验证结束feet70_r2_smoke_resume，返回码0，日志logs/amp_g1/feet70_r2_smoke_resume.log。

- 70维足端特征验证启动feet70_r2_a1_regression，driver PID2797838、child PID2801271；配置/命令/log见logs/amp_g1/feet70_r2_validation.pipeline.json，勿重复启动。

- 70维足端特征验证结束feet70_r2_a1_regression，返回码0，日志logs/amp_g1/feet70_r2_a1_regression.log。

- 70维足端特征验证全部通过：CPU61、参考训练段几何/梯度、原生接口/终止/命令/reset、编译返回/actor梯度、四网四优化器20→25/CLI schema恢复、61/64维旧模型metadata与D加载、A1回归；证据logs/amp_g1/feet70_r2_validation.audit.json。短跑不算收敛；下一步先提交实现，再启动同源1000轮诊断。

- 2026-11-04T09:47:30+08:00 关键验证完成：70维CPU61、独立CUDA fullgraph、完整原生/想象编译、四网四优化器20→25及CLI自动schema恢复、61/64旧metadata/D加载、A1 GPU回归全部通过，feet70_r2_validation.audit.json。FK常量广播编译问题已修复；短跑不证明收敛。准备提交可选70维实现后，从同9000模型/与64维同配置做1000轮诊断。
