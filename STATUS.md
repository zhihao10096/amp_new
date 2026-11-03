# 当前状态与恢复入口

## 目标、版本与目录
- 权威目录`/pfs/user/learning/amp_new`，SSH `ssh -p 9205 root@118.196.87.69`；本地旧镜像仅供参考。恢复先读GOAL/PLAN/本文件/PROGRESS，再核实HEAD、队列PID与GPU，避免重复启动。
- 当前代码已验证commit `754e1fd8410fc1fbd805461d17ced77e018c5209`；本次记录更新前HEAD `7d26d21cb7e41ff57e4614d369ea4f1cc3c1870e`，之后仅文档提交。当前文档HEAD以`git rev-parse HEAD`核实；R3启动后以process.json记录源commit。
- Manager/A1已完成 → 当前G1平地walk → 成功提交后X1下半身12DOF AMP。全程WM可微想象、禁PPO，各阶段独立验收和提交。X1部署配置参考reference/AMP、跳过RKNN；其动作复制项目后.gitignore忽略，来源/许可/SHA256/split清单入Git。
- 保留未跟踪reference/、exploration.py、explore_eval.py、dynamics_eval.py、test_exploration.py，勿误提交或改写。

## 进程与下一轮配置
- R2原队列PID2611110及所有训练/评估子进程均已退出，状态formal_r2.pipeline.json为assessment3000_complete；三份完整评估均失败，不续训原配置。动作响应/零对照/噪声覆盖诊断也均退出，报告已解析；未启动R3。
- R3准备脚本`logs/amp_g1/formal_r3.pipeline.py`；计划新随机初始化seed0，num_envs18432、collect1/buffer128，WM4096×4/window8/hidden512×3，imag8192/H32，actor/critic512,256,128，critic3×4；actor_lr_scale.15，预热WM300+critic200/actor_ramp500，FP32 highest/compile。
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
- 下一步先提交本轮决定，再核实无R3进程、无stop_formal_r3，启动logs/amp_g1/formal_r3.pipeline.py；启动后立即补PID、实际目录与源commit。随后`cat logs/amp_g1/formal_r3.pipeline.json && tail -n 2 logs/amp_g1/formal_r3_train.log && nvidia-smi`。若parent退出而active_pid还活着，先核实该子进程，不能重复启动。
- G1仍未成功；按R3真实迈步/完整独立结果决定后续，不降标准。X1仅只读预查logs/amp_x1/reference_prereview.json（源6189ae4）提示旧31DOF审计工具与12DOF接口不同，G1完成前不接入。

历史：[R2诊断](docs/history/STATUS_2026-11-04_g1_r2_diagnosis.md)、[R1诊断](docs/history/STATUS_2026-11-04_g1_r1_diagnosis.md)、[G1实现](docs/history/STATUS_2026-11-04_g1_implementation.md)、[A1](docs/history/STATUS_2026-11-04_a1_final_eval.md)。
