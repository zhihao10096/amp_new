# 当前状态与恢复入口

## 目标、版本与目录
- 开发机权威目录`/pfs/user/learning/amp_new`；SSH `ssh -p 9205 root@118.196.87.69`。本地旧镜像`/home/user/Desktop/dream_codex_workspace/amp_new_src`仅供参考。
- 当前代码/正式R2 commit `754e1fd8410fc1fbd805461d17ced77e018c5209`，标签`g1-amp-discriminator-ready-20261104`。恢复先`git rev-parse HEAD`/`git status --short`核实；运行期间后续文档提交不改变训练来源。
- 总目标：Manager/A1已独立成功 → 当前G1 AMP平地walk → G1成功并提交后才X1 AMP行走；全程SuperMimic WM/可微想象，禁止PPO，各阶段独立验收/提交。
- X1仅下半身12DOF；部署配置参考reference/AMP，跳过RKNN；实际动作复制项目后.gitignore忽略，来源/许可/SHA256/split清单纳入Git。X1仅只读预查，尚未实施。
- 保留未跟踪reference/、exploration.py、explore_eval.py、dynamics_eval.py、test_exploration.py，勿误提交或改写。

## 当前进程、配置与路径
- 核实时间2026-11-04 04:15:05 CST：正式R2队列PID2611110、当前子进程PID2611283，阶段`formal_r2_train`；均以`logs/amp_g1/formal_r2.pipeline.json`实际active_pid为准，恢复需ps/GPU核实，不得重复启动。R1、续训、诊断和节流验证队列均已结束。
- 队列脚本`logs/amp_g1/formal_r2.pipeline.py`，启动`formal_r2.launch.json`，源/命令`formal_r2_train.process.json`，日志`formal_r2_train.log`；运行目录`logs/supermimic/2026-11-04_04-14-08_351497_g1_amp_formal_r2_throttled`。
- 正式R2：新随机初始化seed0，无resume/warm-start/参考控制。18432env/collect1/buffer128；WM4096×4/window8/hidden512×3，imag8192/H32，actor/critic512,256,128，critic3×4；actor_lr_scale=.15，WM预热300+critic200/actor_ramp500；FP32 highest/compile。
- 仅判别器配置改为AMP2048×2、每5个预热后全局迭代更新一次、lr1e-5、GP40（原每迭代/lr1e-4/GP10）；hidden512,256、最终weight.5/ramp1000/RSI.5及任务/动作/split/验收不变。CLI恢复继承AMP配置，显式amp-lr覆盖优化器保存值。
- R2训练到3000，保存0/1000/2000/3000，再初始baseline及三个检查点分别完整速度/步态/留出风格评估。若三点都过，再最终加噪/录像/审计。停止文件`logs/amp_g1/stop_formal_r2`可请求保存后退出；先核实原因，勿带着旧停止文件重启。

## 最新/最佳检查点与指标
- R2最新`logs/supermimic/2026-11-04_04-14-08_351497_g1_amp_formal_r2_throttled/model_0.pt`；初始审计见`formal_r2_initial_audit.json`。R2尚未独立评估，尚无通过验收的最佳或已收敛G1模型。最新路径随队列JSON更新，不能仅凭此快照判断进度。
- R1原目录`logs/supermimic/2026-11-04_03-23-40_354760_g1_amp_formal_r1`含model_0/1000；续训目录`logs/supermimic/2026-11-04_03-36-52_174804_g1_amp_formal_r1_to3000`含2000/3000。全部完整独立评估失败，四网络/四优化器及随机来源审计通过；不作热启动或成功来源。
- R1 1000：固定RMSE .839/.314/.380、1501摔，风格改善30.2%/25.6%；2000固定.651/.192/.427、1摔/随机13/8/4摔，但主要原地站立，步频0；3000固定.623/.308/.340、159摔，随机112/112/106摔，风格3.3283/4.4518也失败。证据`formal_r1_assessment{1000,2000,3000}.json`及原始velocity/gait报告。
- A1已完成：`checkpoints/a1_amp_converged.pt`（3000，SHA256 09a16f5f8bc4bcbf64a1c2dfd80010d3756b5c09224cc706d9a717b155a533ed），1000/2000/3000、加噪/录像/来源审计通过；最终固定RMSE .0498/.0524/.0385，风格改善36.3%/40.7%，证据AMP_CONVERGENCE.md及logs/amp_a1/convergence_report.json。勿重训。
- Manager已完成：`checkpoints/go2_manager_converged.pt`，7000/8000/9000、加噪/录像/实际审计通过，证据MANAGER_CONVERGENCE.md。勿重训。

