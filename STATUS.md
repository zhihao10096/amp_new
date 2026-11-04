# 当前状态与恢复入口

核实时间：2026-11-04T12:55:53+08:00。权威目录 `/pfs/user/learning/amp_new`；SSH `ssh -p 9205 root@118.196.87.69`。
恢复先读 GOAL/PLAN/本文件，再核实 HEAD、pipeline、PID 和 GPU，避免重复启动。

## 版本、范围和决定

- 当前 HEAD `20ad0d3a2490b0c2771b6c8d0b8748674832e0cf`；训练受测源码 `20ad0d3a2490b0c2771b6c8d0b8748674832e0cf`，23份源码SHA256一致。控制f32755e、奖励29b1875、终止eee92bb、RSI/严格评估/四帧审计20ad0d3。
- Manager/A1已独立完成；G1仅29DOF/平地/walk，SuperMimic世界模型与可微想象，禁PPO。G1成功后才做X1下半身12DOF，跳过RKNN，部署参考reference/AMP；总目标未完成。
- 控制 `g1_implicit_pd_v1`，固定限矩88/139/25/5Nm，无DC转速降额；用户允许IdealPD备选，已核对其显式PD/固定限矩源码。当前无隐式PD故障证据，保持与legged_lab一致；切换执行器须独立类型/新WM谱系，不直接续用旧动力学。
- state `g1_state84_base_contact_v1`（WM84/critic125/actor480）；旧DC/83维WM禁止训练复用，旧隐式PD actor可独立评估。reward `g1_legged_lab_walk_v1`，16项及最终R=.5task+dtstyle。
- 训练height<.2/torso或pelvis接触终止；独立评估保留height<.5/tilt>60°，`fall_definition=native_or_height05_tilt60_v1`。严格越界采样可连续累计，不等于独立摔倒回合数。
- G1七份动作 `assets/motions/g1/` Git/SHA256复核7/7通过。A1/G1实际动作须由项目Git管理，X1复制后按GOAL忽略。

## 唯一队列、运行目录和配置

- 队列 `logs/amp_g1/aligned_baseline_r1.pipeline.json`，driver `2915722`，阶段 `complete`，active PID `None`；driver和训练/评估子进程均已核对退出，GPU0%/1MiB，无当前作业。勿重复启动。
- 正式run `logs/supermimic/2026-11-04_12-45-04_890456_g1_aligned_formal_r1`；配置同目录 `config.json`；训练日志 `logs/amp_g1/aligned_formal_r1.log`；评估日志/完整命令/PID见pipeline.jobs。
- profiling16384/18432完整反传通过：约46307/50820真实转移/s、峰值22196/23208MiB；选四网更新且无OOM/PhysX错误的18432。按余量跳过20480，不代表已OOM。汇总 `logs/amp_g1/aligned_performance_summary.json`。
- 正式18432env/随机seed0/model0→1000，不继承profile权重；WM512×3/batch4096×4/window8，actor/critic512,256,128，imag8192/H32，critic3×4，buffer128/collect1，FP32最高精度/编译。
- AMP61维四帧，D512,256/2048×2/lr1e-5/GP40/interval5/AMP ramp1000；RSI.5/同帧命令对齐True，评估关闭。OU.3/25%+Gaussian.1，actor_lr_scale.15；WM预热300/critic200/actor ramp500。

## 最新/最佳模型和评估

- 最新 `logs/supermimic/2026-11-04_12-45-04_890456_g1_aligned_formal_r1/model_1000.pt`，初始同目录 `model_0.pt`。新PD下无已验收最佳/收敛G1模型；profile/接口模型不是行走候选。
- 1000训练正常退出，actor/critic/WM/D更新500/8400/4000/280，四网/优化器有限且参数变化，随机来源审计通过，峰值23374MiB；1000总迭代包含500轮预热，actor仅更新500次。证据 `logs/amp_g1/aligned_formal_r1_update_audit.json`。
- 独立七指令20s×8env共24项失败：0.6/1m/s每足步频0/.013Hz、腾空0/.085s，vx RMSE1.387/1.440；严格fall/越界采样608/614。风格距4.204→2.648、4.210→2.634（约37%改善），仍未学会稳定行走。原始 `logs/amp_g1/aligned_formal_r1_gait0_1000.json`。
- 完整速度30s/96env/12固定+3随机已完成，单点passed=False：速度30项失败、步态24项失败；固定整体RMSE(vx/vy/yaw)=1.293/.533/.613，三随机vx RMSE1.281–1.300。完整速度输出 `logs/amp_g1/aligned_formal_r1_velocity1000.json`；单点结论 `logs/amp_g1/aligned_formal_r1_assessment1000.json`，以pipeline阶段为准。不能代替三连续点、加噪、录像和最终审计。
- 已完成接口回归：CPU92、原生GPU/编译梯度、四网保存恢复、RSI/严格评估/四帧metadata、旧DC/schema拒绝及A1三点审计passed，见 `logs/amp_g1/rsi_alignment_validation.audit.json`。本轮仅文档变更，不重跑GPU训练。
- 已完成模型 `checkpoints/go2_manager_converged.pt`、`checkpoints/a1_amp_converged.pt` 保留，无需重训。

## 已排除方向、未解决问题和下一步

- 历史增加OU/节流D/真实TD/MPC/补动态拟合/61→64→70/四帧未通过walk；旧Go2课程使G1移动但碎步。历史DC9000不能导入新PD WM。严重骨架错配/RSI穿透无证据支持；A1/G1随机命令冲突约55%是共有现象。
- RSI本机counter1/2差异、默认关闭/同帧命令、严格评估及四帧审计均已修复。接口通过不证明训练收益，1000早期点失败也不证明隐式PD是根因。
- 仍需区分仅500次actor更新与稳定性/WM梯度问题；先读完整速度/checkpoint报告，再决定有证据的单变量验证，不开权重网格或盲切IdealPD。
- 已知差异：端点力矩/控制周期加速度与接触计时代理、yaw-rate而非heading、混合RSI、D512/256 LeakyReLU及统一decay（上游1024/512 ELU/输出decay.1）；尚无独立因果结论。
- 历史已归档 `docs/history/PROGRESS_2026-11-04_before_aligned_result.md`、`docs/history/STATUS_2026-11-04_before_aligned_result.md`；本轮思路/结果 `doc/G1_ALIGNED_BASELINE_2026-11-04.md`，PD候选 `doc/G1_IMPLICIT_PD_RESTORE_2026-11-04.md`，正式标准 `G1_CONVERGENCE.md` 不变。

下一条命令：

```bash
cd /pfs/user/learning/amp_new
git rev-parse HEAD
cat logs/amp_g1/aligned_baseline_r1.pipeline.json
cat logs/amp_g1/aligned_formal_r1_assessment1000.json
ps -p 2915722,2927150 -o pid,ppid,etime,stat,args
nvidia-smi
```

下一阶段先读 `logs/amp_g1/aligned_formal_r1_assessment1000.json`，审计仅500次actor更新与实际策略/WM响应，再决定训练时长或IdealPD单变量对照；尚未启动。

- 2026-11-04T12:56:59+08:00 原队列已于2026-11-04T12:54:17.660648+08:00完成并退出，GPU0%/1MiB；1000单点passed=False，步态失败24项、速度失败30项。固定整体RMSE(vx/vy/yaw)=1.293/0.533/0.613，三随机种子vx RMSE1.281–1.300；没有已验收G1最佳模型，X1未开始。本轮未修改训练源码或启动额外实验，IdealPD仍为允许的独立候选，不能将当前失败归因于隐式PD。
