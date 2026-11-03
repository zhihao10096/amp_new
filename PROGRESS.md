# 进度与恢复入口

恢复先读STATUS/GOAL/PLAN，核实HEAD、队列active_pid及GPU，避免重复启动。

- 总目标：Manager/A1已独立成功 → G1平地walk → X1下半身12DOF AMP；禁PPO，WM可微想象，G1/X1未成功前总目标未完成。
- Manager/A1三点/加噪/录像/实际审计均通过并提交，归档checkpoints/go2_manager_converged.pt、a1_amp_converged.pt；勿重训。G1参考动作已复制assets/motions/g1并Git管理，七份SHA256/HEAD复核通过；新增/替换也必须归档提交。
- G1原生Lab2.1 plane接口、编译梯度、四网更新/恢复和A1回归通过；CPU50项及D节流实际计数/旧模型兼容通过。代码754e1fd，验收预先锁定G1_CONVERGENCE.md，18432环境保留完整学习批次。
- R1三点失败；R2仅判别器节流，训练到3000后三点完整评估仍全部失败：固定RMSE(.805,.331,.391)/(.648,.191,.440)/(.637,.226,.410)、摔倒1620/2/52、0.6m/s步频均0。D信号/风格改善未解决实际步行，停止两轮同配置续训；formal_r2_summary.json及assessment/模型审计是依据。
- 动作响应加入零扰动对照后，普通站立组接触求解噪声与响应同量级，不能证明模型梯度错误；参考组1步cos=.838、4步=.312，暂不改WM结构。action_response_r2{,_control}.json。
- 真实噪声覆盖：OU .3→.6，单脚支撑5.75%→20.93%、接触变化1.17→3.35/s、腾空仍<.2%；噪声越大摔倒也增加。Gaussian .6以上腾空>7%暂不采用。noise_coverage_r2.json；GitHub SHAC可微随机actor已核实，只参考思路，不移植算法/参数。
- 决定R3新随机初始化，仅OU .3→.6，仍25%OU/其余Gaussian.1；18432环境及R2其他学习/任务/奖励/数据/验收不变，到3000并完整评估1000/2000/3000。初始审计要求与R2四网逐位一致、cfg仅噪声/run_name/stop_file变化；队列脚本已准备，尚未启动。
- 已排除普通站立WM整体爆炸、严重RSI穿透及直接参考PD采样；D存在姿态捷径，不以风格分当成功。X1待G1成功提交后实施，动作复制后.gitignore忽略、清单入Git，部署参考reference/AMP并跳过RKNN；保留原未跟踪文件。

下一步：提交本轮决定，核实无R3重复进程/停止文件后启动formal_r3.pipeline.py，立即补PID/源commit/目录；再读同一队列状态。历史与报告路径见STATUS.md及G1_CONVERGENCE.md，不复制原始日志。
