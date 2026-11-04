# 当前状态与恢复入口

核实时间：2026-11-04T13:54:29+08:00。权威目录 `/pfs/user/learning/amp_new`；SSH `ssh -p 9205 root@118.196.87.69`。
恢复先读 GOAL / PLAN / 本文件，再核实 HEAD、pipeline、实际 PID / GPU，避免重复启动。

## 版本、范围与控制决定

- 当前 HEAD `cddcbde66235e12d1a0ac33c477ab11485745768`；本次受测训练内核 `20ad0d3a2490b0c2771b6c8d0b8748674832e0cf`，23 份训练相关源码 SHA256 与续训 pipeline 一致。HEAD 的文档及诊断工具不改变训练内核。
- Manager / A1 已独立完成；G1 仅 29DOF / 平地 / walk，沿用 SuperMimic 世界模型和可微想象，禁 PPO。G1 成功后才做 X1 下半身 12DOF，部署参考 reference/AMP，跳过 RKNN；总目标未完成。
- G1 控制 `g1_implicit_pd_v1`：上游隐式 PD，固定限矩 88 / 139 / 25 / 5 Nm，无 DC 转速降额。用户允许 Isaac Lab IdealPD 候选；当前无隐式 PD 缺陷证据，暂不切换。后续若对照须独立类型及新 WM 谱系。
- state `g1_state84_base_contact_v1`（WM84 / critic125 / actor480），reward `g1_legged_lab_walk_v1`，16 项及最终 `R=.5task+dt*style`。旧 DC / 83 维 WM 禁止直接训练复用。
- 训练 height<.2 / torso 或 pelvis 接触终止；独立评估仍为 height<.5 / tilt>60°，`fall_definition=native_or_height05_tilt60_v1`。严格越界采样可连续累计，不等于独立摔倒回合数。
- A1 / G1 实际参考动作已在项目 assets/motions 下由 Git 管理，G1 七份动作及 SHA256 复核通过。X1 动作复制后忽略、清单入 Git，按 GOAL 执行。

## 进程、运行目录与配置

- 续训及两点完整评估 `logs/amp_g1/aligned_extension_r1.pipeline.json` 已 **complete**。训练 driver2938989 / child2939097、仅评估恢复 driver2951034 / child2951152 / 2952473 均退出；当前 active_pid=null。
- 冻结模型 `logs/amp_g1/aligned_model_audit3000.pipeline.json`、配对方向 `logs/amp_g1/aligned_return_direction3000.pipeline.json` 均 **complete**；原 driver2951902 / child2951903、driver2956933 / child2956934 均退出。GPU 核实 0% / 1 MiB，无本项目作业。不重复训练 / 评估。
- 正式续训目录 `logs/supermimic/2026-11-04_13-09-39_985939_g1_aligned_formal_r1_to3000`，配置同目录 `config.json`，训练日志 `logs/amp_g1/aligned_extension_train3000.log`；完整命令与 PID 以 pipeline.jobs 为准。
- 来源 `logs/supermimic/2026-11-04_12-45-04_890456_g1_aligned_formal_r1/model_1000.pt`，使用四网 / 四优化器 `--continue-run` 到 3000，不重计数或重复预热；随机对照为同来源目录 model_0.pt。
- 18432env / seed0，WM512×3 / batch4096×4 / window8，actor 和 critic512,256,128，imag8192 / H32，critic3×4，buffer128 / collect1，FP32最高精度 / 编译。
- AMP61 四帧，D512,256 / batch2048×2 / lr1e-5 / GP40 / interval5 / ramp1000；RSI.5 / 同帧命令对齐 True，评估关闭。OU.3 / 25% + Gaussian.1，actor_lr_scale.15；WM预热300 / critic200 / actor ramp500。
- 完整反传 profiling：16384 / 18432 环境约 46307 / 50820 真实转移/s，选18432（+9.7%）。续训峰值24134MiB、无OOM/PhysX错误；余量不足未试20480，不等于20480已OOM。

## 最新 / 最佳模型与评估

