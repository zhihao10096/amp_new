# 当前状态与恢复入口

## 目标与版本
- 总目标：Manager随机来源完整收敛后，再参考reference/rl_amp实现Go2 AMP；禁用PPO。
- 开发机：/pfs/user/learning/amp_new；当前代码commit a3ea68e00bda8c6a78b9efc6fc03ca38c4bb0637。
- 本轮修复：初期奖励恢复可收敛速度基线的关节平方惩罚，平滑过渡到最终范数；非足接触惩罚初期置零，真实/想象公式及权重同步。依据见MANAGER_BASELINE.md。
- 用户reference/保持未跟踪原状；旧诊断/探索脚本仍未跟踪，未接入正式训练。

## 当前实验与恢复命令
- 训练PID=2381345；GPU监控PID=2381346。启动命令完整保存在logs/manager_4090/baseline_squared.process.json，工作目录为上述项目目录。
- 本轮从随机初始化启动，不resume/warm-start。run-name=manager_baseline_squared，运行目录logs/supermimic/2026-11-03_23-14-56_505712_manager_baseline_squared。
- 配置：8192env，collect4，buffer256，WM4096×4/window8/hidden512×3，imag8192/horizon32；warmup300+critic200，actor ramp500/scale.3；先至3000，save500，seed0。
- 初期奖励保持到6000、9000到最终；本段只验证速度学习。目标任务及完整验收标准不变，未到最终奖励不能验收。
- 日志logs/manager_4090/baseline_squared_train.log；显存/利用率logs/manager_4090/baseline_squared.gpu.csv；停止文件baseline_squared.stop当前不存在。
- 下一条命令：`ps -p 2381345 -o pid,stat,etime,args; tail -n 3 logs/manager_4090/baseline_squared_train.log`。恢复必须先核实进程及checkpoint，禁止重复启动。

## Checkpoint与最近指标
- 本轮初始checkpoint=logs/supermimic/2026-11-03_23-14-56_505712_manager_baseline_squared/model_0.pt，最新model_500.pt（actor尚未更新），日志已到600，actor从501开始更新；最佳Manager尚无，尚未证明收敛。出现model1500/2000时做独立7指令诊断。
- 上一有效轮：logs/supermimic/2026-11-03_22-28-23_077303_manager4090_curriculum_fixed/model_2500.pt，前进1m/s实际vx约.00075、转弯yaw约.104/目标.5。该轮仅改权重，未恢复平方公式。
- 原Manager随机来源：logs/supermimic/2026-11-03_20-51-11_991689_manager_from_scratch/model_0.pt和model_1000.pt（两者actor相同）；旧Direct最佳仅作对照：logs/supermimic/2026-11-03_20-07-39_561455_gait_slip_refinement/model_1500.pt。

## 已完成与已排除
- 本轮CPU29项；原生GPU观测/奖励、80reset/强制翻倒/144指令切换、课程初中末公式一致；32env真实三网络/优化器更新、保存、CLI恢复20→24（继承4/12调度）和2秒评估均PASS。证据logs/manager_4090/baseline_reward_regression.json及baseline_reward_*.log，全日志零PhysX/CUDA错误。
- 已修复PhysX patch容量，24576env回归122880reset/221184指令切换零错误。原16k/24k溢出性能结果及curriculum_train.log作废，不复用。
- d9eee9b3是MuJoCo chase/dodge；Direct中间版本提供Isaac速度学习对照。Manager迁移未改WM损失/actor目标。先前“弱正则成功”已排除；其初期范数惩罚与平方基线不等价。
- 低速WM单步/32步线速度RMSE .0032/.0132不足以验证运动区间；63维WM与稀有事件采样差异仍未排除。
- 周期探索仅扫描，未用于训练。PID2371518已结束，112组报告trot_phase_scan.json，有7组前进>.2且零摔倒（最佳vx .389/.588，相位3π/2），仅作为运动数据覆盖后备；暂停扩展该方向，优先基线对照。GitHub源码检索超时，依据本地历史源码核对，记录baseline_reward_research.json。

## 环境与下一阶段
- RTX4090D 24GB；.venv Python3.10.12/Torch2.5.1+cu124/Lab2.1/Sim4.5；启动仿真设置OMNI_KIT_ACCEPT_EULA=YES/OMNI_KIT_ALLOW_ROOT=1并清除PYTHONPATH。开发机无rg。
- 未解决：平方初期奖励是否足以恢复运动学习；若仍静止再按数据覆盖/WM运动梯度排查。有效后才推进最终步态及连续三个相隔1000迭代完整评估、加噪、录像和审计。
- AMP尚未实施：reference/rl_amp包含A1 motion61/AMP43维及LSGAN，后续需Go2坐标/关节/足端适配，接入SuperMimic可微奖励，禁止PPO。
- 目标GOAL.md；计划PLAN.md；事件PROGRESS.md；验收MANAGER_CONVERGENCE.md。

- 效率验证：可选编译单步实现未提交、默认关闭；CPU30项含AOT前后返回和梯度一致。CUDA比较PID2386070，日志logs/manager_4090/compiled_imagination_cuda.log。当前正式训练仍使用a3ea68e。

- 编译GPU比较首轮在TF32 high下返回最大差约6.4e-4，严格一致性未通过；尚未用于正式训练。CPU AOT一致，当前检验FP32 highest是否消除累计舍入差，PID2388047，日志logs/manager_4090/compiled_imagination_fp32.log。正式训练model1000已保存，linear_error约.695。

- FP32 highest下CUDA编译一致性PASS：actor梯度最大绝对差4.84e-8，128batch/H8单步链暖运行.0753→.0147秒（仅微基准，不代表训练加速）。编译仅在固定奖励阶段启用，课程插值期自动用普通路径避免逐轮重编译。启动真实32env更新/保存及课程切换烟测PID2388957，日志logs/manager_4090/compiled_imagination_smoke.log；最终CPU复验PID2388958。

- 编译32env真实更新/课程切换/保存PASS、CPU30项PASS；恢复验证PID2391480，日志logs/manager_4090/compiled_imagination_resume.log。已请求当前非编译主训练在迭代边界保存停止，准备对比8192×4与16384×2采样配置（每轮真实样本同为32768）及编译吞吐，然后从同一随机来源继续。

- 非编译主训练已在边界保存停止，最新checkpoint=logs/supermimic/2026-11-03_23-14-56_505712_manager_baseline_squared/model_1522.pt；启动7指令×4env×8秒早期真实步态诊断PID2392032，日志logs/manager_4090/baseline_squared_early_gait.log。该模型仅初期奖励，不作最终验收。
