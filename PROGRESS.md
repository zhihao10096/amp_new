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

- R3已保存model_1000，早期实际审计通过：actor/critic/WM/D优化器步数500/8400/4000/280，四网参数均更新且模型/优化器有限，随机来源/最终权重/任务/动作split一致；报告logs/amp_g1/formal_r3_early_checkpoint1000_audit.json。继续同一训练至3000再三点完整评估，不将更新审计视为行走收敛。

- 只读提取项目USD的12条腿部关节链并完成CPU足端几何原型：解析速度与autograd JVP最大误差1.55e-15。原型/数据仅在logs/amp_g1/g1_kinematics_*，尚未在PhysX验证，也未接入R3。后续用真实状态量化WM足端预测与关节几何的一致性，不凭原型内部检查宣称改进。

- USD几何原型与七份动作的训练split key_body_pos核对：足端世界坐标RMSE1.67e-7–3.19e-7m，支持项目资产/关节映射/原动作几何一致；未发现重定向骨架不匹配。证据logs/amp_g1/g1_kinematics_reference_consistency.json；仍需PhysX状态与WM预测的一致性检查，原型未接入训练。

- 已排队G1足端几何一致性诊断driver PID2645840，等待同一R3训练退出并释放显存后才启动GPU；状态logs/amp_g1/kinematics_r3.pipeline.json，不修改训练模型或队列。

- R3推进3000，最新logs/supermimic/2026-11-04_04-51-38_136861_g1_amp_formal_r3_exploration/model_3000.pt；几何诊断driver PID2645840已排队等待训练释放GPU。运行状态分别formal_r3.pipeline.json、kinematics_r3.pipeline.json；未启动其他正式训练。

- G1正式R3结束formal_r3_train，返回码0，日志logs/amp_g1/formal_r3_train.log。

- G1正式R3启动formal_r3_baseline_gait，PID2646457，命令/日志logs/amp_g1/formal_r3_baseline_gait.process.json及.log，状态logs/amp_g1/formal_r3.pipeline.json；不得重复启动。

- 启动G1真实足端几何/WM一致性诊断PID2646685，日志logs/amp_g1/kinematics_r3.log；原R3完整独立评估继续。

- G1真实足端几何/WM一致性诊断结束，报告logs/amp_g1/kinematics_r3.json；仅诊断，不能替代行走独立验收。

- G1正式R3结束formal_r3_baseline_gait，返回码0，日志logs/amp_g1/formal_r3_baseline_gait.log。

- G1正式R3启动formal_r3_velocity1000，PID2647590，命令/日志logs/amp_g1/formal_r3_velocity1000.process.json及.log，状态logs/amp_g1/formal_r3.pipeline.json；不得重复启动。

- R3已至3000并正常退出训练（returncode0），最新logs/supermimic/2026-11-04_04-51-38_136861_g1_amp_formal_r3_exploration/model_3000.pt。末训练线速度误差.66161、摔倒15.436/分钟、style.38457，仅训练信号；同一队列继续三点完整评估。几何诊断已完成，报告logs/amp_g1/kinematics_r3.json，待依据实际误差决定模型修复。

- 真实GPU几何核对完成：128env×256步混合RSI，FK足端位置max6.03e-6m、link速度max2.71e-5m/s，与PhysX一致。WM足端与其关节FK不一致从1步1.12mm至32步3.74mm；直接替换FK对32步真实足端预测RMSE仅12.71→12.59mm，暂无大幅改善证据，暂不增加几何投影结构。报告logs/amp_g1/kinematics_r3.json；根/足速度通道为COM，原型验证为link，已明确区分。

- G1正式R3结束formal_r3_velocity1000，返回码0，日志logs/amp_g1/formal_r3_velocity1000.log。

- G1正式R3启动formal_r3_gait1000，PID2649540，命令/日志logs/amp_g1/formal_r3_gait1000.process.json及.log，状态logs/amp_g1/formal_r3.pipeline.json；不得重复启动。

- G1正式R3结束formal_r3_gait1000，返回码0，日志logs/amp_g1/formal_r3_gait1000.log。

