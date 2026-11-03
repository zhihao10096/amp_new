# 当前状态与恢复入口

## 目标、版本与目录
- 权威目录`/pfs/user/learning/amp_new`，SSH `ssh -p 9205 root@118.196.87.69`；本地旧镜像仅供参考。恢复先读GOAL/PLAN/本文件/PROGRESS，再核实HEAD、队列PID与GPU，避免重复启动。
- R3来源commit `9bc7115a082eafc403d5f8fb2947d10e3cac38b2`（训练代码与已验证754e1fd相同，后续为文档提交）；当前文档HEAD以`git rev-parse HEAD`核实，训练来源见formal_r3.launch.json/process.json。
- Manager/A1已完成 → 当前G1平地walk → 成功提交后X1下半身12DOF AMP。全程WM可微想象、禁PPO，各阶段独立验收和提交。X1部署配置参考reference/AMP、跳过RKNN；其动作复制项目后.gitignore忽略，来源/许可/SHA256/split清单入Git。
- 保留未跟踪reference/、exploration.py、explore_eval.py、dynamics_eval.py、test_exploration.py，勿误提交或改写。

## 进程与下一轮配置
- R2原队列PID2611110及所有训练/评估子进程均已退出，状态formal_r2.pipeline.json为assessment3000_complete；三份完整评估均失败，不续训原配置。动作响应/零对照/噪声覆盖诊断也均退出，报告已解析。2026-11-04T04:51:09核实R3队列PID2636134和训练PID2636299均存活，阶段formal_r3_train；运行目录`logs/supermimic/2026-11-04_04-51-38_136861_g1_amp_formal_r3_exploration`；本次核实最新`logs/supermimic/2026-11-04_04-51-38_136861_g1_amp_formal_r3_exploration/model_3000.pt`，尚无通过验收的最佳G1模型。
- R3运行脚本`logs/amp_g1/formal_r3.pipeline.py`；新随机初始化seed0，num_envs18432、collect1/buffer128，WM4096×4/window8/hidden512×3，imag8192/H32，actor/critic512,256,128，critic3×4；actor_lr_scale.15，预热WM300+critic200/actor_ramp500，FP32 highest/compile。
- 仅OU explore_noise .3→.6，其余与R2相同：explore_frac.25、Gaussian action_noise.1；AMP2048×2/interval5/lr1e-5/GP40/hidden512,256、weight.5/ramp1000/RSI.5；任务、动作、split及验收不变。训练至3000，保存0/1000/2000/3000，再三点分别完整评估；三点全过才最终加噪/录像/审计。
- R3初始审计要求与R2初始四网逐位一致、全新优化器、cfg仅run_name/stop_file/explore_noise不同、动作/资产Git副本和split一致；停机请求路径logs/amp_g1/stop_formal_r3，存在时先核实原因，不带旧停止文件重启。

## 检查点与最近指标
- R2最新`logs/supermimic/2026-11-04_04-14-08_351497_g1_amp_formal_r2_throttled/model_3000.pt`。完整1000/2000/3000固定RMSE(.805,.331,.391)/(.648,.191,.440)/(.637,.226,.410)，摔倒1620/2/52；0.6m/s步频全0。3000留出风格改善41.8%/46.5%但仍原地站立。无通过验收的最佳G1模型。汇总logs/amp_g1/formal_r2_summary.json及formal_r2_assessment*.json；实际四网/四优化器/随机来源审计均通过。
- R2末训练D专家/策略.374/-.648、style.320、线速度误差.6307、摔倒12.54/分钟，信号改善不足以证明行走。10s诊断0.6m/s平均vx=.001088m/s，视频videos/g1_r2_diagnostic_walk3000.mp4、指标r2_diagnostic_video.json；非验收录像，人工检查尚待进行。
- R1三个检查点也失败：2000主要站立、3000退化；原目录logs/supermimic/2026-11-04_03-23-40_354760_g1_amp_formal_r1及03-36-52_174804_g1_amp_formal_r1_to3000，报告formal_r1_assessment*.json，勿作为成功或热启动来源。
- A1成功归档`checkpoints/a1_amp_converged.pt`（3000；SHA256 09a16f5f8bc4bcbf64a1c2dfd80010d3756b5c09224cc706d9a717b155a533ed），三点/加噪/录像/审计通过，固定RMSE .0498/.0524/.0385，风格改善36.3%/40.7%；AMP_CONVERGENCE.md及logs/amp_a1/convergence_report.json。Manager成功checkpoints/go2_manager_converged.pt，三点/加噪/录像/审计证据MANAGER_CONVERGENCE.md。两者勿重训。

