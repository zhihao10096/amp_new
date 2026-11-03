# 当前状态与恢复入口

## 目标、commit与运行目录
- 范围：已完成Go2 Manager收敛 → 当前A1 AMP平地行走 → 后续G1平地walk；全程禁PPO。Go2 AMP已替换为A1，目标/预算见GOAL.md，独立指标见AMP_CONVERGENCE.md。
- 权威目录：开发机`/pfs/user/learning/amp_new`，SSH `ssh -p 9205 root@118.196.87.69`；本地镜像`/home/user/Desktop/dream_codex_workspace/amp_new_src`。
- 当前实现commit标识：`a1-amp-implementation-20261104`（提交后创建的本地标签，指向本阶段HEAD；恢复执行`git rev-parse HEAD a1-amp-implementation-20261104`核实）。基于f3abed8cc83e294c560bd872e92aeb07f106666e；本轮验证在该base的未提交实现上运行，提交后的准确SHA和证据摘要见logs/amp_a1/implementation_validation.json。
- Manager标签manager-converged-20261104指向b1f59eb。reference/保留原状，不提交；早期诊断exploration.py、explore_eval.py、dynamics_eval.py、test_exploration.py未用于正式训练，继续保留未跟踪。

## 当前进程、运行目录与配置
- **本阶段验证全部结束，无当前训练/评估作业，尚未启动正式A1收敛训练。** 最新PID：GPU集成2499777、CPU2499778、短训练2500730、CLI恢复2503107、速度2504407、步态2505187；均已退出，最终核对见implementation_validation.json。恢复必须先核实/proc和nvidia-smi，避免重复启动。
- 初始/12迭代短训练目录：logs/supermimic/2026-11-04_01-45-05_377350_a1_amp_bundled；CLI恢复目录：logs/supermimic/2026-11-04_01-46-42_010581_a1_amp_bundled_resume。
- 短检查配置：A1-AMP-Flat/32env，warmup2/critic_warmup2/actor_ramp1，collect2/buffer32；WM32×1/window4/hidden512×3，imag32/H4，critic1×2，AMP32×1/hidden512,256/ramp8/weight.5/reference_reset.5；FP32 highest/compile=true。actor/WM从checkpoints/go2_manager_converged.pt明确跨机器人热启动，critic/D/四优化器新建。
- 完整命令/日志均在logs/amp_a1：train_bundled、train_bundled_resume、integration_bundled、cpu_bundled、velocity_smoke、gait_smoke各自.process.json和.log。进程记录中的base SHA+uncommitted_implementation=true不代表旧base已包含A1代码。

## 最新/最佳checkpoint与最近指标
- 正式A1最新/最佳：**尚无**。最新短检查：上述恢复目录/model_16.pt；初始model_0.pt和model_12.pt位于短训练目录。短跑模型不得当作收敛结果或正式风格基线。
- CPU最终相关39项通过（排除未提交旧诊断候选）：cpu_bundled.log；含四份项目内动作的manifest/SHA256与训练/留出采样验证。
- GPU原生接口通过：integration_bundled.json。32env、160次reset、1次人工翻倒终止、288次指令重采样；参考/普通站立reset、终止状态/历史、真实/想象AMP奖励及真实权重0/.123/.5通过。本体FK误差max2.29e-6m，编译返回/actor梯度误差max5.96e-8。
- 四网络/优化器真实更新审计training_bundled_audit.json通过：参数最大改变量actor=.000480、critic=.003642、WM=.002377、D=.001015，优化器步数8/20/12/10；全有限，AMP已到最终权重。
- CLI未传task/amp参数自动恢复A1并续至16迭代；resume_bundled_audit.json核实四网络继续更新，优化器步数→12/28/16/14，任务/AMP配置/数据/来源一致。
- 短速度报告velocity_smoke.json：3秒×24env、12固定+seed42随机，两组零摔倒；固定总体RMSE=.3498/.1204/.1058、随机=.3143/.1129/.0823。只验证接口，不满足正式时长/覆盖/误差标准。
- 短步态报告gait_smoke.json：4秒×56env、7指令、model_0/16均零摔倒；留出风格距离forward=.73435→.71775，fast=1.08452→1.16614。未达到两个速度均改善10%的要求，不能宣称AMP收敛。
- Manager已验收模型checkpoints/go2_manager_converged.pt（9000），7000/8000/9000连续通过完整速度/步态，最终加噪/录像/审计通过；四轮完整速度合计1280机器人分钟零摔倒。证据MANAGER_CONVERGENCE.md与logs/manager_4090/convergence_report.json；不重复训练。