- G1正式R3 1000完整独立评估结束，速度失败30项、步态失败22项，报告logs/amp_g1/formal_r3_assessment1000.json；单次通过也不能代替连续三点/最终加噪/录像/审计。

- G1正式R3启动formal_r3_velocity2000，PID2650190，命令/日志logs/amp_g1/formal_r3_velocity2000.process.json及.log，状态logs/amp_g1/formal_r3.pipeline.json；不得重复启动。

- G1正式R3结束formal_r3_velocity2000，返回码0，日志logs/amp_g1/formal_r3_velocity2000.log。

- G1正式R3启动formal_r3_gait2000，PID2651947，命令/日志logs/amp_g1/formal_r3_gait2000.process.json及.log，状态logs/amp_g1/formal_r3.pipeline.json；不得重复启动。

- G1正式R3结束formal_r3_gait2000，返回码0，日志logs/amp_g1/formal_r3_gait2000.log。

- G1正式R3 2000完整独立评估结束，速度失败19项、步态失败15项，报告logs/amp_g1/formal_r3_assessment2000.json；单次通过也不能代替连续三点/最终加噪/录像/审计。

- G1正式R3启动formal_r3_velocity3000，PID2652562，命令/日志logs/amp_g1/formal_r3_velocity3000.process.json及.log，状态logs/amp_g1/formal_r3.pipeline.json；不得重复启动。

- 启动G1参考MPC诊断PID2653125（driver2653119）：同16个前向训练参考初态比较PD+速度前馈与冻结WM/H16/8次Adam/步，2s仅初态写状态；状态logs/amp_g1/reference_mpc_r3.process.json，日志reference_mpc_r3.log。正式R3三点评估继续。

- G1参考MPC诊断结束，返回码0，报告logs/amp_g1/reference_mpc_r3.json；仅采样行为/模型诊断，不是行走验收或正式训练来源。

- G1正式R3结束formal_r3_velocity3000，返回码0，日志logs/amp_g1/formal_r3_velocity3000.log。

- G1正式R3启动formal_r3_gait3000，PID2654726，命令/日志logs/amp_g1/formal_r3_gait3000.process.json及.log，状态logs/amp_g1/formal_r3.pipeline.json；不得重复启动。

- G1正式R3结束formal_r3_gait3000，返回码0，日志logs/amp_g1/formal_r3_gait3000.log。

- G1正式R3 3000完整独立评估结束，速度失败21项、步态失败15项，报告logs/amp_g1/formal_r3_assessment3000.json；单次通过也不能代替连续三点/最终加噪/录像/审计。

- G1正式R3训练/三检查点完整独立评估队列已结束；根据formal_r3_assessment1000/2000/3000.json决定续训或修复，若三点都过再最终加噪/录像/审计；不自动进入X1。

- 冻结WM参考MPC诊断完成：同16个前向参考初态，PD/前馈平均存活.779s，MPC/H16/8次Adam提高到1.442s、单脚支撑20.9%→56.0%；但两组均16/16在2s内摔倒，不接入正式训练。MPC真实一步速度预测误差.0984m/s（PD.0342），提示动态迈步分布仍是模型薄弱区。报告logs/amp_g1/reference_mpc_r3.json；后续先验证增加此类真实转移能否改善留出动力学误差，再决定采样行为改动，不把模型内部cost下降当成功。

- R3训练及三点完整独立评估已全部结束，父/子进程均退出；1000/2000/3000固定RMSE(.963,.299,.410)/(.649,.192,.438)/(.630,.240,.390)，摔倒1460/2/63，0.6m/s每足步频全部0。3000留出风格改善59.2%/59.0%，但实际仍原地站立；扩大OU噪声不足以解决问题，不继续原配置训练。汇总logs/amp_g1/formal_r3_summary.json及assessment/四网审计。当前无通过验收的最佳G1模型。下一步先导出更多MPC真实转移，按独立初态划分拟合/留出，检验动态模型误差是否可由覆盖改善，再决定采样实现。
