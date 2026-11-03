# 当前状态与恢复入口

## 目标与版本
- 总目标：先Manager完整收敛，再参考reference/rl_amp实现Go2 AMP行走；禁止PPO，保留SuperMimic世界模型/想象更新。
- 开发机目录/pfs/user/learning/amp_new，当前代码commit917072e（奖励调度+PhysX patch扩容）；用户reference/未跟踪且保持原状。

## 当前实验（先核实进程，不重复启动）
- PID=2351410；日志logs/manager_4090/curriculum_fixed.log，精确命令curriculum_fixed.command.json，GPU采样curriculum_fixed.gpu.csv；运行目录logs/supermimic/2026-11-03_22-28-23_077303_manager4090_curriculum_fixed。
- 24576env/collect1/buffer128/WM4096×4/imag4096/horizon32；从原Manager model1000继续至2500，每500保存；WM预热阈值1000+critic200；奖励3000开始增加、5000达到最终权重。
- 初始模型：logs/supermimic/2026-11-03_20-51-11_991689_manager_from_scratch/model_1000.pt；actor网络已逐张量证明与model0相同，随机来源保留。禁止使用作废实验权重。
- 当前任务是弱正则运动学习诊断，尚未完成最终奖励，更未证明收敛。最新有效checkpoint尚未更新，预计下一model1500；最佳Manager尚无。
- 监测进程自动记录GPU并在PhysX/CUDA错误时作废停止，告警文件curriculum_fixed.invalid.json。下次先读该文件（若有）、日志及进程状态。
- 下一条命令：`ssh -p 9205 root@118.196.87.69 'cd /pfs/user/learning/amp_new && ps -p 2351410 -o pid,stat,etime,args && tail -n 3 logs/manager_4090/curriculum_fixed.log && nvidia-smi'`。

## 已验证
- CPU25项PASS；16环境及24576环境GPU接口/奖励调度一致性PASS；大规模回归122880reset/1强制翻倒/221184指令切换，完整日志零PhysX错误（logs/manager_4090/large_scene_integration.log）。
- 32环境12轮、恢复16轮及2秒评估PASS，actor/critic/WM均更新且有限（curriculum_smoke_report.json）；默认关闭调度，最终任务配置不变，验收拒绝未达最终权重的模型。
- RTX4090D 24564MiB，Python3.10.12/Torch2.5.1+cu124/Lab2.1/Sim4.5；pytest/mediapy/editable安装完成。OMNI_KIT_ACCEPT_EULA=YES、OMNI_KIT_ALLOW_ROOT=1，清除PYTHONPATH。无rg。

## 产物与关键结论
- logs/videos已上传。原Manager目录有model0/1000/2000/2025；旧Direct最佳步态位于logs/supermimic/2026-11-03_20-07-39_561455_gait_slip_refinement/model_1500.pt，仅作历史基线。
- 有效8192env续训200更新后线速度误差仍约.69，真实吞吐约5.8万/s；原16k/24k吞吐实验发现初始化patch溢出，全部作废，不能引用其吞吐/模型作为有效证据（physics_log_audit.json）。
- 上轮curriculum_train.log也触发patch溢出，已核实身份强制停止；不用其数据/权重。当前新实验已把默认163840 patch扩至786432（32/env），通过大规模落地/reset复验。
- 原model2000独立诊断1m/s平均vx约.0006、无腾空，未收敛；世界模型想象回报提升而真实速度不变。

## 未解决/下一步
- 假设：从零全量最终步态正则抑制运动，叠加模型偏差；新调度须由真实评估验证。物理容量问题与原8192静止问题分别处理，不能混为一个根因。
- 下一阶段：读取model1500/2000真实固定指令及步态指标，确认弱正则能否启动运动，再调整调度/模型；同时记录修复后的吞吐/显存，保留有用的大并行配置。
- Manager通过三个1000间隔检查点的完整速度/步态、最终加噪和录像审计后，才实施AMP；reference已有A1的61维运动数据、43维AMP特征和LSGAN判别器，需要Go2关节/足端坐标适配，不移植其PPO。

详细标准MANAGER_CONVERGENCE.md；历史记录docs/history/PROGRESS_2026-11-03.md；当前阶段计划PLAN.md。

- 本轮实际运行目录：logs/supermimic/2026-11-03_22-28-23_077303_manager4090_curriculum_fixed；最新日志检查无PhysX/CUDA/Traceback错误。

- 发现并修复新调度的恢复边界：resume若未显式给参数，现继承checkpoint调度；显式0/部分覆盖仍有效。CPU26项PASS，旁路32env CLI回归PID=2354765，日志schedule_restore.log；主训练PID2351410继续。

- 最新有效checkpoint：logs/supermimic/2026-11-03_22-28-23_077303_manager4090_curriculum_fixed/model_1500.pt（初期调度比例0，未达最终验收），已启动7指令×4env×8秒诊断PID=2356116，日志curriculum_gait1500.log/报告curriculum_gait1500.json，主训练继续。
