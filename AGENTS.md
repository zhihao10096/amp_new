# 长期协作规则

- 恢复任务先读 [GOAL.md](GOAL.md)、[PLAN.md](PLAN.md)、[STATUS.md](STATUS.md)，核实 commit、进程和产物后再操作，避免重复启动实验。
- 关键决定、重要问题定位、实验启动/结束、关键评估完成、切换任务或上下文压缩后立即更新记录。STATUS 必须包含当前 commit、运行目录、配置、PID/作业 ID、最新/最佳 checkpoint、最近指标、已排除方案、未解决问题及下一条命令。
- 文档仅保存结论、依据和日志路径，不粘贴大段原始日志；长任务同步维护 [PROGRESS.md](PROGRESS.md)。
- 可直接使用 `git commit` 管理版本；勿提交日志、模型、视频、缓存或虚拟环境。保留用户的未跟踪 `reference/`。
- 训练实测并行环境数、batch、吞吐和显存；增加环境数能提高效率时，尽量提高 GPU 利用率，同时检查学习效果。OOM 后根据峰值来源调整对应配置。
- 遇到问题先梳理并存问题与因果依赖，按收益、阻塞程度和成本排序；形成可验证假设后检索 GitHub 项目/Issues/现成方案，核对适用条件，修复后验证并重新排序。
- 代码沿用两空格缩进、类型标注和批量 Torch 操作，保持 device/dtype；共享观测/奖励等纯 Torch 代码不得依赖 Isaac Lab。
- 仿真相关导入须在 AppLauncher 启动后进行。提交代码变更前运行 CPU 测试；仿真变更还需真实 GPU 更新、保存/恢复和评估，覆盖真实/想象接口、终止状态及 reset。短跑不能证明收敛。

文档入口：[README.md](README.md)（用途/命令/结构）、[MANAGER_CONVERGENCE.md](MANAGER_CONVERGENCE.md)（新环境验收）、[CONVERGENCE.md](CONVERGENCE.md) / [GAIT.md](GAIT.md)（历史基线）。
