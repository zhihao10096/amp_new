# 进度与恢复入口

恢复先读STATUS/GOAL/PLAN，核实HEAD、队列active_pid及GPU，避免重复启动。

- 总目标：Manager/A1已独立成功 → G1平地walk → X1下半身12DOF AMP；禁PPO，WM可微想象，G1/X1未成功前总目标未完成。
- Manager/A1三点/加噪/录像/实际审计均通过并提交，归档checkpoints/go2_manager_converged.pt、a1_amp_converged.pt；勿重训。G1参考动作已复制assets/motions/g1并Git管理，七份SHA256/HEAD复核通过；新增/替换也必须归档提交。
- G1原生Lab2.1 plane接口、编译梯度、四网更新/恢复和A1回归通过；CPU50项及D节流实际计数/旧模型兼容通过。代码754e1fd，验收预先锁定G1_CONVERGENCE.md，18432环境保留完整学习批次。
- R1三点失败；R2仅判别器节流，训练到3000后三点完整评估仍全部失败：固定RMSE(.805,.331,.391)/(.648,.191,.440)/(.637,.226,.410)、摔倒1620/2/52、0.6m/s步频均0。D信号/风格改善未解决实际步行，停止两轮同配置续训；formal_r2_summary.json及assessment/模型审计是依据。
- 动作响应加入零扰动对照后，普通站立组接触求解噪声与响应同量级，不能证明模型梯度错误；参考组1步cos=.838、4步=.312，暂不改WM结构。action_response_r2{,_control}.json。
- 真实噪声覆盖：OU .3→.6，单脚支撑5.75%→20.93%、接触变化1.17→3.35/s、腾空仍<.2%；噪声越大摔倒也增加。Gaussian .6以上腾空>7%暂不采用。noise_coverage_r2.json；GitHub SHAC可微随机actor已核实，只参考思路，不移植算法/参数。
- 决定R3新随机初始化，仅OU .3→.6，仍25%OU/其余Gaussian.1；18432环境及R2其他学习/任务/奖励/数据/验收不变，到3000并完整评估1000/2000/3000。初始审计要求与R2四网逐位一致、cfg仅噪声/run_name/stop_file变化；已提交决定9bc7115并启动队列PID2636134/训练PID2636299；状态logs/amp_g1/formal_r3.pipeline.json。
- 已排除普通站立WM整体爆炸、严重RSI穿透及直接参考PD采样；D存在姿态捷径，不以风格分当成功。X1待G1成功提交后实施，动作复制后.gitignore忽略、清单入Git，部署参考reference/AMP并跳过RKNN；保留原未跟踪文件。

下一步：读取formal_r3.pipeline.json并核实同一训练PID，补实际运行目录、初始审计及最新检查点，跟进真实迈步与完整独立评估；不得重复启动。历史与报告路径见STATUS.md及G1_CONVERGENCE.md，不复制原始日志。

- G1正式R3启动formal_r3_train，PID2636299，命令/日志logs/amp_g1/formal_r3_train.process.json及.log，状态logs/amp_g1/formal_r3.pipeline.json；不得重复启动。

- G1正式R3 model_0随机来源/四优化器全新/任务与动作split/SHA256及Git资产副本审计通过，证据logs/amp_g1/formal_r3_initial_audit.json；尚未收敛。

- R3 model_0初始审计通过：四网与R2逐位一致、四优化器全新、task/split/SHA256/Git资产一致；cfg仅explore_noise/run_name/stop_file变化，证据logs/amp_g1/formal_r3_initial_audit.json。训练已实际推进50（WM预热），不作收敛判断。

- 2026-11-04T04:55:14.663735核实同一R3 PID2636299训练至800；最新logs/supermimic/2026-11-04_04-51-38_136861_g1_amp_formal_r3_exploration/model_0.pt，无已验收最佳模型。训练线速度误差0.63146、摔倒53.613/分钟、actor梯度0.50006；GPU实测峰值约23124MiB、利用率86%。此为训练过程信号，不是行走结果。精确快照logs/amp_g1/formal_r3_latest_observation.json；继续同一队列至3000及三点完整评估。