## 数据、已排除问题与环境
- A1实际动作已原样复制至Git管理的assets/motions/a1/{trot1,pace1,left_turn1,right_turn1}.txt，默认从此加载。manifest记录来源rl_amp commit b4666fa、SHA256/帧数/dt/权重，附源许可；前80%训练/重置、后20%留出，dt=.02，不跨split/loop。
- G1阶段也必须把所用参考动作复制到本项目Git目录，记录来源/许可/SHA256/划分并默认从项目内加载，随实现提交；已写入PLAN第7阶段及GOAL。
- A1构造失败已定位并修复为Go2专属Head_.*正则不匹配A1，现使用trunk/hip/thigh/calf；不是资产缺失或CUDA故障。
- 原生USD与参考URDF有毫米差异；1280真实状态拟合FK=(.1805,.047,.0838,.2,.2)，误差max2.11e-6m（geometry_fit.json）；专家/策略统一原生FK，排除形态差异判别标签。
- 编译首轮失败为夹具两次随机重采样指令；固定相同窗口后原阈值通过。首次短训练权重0日志缺amp_style，GitHub IsaacLab v2.1.0源码确认会跳过零权重term；将分数采集移到转移快照，原生manager仍只乘一次权重/dt，GPU和训练复测通过。
- 早期失败/引用reference路径的smoke仅留作诊断，不能作正式结果。Manager历史平方惩罚修复及PhysX溢出/TF32排除见MANAGER_BASELINE.md与历史记录；PPO/周期探索/优先采样未用于正式Manager训练。
- RTX4090D24GB；.venv Python3.10.12/Torch2.5.1+cu124/Lab2.1/Sim4.5。仿真清除PYTHONPATH，OMNI_KIT_ACCEPT_EULA=YES、OMNI_KIT_ALLOW_ROOT=1、TORCHINDUCTOR_COMPILE_THREADS=4。开发机无rg和系统python，使用.venv/bin/python。

## 未解决问题与下一条命令
- A1实现/数据/真实更新/保存恢复及短评估已验证；尚需实测8k/16k/32k并行数、吞吐和显存，选择效率及质量合适的配置，再启动正式训练并保留新的model_0。尚未有正式训练或任何A1收敛结论，G1尚未启动。
- 恢复第一条命令（项目目录）：`git rev-parse HEAD a1-amp-implementation-20261104; cat logs/amp_a1/implementation_validation.json; nvidia-smi`，再核对上述PID已退出。
- 下一次8k吞吐实验命令：`env -u PYTHONPATH OMNI_KIT_ACCEPT_EULA=YES OMNI_KIT_ALLOW_ROOT=1 TORCHINDUCTOR_COMPILE_THREADS=4 .venv/bin/python scripts/train.py --headless --task A1-AMP-Flat --num-envs 8192 --iterations 100 --warmup-iterations 20 --critic-warmup-iterations 20 --collect-steps 1 --buffer-len 128 --wm-batch 4096 --wm-updates 4 --imag-batch 8192 --horizon 32 --compile-imagination --matmul-precision highest --warm-start checkpoints/go2_manager_converged.pt --log-interval 25 --save-interval 100 --run-name a1_amp_perf8k`。启动前记录PID/命令/日志，编译耗时与稳定吞吐分开，下一档核对OOM/物理错误及学习质量，不能把性能实验模型当作正式来源。
- 完整A1验收仍需连续3个相隔1000迭代checkpoint的速度/步态/留出风格、最终加噪/录像及来源/更新审计，全部通过并提交后进入G1。

历史：[A1实现过程](docs/history/PROGRESS_2026-11-04_a1_implementation.md)、[旧状态](docs/history/STATUS_2026-11-04_a1_implementation.md)、[Manager过程](docs/history/PROGRESS_2026-11-04_manager.md)。
