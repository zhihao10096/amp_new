# 当前状态与恢复入口

核实时间：2026-11-04T12:38:18+08:00。权威目录`/pfs/user/learning/amp_new`；SSH `ssh -p 9205 root@118.196.87.69`。先读GOAL/PLAN/本文件并核对HEAD、PID、GPU和产物，不重复启动实验。旧状态快照`docs/history/STATUS_2026-11-04_before_rsi_alignment.md`。

## 当前代码、范围与决定

- 当前HEAD eee92bbc9b6fdbbbea5dc9e6d82b09133b18cdbe；RSI/严格评估/四帧审计修复已全部验证，待单独提交，之后更新准确HEAD。奖励对齐29b1875，隐式PD f32755e。
- Manager/A1已独立完成；G1仅29DOF平地walk、SuperMimic世界模型/可微想象、禁PPO；成功后才做X1下半身12DOF，跳过RKNN，其他部署参考reference/AMP。总目标未完成。
- G1执行器g1_implicit_pd_v1（固定限矩，无DC转速降额；IdealPD仅备选），state_schema=g1_state84_base_contact_v1（WM84/critic125、actor480）；旧DC与旧83维WM禁止训练复用，旧隐式PDactor仍可评估。
- reward_profile=g1_legged_lab_walk_v1的16项及最终R=.5*task+dt*style已对齐，站立style开启。训练终止height<.2或torso/pelvis接触；独立评估同时保留height<.5或60°倾角越界计数，报告必须有fall_definition=native_or_height05_tilt60_v1。零fall/速度/步态/风格门槛保持。
- RSI amp_reset_command_alignment默认False，只有G1 AMP可开；同帧速度裁剪到walk命令范围，一次性pending适配Lab2.1，无counter猜测；普通/回合中随机、fixed优先、评估关闭。下一个新基线显式启用，CLI/checkpoint记录。
- 七份G1参考动作在assets/motions/g1由Git追踪，来源/SHA256/split保留，本轮复核通过。A1/G1新增动作仍须提交，X1动作按GOAL复制后忽略。

## 当前进程与配置

- 暂无本项目训练/验证进程。RSI driver2907230及所有子进程退出，logs/amp_g1/rsi_alignment_validation.pipeline.json为complete，audit为passed，不重启。终止driver2896882和上游奖励driver2883115也均完成。
- 本轮仅32env接口短跑：velocity8轮→AMP20轮→CLI续到25轮（开关True）→显式关闭续到30。WM64×2、actor/critic64,32、WM/imag batch32/H4、buffer32/window4、collect2；D64,32/batch64/interval5/lr1e-5→2e-5/GP40；61维四帧，FP32编译。实际命令/日志/run/config/PID见pipeline各jobs。
- 下一已确定阶段：完整actor profiling 16384/18432，18432峰值有余量才试20480，必要时12288回退；学习批次固定WM4096×4/window8、imag8192/H32、critic3×4、buffer128/collect1。只用有有效完整更新checkpoint且无OOM/PhysX错误的吞吐选择规模。
- 随后另起全新随机G1 AMP1000轮（不继承profile/旧模型）；61维四帧、RSI.5/对齐True、既有探索.3/actor_lr_scale.15、D512,256/2048×2/lr1e-5/GP40/interval5/最终混合.5，WM预热300/critic200/actor_ramp500/AMP_ramp1000，FP32编译。先独立0/1000七指令及1000完整速度，再决定后续，不开网格。

## 最新与最佳checkpoint

- 最新接口模型（显式关闭）：logs/supermimic/2026-11-04_12-33-11_262546_g1_rsi_alignment_smoke_disabled/model_30.pt，仅30轮，不是行走候选。
- 已启用RSI的25轮接口模型：logs/supermimic/2026-11-04_12-32-46_954366_g1_rsi_alignment_smoke_resume/model_25.pt；初始20轮logs/supermimic/2026-11-04_12-32-19_648885_g1_rsi_alignment_smoke_initial/model_20.pt。
- 新PD/84维/上游奖励下无已验收最佳或已收敛G1模型。历史DC9000稳定移动来源与70维四帧1000负结果保留在旧STATUS快照，不能导入新PD世界模型。
- 已完成阶段checkpoints/go2_manager_converged.pt、checkpoints/a1_amp_converged.pt，无需重训。

## 最近证据与指标

- CPU92通过，logs/amp_g1/rsi_alignment_cpu.log；同帧真实GPU59参考/70普通reset，最大速度/命令误差4.17e-7，编译返回5.96e-8/梯度3.73e-9，默认关闭/旧profile/fixed/定时/历史/终止均通过。
- 四网/优化器20→25→30：actor16→21→26、critic36→46→56、WM20→25→30、D3→4→5，CLI自动继承和显式关闭均正确；rsi_alignment_validation.audit.json。
- 随机25轮七指令严格越界/终止采样6258，风格距4.18055/4.20943；只证明接口，不能证明walk收敛。短速度报告2s/settle0，只是接口，不能当完整30s验收。
- A1原生GPU回归及实际三checkpoint完整审计仍converged；旧G1 DC/schema负例按预期拒绝。rsi_alignment_convergence_audit_regression.json。
- 终止原生1851次oracle一致、CPU88通过；奖励16项原函数oracle最大项9.76e-13、task1.95e-14。历史证据对应contact_termination/upstream_reward_validation.audit.json。

## 已排除方向与未解决问题

- 历史增加OU/节流D/真实TD/MPC/补动态拟合/61→64→70/四帧均未通过最终walk；Go2课程使旧G1稳定移动但仍碎步，不原样加码。严重骨架错配/RSI穿透未获支持，A1/G1随机命令冲突55%是共有现象。
- 本机counter原方法确认reset1/timed2，上游counter0不能直搬；已用pending修复接口，尚无训练收益结论。
- 代理力矩/加速度与原生末子步量存在差异，接触计时有控制周期量化与想象松弛；直接yaw-rate不同于上游heading控制，RSI.5保持混合；不能称完整原生MDP等价。
- 本项目D仍512/256 LeakyReLU和统一decay1e-4，上游1024/512 ELU及输出decay.1；下一基线先检验已修复的控制/奖励/终止/RSI组合，不叠加D变量。若仍失败再按收益/证据排序。
- 新控制大规模完整更新容量尚未测；历史18432约23GiB、24576完整更新OOM/32768PhysX错误，不能以预热吞吐/32env短跑证明容量。
- G1三连续点、最终噪声、录像/人工检查/完整审计未完成；X1未开始。

## 文档与下一条命令

思路/限制/证据：doc/G1_RSI_COMMAND_ALIGNMENT_2026-11-04.md、G1_TERMINATION_ALIGNMENT_2026-11-04.md；正式门槛G1_CONVERGENCE.md不变。

```bash
cd /pfs/user/learning/amp_new
git rev-parse HEAD
git status --short
nvidia-smi
cat logs/amp_g1/rsi_alignment_validation.audit.json
```

下一执行：提交已验证RSI/严格评估/四帧审计，然后启动唯一aligned_baseline_r1.pipeline.py队列（先确认pipeline.json不存在且无同名进程）；该队列顺序profiling→新随机1000训练→独立评估，禁止重复启动。
