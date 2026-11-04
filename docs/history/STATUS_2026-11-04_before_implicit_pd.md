# 当前状态与恢复入口

## 当前工作

- 2026-11-04T11:28:12+08:00 用户明确要求G1不使用DC模型。正在恢复`legged_lab`隐式PD/固定力矩上限，去掉G1真实与想象路径的转速降额；旧DC checkpoint禁止直接resume/warm-start/eval到新动力学，新模型记录`g1_implicit_pd_v1`。仅控制修复，奖励/AMP混合/RSI不同时改。源码基线8f63846，运行目录`/pfs/user/learning/amp_new`；CPU/GPU验证尚待启动，当前无本项目训练。
- 上轮四方源码审计PID2851914已退出，JSON/log均生成且passed：上游相对style/task系数为本项目4倍（假定同task），全29DOF L1偏移惩罚额外约束hip_pitch/knee；这些是公式差异证据，尚非碎步因果结论。证据`logs/amp_g1/go2_a1_g1_legged_lab_source_audit.json`。GPU有其他项目进程，启动验证前复核并记录，不终止未知进程。

- 2026-11-04T11:10:43+08:00 用户最新要求：取消未启动的AMP权重网格，优先Go2/A1/reference/legged_lab系统对照；当前无训练进程，三份权重pipeline JSON均不存在。生产奖励/RSI暂不修改。对照将覆盖AMP混合/缩放/dt、奖励公式、动作/PD、reset命令和训练来源。

- 2026-11-04T11:01:22+08:00 用户要求的小碎步A1/G1对比与RSI解释已完成，报告[doc/A1_G1_SMALL_STEP_COMPARISON_2026-11-04.md](doc/A1_G1_SMALL_STEP_COMPARISON_2026-11-04.md)，本地doc/副本已同步。源码核对基线1b1cc86；本轮仅CPU诊断/文档，没有生产修改或新训练。
- 两轮CPU诊断PID2839319/2840503均退出，process为complete。命令/配置/日志/输出：logs/amp_g1/a1_g1_small_step_comparison_probe[及_r2].process.json；核验5行同1m/s物理指标、4行冻结D及实际D更新计数通过，a1_g1_small_step_comparison.audit.json。
- 新结论：A1/G1同1m/s摆动.1750/.0926s、离地20.77/12.36mm；gait_duration权重-8/-.5，但尚无该项闭环消融。RSI参考-随机命令冲突约55%为共有问题，不能单独解释G1；A1 D冻结速度更敏感但实际D更新1400/280及LR/GP不同，不能混合归因。参考几何阈值代理不作为接触标签。
- 原下一变量仍为默认关闭的两帧70维RSI对齐，尚未实现；本轮对比已降低“RSI是G1特有根因”的证据强度。其后时长约束、D优化强度、参考连续片段分别消融，不混改。报告/交接文档已提交8f63846，本地副本一致且中央弹窗已显示。

## 本轮文档交付

- 2026-11-04T10:44:53+08:00 用户要求的G1 AMP全程问题/方案/效果报告已完成，入口[doc/G1_AMP_ISSUES_AND_SOLUTIONS_2026-11-04.md](doc/G1_AMP_ISSUES_AND_SOLUTIONS_2026-11-04.md)，docs/experiments同名报告同步；本地doc/与artifacts/有交付副本。61条路径、12行/60项指标、7份动作Git/SHA256核验通过，审计logs/amp_g1/g1_issues_review_20261104.audit.json。本轮无新训练；RSI对齐仍未实现。报告/交接文档已提交1b1cc86，实验/源码核对基线45712b3；本地主机中央弹窗已确认显示，交付副本SHA256一致。

本轮最终核实：2026-11-04T11:01:22+08:00；GPU 1 MiB, 0 %，无计算进程。

历史核实时间：2026-11-04T10:23:12。权威项目目录`/pfs/user/learning/amp_new`；SSH `ssh -p 9205 root@118.196.87.69`。恢复先读GOAL/PLAN/PROGRESS，再查ps/GPU及pipeline，勿重复启动。旧记录见docs/history/STATUS_2026-11-04_before_history4_training.md。