## 验证、问题排序与已排除方案
- 接口/真实想象奖励、终止历史/RSI、CUDA编译及四网更新/恢复/A1回归通过。节流修复CPU50项、实际GPU interval5下D3→4、其余三网继续更新、旧检查点默认interval1和显式恢复lr覆盖均通过；证据integration_initial.json、discriminator_throttle_validation.audit.json、cpu_discriminator_throttle.log。
- 首要假设是迈步探索覆盖不足：普通reset噪声实测OU .3→.6，单支撑5.75%→20.93%、接触变化1.17→3.35/s，关节速度RMS .906→1.490、腾空.025%→.192%，摔倒24.69→35.00/分钟；Gaussian .6以上腾空过高，暂不采用。证据noise_coverage_r2.json，参考幅度exploration_action_coverage.json。只证明采样覆盖，不证明学会行走。
- 动作响应零对照：普通站立复制状态接触噪声与信号同量级，该组不能证明WM梯度错误；参考状态腿部1步机身响应cos=.838、4步=.312，仍需关注多步模型。证据action_response_r2{,_control}.json；先保持WM结构。GitHub SHAC可微Normal.rsample源码已核实，仅作方法参考，不移植算法/噪声值，github_action_gradient_research.json、github_shac_actor.json。
- 已排除：原R1/R2同配置盲目续训、普通reset动力学整体爆炸、严重RSI穿透（+.1m反增自由落体）、直接混入参考PD行为（2s内127–128/128摔），以及run/走跑转换/粗糙地形。静态参考姿态虽摔倒D仍≈1，存在姿态捷径；风格单项不能代替行走。诊断路径详见历史记录。
- G1七份Walk_B和manifest在assets/motions/g1，默认项目内加载；前80%训练/RSI、后20%留出，不跨split差分/插值。新增/替换也须复制并Git提交；本次SHA256/HEAD复核g1_motion_tracking_recheck.json通过。29DOF USD在assets/robots/g1。源f33a189 README称MIT、LICENCE为Apache-2.0，冲突原文/哈希已保留，未声称运动独立授权明确。
- RTX4090D24GB；.venv Python3.10.12/Torch2.5.1+cu124/Lab2.1/Sim4.5。实测18432约5.41万真实转移/s、峰值23108MiB（恢复最高23918）；保留完整学习批次。仿真清PYTHONPATH，OMNI_KIT_ACCEPT_EULA=YES、OMNI_KIT_ALLOW_ROOT=1、TORCHINDUCTOR_COMPILE_THREADS=4；Kit后写中文文档显式UTF-8。开发机无rg/系统python，用.venv/bin/python。

## 下一条命令与恢复
- 同一R3训练进行中；下一条命令`cat logs/amp_g1/formal_r3.pipeline.json && tail -n 2 logs/amp_g1/formal_r3_train.log && nvidia-smi`。若parent退出而active_pid还活着，先核实该子进程，不能重复启动。
- G1仍未成功；按R3真实迈步/完整独立结果决定后续，不降标准。X1仅只读预查logs/amp_x1/reference_prereview.json（源6189ae4）提示旧31DOF审计工具与12DOF接口不同，G1完成前不接入。

历史：[R2诊断](docs/history/STATUS_2026-11-04_g1_r2_diagnosis.md)、[R1诊断](docs/history/STATUS_2026-11-04_g1_r1_diagnosis.md)、[G1实现](docs/history/STATUS_2026-11-04_g1_implementation.md)、[A1](docs/history/STATUS_2026-11-04_a1_final_eval.md)。

- G1正式R3启动formal_r3_train，PID2636299，命令/日志logs/amp_g1/formal_r3_train.process.json及.log，状态logs/amp_g1/formal_r3.pipeline.json；不得重复启动。

- G1正式R3 model_0随机来源/四优化器全新/任务与动作split/SHA256及Git资产副本审计通过，证据logs/amp_g1/formal_r3_initial_audit.json；尚未收敛。

- R3 model_0初始审计通过：四网与R2逐位一致、四优化器全新、task/split/SHA256/Git资产一致；cfg仅explore_noise/run_name/stop_file变化，证据logs/amp_g1/formal_r3_initial_audit.json。训练已实际推进50（WM预热），不作收敛判断。