- 最新 `logs/supermimic/2026-11-04_13-09-39_985939_g1_aligned_formal_r1_to3000/model_3000.pt`；SHA256 `426459ba148ddff2e907d7c74336d02b09dbaf5c8593d501f26e3fd7db846ce0`。**无已验收 G1 最佳 / 收敛模型**；2000 是保留的中间点。
- 2000 / 3000 四网及配置审计 passed，actor / critic / WM / D 更新数分别 1500/20400/8000/680、2500/32400/12000/1080。训练正常结束；旧审计 list / tuple 误判已仅恢复审计修正，未重训，原失败记录保留。
- 完整速度 30s / 96env / 12固定+3随机：2000 / 3000 失败项 30 / 19；固定整体 RMSE(vx/vy/yaw) 为 .944/.480/.497、.646/.204/.461。3000 固定严格fall/越界采样94；三随机vx RMSE .659/.649/.648、严格采样81/43/69，均未通过。证据 `logs/amp_g1/aligned_extension_velocity2000_3000.json`。
- 七指令步态20s×8：2000 / 3000 失败22 / 15项。3000 六组零严格fall，转弯16；0.6 / 1m/s 实际vx约.00404/.00370，步频/腾空/净空均0，vx RMSE .596/.996。稳定站立，未迈步；风格距.612/.796不能代替行走。证据 `logs/amp_g1/aligned_extension_gait2000_3000.json`。
- 1000此前速度/步态失败30/24项；续训证实稳定性改善，未验证起步。三连续点、加噪、录像及最终收敛审计尚未通过。已完成模型 checkpoints/go2_manager_converged.pt、checkpoints/a1_amp_converged.pt 保留。
- 本次CPU `pytest -q tests` **92 passed**，`logs/amp_g1/aligned_extension_cpu.log`。此前原生GPU / 编译梯度 / 四网恢复 / A1回归通过，见 `logs/amp_g1/rsi_alignment_validation.audit.json`。

## 冷启动决定（2026-11-04T14:xx+08:00）

- 仍需参考 Go2 的“先基础速度/步态、再最终奖励”的冷启动思路；当前 G1 AMP 随机初始化 3000 轮只站立，不能据此跳过冷启动。
- 当前实现的 `G1-Velocity-Flat` 已存在但尚未正式运行/验收；它关闭 AMP、使用同一 G1 隐式 PD/平地/动作和任务定义，输出可作为后续 G1 AMP 的 actor/世界模型 warm-start。
- 最近 G1 AMP 配置是固定命令范围 `vx[0,1.2]、vy[-.3,.3]、yaw[-.8,.8]`，没有速度范围课程；`reward_curriculum_start/end=0` 对 `g1_legged_lab_walk_v1` 也不产生 Go2 式奖励渐进。WM/critic 预热、actor ramp 和 AMP 权重 ramp 属于优化/AMP 接入时序，不能替代速度冷启动。
- 下一条工作：先从 G1 随机 `model_0` 启动 `G1-Velocity-Flat`，独立评估是否能迈步；若失败，先修 G1 基础速度训练/奖励/动力学接口。若成功，再用同机器人 actor/WM warm-start `G1-AMP-Flat`，重新创建 critic、判别器和优化器。不得直接续训当前 AMP model_3000。

## 最新诊断、未解决问题与下一步

