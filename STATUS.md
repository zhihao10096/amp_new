# 当前状态与恢复入口

## 目标、版本与目录
- 当前阶段：新Manager随机初始化训练的速度/步态完整收敛验收已完成；下一阶段Go2 AMP，再G1平地walk。全程不用PPO，AMP尚未启动。范围/预算见GOAL，计划见PLAN。
- 开发机 `/pfs/user/learning/amp_new`。当前commit标识 `manager-converged-20261104`（本地标签与本阶段提交HEAD相同，恢复执行 `git rev-parse HEAD manager-converged-20261104` 核实）；训练/评估代码commit `a86c036f51aaf2bfc7c70d78f0f46f498d28a95c`。
- 原始基线提示d9eee9b3已对照；实现差异、证据和限制见MANAGER_BASELINE.md，完整验收见MANAGER_CONVERGENCE.md。
- 用户reference/保持原状；未跟踪exploration.py、explore_eval.py、dynamics_eval.py、test_exploration.py为早期诊断候选，未用于正式训练，勿误提交。

## 运行目录、配置与进程
- 正式随机初始化：logs/supermimic/2026-11-03_23-14-56_505712_manager_baseline_squared，无resume/warm-start。
- 最后训练目录：logs/supermimic/2026-11-04_00-32-55_866984_manager_final9000；完整命令/代码版本 manager_train9000.process.json，日志manager_train9000.log，均位于logs/manager_4090/。
- 配置：32768env/collect1/buffer128（每env回放2.56s）；WM4096×4/window8/hidden512×3，imag8192/H32；compile=true/matmul_precision=highest；seed0/actor_scale=.15。课程3000→5000后保持最终任务；末段12.2–12.6万真实转移/s，显存21792MiB。
- 所有项目训练、评估、录像及监控已结束，无当前作业。最后训练PID2446275，评估2452443/2452444，加噪2453357，侧面录制器2464255；GPU监控2381346已停止。
- 完整PID/命令/返回码：manager_train9000.process.json、manager_eval9000.process.json、manager_noisy9000.process.json、manager_videos_side.process.json；最终进程核实final_process_check.json。先读记录并核实 /proc，避免重复启动。

## 最新/最佳checkpoint与结果
- 最新/最佳正式模型：checkpoints/go2_manager_converged.pt，元数据go2_manager_converged.json；源文件最后训练目录/model_9000.pt，model_8000.pt同目录。
- 7000：logs/supermimic/2026-11-04_00-24-18_384210_manager_final7000/model_7000.pt。
- 随机初始证明：正式随机初始化目录/model_0.pt；所有后续checkpoint保持random_initialization/Manager来源。
- 7000/8000/9000完整速度、步态均达标，最终9000加噪通过；四轮完整速度共1280机器人分钟零摔倒，三轮7指令步态均零摔倒。
- 9000随机稳态vx/vy/yaw RMSE=.04054/.04416/.03648，加噪=.04285/.04726/.05306；1/1.5m/s步频均3.530Hz，腾空均约.1312s，离地.01697/.01893m，短摆动均0，足滑.07295/.11357m/s，站立步频0。
- 审计logs/manager_4090/convergence_report.json为converged=true/failures=[]，核实实际模型来源、task一致、最终奖励、三网络和优化器更新、有限性及SHA256。
- 最终SHA256：07fc3f6e0e6801a3e60ab591be25dbeb3071c930809f847dd14284477dbfa9dd。
- 报告：manager_{velocity,gait}7000.json、manager_{velocity,gait}8000_9000.json、manager_noisy9000.json；汇总manager_evaluation_summary.{json,png}，均在logs/manager_4090/。
- 录像：videos/manager_gait_comparison.mp4（左3000/右9000）、manager_fast_side.mp4、manager_stand.mp4。侧面2/2.08/5/8秒抽帧检查通过，manager_side_contact_sheet.jpg；录像指标零摔倒。相机设置/副本保留logs/manager_4090/eval_side.py（eye1.2/-1.8/.6、lookat0/0/-.1），不改训练代码。

## 已排除与环境
- 初期静止路线的重要差异为未还原平方关节惩罚，已修正；无单因素消融，不宣称唯一根因。周期探索、外部策略、优先采样和PPO未用于正式训练。旧候选备份priority_candidate/，未接入。
- 旧16k/24k及curriculum_train的PhysX patch溢出轮作废；按32×env扩容后零物理错误。32k约12.5万/s优于16k11.9万/s和8k编译10.4万/s。TF32严格数值比较未过，正式FP32 highest。
- CPU31项、原生GPU接口/reset/终止/指令切换、真实三网络更新、保存/CLI恢复、动态课程和编译梯度一致性此前均通过。最后各训练日志零物理/CUDA错误；短跑从未用作收敛证明。
- RTX4090D24GB；.venv Python3.10.12/Torch2.5.1+cu124/Lab2.1/Sim4.5；仿真清除PYTHONPATH，OMNI_KIT_ACCEPT_EULA=YES、OMNI_KIT_ALLOW_ROOT=1；编译线程4；开发机无rg。

## 未解决问题与下一条命令
- Manager阶段无未完成验收项。Go2 AMP及G1 walk尚未实现；旧Direct模型仅历史对照。不要把完成Manager理解为已完成AMP。
- 恢复第一条命令：`git rev-parse HEAD manager-converged-20261104; cat checkpoints/go2_manager_converged.json; cat logs/manager_4090/final_process_check.json`，再核实记录中的PID已退出。
- 后续Go2 AMP先核对reference/rl_amp的运动库/坐标/重置/判别器及本项目世界模型和可微奖励接入点，预先记录训练数据与验收标准后再实现/启动。全过程不用PPO。
