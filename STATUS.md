# 当前状态与恢复入口

核实时间：2026-11-04T13:36:55+08:00。权威目录 `/pfs/user/learning/amp_new`；SSH `ssh -p 9205 root@118.196.87.69`。
恢复先读 GOAL / PLAN / 本文件，再核实 HEAD、pipeline、实际 PID / GPU，避免重复启动。

## 版本、范围与控制决定

- 当前 HEAD `9fb00b305aea39a71944361b78d0a20cc8a81133`；本次受测训练内核 `20ad0d3a2490b0c2771b6c8d0b8748674832e0cf`，23 份训练相关源码 SHA256 与续训 pipeline 一致。HEAD 的文档及诊断工具不改变训练内核。
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

## 已排除方向、未解决问题与下一步

- 历史增加OU / 节流D / 真实TD / MPC / 补动态拟合 / 61→64→70 / 四帧均未通过 walk；旧Go2课程使G1移动但碎步。不能直接导入历史DC9000 WM。严重骨架错配 / RSI穿透无证据；RSI本机counter/同帧命令、奖励混合、state84终止及严格评估已修复。
- 新3000冻结H32普通实际/想象bootstrap3.297/2.297，参考.826/.318；梯度有限但参考线速度预测误差仍在。`logs/amp_g1/aligned_model_audit3000.json`。
- 配对首动作方向：32起点×10分支 / 8步预热，普通H32全关节±.1真实/模型中央斜率.231/2.751，参考.131/.335。正扰动相对零对照增益+.00106/-.00164，零对照差RMS.00294/.00597；不能据此证明有效更新。预热后配对状态仍有差异，分支未随机交换、未给置信区间、bootstrap共用critic，尚未排除配对噪声/critic偏差。JSON的余弦是跨样本斜率向量余弦，不是完整动作梯度夹角。证据 `logs/amp_g1/aligned_return_direction3000.json`。
- 下一项先复核并改进配对审计方法：统一控制历史、随机交换分支、记录动作/观测差异、加入零对照与成对置信区间、分离物理累计奖励和critic尾项；形成假设后检索适用公开方案。当前不盲续、不切PD、不做奖励网格，不把IdealPD表述为已验证修复。
- 完整结果 / 方法限制 / PD决定：[doc/G1_ALIGNED_3000_AND_PD_DECISION_2026-11-04.md](doc/G1_ALIGNED_3000_AND_PD_DECISION_2026-11-04.md)；历史源记录归档 docs/history/STATUS_2026-11-04_before_aligned_3000_handover.md 与对应PROGRESS文件；正式标准 G1_CONVERGENCE.md 不变。

下一条命令（核实进程后先审工具，不重复启动实验）：

```bash
cd /pfs/user/learning/amp_new
git rev-parse HEAD
cat logs/amp_g1/aligned_extension_r1.pipeline.json
ps -p 2951034,2951902,2956933 -o pid,ppid,etime,stat,args
nvidia-smi
sed -n '1,260p' scripts/g1_return_direction_audit.py
```
