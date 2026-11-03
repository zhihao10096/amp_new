# 当前状态与恢复入口

## 目标/版本
- 总目标：先Manager收敛，再参考reference/rl_amp实现Go2 AMP行走；禁止PPO。
- 工作目录：开发机/pfs/user/learning/amp_new；当前交接提交HEAD（源码基线2eaccf5，正在提交本轮奖励调度）。reference/保留未跟踪。
- 当前阶段：调度实现验证完成，准备启动弱正则速度训练；所有吞吐/接口/小规模训练进程已退出，当前PID/作业ID无。

## 下一实验
- 拟从logs/supermimic/2026-11-03_20-51-11_991689_manager_from_scratch/model_1000.pt恢复至2500；该点actor网络与model0相同，来源是Manager随机初始化，已有世界模型预热。
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
