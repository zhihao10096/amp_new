# 当前状态与恢复入口

本轮最终核实：2026-11-04T10:33:32；GPU 1 MiB, 0 %，无计算进程。

历史核实时间：2026-11-04T10:23:12。权威项目目录`/pfs/user/learning/amp_new`；SSH `ssh -p 9205 root@118.196.87.69`。恢复先读GOAL/PLAN/PROGRESS，再查ps/GPU及pipeline，勿重复启动。旧记录见docs/history/STATUS_2026-11-04_before_history4_training.md。

## 版本、范围与当前阶段
- 当前HEAD `5f8c17e2e260296bccb7c9cdd1834dc3b72978d2`；四帧AMP实现与验证已完成并提交。默认两帧兼容；其他既有未提交文件以git status为准，保留reference及exploration/dynamics诊断文件。
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
每项工作在doc/保存解决思路；本轮doc/G1_AMP_TEMPORAL_HISTORY_2026-11-04.md。全程问题报告docs/experiments/G1_AMP_ISSUES_AND_SOLUTIONS_2026-11-04.md与四臂对照保留历史截止事实。

```bash
cd /pfs/user/learning/amp_new
nvidia-smi
cat logs/amp_g1/history4_validation.audit.json
cat logs/amp_g1/g1_amp_warm9000_feet70_history4_diag.pipeline.json
```

原四帧pipeline已完成，不再启动。下一条开发命令为阅读doc/G1_AMP_REFERENCE_COMMAND_ALIGNMENT_2026-11-04.md及env/mdp.py，先设计默认关闭的G1对齐开关和实际reset遥测；使用pending参考标志，不能照搬上游counter==0（本机reset回调counter=1）。新训练前必须CPU/GPU/恢复/兼容验证并提交。

- 70维四帧同源诊断启动g1_amp_warm9000_feet70_history4_diag，driver PID2823523、child PID2823690；命令/配置/日志见logs/amp_g1/g1_amp_warm9000_feet70_history4_diag.pipeline.json，仅单变量诊断，不是正式成功来源，勿重复启动。

- 70维四帧同源诊断结束g1_amp_warm9000_feet70_history4_diag，日志logs/amp_g1/g1_amp_warm9000_feet70_history4_diag.log；必须继续检查模型/独立报告，不以退出码或D分数代替成功。

- 70维四帧同源诊断启动g1_amp_warm9000_feet70_history4_diag_assessment，driver PID2823523、child PID2829046；命令/配置/日志见logs/amp_g1/g1_amp_warm9000_feet70_history4_diag.pipeline.json，仅单变量诊断，不是正式成功来源，勿重复启动。

- 70维四帧同源诊断结束g1_amp_warm9000_feet70_history4_diag_assessment，日志logs/amp_g1/g1_amp_warm9000_feet70_history4_diag_assessment.log；必须继续检查模型/独立报告，不以退出码或D分数代替成功。

- 70维四帧同源1000轮及model_0/1000独立七指令步态评估全部结束，报告logs/amp_g1/g1_amp_warm9000_feet70_history4_diag_assessment.json；下一步对照同源两帧70维和无AMP的步频/摆动/离地/足滑及速度，只有真实步态收益才延长。G1尚未宣布成功。
