# G1 AMP 参考重置与命令对齐：方案前置核对

## 问题及优先级

当前四帧时序实验运行中，不修改其配置或生产代码。若其仍不能改善短摆动/低抬脚，下一独立候选为RSI参考帧与速度指令对齐。既有离线统计约55.09%随机命令与参考初态的平面速度差>.5m/s，但尚无真实reset遥测或闭环因果证明，不能提前称为根因。

## 现成方案与适配风险

reference/legged_lab固定f33a189的AmpVelocityCommand从同一参考帧读取world速度，变到机体系后限幅；仅reset对齐，回合中间随机重采样。其代码注释和逻辑使用command_counter==0辨认reset，假定计数在_resample_command之后增加。

本机Lab2.1源码核对发现不同：CommandTerm.reset先将counter置0，但_resample在调用_resample_command前已+1，因此reset回调看到counter=1。直接照搬上游==0会静默失效。ManagerBasedRLEnv._reset_idx顺序为reset事件→action/reward等manager→command manager→episode_length_buf清零，也不能使用episode_length_buf辨认reset。

依据文件：
- reference/legged_lab/source/legged_lab/legged_lab/tasks/locomotion/amp/mdp/commands/velocity_command.py
- .venv/lib/python3.10/site-packages/isaaclab/source/isaaclab/isaaclab/managers/command_manager.py
- .venv/lib/python3.10/site-packages/isaaclab/source/isaaclab/isaaclab/envs/manager_based_rl_env.py

## 拟采用的最小适配

由reset_robot保存同一参考帧的机体系vx/vy/wz和实际use_reference标志；BodyVelocityCommand在随后command reset中消费一次pending标志，而不依赖版本特有counter。普通reset和中途重采样仍随机；显式fixed_command优先。只对G1新增默认关闭开关，不更换数据/AMP历史/奖励；与四帧试验分开对照。

训练前需验证真实reset：参考初态速度、原随机指令、对齐/限幅后指令、RSI比例、待消费标志清除；检查部分reset、首次reset、超时/摔倒和fixed_command不会泄漏。yaw使用机体系wz且限幅，避免参考尖峰形成长期极端指令。之后仍用普通站立reset独立评估，不能用参考初态短期存活声称walk成功。

当前仅完成只读研究，尚未实现或启动该实验；先完成原四帧队列。时序/对齐/辅助奖励互不叠加，最终验收不变。
