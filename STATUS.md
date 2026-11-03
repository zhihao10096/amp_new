# 当前状态与恢复入口

## 目标、代码与工作目录
- 目标：先Manager随机来源完整收敛，再参考reference/rl_amp做Go2 AMP；禁止PPO。最终速度/步态验收标准不变。
- 开发机/pfs/user/learning/amp_new；当前HEAD=8cb89bb6a27ede6028ffc50f46ae90b6ba68cb3b。修复a3ea68e还原初期平方关节惩罚，8cb89bb加入可选编译想象单步及FP32精度配置；依据MANAGER_BASELINE.md。
- reference/用户目录保持未跟踪原状；旧诊断dynamics_eval.py/explore_eval.py及探索生成器/测试未跟踪，均未接入正式训练。

## 正在运行与恢复命令
- 训练PID2401448已完成3000（可能仍在释放32k场景）；GPU监控PID=2381346。命令及初始来源保存在logs/manager_4090/baseline_squared_fast.process.json；运行目录logs/supermimic/2026-11-03_23-40-16_677008_manager_baseline_squared_fast，run-name=manager_baseline_squared_fast。
- 本轮为新Manager随机来源的继续训练，从32k吞吐对照model1622继续至3000；首个model0无resume/warm-start，所有阶段training_origin一致。
- 配置：32768env/collect1/buffer128（每轮32768真实转移、单env回放2.56s）；WM4096×4/window8/hidden512×3，imag8192/H32，compile_imagination=true/matmul_precision=highest；actor_scale.3，seed0；log100/save500。
- 初期奖励保持至6000，9000达最终；本段仍在初期公式，不可做最终验收。warmup300+critic200已完成，actor从501更新。
- 日志logs/manager_4090/baseline_squared_fast.log；显存/利用率baseline_squared.gpu.csv；停止文件baseline_squared_fast.stop不存在。
- 下一条命令：`ps -p 2401448 -o pid,stat,etime,args; tail -n 3 logs/manager_4090/baseline_squared_fast.log`。恢复先核实进程、日志和checkpoint，禁止重复启动。3000后暂停做真实7指令/WM运动诊断，再决策。

## 最新/最佳checkpoint及最近指标
- 初始证明：logs/supermimic/2026-11-03_23-14-56_505712_manager_baseline_squared/model_0.pt。
- 当前最新正式来源：logs/supermimic/2026-11-03_23-35-17_867483_manager_compiled_profile32768/model_1622.pt；新运行最新=logs/supermimic/2026-11-03_23-40-16_677008_manager_baseline_squared_fast/model_2000.pt；将继续保存2500/3000。最佳Manager尚无，尚未证明收敛。
- model1522独立7指令×4env×8秒：前进1m/s实际vx=.0045，转弯yaw=.0165（目标.5），各组零摔倒，仍几乎静止；报告baseline_squared_early_gait.json。训练2100的linear_error=.60986、yaw_error=.33207，较1700的.69878首次明显下降；不能代替独立评估。
- 上一旧课程model2500：logs/supermimic/2026-11-03_22-28-23_077303_manager4090_curriculum_fixed/model_2500.pt，前进vx=.00075；该轮仅调权重未恢复平方公式。
- 历史Direct最佳仅作对照：logs/supermimic/2026-11-03_20-07-39_561455_gait_slip_refinement/model_1500.pt。

