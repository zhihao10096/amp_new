# 进度索引

当前目标见 [GOAL.md](GOAL.md)，阶段计划见 [PLAN.md](PLAN.md)，恢复必须先读 [STATUS.md](STATUS.md) 并核实进程。
旧的长篇进度已保存在 [历史归档](docs/history/PROGRESS_2026-11-03.md)；历史路径不代表当前开发机存在。

## 2026-11-03 21:56:01 CST：熟悉项目与交接整理
- 已梳理 ManagerBasedRLEnv、共享 Torch 接口、SuperMimic 训练/评估链路和验收标准；代码基线24046e2。
- 核实当前RTX4090D 24GB且无实验进程；logs/checkpoints/videos缺失，旧Manager训练仍无收敛证据。
- 测试基线受缺少pytest阻塞；同时发现mediapy/项目安装元数据缺失、Isaac Sim许可尚未确认。本轮未安装依赖、未接受许可或启动训练。
- 采纳规则：精简AGENTS，维护GOAL/PLAN/STATUS；可直接commit；后续训练根据实测吞吐/显存尽量提高GPU利用率。
- 文档整理及交叉链接/diff检查完成，纳入本次文档提交；当前任务完成。后续实验等待新指示，恢复入口见STATUS。

## 继续Manager实现
- 用户已上传logs/videos并明确继续，暂停约束解除；核实145个日志/模型文件、5视频，Manager model0/1000/2000/2025存在，当前无实验进程。
- 优先解决依赖/仿真可执行性并分析静止策略；不直接假定继续训练即可收敛。
- 依赖安装完成，GPU集成检查已启动PID2336158，日志`logs/manager_4090/integration.log`。
- 总目标明确为Manager收敛后接入Go2 AMP（参考rl_amp，禁用PPO）。CPU23项/GPU集成PASS；8192环境吞吐实验PID2336854运行中。
- 8192env恢复200更新完成，吞吐约54553.0转移/s，真实线速度误差仍约0.69059；启动16384env同起点对照PID2337710。
- 已实现可选训练奖励渐进调度，真实RewardManager/想象同步权重，checkpoint保留最终任务并记录当前调度比例；验收拒绝未到最终权重的模型。CPU结果见logs/manager_4090/curriculum_cpu.log，GPU验证待吞吐实验结束。
- 16384env完成，最终吞吐99421.0转移/s、显存观测17918MiB，误差仍约.69；启动24576env对照PID2339624并连续采样GPU。
- 24576env完整100更新通过，峰值22506.0MiB、吞吐约133888/s；调度GPU检查PID2341954启动。
- 调度GPU一致性PASS，覆盖初始/中间/最终权重；开始32环境真实更新/保存恢复和2秒评估验证。
- 调度验证curriculum_smoke结束，退出码0，日志logs/manager_4090/curriculum_smoke.log。
- 调度验证curriculum_resume结束，退出码0，日志logs/manager_4090/curriculum_resume.log。
- 调度验证curriculum_eval结束，退出码0，日志logs/manager_4090/curriculum_eval.log。
- 调度全部验证通过（CPU25项/GPU三阶段奖励一致/32环境实际更新保存恢复短评估）；准备从Manager model1000的未更新actor起步验证弱正则，最终目标/验收不变。
- 提交6304099；核实model1000 actor网络与model0逐张量相同，已启动24576env/collect1/WM4096×4/imag4096/buffer128从1000至2500的弱正则实验PID2345789，日志logs/manager_4090/curriculum_train.log。
- 重要定位：24576随机actor落地触发PhysX patch buffer overflow（需求>=294912）；已停止PID2345789并作废本轮，优先按环境规模增大物理patch容量，重跑后再评估学习。
- patch默认163840已按32×envs扩至786432；错误进程SIGTERM未退出后核实身份并强制停止，开始24576env实际落地/reset GPU回归PID2349431。
- 复查全部性能日志：logs/manager_4090/profile16384.log, logs/manager_4090/profile24576.log也有物理patch错误，已标记该配置吞吐无效，扩容后须重测；原8192若无错误可保留。
- 扩容后24576env GPU回归PASS：122880reset/221184指令切换，奖励观测/三阶段调度一致，完整日志零PhysX错误。原16k/24k性能结果因初始化溢出作废；下一轮从原model1000重启，不使用错误轮权重。
- 提交917072e；已从原model1000重启修复后的24576env/collect1/imag4096/buffer128实验PID2351410，日志curriculum_fixed.log，持续GPU/物理错误监测；初始错误轮作废。
- 修复调度恢复默认值会意外禁用课程的边界；CPU26项PASS，开始32env省略调度参数的实际CLI恢复回归，主训练继续。
- 新增实际CLI恢复已验证省略参数仍保留调度4/12；model1500已保存，启动7指令运动诊断PID2356116，不把短评估当收敛。
