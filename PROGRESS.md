# 进度与恢复入口

恢复先读STATUS/GOAL/PLAN，再核实HEAD、formal_r2.pipeline.json及active_pid/GPU/检查点；不得重复启动。

- 总目标：Manager/A1已独立成功，当前G1平地walk，之后X1下半身12DOF AMP；全程禁PPO、WM可微想象，各阶段独立提交，G1/X1未成功前总目标未完成。
- Manager b1f59eb、A1 37b6b58/7f49486完成全部三点/加噪/录像/审计；模型checkpoints/go2_manager_converged.pt、a1_amp_converged.pt；无需重训。
- 用户G1数据要求已落实PLAN：所有实际动作（含新增/替换）复制assets/motions/g1并纳入Git；现有七份Walk_B/顺序/split/SHA256与HEAD核对一致。README的MIT与LICENCE的Apache-2.0冲突已纠正记录并保留原文，未修改动作字节或训练metadata。
- G1 29act/83state/8gait/480obs与61维两帧AMP接入原生Lab2.1 plane；接口/编译梯度/实际四网四优化器/保存恢复/A1回归通过，验收训练前锁定G1_CONVERGENCE.md。并行4k–18k后选18432，保留完整学习batch。
- R1随机初始化及同源1000→3000全结束，三检查点完整评估均失败：1000高摔，2000主要站立（固定仅1摔但步频0），3000退化（固定159摔、风格也失败）；停止同配置盲目续训，完整结果/来源审计见logs/amp_g1/formal_r1_assessment{1000,2000,3000}.json。
- 定位：普通站立分布WM无整体爆炸，严重RSI穿透未获支持，不照搬上游+.1m；连续参考关节PD/前馈仍几乎全摔，暂不作为采样行为。D能给全摔的静态参考姿态≈1风格分，存在姿态捷径；状态梯度非完全零。各诊断路径见STATUS，不用这些短诊断作行走验收。
- GitHub参考项目Issue28的同症状缓解已核实；新增amp_update_interval（默认1保留旧行为），并修复显式恢复amp_lr覆盖优化器。CPU50项通过；实际GPU interval5下20→25的D3→4，其余三网继续更新；旧缺字段检查点仍D18→23，CLI继承/显式lr覆盖均通过。证据discriminator_throttle_validation.audit.json。
- 修复已提交754e1fd（标签g1-amp-discriminator-ready-20261104）。正式R2随机初始化训练已至3000并正常退出；原队列PID2611110正在formal_r2_gait2000（active_pid=2626599），目录logs/supermimic/2026-11-04_04-14-08_351497_g1_amp_formal_r2_throttled，最新model_3000.pt。仅D interval5/lr1e-5/GP40改变，任务/数据/标准不变；1000完整评估速度30项/步态28项失败，风格改善27.1%/23.2%；2000/3000待完成。
- X1仅只读预查，待G1独立成功提交后实施；动作复制进项目后.gitignore忽略，清单纳入Git，部署配置参考reference/AMP，跳过RKNN；保留reference和其他原未跟踪文件。

下一步：`cat logs/amp_g1/formal_r2.pipeline.json && tail -n 2 logs/amp_g1/formal_r2_train.log && nvidia-smi`，核实同一队列，重点检查D信号/真实跟踪与独立评估；不得重复启动或降标准。

历史与失败细节：[R1定位](docs/history/STATUS_2026-11-04_g1_r1_diagnosis.md)、G1_CONVERGENCE.md；原始日志仅保留路径和结论，不复制进上下文文档。

- R2训练末D专家/策略.374/-.648、style.320，线速度误差.6307、摔倒12.54/分钟；D信号改善但未证明实际行走收益。3000诊断录像0.6m/s指令下平均vx=.001088m/s，主要原地站立；报告r2_diagnostic_video.json、视频videos/g1_r2_diagnostic_walk3000.mp4。等待同一队列完整独立结果，不重复启动、不以短录像判收敛。
- 本次将G1参考动作复制并Git管理列为PLAN必要验收条件，明确新增/替换后重复核验；七份Walk_B的Git追踪/manifest SHA256/HEAD逐字节复核通过。证据logs/amp_g1/g1_motion_tracking_recheck.json；不改变运行配置或模型。

- G1正式R2结束formal_r2_gait2000，返回码0，日志logs/amp_g1/formal_r2_gait2000.log。

- G1正式R2 2000完整独立评估结束，速度失败15项、步态失败14项，报告logs/amp_g1/formal_r2_assessment2000.json；单次通过也不能代替连续三点/最终加噪/录像/审计。

- G1正式R2启动formal_r2_velocity3000，PID2627218，命令/日志logs/amp_g1/formal_r2_velocity3000.process.json及.log，状态logs/amp_g1/formal_r2.pipeline.json；不得重复启动。
