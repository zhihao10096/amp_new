# 进度与恢复入口

恢复先读STATUS/GOAL/PLAN，再核实HEAD、formal_r2.pipeline.json及active_pid/GPU/检查点；不得重复启动。

- 总目标：Manager/A1已独立成功，当前G1平地walk，之后X1下半身12DOF AMP；全程禁PPO、WM可微想象，各阶段独立提交，G1/X1未成功前总目标未完成。
- Manager b1f59eb、A1 37b6b58/7f49486完成全部三点/加噪/录像/审计；模型checkpoints/go2_manager_converged.pt、a1_amp_converged.pt；无需重训。
- 用户G1数据要求已落实PLAN：所有实际动作（含新增/替换）复制assets/motions/g1并纳入Git；现有七份Walk_B/顺序/split/SHA256与HEAD核对一致。README的MIT与LICENCE的Apache-2.0冲突已纠正记录并保留原文，未修改动作字节或训练metadata。
- G1 29act/83state/8gait/480obs与61维两帧AMP接入原生Lab2.1 plane；接口/编译梯度/实际四网四优化器/保存恢复/A1回归通过，验收训练前锁定G1_CONVERGENCE.md。并行4k–18k后选18432，保留完整学习batch。
- R1随机初始化及同源1000→3000全结束，三检查点完整评估均失败：1000高摔，2000主要站立（固定仅1摔但步频0），3000退化（固定159摔、风格也失败）；停止同配置盲目续训，完整结果/来源审计见logs/amp_g1/formal_r1_assessment{1000,2000,3000}.json。
- 定位：普通站立分布WM无整体爆炸，严重RSI穿透未获支持，不照搬上游+.1m；连续参考关节PD/前馈仍几乎全摔，暂不作为采样行为。D能给全摔的静态参考姿态≈1风格分，存在姿态捷径；状态梯度非完全零。各诊断路径见STATUS，不用这些短诊断作行走验收。
- GitHub参考项目Issue28的同症状缓解已核实；新增amp_update_interval（默认1保留旧行为），并修复显式恢复amp_lr覆盖优化器。CPU50项通过；实际GPU interval5下20→25的D3→4，其余三网继续更新；旧缺字段检查点仍D18→23，CLI继承/显式lr覆盖均通过。证据discriminator_throttle_validation.audit.json。
- 修复已提交754e1fd（标签g1-amp-discriminator-ready-20261104）。正式R2队列PID2611110、当前active_pid=2611283，运行目录logs/supermimic/2026-11-04_04-14-08_351497_g1_amp_formal_r2_throttled；最新logs/supermimic/2026-11-04_04-14-08_351497_g1_amp_formal_r2_throttled/model_0.pt。新随机seed0，不热启动，仅D interval5/lr1e-5/GP40，其他配置/任务/数据/阈值保持；到3000保存并完整独立评估1000/2000/3000，尚未收敛。
- X1仅只读预查，待G1独立成功提交后实施；动作复制进项目后.gitignore忽略，清单纳入Git，部署配置参考reference/AMP，跳过RKNN；保留reference和其他原未跟踪文件。

下一步：`cat logs/amp_g1/formal_r2.pipeline.json && tail -n 2 logs/amp_g1/formal_r2_train.log && nvidia-smi`，核实同一队列，重点检查D信号/真实跟踪与独立评估；不得重复启动或降标准。

历史与失败细节：[R1定位](docs/history/STATUS_2026-11-04_g1_r1_diagnosis.md)、G1_CONVERGENCE.md；原始日志仅保留路径和结论，不复制进上下文文档。

- 正式R2 model_0已完成随机来源/四优化器全新/任务、动作split/SHA256及Git资产副本审计；与R1 model_0的actor/critic/WM/D全部逐位一致，任务与动作metadata相同，确保仅判别器优化控制的对比，证据formal_r2_initial_audit.json、formal_r2_initial_comparison.json。当前WM/critic预热，不作收敛判断。
