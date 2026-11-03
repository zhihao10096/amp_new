# 进度与恢复入口

先读STATUS/GOAL/PLAN，核实HEAD、队列active_pid、GPU及产物，避免重复实验。

- Manager完成b1f59eb；A1完成37b6b58/7f49486。各自三连续检查点、最终加噪/录像与实际模型审计通过，模型分别checkpoints/go2_manager_converged.pt、a1_amp_converged.pt；无需重训。
- 当前G1平地walk，之后X1 AMP：X1仅下半身12DOF，复制实际动作后.gitignore忽略；部署配置参考reference/AMP，明确跳过RKNN。全程禁PPO，各阶段独立提交，G1/X1未成功前总目标未完成。
- G1参考f33a189/GitHub固定源一致；七份Walk_B及29DOF USD已复制项目assets/motions/g1、assets/robots/g1并保留来源/许可实际状态/SHA256/split/顺序。显式排除run/走跑转换/粗糙地形，适配本机Lab2.1而非直接导入Lab3参考。
- G1接入原生Manager，29act/83state/8gait/480obs、参考RSI、61维相邻帧AMP/LSGAN/GP及真实/想象共享奖励和DC电机；共用训练/回放/想象按维度参数化。正式速度/步态/独立风格与三检查点/加噪/录像/审计标准在训练前锁定G1_CONVERGENCE.md。
- CPU48项通过；GPU验证65reset/13终止/356切换、真实想象奖励/历史/终止快照，专家/PhysX max7.15e-7、编译返回max1.19e-7/actor梯度max1.46e-11。真实四网络四优化器更新/保存通过，CLI恢复20→25步数actor16→21/critic36→46/WM20→25/D18→23且继续更新/有限。A1 GPU回归通过。证据logs/amp_g1/{integration_initial,smoke_initial.audit,smoke_resume.audit,a1_regression}.json。
- G1完整初始步态和留出风格可执行（诊断基线3.5375/3.5631，未收敛）；实现验证队列已退出。当前性能队列串行4k/8k/12k/16k，固定WM4096×4/imag8192×H32/AMP2048×2/buffer128；4k稳定1.61万真实转移/s、峰值14382MiB。PID/活跃子任务/日志见STATUS及logs/amp_g1/performance_queue.json，性能模型不作正式来源。

下一步：完成并行数实测，确认评估/验收负例后提交实现，从随机初始化正式G1训练并保存model_0；按锁定标准持续训练/独立评估，不把短检查称收敛。G1成功提交后再实施X1。

历史事件docs/history/PROGRESS_2026-11-04_g1_implementation.md；原始日志保留路径和结论，不复制到记录。