- 2026-11-04T04:55:14.663735核实同一R3 PID2636299训练至800；最新logs/supermimic/2026-11-04_04-51-38_136861_g1_amp_formal_r3_exploration/model_0.pt，无已验收最佳模型。训练线速度误差0.63146、摔倒53.613/分钟、actor梯度0.50006；GPU实测峰值约23124MiB、利用率86%。此为训练过程信号，不是行走结果。精确快照logs/amp_g1/formal_r3_latest_observation.json；继续同一队列至3000及三点完整评估。

- R3已保存model_1000，早期实际审计通过：actor/critic/WM/D优化器步数500/8400/4000/280，四网参数均更新且模型/优化器有限，随机来源/最终权重/任务/动作split一致；报告logs/amp_g1/formal_r3_early_checkpoint1000_audit.json。继续同一训练至3000再三点完整评估，不将更新审计视为行走收敛。

- 只读提取项目USD的12条腿部关节链并完成CPU足端几何原型：解析速度与autograd JVP最大误差1.55e-15。原型/数据仅在logs/amp_g1/g1_kinematics_*，尚未在PhysX验证，也未接入R3。后续用真实状态量化WM足端预测与关节几何的一致性，不凭原型内部检查宣称改进。

- USD几何原型与七份动作的训练split key_body_pos核对：足端世界坐标RMSE1.67e-7–3.19e-7m，支持项目资产/关节映射/原动作几何一致；未发现重定向骨架不匹配。证据logs/amp_g1/g1_kinematics_reference_consistency.json；仍需PhysX状态与WM预测的一致性检查，原型未接入训练。

- 已排队G1足端几何一致性诊断driver PID2645840，等待同一R3训练退出并释放显存后才启动GPU；状态logs/amp_g1/kinematics_r3.pipeline.json，不修改训练模型或队列。

- 最新核实2026-11-04T05:07:01：R3迭代3000，checkpoint=logs/supermimic/2026-11-04_04-51-38_136861_g1_amp_formal_r3_exploration/model_3000.pt；训练过程指标{"wm_loss": 0.25151, "actor_grad_norm": 1.5992, "imagined_survival": 0.83729, "env_samples_per_second": 57534.0, "linear_error": 0.66161, "reward/diagonal_gait": 0.040117, "amp_real_style": 0.38457, "falls_per_minute": 15.436}，完整评估尚待结束。几何诊断driver PID2645840状态waiting_for_r3_training，恢复须同时核实kinematics_r3.pipeline.json，避免重复启动。

- G1正式R3结束formal_r3_train，返回码0，日志logs/amp_g1/formal_r3_train.log。

- G1正式R3启动formal_r3_baseline_gait，PID2646457，命令/日志logs/amp_g1/formal_r3_baseline_gait.process.json及.log，状态logs/amp_g1/formal_r3.pipeline.json；不得重复启动。

- 启动G1真实足端几何/WM一致性诊断PID2646685，日志logs/amp_g1/kinematics_r3.log；原R3完整独立评估继续。

- G1真实足端几何/WM一致性诊断结束，报告logs/amp_g1/kinematics_r3.json；仅诊断，不能替代行走独立验收。

- G1正式R3结束formal_r3_baseline_gait，返回码0，日志logs/amp_g1/formal_r3_baseline_gait.log。

- G1正式R3启动formal_r3_velocity1000，PID2647590，命令/日志logs/amp_g1/formal_r3_velocity1000.process.json及.log，状态logs/amp_g1/formal_r3.pipeline.json；不得重复启动。

- R3已至3000并正常退出训练（returncode0），最新logs/supermimic/2026-11-04_04-51-38_136861_g1_amp_formal_r3_exploration/model_3000.pt。末训练线速度误差.66161、摔倒15.436/分钟、style.38457，仅训练信号；同一队列继续三点完整评估。几何诊断已完成，报告logs/amp_g1/kinematics_r3.json，待依据实际误差决定模型修复。

- 真实GPU几何核对完成：128env×256步混合RSI，FK足端位置max6.03e-6m、link速度max2.71e-5m/s，与PhysX一致。WM足端与其关节FK不一致从1步1.12mm至32步3.74mm；直接替换FK对32步真实足端预测RMSE仅12.71→12.59mm，暂无大幅改善证据，暂不增加几何投影结构。报告logs/amp_g1/kinematics_r3.json；根/足速度通道为COM，原型验证为link，已明确区分。