## 版本、范围与当前阶段

- 当前HEAD `8f63846a6571f7a434c69fd1b81a6afe040c9cd7`（A1/G1小碎步对比文档提交；已验证四帧实现5f8c17e）；已验证实现提交5f8c17e。默认两帧兼容；其他既有未提交文件以git status为准，保留reference及exploration/dynamics诊断文件。
- Manager与A1 AMP已独立完成；G1 walk仍未成功。G1只平地/walk/29DOF，SuperMimic世界模型与可微想象，全程禁PPO；G1全部标准通过后才进入X1下半身12DOF，RKNN不在X1范围。
- 七份G1实际动作在Git管理assets/motions/g1/，80%训练/20%留出；新增/替换先复制/追踪/SHA256及来源许可归档。X1动作的忽略规则仅对X1生效。

## 当前进程、运行目录与配置

- 四帧完整验证driver2818662已complete，全部子进程退出；audit logs/amp_g1/history4_validation.audit.json。1000轮同源诊断和model_0/1000七指令评估均已完成，pipeline complete；原driver2823523/训练2823690/评估2829046均退出，勿重复启动。
- CPU68通过history4_cpu_r2.log；真实GPU原生/编译/四网20→25/CLI四帧继承/A1回归及独立步态接口全部完成。默认两帧相对af59616的D一步更新、回放采样、G1想象回报及actor梯度逐位一致，history4_default2_compatibility.json。
- 诊断配置锁定：G1-AMP-Flat、g1_amp_70_feet_v1、amp_num_frames=4；同9000来源、18432env、1000迭代、seed0；WM4096×4/window8/hidden512×3、imag8192/H32、critic3×4、actor/critic512,256,128、actor_lr_scale=.15、WM预热300/critic200/actor_ramp500、collect1/buffer128、FP32 highest/compile；OU .6占25%，其余Gaussian .1。
- AMP D2048×2/interval5/lr1e-5/GP40/weight.5/ramp1000/RSI.5。仅时序2→4（20→60ms），特征/奖励/数据/RSI不改；回放逻辑最早2个起点因历史不足排除，物理采集/WM采样不变，此限制写入思路文档。

## 最新与最佳checkpoint

- 最新训练诊断：logs/supermimic/2026-11-04_10-24-56_796290_g1_amp_warm9000_feet70_history4_diag/model_1000.pt（四帧70维，model_0保留；未通过walk）。
- 四帧接口短跑：logs/supermimic/2026-11-04_10-19-52_306675_g1_history4_smoke_resume/model_25.pt；仅验证，不是正式训练来源。
- 上轮两帧对照：logs/supermimic/2026-11-04_09-49-14_815830_g1_amp_warm9000_feet70_diag/model_1000.pt（70维两帧，保留model_0）；七指令零摔但未达walk。
- 稳定运动/下一诊断来源：logs/supermimic/2026-11-04_08-00-37_784295_g1_velocity_cold_start18432_to9000/model_9000.pt；G1随机谱系+3000→5000奖励课程，无AMP，不能称G1 AMP成功。
- 最后直接随机AMP正式来源：logs/supermimic/2026-11-04_04-51-38_136861_g1_amp_formal_r3_exploration/model_3000.pt；R1/R2/R3均失败。不存在已验收G1最佳/已收敛checkpoint。
- 已完成阶段归档checkpoints/go2_manager_converged.pt、checkpoints/a1_amp_converged.pt，无须重训。

## 最近指标与结论

- 9000来源前进/快走vx=.601/.999，七指令零摔；步频3.672/4.258Hz、腾空.087/.093s、离地7.20/14.10mm，未达walk。
- 70维两帧1000轮vx=.5932/1.0199、步频3.533/3.800Hz、腾空.0815/.0913s、离地7.13/14.18mm、足滑.1072/.2087m/s；七指令零摔但未通过。风格内部改善23.95%/19.02%，不能跨schema直接比绝对距离。
- 四帧1000轮vx=.56589/.94685、步频3.70456/3.89226Hz、摆动.08454/.09259s、离地6.12/12.36mm、足滑.07337/.17637m/s，七组零摔但未通过；风格内部改善30.03%/26.95%，不延长原配置。
- 四帧25轮随机短跑评估共803摔，风格距3.4829/3.4801；只证明评估接口，不能算步态收益。四帧1000轮已完成，七指令零摔但步态未通过。

