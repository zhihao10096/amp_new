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
- model1500独立7指令仍近似静止（forward均速约0），尚属早期300actor更新；model2000已保存并启动同标准诊断PID2360644，主训练继续。
- model2000弱正则评估仍静止；本轮至2500完成，启动gait2500诊断PID2363114，世界模型分组误差报告dynamics2000.json待复核；未开始最终约束。
- dynamics2000：现有低速数据单步/32步线速度误差.0032/.0132m/s，接触归一化误差约1；不能把停滞简单归因于已测轨迹预测很差。重点转向运动数据覆盖与闭环想象，暂不增加最终步态惩罚。
- model2500前进仍.00075，转弯约.104；停止同类续跑，转向真实运动覆盖假设。新增仅采样用周期trot生成器（actor仍无phase、无PPO），CPU28项PASS；启动参数物理扫描PID2367897，见trot_exploration_scan.log。
- 周期探索物理扫描结束：slow前进>.2m/s且零摔倒的组0个，报告trot_exploration_scan.json；需核对其它方向与可用状态覆盖再定训练方案。
- 首轮周期动作扫描未得到有效前进组（有-.3～-.65m/s后退覆盖），方向假设待核对；不将其直接当跟踪策略或投入长跑。启动PhysX足端Jacobian测量PID2370099，核对Go2实际关节方向/几何。
- 实测PhysX足端Jacobian确认几何符号基本正确；下一假设是抬腿相位/伺服与接触时序。启动2频率×2幅度×4相位的真实运动扫描PID2371518，日志trot_phase_scan.log；探索尚未接入训练。
- 用户指出d9eee9b3f248e5300e636c433255db2c1c3e086a可收敛；停止扩展未验证探索路线，优先系统对照该基线算法/状态/奖励/数据分布，找迁移差异。周期探索未进入正式训练。

- 恢复核实HEAD8029aaa、周期扫描已结束且GPU空闲。d9eee9b3是MuJoCo chase/dodge基线；同时用已收敛Isaac Lab Direct作中间对照。Manager迁移本身未改变WM/actor损失。发现此前弱正则仅复用权重，joint_deviation仍为L2范数/站立5倍，而已收敛速度阶段为平方和，且undesired_contacts仍为-1；需用数学一致的初期奖励作受控验证。
- 已实现初期奖励与已收敛速度阶段的数学对齐：关节平方惩罚渐变至最终范数、初期关闭非足接触惩罚；真实manager/想象共享有效训练配置，最终任务不变。CPU29项通过；GPU原生接口回归PID2377737，日志logs/manager_4090/baseline_reward_integration.log。GitHub源码检索因开发机外网超时，已有本地原始提交可直接验证平方惩罚定义；不引入未验证外部方案。
- 修正后的GPU原生manager回归PASS（80reset/1强制翻倒/144指令重采样/初中末奖励一致）；开始32env实际WM/actor/critic更新和保存烟测PID2378486，日志logs/manager_4090/baseline_reward_smoke.log。

- 烟测完成，model20=logs/supermimic/2026-11-03_23-10-31_076350_baseline_reward_smoke/model_20.pt，真实WM/actor/critic更新及保存成功；恢复CLI验证PID2379347（20→24，省略调度参数），日志logs/manager_4090/baseline_reward_resume.log。

- 恢复验证PASS：model24三网络/优化器均更新且有限，CLI继承4/12调度和最终公式；开始32env/2秒评估PID2380247，日志logs/manager_4090/baseline_reward_eval.log；证据baseline_reward_regression.json。
- 修正初期奖励的全链路验证完成：CPU29项、原生GPU接口、实际三网络更新/保存/CLI恢复及32env短评估均PASS，全日志零PhysX/CUDA错误；短评估仅证明可执行，不作收敛依据。准备提交修复后以8192env/collect4/WM4096×4/imag8192/buffer256从Manager随机初始化重训。
