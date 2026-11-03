# 当前状态与恢复入口

## 目标、版本与目录
- 开发机权威目录`/pfs/user/learning/amp_new`，SSH `ssh -p 9205 root@118.196.87.69`；本地镜像`/home/user/Desktop/dream_codex_workspace/amp_new_src`。
- 当前正式训练代码commit `14b7dcbaf7257b8b32dce1d8db467b16225595be`，标签`g1-amp-training-ready-20261104`；实现5c02bf2。后续文档提交不改变在跑训练版本，当前工作树HEAD用`git rev-parse HEAD`核实。A1完成37b6b58/7f49486，Manager完成b1f59eb。
- 总目标：Manager/A1已完成 → 当前G1 AMP平地walk → G1成功后X1 AMP行走。全程无PPO，SuperMimic WM/可微想象，各阶段独立验收/提交。GOAL/PLAN及G1_CONVERGENCE.md保留范围、预算及锁定标准。
- X1参考reference/AMP，只策略控制下半身12DOF；实际动作复制进项目后.gitignore忽略（来源/SHA256/split清单纳入Git），部署配置参照参考实现；用户明确无需处理RKNN。X1尚未开始。
- 保留未跟踪reference/和原有exploration.py、explore_eval.py、dynamics_eval.py、test_exploration.py，勿误提交。

## 当前进程与配置
- 状态核实时间：2026-11-04 03:37:27 CST，当前工作树HEAD e3d4439b5698a43ac5b3d784875d5c0be860a3ac。原1000队列已完成并退出；同源续训队列PID2586501、训练PID2586592均存活，阶段formal_r1_to3000_train，状态logs/amp_g1/formal_r1_to3000.pipeline.json。
- 正式配置：18432env/collect1/buffer128，WM4096×4/window8/hidden512×3，imag8192/H32，actor/critic512,256,128，critic3×4；actor_lr_scale=.15，WM预热300+critic200、actor_ramp500；AMP2048×2/hidden512,256/lr1e-4/GP10/weight.5/ramp1000/RSI.5；seed0，FP32 highest/compile。无warm-start/resume，性能模型排除。
- 当前队列脚本logs/amp_g1/formal_r1_to3000.pipeline.py，状态formal_r1_to3000.pipeline.json（完整命令/active_pid/运行目录/最新检查点），启动记录formal_r1_to3000.launch.json；训练日志formal_r1_to3000_train.log、命令formal_r1_to3000_train.process.json。运行目录logs/supermimic/2026-11-04_03-36-52_174804_g1_amp_formal_r1_to3000；从原model_1000 --resume/--continue-run到3000，继承四网络/四优化器/计数/随机来源，2000/3000分别独立评估；停止文件logs/amp_g1/stop_formal_r1_to3000。
- G1初始接口/更新/恢复/评估及A1原生回归队列已全部退出，CPU48项和实际更新/恢复/评估证据保留。