- 首动作随机配对v2两seed1701/2026均complete：128组×14分支，8步共同动作预热；普通起点+.03全关节的128步纯物理奖励增益+.01056[.00369,.02144]、+.00500[.00426,.00575]，参考同项CI跨0。前动作/命令配对一致，状态/观测接触差仍在。证据 logs/amp_g1/randomized_return3000_r2.pipeline.json 及两seed.json。
- 完整actor临时Adam一步v3两seed均complete：256组×6随机分支，恢复原Adam动量、3001轮lr2.92874e-5/grad_clip1。普通128步纯物理奖励增益+.00784[.00721,.00848]、+.00742[.00676,.00806]；参考+.00548[.00038,.01287]、+.00496[.00038,.01029]。普通H32模型bootstrap改进约.0703/.0656，实际.00763/.00709，幅度仍高估。证据 logs/amp_g1/policy_step3000.pipeline.json 及两seed.json。
- 上述区间为2048次克隆组bootstrap，条件于当前reset分布，未做多重比较校正。临时Adam使用当前起点批次，不能等同生产replay/持续四网交互。参考128步原生存活仅30.9%/23.0%，仍未验证walk；不能把局部回报改善解释为收敛。
- 新审计原driver2968029/child2968031及其第二seed子进程、driver2972307及两seed子进程均结束，active_pid=null。当前无作业，未启动新长训，正式最新仍为model3000，无已验收最佳，X1未开始。受测工具副本 logs/amp_g1/policy_step3000_tested_source.py，SHA256 ff9d5272bb0e019c5cbbcd24598415c7bdcefabe25097259ea2791816a173e20；最终源码仅校正描述文字。
- 第一轮审计后台缺README既有OMNI_KIT_ACCEPT_EULA=YES，在AppLauncher导入前EOF，未进入物理仿真；已按项目既有启动环境修复，失败证据 logs/amp_g1/randomized_return3000.pipeline.json 保留。没有学习结论，不重复原失败配置。
- 用户询问当前课程：已核对正式config与源码，速度从开始固定vx[0,1.2]/vy±.3/yaw±.8，无速度范围课程；16项任务奖励亦无渐进课程。WM300/critic200预热后501轮起更新actor；D305起每5轮2步，AMP占比w=.5*min(iter/1000,1)，最终R=.5task+dt*style。RSI.5且首次命令对齐。本轮没有调整课程或AMP权重。
- 历史增加OU/节流D/真实TD/MPC/动态拟合/61→64→70/四帧未通过walk；旧DC WM不能导入新PD。RSI本机counter/命令对齐、奖励混合、终止state84和严格评估已修复。
- 新证据不支持普通局部梯度完全无效或完整参数一步必然损害真实回报；停止重复该方向审计，不据此归咎隐式PD或切IdealPD。仍需定位参考动态状态的训练覆盖/存活及上游D实现/样本预算差异；当前D512/256 LeakyReLU、专家+策略归一化/统一decay，上游1024/512 ELU、策略更新归一化/输出层独立decay，interval计数与样本复用率须按物理采样量核对，尚未确认因果。
- 完整结果与当前课程见 [doc/G1_RANDOMIZED_GRADIENT_AUDIT_2026-11-04.md](doc/G1_RANDOMIZED_GRADIENT_AUDIT_2026-11-04.md)；正式G1/X1验收不变。旧事件归档 docs/history/STATUS_2026-11-04_before_randomized_gradient_result.md 与对应PROGRESS。CPU检查见 logs/amp_g1/randomized_return_cpu_final.log。

下一条命令（核实HEAD/进程后核对上游D与采样预算，不重复梯度实验）：

```bash
cd /pfs/user/learning/amp_new
git rev-parse HEAD
cat logs/amp_g1/policy_step3000.pipeline.json
nvidia-smi
sed -n 85,130p reference/legged_lab/source/legged_lab/legged_lab/rsl_rl/amp/ppo_amp.py
sed -n 255,338p reference/legged_lab/source/legged_lab/legged_lab/rsl_rl/amp/ppo_amp.py
sed -n 390,427p go2_supermimic/supermimic/train.py
```

- 2026-11-04T13:55:49+08:00 随机分支/完整Adam诊断、当前课程说明及交接记录已提交 `cddcbde66235e12d1a0ac33c477ab11485745768`；最终CPU92通过，GPU四任务正常结束、无本项目活动作业。提交后仅回填HEAD，不改变正式训练内核/模型。

- 2026-11-04T14:00:24+08:00 上一轮为progress(cddcbde，两seed真实首动作/完整Adam验证改变下一步)，当前已核实旧作业结束/GPU空闲。新假设：当前D实现偏离已验证legged_lab（ELU1024/512、policy-only归一化/eps.01/无clip/1e8冻结、优化后更新统计、输出decay.1）。已核对GitHub固定f33a189及RSL-RL v5.4.1；本机旧rsl normalizer.forward会自动更新，而5.4.1不会，不能据本机旧模块推断上游统计。决定实现独立legged_lab_v1 D profile，旧模型按legacy加载，A1保持兼容；先CPU/oracle/真实GPU编译四网恢复验证，再新随机来源容量profiling及受控训练，不改PD、16项奖励、混合/RSI或做奖励网格。D样本预算先量化，不与组件对齐同时改变。
