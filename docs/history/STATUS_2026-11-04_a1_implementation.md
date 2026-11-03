# 当前状态与恢复入口

## 目标、版本与目录
- 当前阶段：Manager已验收并提交；正在实现A1 AMP平地行走，后续G1平地walk；全程禁PPO，总目标未完成，AMP尚未启动训练。范围/预算见GOAL，计划见PLAN。
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
- Manager阶段无未完成验收项。A1 AMP及G1 walk尚未实现；旧Direct模型仅历史对照。不要把完成Manager理解为已完成AMP。
- 恢复第一条命令：`git rev-parse HEAD manager-converged-20261104; cat checkpoints/go2_manager_converged.json; cat logs/manager_4090/final_process_check.json`，再核实记录中的PID已退出。
- 后续A1 AMP先核对reference/rl_amp的运动库/坐标/重置/判别器及本项目世界模型和可微奖励接入点，预先记录训练数据与验收标准后再实现/启动。全过程不用PPO。

## 进入Go2 AMP平地阶段
- 恢复核实HEAD b1f59eb，前阶段记录的训练/评估/监控均已退出，GPU空闲；Manager验收和模型保留，不重复训练。
- 用户明确Go2 AMP也仅平地；G1后续仅平地walk，禁run和其它动作。全程禁止PPO，按阶段提交，总目标仍未完成。
- 已核对reference/rl_amp：43维状态（绝对关节角、局部足端、机体系线/角速度、关节速度、高度）相邻帧LSGAN与专家零中心梯度惩罚。现有63维WM状态足够，拟接入同一纯Torch特征和冻结判别器可微奖励，actor继续世界模型反传，不使用参考PPO训练器。
- A1运动数据为FL/FR/RL/RR逐腿顺序，当前IsaacLab关节顺序及Go2几何必须实测；拟用Go2 FK重算足端和高度，避免A1/Go2几何混入判别标签。先GPU探测，再锁定数据/验收，尚未启动AMP训练。

## 用户范围变更：A1替代Go2 AMP
- 按用户最新要求，将后续Go2 AMP改为A1 AMP平地行走，G1仅平地walk和全程禁PPO保持；已更新GOAL.md和PLAN.md，不能把A1阶段省略或以Go2结果代替。
- 尚未启动Go2几何探测或AMP实验，只有日志目录中的探测脚本草稿；无需停止运行作业。当前HEAD仍b1f59eb，GPU空闲，无最新/最佳AMP checkpoint。
- A1原生IsaacLab资产与reference/rl_amp的mocap_motions_a1对应，优先验证A1 Manager环境、关节顺序和FK，而非继续Go2几何适配。AMP判别器/纯Torch特征与世界模型可微想象方案继续适用。
- 下一条命令：核对UNITREE_A1_CFG、参考A1 URDF与运动库，随后建立A1-AMP-Flat配置和GPU接口验证。

- A1原生资产/关节/FK实测开始PID2474180，运行目录/pfs/user/learning/amp_new，命令logs/amp_a1/geometry_probe.process.json，日志geometry_probe.log；无AMP训练，HEAD f3abed8。

- A1 AMP纯Torch模块新增6项CPU测试全部通过，覆盖URDF零角FK/关节顺序、专家/真实特征一致、时间采样与留出边界、四元数反向同表示、冻结判别器状态梯度及LSGAN/GP更新。AMP训练尚未启动。原生A1几何探测PID2474180仍存活但停在sim启动后，正在采集栈定位，未重复启动。

- A1探测首轮栈证实在异常后的SimulationApp.close挂住（set_device/render/_app_control_on_stop）；补显式traceback后已停止旧PID2474180，重启仅诊断PID2477500，日志geometry_probe_v2.log，记录geometry_probe_v2.process.json。GitHub搜索#4365/#7361版本不适用，#7152支持先dump栈诊断，未盲目升级依赖。

- 重要定位：A1构造失败源于Go2专用非足接触正则Head_.*在A1资产不存在（有trunk），IsaacLab要求每个正则匹配。v2 traceback完整定位，不是资产缺失或CUDA问题；将非足接触pattern作为机器人配置，A1使用trunk/hip/thigh/calf，保留Go2原配置。两轮探测无有效样本，均不用于训练。

- 已实现A1-AMP-Flat原生Manager配置（plane/A1资产/独立接触pattern）、可选参考帧reset及原生AMP奖励term。Go2默认配置不变。重新启动A1 GPU探测PID2479004，日志geometry_probe_v3.log，记录geometry_probe_v3.process.json；新增源尚未提交，需全量CPU和GPU接口验证。

- A1原生任务GPU探测v3已完成，关节顺序为FL/FR/RL/RR的hip四项、thigh四项、calf四项；原生USD与reference URDF有2.5mm髋x、1.25mm侧向差异。1280真实状态拟合得到(.1805,.047,.0838,.2,.2)，残差max2.11e-6m/RMSE3.38e-7m，证据logs/amp_a1/geometry_{probe,fit}.json；专家/策略统一以原生FK重算足端，避免形态差异成为判别标签。
- 已接入A1 Manager配置、RSI重置、原生AMP奖励term、WM想象中的AMP梯度、判别器真实pair训练和checkpoint保存/恢复；新增纯Torch模块与7项AMP测试（新增编译/actor梯度覆盖），全量CPU运行中logs/amp_a1/cpu.log，尚未真实更新/保存恢复，因此尚未提交实现或启动正式训练。
- 当前HEAD f3abed8，未提交文件见git diff；本地编辑镜像/home/user/Desktop/dream_codex_workspace/amp_new_src，开发机为运行权威。下一步CPU结果→tests/check_amp_isaaclab.py真实接口→32env更新保存CLI恢复→锁定正式AMP验收→吞吐/正式训练。

- 全量CPU38项PASS（logs/amp_a1/cpu.log）。开始A1真实GPU接口/参考与站立reset/翻倒终止/指令切换/AMP真实想象奖励/本体FK和CUDA编译actor梯度验证PID2486508，完整命令logs/amp_a1/integration.process.json，日志integration.log；正式训练未开始。

- GPU首轮原生接口/RSI及站立reset/翻倒/指令切换/真实AMP奖励/FK断言通过，编译返回比较未过（max .205），尚不能启用正式编译训练。定位验证夹具用了即将过期的真实指令时间，两次滚动触发不同随机重采样；改为同一固定10s指令窗口，保留原返回/梯度阈值重新验证PID2490890，日志integration_v2.log；旧PID2486508已结束，无重复进程。
- checkpoint感知A1评估与独立留出风格距离已接入，预先标准AMP_CONVERGENCE.md已写入，正式训练尚未启动。新增评估/判定测试后全量CPU重跑PID2490891，日志cpu_v2.log；HEAD仍f3abed8，实现未提交。