## 已排除方向与未解决问题

- 严重RSI穿透和骨架/关节映射错误假设未获支持；旧随机AMP单独增加OU/节流D/真实TD0-.5、补动态拟合/局部响应/MPC均无稳定步行收益，不重复原样加码。
- Go2启动流程使G1稳定移动，但碎步/短摆动/低抬脚未解决；无AMP/61/64/70维两帧对照均未通过。四帧1000轮未解决碎步，停止原配置延长；下一单变量为两帧70维RSI命令对齐，尚未实现/启动，随后参考筛选/辅助奖励分开消融。
- 24576完整actor更新OOM、32768 PhysX allocator错误均作废；保持已验证18432，四帧完整反传已完成，峰值23122MiB/观测GPU97%，不以预热吞吐作容量结论。
- 全套速度/三连续点/加噪/录像/实际模型审计仍未通过；G1/X1总目标保持未完成。

## 文档与下一条执行命令

每项工作在doc/保存解决思路；本轮doc/A1_G1_SMALL_STEP_COMPARISON_2026-11-04.md，四帧思路doc/G1_AMP_TEMPORAL_HISTORY_2026-11-04.md。全程问题报告doc/G1_AMP_ISSUES_AND_SOLUTIONS_2026-11-04.md已更新至四帧负结果，docs/experiments同名报告同步；四臂对照保留其历史截止事实。

```bash
cd /pfs/user/learning/amp_new
nvidia-smi
git status --short
sed -n '1,180p' doc/G1_IMPLICIT_PD_RESTORE_2026-11-04.md
OMP_NUM_THREADS=2 .venv/bin/python -m pytest tests -q
```

本轮先完成隐式PD修复的CPU与真实GPU验证、四网更新/保存恢复、旧DC拒绝和A1回归，然后单独提交。尚未启动新收敛实验；旧9000及两/四帧G1模型均为DC动力学，不能作为隐式PD成功模型或直接导入世界模型。RSI对齐/奖励网格暂停。新训练从新PD随机来源建立谱系，待完成对照再确定启动配置。思路`doc/G1_IMPLICIT_PD_RESTORE_2026-11-04.md`。


历史四帧启动/结束事件保存在PROGRESS.md与全程复盘，不重复启动已完成队列。

- 2026-11-04T11:30:43.135817+08:00 隐式PD完整CPU75通过；GPU验证driver PID2858666已启动，状态logs/amp_g1/implicit_pd_validation.pipeline.json。将核对原生PD驱动、编译、同PD velocity→AMP热启动、四网20→25保存恢复及A1回归；非收敛训练。

- 2026-11-04T11:30:44.518658+08:00 隐式PD验证启动implicit_pd_reject_old_resume，driver PID2858666、child PID2858779；命令/配置/日志见logs/amp_g1/implicit_pd_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T11:30:47.548538+08:00 隐式PD验证结束implicit_pd_reject_old_resume，返回码1，预期拒绝=True，证据logs/amp_g1/implicit_pd_reject_old_resume.log。

- 2026-11-04T11:30:47.553505+08:00 隐式PD验证启动implicit_pd_reject_old_warm-start，driver PID2858666、child PID2858805；命令/配置/日志见logs/amp_g1/implicit_pd_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T11:30:50.584068+08:00 隐式PD验证结束implicit_pd_reject_old_warm-start，返回码1，预期拒绝=True，证据logs/amp_g1/implicit_pd_reject_old_warm-start.log。

- 2026-11-04T11:30:50.585415+08:00 隐式PD验证启动implicit_pd_integration，driver PID2858666、child PID2858852；命令/配置/日志见logs/amp_g1/implicit_pd_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T11:31:48.144176+08:00 隐式PD验证结束implicit_pd_integration，返回码0，预期拒绝=False，证据logs/amp_g1/implicit_pd_integration.log。

