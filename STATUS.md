# 当前状态与恢复入口

## 目标/版本
- 总目标：先Manager收敛，再参考reference/rl_amp实现Go2 AMP行走；禁止PPO。
- 工作目录：开发机/pfs/user/learning/amp_new；当前代码提交6304099（本轮奖励调度已提交）。reference/保留未跟踪。
- 当前阶段：弱正则速度训练PID=2345789已停止并作废：PhysX patch buffer溢出；之前接口/吞吐/小规模验证进程已退出。当前commit6304099。

## 当前实验
- 已从logs/supermimic/2026-11-03_20-51-11_991689_manager_from_scratch/model_1000.pt恢复至2500；该点actor网络与model0相同，来源是Manager随机初始化，已有世界模型预热。
- 配置：24576env、collect1、buffer128、WM4096×4、imag4096、horizon32；WM预热阈值1000、critic200，actor_lr_scale.3；奖励初期弱正则，3000开始增加、5000达到完整权重。每500保存。
- 用较少每轮采样/想象批次增加每秒模型和策略更新，同时保留较大并行环境数；实测吞吐/显存/真实速度后调整，不能只比较真实采样数。
- 下一条命令：`ssh -p 9205 root@118.196.87.69 'cd /pfs/user/learning/amp_new && cat STATUS.md && ps -eo pid,stat,etime,args | grep -E "[p]ython.*scripts/(train|eval|benchmark|gait_eval)" || true'`；确认无重复进程后启动，精确命令写入logs/manager_4090/curriculum_train.command.json。

## 已完成验证/最近指标
- CPU25项PASS（logs/manager_4090/curriculum_cpu.log）；GPU接口PASS且初始/中间/最终调度奖励与想象一致（curriculum_integration.log）。
- 32环境12轮、恢复16轮、2秒评估通过，actor/critic/WM均实际更新且有限，调度比例0→1且最终task配置不变；报告curriculum_smoke_report.json，全部路径相对logs/manager_4090/。
- 8192env恢复200更新真实误差仍约.69、吞吐约5.8万；16384env约9.9万；24576env约13.4万，峰值22506MiB。24576采样GPU均值25%含启动空闲，稳定更新段需单独统计。原始profile*.log/.summary.json/.gpu.csv在logs/manager_4090/。
- 当前GPU RTX4090D 24564MiB；Python3.10.12/Torch2.5.1+cu124/Lab2.1/Sim4.5；项目editable/pytest/mediapy已安装。
- 仿真使用OMNI_KIT_ACCEPT_EULA=YES、OMNI_KIT_ALLOW_ROOT=1，清除PYTHONPATH；远端无rg。

## 模型/产物
- logs/videos已上传，checkpoints/快捷副本仍缺失。
- 最新Manager：logs/supermimic/2026-11-03_22-11-58_083075_manager4090_profile24576/model_2125.pt；较高迭代数为22-08-30_896832_manager4090_profile16384/model_2225.pt（同为短期诊断，未达标）。
- 最佳Manager：尚无；恢复根目录为logs/supermimic/2026-11-03_20-51-11_991689_manager_from_scratch/，保留model0/1000/2000/2025。
- 旧Direct最佳步态：logs/supermimic/2026-11-03_20-07-39_561455_gait_slip_refinement/model_1500.pt；报告logs/gait，视频videos/，仅历史基线。

## 已排除/未解决
- GPU观测/奖励/reset/clip接口已通过，静止并非已证实的manager接口错误；单纯最终奖励续跑200更新未改善，排除“已收敛”判断。
- 假设：从零全量强步态惩罚抑制运动，叠加模型回报利用；调度在官方legged_gym弱初期运动正则和本项目旧Direct分阶段成功记录基础上提出，尚须真实学习验证。来源存logs/manager_4090/curriculum_sources.json。
- 旧16GB机器OOM上限不适用于24GB；大环境数增加采样吞吐但略降每秒策略更新，故调整collect/imag配置后再评估。
- 未解决：弱正则能否学会速度、如何平稳完成最终步态权重、完整三检查点/带噪/录像验收，之后再做AMP。

验收标准见MANAGER_CONVERGENCE.md。每次关键决定、实验开始/结束、评估后及时替换本页状态并更新PROGRESS。

- 实验启动：PID=2345789，logs/manager_4090/curriculum_train.log / .gpu.csv；精确命令curriculum_train.command.json；运行目录待日志Log directory出现后补充。最新检查点仍为上述历史模型，下一计划保存model1500。

## 当前关键问题（最高优先级）
- 24576环境随机actor起步触发PhysX Patch buffer overflow，日志curriculum_train.log要求至少294912；不能使用该轮数据/模型作有效训练证据。PID已SIGTERM停止，待确认释放GPU。
- 假设已明确：原默认patch容量不足大规模机器人落地接触，需要在仿真创建前按num_envs扩容。此前profile已训练姿态未暴露，不能以其无OOM替代物理容量正确性。
- 下一步：核对IsaacLab官方配置/GitHub相关问题，增加容量、GPU接口复验、从未受影响model1000重新训练。

- 错误实验SIGTERM后未退出，已核实命令身份并SIGKILL停止；未保留其权重。修复configure_task按max(默认,32×envs)分配patch，24576环境786432。当前大规模GPU接口回归PID=2349431，日志logs/manager_4090/large_scene_integration.log；CPU25项复验通过。

- 全日志物理审计发现此前性能实验也有patch错误：logs/manager_4090/profile16384.log, logs/manager_4090/profile24576.log；相关吞吐只作无效配置参考，不能作为正确仿真的选型证据。需要扩容后重测。审计logs/manager_4090/physics_log_audit.json。