## 验证、数据与已排除方向
- G1原生Manager接口/真实想象奖励/终止历史/RSI/编译梯度、实际四网更新与CLI恢复、A1GPU回归均通过；专家/PhysX特征max7.15e-7，编译返回1.19e-7、梯度1.46e-11。证据logs/amp_g1/integration_initial.json、smoke_initial.audit.json、smoke_resume.audit.json、a1_regression.json。
- 节流修复CPU50项（48跟踪+原未跟踪exploration2项）通过cpu_discriminator_throttle.log；真实GPU/编译/保存恢复通过discriminator_throttle_validation.audit.json：interval5下20→25，actor16→21/critic36→46/WM20→25/D3→4；旧检查点缺字段仍interval1、D18→23；显式恢复D lr2e-5生效。此为接口验证，不是收敛。
- R1普通reset动力学未整体爆炸：1/32步线速度RMSE .0141/.0475，32步高度.00461、gravity .0192，formal_r1_dynamics3000.json；不能证明迈步分布准确。
- RSI严重穿透假设不获支持：128同帧×0/.05/.1m对比，0偏移脚link最低.02735m，无link低于地面、首步最大速度1.069m/s且.4s无摔；+.1反而增大自由落体。保持原高度，报告reference_reset_diagnostic_r2.json。
- 连续参考关节PD/速度前馈2s内127–128/128摔，暂不接入采样。静态参考姿态虽全摔，D仍≈+.996/style≈1，actor≈-.996/style≈.004，存在姿态捷径；actor输入style梯度范数≈.99，不能说完全零梯度。报告reference_behavior_diagnostic_r2.json。首跑诊断索引/UTF8/Lab3参数错误已修正，失败日志保留。
- 已在GitHub参考项目Issue28找到同症状，作者建议节流D；仅采用判别器优化控制，未移植PPO/其奖励尺度。原文github_legged_lab_issue28.json，决策与锁定标准见G1_CONVERGENCE.md。R1同配置盲目续训、直接导入Lab3参考、run/走跑转换/粗糙地形均排除。
- 实际G1七份Walk_B与manifest在`assets/motions/g1/`受Git管理，SHA256与HEAD一致；默认加载go2_supermimic/g1.py:31。前80%训练/RSI，后20%留出，采样/插值/差分不跨边界；29DOF USD在assets/robots/g1。后续新增/替换动作也必须复制并提交。
- 源legged_lab f33a189：README声明MIT、LICENCE为Apache-2.0，两者冲突；原文及SHA256均已保留在数据目录，运动特定授权未说明。GitHub核实upstream_license_verification.json；此前“无独立LICENSE”表述已纠正。
- RTX4090D24GB；.venv Python3.10.12/Torch2.5.1+cu124/Lab2.1/Sim4.5。并行实测4k–18k后选18432（约5.41万真实转移/s、初始峰值23108MiB；R1恢复峰值23918MiB），保留完整学习批次。仿真清PYTHONPATH，OMNI_KIT_ACCEPT_EULA=YES、OMNI_KIT_ALLOW_ROOT=1、TORCHINDUCTOR_COMPILE_THREADS=4；Kit后写中文文档须encoding=UTF-8。开发机无rg/系统python，使用.venv/bin/python。

## 未解决与下一条命令
- G1行走尚未收敛；R2需验证节流是否改善D信号、真实迈步与独立验收。不得降阈值，不以吞吐/训练奖励/风格单项或短跑代替收敛。
- 下一条命令：`cat logs/amp_g1/formal_r2.pipeline.json && tail -n 2 logs/amp_g1/formal_r2_train.log && nvidia-smi`；核对active_pid/运行目录/最新检查点后跟进同一队列。若parent失败但active_pid仍活着，先检查该子进程，不重复启动。三检查点评估完成后依据formal_r2_assessment1000/2000/3000.json决定继续或修复。
- X1待G1成功并单独提交后才接入；只读预查logs/amp_x1/reference_prereview.json（源6189ae4）已提示旧31DOF审计工具与当前12DOF策略接口不一致，需按实际源/数据核对，跳过RKNN。

历史：[R1失败与诊断](docs/history/STATUS_2026-11-04_g1_r1_diagnosis.md)、[G1实现](docs/history/STATUS_2026-11-04_g1_implementation.md)、[A1](docs/history/STATUS_2026-11-04_a1_final_eval.md)、[Manager](docs/history/PROGRESS_2026-11-04_manager.md)。

- 正式R2 model_0已完成随机来源/四优化器全新/任务、动作split/SHA256及Git资产副本审计；与R1 model_0的actor/critic/WM/D全部逐位一致，任务与动作metadata相同，确保仅判别器优化控制的对比，证据formal_r2_initial_audit.json、formal_r2_initial_comparison.json。当前WM/critic预热，不作收敛判断。