- 2026-11-04T11:31:48.145821+08:00 隐式PD验证启动implicit_pd_velocity_smoke，driver PID2858666、child PID2859860；命令/配置/日志见logs/amp_g1/implicit_pd_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T11:32:30.569571+08:00 隐式PD验证结束implicit_pd_velocity_smoke，返回码0，预期拒绝=False，证据logs/amp_g1/implicit_pd_velocity_smoke.log。

- 2026-11-04T11:32:30.575378+08:00 隐式PD验证启动implicit_pd_smoke_initial，driver PID2858666、child PID2860665；命令/配置/日志见logs/amp_g1/implicit_pd_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T11:32:40.122420+08:00 用户允许IdealPD备选；当前先验证上游隐式PD，不引入第二个控制变量。原生GPU验证已passed：所有驱动为ImplicitActuator、PhysX Kp/Kd精确对应配置，Lab同状态力矩估算误差0，编译返回max1.79e-7/actor梯度max2.91e-11；65reset/11摔倒/54超时/355命令切换。后续driver继续短跑四网保存恢复/A1回归。

- 2026-11-04T11:33:22.216697+08:00 隐式PD验证结束implicit_pd_smoke_initial，返回码0，预期拒绝=False，证据logs/amp_g1/implicit_pd_smoke_initial.log。

- 2026-11-04T11:33:22.240634+08:00 隐式PD验证启动implicit_pd_smoke_resume，driver PID2858666、child PID2861584；命令/配置/日志见logs/amp_g1/implicit_pd_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T11:33:46.495111+08:00 隐式PD验证结束implicit_pd_smoke_resume，返回码0，预期拒绝=False，证据logs/amp_g1/implicit_pd_smoke_resume.log。

- 2026-11-04T11:33:46.502882+08:00 隐式PD验证启动implicit_pd_a1_regression，driver PID2858666、child PID2862118；命令/配置/日志见logs/amp_g1/implicit_pd_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T11:34:06.263567+08:00 AMP站立门控CPU只读探针启动PID2862594，执行固定上游原方法与当前D；不改参数、不训练，输出logs/amp_g1/upstream_amp_command_gate_probe.json。

- 2026-11-04T11:34:06.273009+08:00 AMP站立门控CPU探针结束passed：相同D score=1时本项目stand/walk原始style为0/1，上游均1；属已验证公式差异，不是闭环根因。证据upstream_amp_command_gate_probe.json。

- 2026-11-04T11:34:07.756146+08:00 隐式PD验证结束implicit_pd_a1_regression，返回码0，预期拒绝=False，证据logs/amp_g1/implicit_pd_a1_regression.log。

- 2026-11-04T11:34:07.757699+08:00 隐式PD验证启动implicit_pd_smoke_gait，driver PID2858666、child PID2862646；命令/配置/日志见logs/amp_g1/implicit_pd_validation.pipeline.json。仅接口验证，勿重复启动。

- 2026-11-04T11:35:11.419129+08:00 隐式PD验证结束implicit_pd_smoke_gait，返回码0，预期拒绝=False，证据logs/amp_g1/implicit_pd_smoke_gait.log。

- 2026-11-04T11:35:11.420126+08:00 隐式PD CPU/原生GPU/想象编译梯度/同控制velocity→AMP热启动/四网20→25/旧DC恢复拒绝/A1回归/七指令评估接口均完成。短跑不证明walk收敛。

- 2026-11-04T11:37:56.012769+08:00 隐式PD验证全部完成，driver2858666退出，pipeline/audit passed；原生力矩估算误差0，四网20→25更新actor16→21/critic36→46/WM20→25/D3→4；A1真实GPU回归及最终三点审计均通过，旧DC审计新增执行器拒绝通过。model25七指令829摔，仅验证评估接口，不是收敛。无本项目GPU作业，保留其他项目约5895MiB使用。准备更新文档并提交控制修复。