## 最新/最佳checkpoint与证据
- 最新已保存`logs/supermimic/2026-11-04_03-36-52_174804_g1_amp_formal_r1_to3000/model_2000.pt`（尚未独立评估）；原首轮model_1000已完整评估但未通过速度/步态，model_0为原目录初始基线。尚无通过验收的最佳或已收敛模型。链路诊断`logs/supermimic/2026-11-04_03-04-30_578700_g1_smoke_resume/model_25.pt`；初始诊断目录`logs/supermimic/2026-11-04_03-00-37_568059_g1_smoke_initial/`，不能作正式成绩。性能模型目录logs/supermimic/*_g1_perf_N。
- CPU最终48项通过logs/amp_g1/cpu_implementation.log。GPUintegration_initial.json覆盖65reset/13终止/356指令切换/终止前状态和历史/普通与RSI reset/真实想象奖励一次dt；专家与PhysX特征max7.15e-7，编译返回max1.19e-7、actor梯度max1.46e-11。
- 实际四网络/四优化器更新及保存通过smoke_initial.audit.json；CLI恢复20→25继承任务/数据/来源，四网络继续更新且有限，步数actor16→21/critic36→46/WM20→25/D18→23；smoke_resume.audit.json。
- A1原生GPU接口回归a1_regression.json通过；G1完整七指令初始步态/独立留出评估可执行，smoke_baseline_gait.json风格距3.5375/3.5631（初始策略未收敛，仅验证评估链路）。完整评估入口benchmark.py/gait_eval.py/check_amp_convergence.py --robot g1。
- 已完成A1：checkpoints/a1_amp_converged.pt，源3000，SHA256 09a16f5f8bc4bcbf64a1c2dfd80010d3756b5c09224cc706d9a717b155a533ed；1000/2000/3000、最终加噪/录像/审计全部通过，证据AMP_CONVERGENCE.md及logs/amp_a1/convergence_report.json。3000固定RMSE .0498/.0524/.0385、随机约.045/.035/.026，风格改善36.3%/40.7%；视频videos/a1_amp_{stand,walk,fast}.mp4。
- Manager已完成：checkpoints/go2_manager_converged.pt，7000/8000/9000与最终加噪/录像/审计通过，证据MANAGER_CONVERGENCE.md。无需重训Manager/A1。

## 数据、关键决定与已排除方向
- G1七份Walk_B原样复制assets/motions/g1并纳入Git，源legged_lab f33a189（已核对GitHub固定源与本地一致）；本地29DOF USD复制assets/robots/g1。来源README声明MIT、同commit的LICENCE为Apache-2.0；两者冲突，原文/SHA256均已保留在assets/motions/g1，运动特定授权未另行说明。GitHub核实upstream_license_verification.json；此前“无独立LICENSE”表述已更正。
- manifest保存WXYZ、Lab 29关节和6关键体顺序及SHA256；前80%训练/RSI、后20%时间留出，速度分split差分，插值与对采样不跨边界。专家/PhysX顺序和特征已原生GPU验证；评估始终普通站立reset。
- 参考flat默认混有run/走跑转换且实现面向Lab3，不直接导入；采用七份walk白名单和本机Lab2.1原生plane。只用参考的角速度/绝对关节位置/速度61维AMP特征，沿本项目两帧LSGAN，不使用PPO。
- G1动作29、历史480、WM状态83、双足计时8；共用WM/回放/想象已按机器人维度参数化，Go2/A1默认接口不变且CPU/A1GPU回归通过。多电机组常量逐关节组装，原生DC PD/限幅与想象同公式。
- A1此前critic预热保留无用actor图导致OOM已修复；G1保留无actor更新时关闭梯度的路径。后续OOM按峰值来源定位，不盲目减学习batch。
- RTX4090D24GB；.venv Python3.10.12/Torch2.5.1+cu124/Lab2.1/Sim4.5。仿真清除PYTHONPATH，OMNI_KIT_ACCEPT_EULA=YES、OMNI_KIT_ALLOW_ROOT=1、TORCHINDUCTOR_COMPILE_THREADS=4。开发机无rg/系统python，使用.venv/bin/python。

## 未解决问题及下一条命令
- 当前G1实现/接口/更新/恢复/并行性能与验收负例已通过，正式首轮1000训练及四网络/四优化器随机来源审计通过；1000完整评估已结束且速度/步态失败，独立风格通过；正式收敛未验证。后续仍须连续三检查点/加噪/录像/实际审计，失败须定位，不能降低阈值。
- 下一条命令：`cat logs/amp_g1/formal_r1_to3000.pipeline.json && tail -n 2 logs/amp_g1/formal_r1_to3000_train.log && nvidia-smi`，核实active_pid后继续同一队列，禁止重复启动。2000/3000各自完整速度/步态/留出风格评估后队列停止，依据formal_r1_assessment2000.json与3000.json决定后续。
- X1仅只读核对参考commit6189ae4，含资产、关节顺序、预处理和导出审计；待G1独立成功/提交后才接入，不处理RKNN。

历史：[G1实现/验证事件](docs/history/STATUS_2026-11-04_g1_implementation.md)、[A1](docs/history/STATUS_2026-11-04_a1_final_eval.md)、[Manager](docs/history/PROGRESS_2026-11-04_manager.md)。

- 正式1000完整评估结束：固定总RMSE .839/.314/.380、1501次摔倒；随机三组约.79–.81/.28–.29/.39–.40且均摔倒；步态稳定性/摆动未通过。独立风格距2.471764/2.669591，相对正式model_0改善30.2%/25.6%，风格通过不能替代行走通过。证据logs/amp_g1/formal_r1_assessment1000.json及对应velocity/gait报告。
- 决定沿同一随机初始化来源从model_1000继续到3000，保留18432环境及全部学习/奖励/验收配置，保存2000/3000并分别完整独立评估。依据：actor仅更新500次，训练末段摔倒54→45次/分钟、想象生存约.43→.52，风格有独立改善；先检验训练不足，若稳定性/跟踪不再改善再定位配置或接口。此处尚未收敛，不启动X1。
- G1动作文件要求已落实PLAN：assets/motions/g1七份文件均已纳入Git且工作树/HEAD/SHA256一致；后续新增/替换同规则，默认入口go2_supermimic/g1.py:31。

- G1同源续训1000→3000队列已启动，PID2586501，代码/文档HEAD e3d4439b5698a43ac5b3d784875d5c0be860a3ac；状态logs/amp_g1/formal_r1_to3000.pipeline.json，完整启动记录formal_r1_to3000.launch.json；从model_1000继承四网络/四优化器/计数及来源，全部18432环境与学习/奖励配置不变，2000/3000分别审计与完整独立评估，禁止重复启动。

- G1同源续训队列启动formal_r1_to3000_train，PID2586592；完整命令/配置logs/amp_g1/formal_r1_to3000_train.process.json，日志logs/amp_g1/formal_r1_to3000_train.log；状态logs/amp_g1/formal_r1_to3000.pipeline.json，不要重复启动。

- 核实上游许可记录存在错误：固定f33a189含LICENCE（Apache-2.0），而README声明MIT；GitHub固定源README/LICENCE与本地逐字节一致，证据logs/amp_g1/upstream_license_verification.json。将保留原文并如实记录两者冲突/动作特定授权未说明；纠正此前“无独立LICENSE”的表述，不修改实际动作或训练划分/特征。

- 更正G1来源许可记录并复制UPSTREAM_LICENCE（Apache-2.0）至Git管理的数据目录；与README的MIT声明冲突如实保留，manifest记录原文SHA256。动作字节/数据split/训练metadata未改，当前续训不受影响。最新已保存同源model_2000，训练采样摔倒约20次/分钟、线速度误差约.70，独立评估待队列完成训练后执行。