## 已验证、已排除及剩余问题
- CPU30项；原生GPU观测/奖励/80reset/强制翻倒/144指令切换/三阶段课程一致。真实32env三网络及优化器更新、保存/CLI恢复和短评估通过。
- 编译CUDA FP32返回/梯度一致，actor梯度最大差4.84e-8；真实编译更新、课程切换和保存恢复20→24通过。TF32 high严格对比未通过，本轮用highest；课程插值时自动绕过编译，避免逐轮重编译。日志compiled_imagination_*.log/json。
- 完整100次更新吞吐：8192×4编译约10.4万/s、3.16Hz、13434MiB；16384×2约11.9万/s、3.65Hz、17502MiB；32768×1约12.5万/s、3.82Hz、21728MiB，均零PhysX/CUDA错误。原非编译8192约6.1万/s、1.86Hz；采样总数一致。报告compiled_profiles.json；短跑只证明执行及吞吐。
- PhysX patch已按32×env扩容，32k为1048576；此前旧16k/24k溢出性能和curriculum_train.log作废。
- 已确认旧弱正则的范数/站立放大公式不等于平方基线；已修复。其是否足以学运动仍未证实，1522评估尚静止。
- d9eee9b3原始版本还有接触优先采样/稀有事件存档及1024宽WM，当前是均匀采样/512宽/63维接触状态；若3000仍停滞，优先分析运动覆盖和闭环WM梯度，不盲目加步态权重。
- 周期探索未接入训练；trot_phase_scan.json中有7组前进>.2且零摔倒，最佳vx .389/.588（抬腿相位3π/2），仅作为运动覆盖后备。低速WM误差.0032/.0132不足以说明运动区间准确。

## 环境与后续
- RTX4090D 24GB；.venv Python3.10.12/Torch2.5.1+cu124/Lab2.1/Sim4.5。仿真设置OMNI_KIT_ACCEPT_EULA=YES、OMNI_KIT_ALLOW_ROOT=1并清除PYTHONPATH；编译线程4。开发机无rg。
- 速度学习有效后再渐进最终步态，完成三个相隔1000迭代检查点的完整速度/步态、最终噪声复测/录像/审计；AMP等Manager验收通过后再接入。
- GOAL.md目标；PLAN.md计划；PROGRESS.md事件；MANAGER_CONVERGENCE.md验收。

- 未提交开发：参考d9eee9b3准备可选接触优先/稀有窗口archive（wm_prioritized_frac/wm_archive_frac默认0），CPU33项通过（含3项新增采样测试），日志priority_cpu.log。当前主进程不使用此改动；是否试用待3000独立评估后决定。

- 到2300，真实linear_error已降至.402（2100为.610），说明当前路线开始学习运动。为保持实验单一，已将未启用的接触优先采样候选移出源码，备份logs/manager_4090/priority_candidate/priority.patch及测试；CPU33项仅为候选验证，正式代码恢复为8cb89bb（原CPU30项）。不启用额外采样方案。

- 当前训练已到3000结束，最新checkpoint=logs/supermimic/2026-11-03_23-40-16_677008_manager_baseline_squared_fast/model_3000.pt。训练最近linear_error=.16393/yaw_error=.12427，首次明确运动学习。当前运行完整速度/步态独立评估：{"velocity3000": 2411127, "gait3000": 2411128}，日志baseline_squared_velocity3000.log / baseline_squared_gait3000.log，命令见baseline_squared_eval3000.process.json。下一条命令：核实这两个PID并读取对应JSON；不重复启动训练。

- model3000步态报告baseline_squared_gait3000.json已完成：7指令速度RMSE全达标且零摔倒，1m/s实际.99854；步频6.087Hz/腾空.0422s/离地.00664m/足滑.2857，未达步态标准。速度全覆盖报告尚未完成。下一阶段拟3000→5000渐进最终权重，降低actor_scale至.15；先验证课程期编译复用图，减少执行开销。

- 完整速度3000已通过velocity_failures=[]，随机稳态平均RMSE(.0566,.0701,.0561)，随机摔倒1/2/0；步态未过。当前未运行正式训练，正在验证动态GPU奖励系数编译：dynamic_reward.process.json记录CUDA/真实烟测PID，CPU日志dynamic_reward_cpu_fixed.log。准备3000→5000课程并继续最终奖励训练。

- GPU张量奖励系数验证：CPU31项PASS，5个课程比例返回/梯度一致且复用同一组梯度输入图；CUDA中间比例actor梯度最大差2.98e-8；真实32env初中末课程更新/保存PASS。开始CLI恢复20→24 PID2417071，日志logs/manager_4090/dynamic_reward_resume.log。完成后提交并从model3000按3000→5000渐进最终权重、actor_scale=.15继续训练。