- G1正式R3结束formal_r3_velocity1000，返回码0，日志logs/amp_g1/formal_r3_velocity1000.log。

- G1正式R3启动formal_r3_gait1000，PID2649540，命令/日志logs/amp_g1/formal_r3_gait1000.process.json及.log，状态logs/amp_g1/formal_r3.pipeline.json；不得重复启动。

- G1正式R3结束formal_r3_gait1000，返回码0，日志logs/amp_g1/formal_r3_gait1000.log。

- G1正式R3 1000完整独立评估结束，速度失败30项、步态失败22项，报告logs/amp_g1/formal_r3_assessment1000.json；单次通过也不能代替连续三点/最终加噪/录像/审计。

- G1正式R3启动formal_r3_velocity2000，PID2650190，命令/日志logs/amp_g1/formal_r3_velocity2000.process.json及.log，状态logs/amp_g1/formal_r3.pipeline.json；不得重复启动。

- G1正式R3结束formal_r3_velocity2000，返回码0，日志logs/amp_g1/formal_r3_velocity2000.log。

- G1正式R3启动formal_r3_gait2000，PID2651947，命令/日志logs/amp_g1/formal_r3_gait2000.process.json及.log，状态logs/amp_g1/formal_r3.pipeline.json；不得重复启动。

- G1正式R3结束formal_r3_gait2000，返回码0，日志logs/amp_g1/formal_r3_gait2000.log。

- G1正式R3 2000完整独立评估结束，速度失败19项、步态失败15项，报告logs/amp_g1/formal_r3_assessment2000.json；单次通过也不能代替连续三点/最终加噪/录像/审计。

- G1正式R3启动formal_r3_velocity3000，PID2652562，命令/日志logs/amp_g1/formal_r3_velocity3000.process.json及.log，状态logs/amp_g1/formal_r3.pipeline.json；不得重复启动。

- 启动G1参考MPC诊断PID2653125（driver2653119）：同16个前向训练参考初态比较PD+速度前馈与冻结WM/H16/8次Adam/步，2s仅初态写状态；状态logs/amp_g1/reference_mpc_r3.process.json，日志reference_mpc_r3.log。正式R3三点评估继续。

- G1参考MPC诊断结束，返回码0，报告logs/amp_g1/reference_mpc_r3.json；仅采样行为/模型诊断，不是行走验收或正式训练来源。

- G1正式R3结束formal_r3_velocity3000，返回码0，日志logs/amp_g1/formal_r3_velocity3000.log。

- G1正式R3启动formal_r3_gait3000，PID2654726，命令/日志logs/amp_g1/formal_r3_gait3000.process.json及.log，状态logs/amp_g1/formal_r3.pipeline.json；不得重复启动。

- G1正式R3结束formal_r3_gait3000，返回码0，日志logs/amp_g1/formal_r3_gait3000.log。

- G1正式R3 3000完整独立评估结束，速度失败21项、步态失败15项，报告logs/amp_g1/formal_r3_assessment3000.json；单次通过也不能代替连续三点/最终加噪/录像/审计。

- G1正式R3训练/三检查点完整独立评估队列已结束；根据formal_r3_assessment1000/2000/3000.json决定续训或修复，若三点都过再最终加噪/录像/审计；不自动进入X1。

- 冻结WM参考MPC诊断完成：同16个前向参考初态，PD/前馈平均存活.779s，MPC/H16/8次Adam提高到1.442s、单脚支撑20.9%→56.0%；但两组均16/16在2s内摔倒，不接入正式训练。MPC真实一步速度预测误差.0984m/s（PD.0342），提示动态迈步分布仍是模型薄弱区。报告logs/amp_g1/reference_mpc_r3.json；后续先验证增加此类真实转移能否改善留出动力学误差，再决定采样行为改动，不把模型内部cost下降当成功。

- R3训练及三点完整独立评估已全部结束，父/子进程均退出；1000/2000/3000固定RMSE(.963,.299,.410)/(.649,.192,.438)/(.630,.240,.390)，摔倒1460/2/63，0.6m/s每足步频全部0。3000留出风格改善59.2%/59.0%，但实际仍原地站立；扩大OU噪声不足以解决问题，不继续原配置训练。汇总logs/amp_g1/formal_r3_summary.json及assessment/四网审计。当前无通过验收的最佳G1模型。下一步先导出更多MPC真实转移，按独立初态划分拟合/留出，检验动态模型误差是否可由覆盖改善，再决定采样实现。
