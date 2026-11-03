# 进度与恢复入口

先读STATUS/GOAL/PLAN，核实HEAD、队列active_pid、GPU及产物，避免重复实验。

- Manager完成b1f59eb；A1完成37b6b58/7f49486。各自三连续检查点、最终加噪/录像与实际模型审计通过，模型分别checkpoints/go2_manager_converged.pt、a1_amp_converged.pt；无需重训。
- 当前G1平地walk，之后X1 AMP：X1仅下半身12DOF，复制实际动作后.gitignore忽略；部署配置参考reference/AMP，明确跳过RKNN。全程禁PPO，各阶段独立提交，G1/X1未成功前总目标未完成。
- G1参考f33a189/GitHub固定源一致；七份Walk_B及29DOF USD已复制项目assets/motions/g1、assets/robots/g1并保留来源/许可实际状态/SHA256/split/顺序。显式排除run/走跑转换/粗糙地形，适配本机Lab2.1而非直接导入Lab3参考。
- G1接入原生Manager，29act/83state/8gait/480obs、参考RSI、61维相邻帧AMP/LSGAN/GP及真实/想象共享奖励和DC电机；共用训练/回放/想象按维度参数化。正式速度/步态/独立风格与三检查点/加噪/录像/审计标准在训练前锁定G1_CONVERGENCE.md。
- CPU48项通过；GPU验证65reset/13终止/356切换、真实想象奖励/历史/终止快照，专家/PhysX max7.15e-7、编译返回max1.19e-7/actor梯度max1.46e-11。真实四网络四优化器更新/保存通过，CLI恢复20→25步数actor16→21/critic36→46/WM20→25/D18→23且继续更新/有限。A1 GPU回归通过。证据logs/amp_g1/{integration_initial,smoke_initial.audit,smoke_resume.audit,a1_regression}.json。
- G1完整初始步态和留出风格可执行（诊断基线3.5375/3.5631，未收敛）；实现验证队列已退出。4k/8k/12k/16k/18k性能全部通过，选择18432（54114真实转移/s、峰值23108MiB）。实现5c02bf2、训练就绪14b7dcb已提交。正式1000队列2577168已完成并退出；最新model_1000（速度/步态未通过），目录logs/supermimic/2026-11-04_03-23-40_354760_g1_amp_formal_r1；model_0初始来源/四优化器/锁定任务与数据资产SHA256审计通过，先到1000再完整独立评估。

下一步：先核实正式/诊断进程均已退出；原1000/2000/3000完整评估均失败，停止同配置盲目续训，诊断AMP饱和与参考关节探索，不以风格单项通过称收敛。G1成功提交后再实施X1。

历史事件docs/history/PROGRESS_2026-11-04_g1_implementation.md；原始日志保留路径和结论，不复制到记录。

- 正式1000完整评估结束：固定总RMSE .839/.314/.380、1501次摔倒；随机三组约.79–.81/.28–.29/.39–.40且均摔倒；步态稳定性/摆动未通过。独立风格距2.471764/2.669591，相对正式model_0改善30.2%/25.6%，风格通过不能替代行走通过。证据logs/amp_g1/formal_r1_assessment1000.json及对应velocity/gait报告。
- 决定沿同一随机初始化来源从model_1000继续到3000，保留18432环境及全部学习/奖励/验收配置，保存2000/3000并分别完整独立评估。依据：actor仅更新500次，训练末段摔倒54→45次/分钟、想象生存约.43→.52，风格有独立改善；先检验训练不足，若稳定性/跟踪不再改善再定位配置或接口。此处尚未收敛，不启动X1。
- PLAN已明确G1全部参考动作及后续新增/替换必须复制assets/motions/g1并纳入Git；现有七份SHA256与工作树/HEAD全部一致，数据要求已核实。

- G1同源续训1000→3000队列已启动，PID2586501，代码/文档HEAD e3d4439b5698a43ac5b3d784875d5c0be860a3ac；状态logs/amp_g1/formal_r1_to3000.pipeline.json，完整启动记录formal_r1_to3000.launch.json；从model_1000继承四网络/四优化器/计数及来源，全部18432环境与学习/奖励配置不变，2000/3000分别审计与完整独立评估，禁止重复启动。

- G1同源续训队列启动formal_r1_to3000_train，PID2586592；完整命令/配置logs/amp_g1/formal_r1_to3000_train.process.json，日志logs/amp_g1/formal_r1_to3000_train.log；状态logs/amp_g1/formal_r1_to3000.pipeline.json，不要重复启动。

- 核实上游许可记录存在错误：固定f33a189含LICENCE（Apache-2.0），而README声明MIT；GitHub固定源README/LICENCE与本地逐字节一致，证据logs/amp_g1/upstream_license_verification.json。将保留原文并如实记录两者冲突/动作特定授权未说明；纠正此前“无独立LICENSE”的表述，不修改实际动作或训练划分/特征。

- 更正G1来源许可记录并复制UPSTREAM_LICENCE（Apache-2.0）至Git管理的数据目录；与README的MIT声明冲突如实保留，manifest记录原文SHA256。动作字节/数据split/训练metadata未改，当前续训不受影响。最新已保存同源model_2000，训练采样摔倒约20次/分钟、线速度误差约.70，独立评估待队列完成训练后执行。

- G1同源队列结束formal_r1_to3000_train，返回码0，日志logs/amp_g1/formal_r1_to3000_train.log。

- G1同源续训队列启动formal_r1_velocity2000，PID2595255；完整命令/配置logs/amp_g1/formal_r1_velocity2000.process.json，日志logs/amp_g1/formal_r1_velocity2000.log；状态logs/amp_g1/formal_r1_to3000.pipeline.json，不要重复启动。

- G1同源3000训练已正常结束，原队列正独立评估2000/3000；另启动只读PhysX/世界模型1/4/8/16/32步诊断，PID2595945，状态logs/amp_g1/dynamics3000.process.json，日志formal_r1_dynamics3000.log；不改检查点/训练，诊断与小规模评估同时占用GPU约12GB，不与正式训练重叠。

- G1世界模型只读诊断结束，返回码0，报告logs/amp_g1/formal_r1_dynamics3000.json；结合独立速度/步态报告判断训练不足、模型偏差或控制问题。

- G1同源队列结束formal_r1_velocity2000，返回码0，日志logs/amp_g1/formal_r1_velocity2000.log。

- G1同源续训队列启动formal_r1_gait2000，PID2597557；完整命令/配置logs/amp_g1/formal_r1_gait2000.process.json，日志logs/amp_g1/formal_r1_gait2000.log；状态logs/amp_g1/formal_r1_to3000.pipeline.json，不要重复启动。

- G1同源队列结束formal_r1_gait2000，返回码0，日志logs/amp_g1/formal_r1_gait2000.log。

- G1正式2000完整独立评估结束，速度失败18项/步态失败15项，报告logs/amp_g1/formal_r1_assessment2000.json；仍须三连续检查点/加噪/录像/审计，不以单次成绩判收敛。

- G1同源续训队列启动formal_r1_velocity3000，PID2598200；完整命令/配置logs/amp_g1/formal_r1_velocity3000.process.json，日志logs/amp_g1/formal_r1_velocity3000.log；状态logs/amp_g1/formal_r1_to3000.pipeline.json，不要重复启动。

- 3000动力学只读诊断结束并通过：普通reset+动作噪声下，线速度1步RMSE .0141、32步 .0475；32步高度RMSE .00461、gravity .0192，未见整体爆炸，报告logs/amp_g1/formal_r1_dynamics3000.json。不能据此证明摆动/参考重置分布准确。2000固定评估初步仅1次摔倒但平均vx约0，存在站立局部解；下一步结合完整评估检查AMP饱和与RSI落地，参考flat配置带height_offset=.1而本实现未加，须实测再决定，暂不改训练。

- 启动G1参考重置只读诊断PID2598832：相同128参考帧分别比较高度偏移0/.05/.1m，检查脚高、首步冲量及早期终止；状态logs/amp_g1/reference_reset_diagnostic.process.json，日志reference_reset_diagnostic.log，不修改动作或正式训练。

- 参考重置诊断首跑因诊断脚本gravity广播索引错误退出，原始日志reference_reset_diagnostic.log/进程记录保留，无有效结果；同时修复Kit切换locale后事件写入必须显式UTF-8的问题。修正后以独立r2日志/进程/输出重跑，原正式评估队列继续，不改训练。

- 启动G1参考重置只读诊断PID2599878：相同128参考帧分别比较高度偏移0/.05/.1m，检查脚高、首步冲量及早期终止；状态logs/amp_g1/reference_reset_diagnostic_r2.process.json，日志reference_reset_diagnostic_r2.log，不修改动作或正式训练。

- G1参考重置只读诊断结束，返回码0，报告logs/amp_g1/reference_reset_diagnostic_r2.json；仅检查接触与初始冲量，不作为运动跟踪或收敛证据。

- G1同源队列结束formal_r1_velocity3000，返回码0，日志logs/amp_g1/formal_r1_velocity3000.log。

- G1同源续训队列启动formal_r1_gait3000，PID2600859；完整命令/配置logs/amp_g1/formal_r1_gait3000.process.json，日志logs/amp_g1/formal_r1_gait3000.log；状态logs/amp_g1/formal_r1_to3000.pipeline.json，不要重复启动。

- G1同源队列结束formal_r1_gait3000，返回码0，日志logs/amp_g1/formal_r1_gait3000.log。

- G1正式3000完整独立评估结束，速度失败20项/步态失败19项，报告logs/amp_g1/formal_r1_assessment3000.json；仍须三连续检查点/加噪/录像/审计，不以单次成绩判收敛。

- G1同源1000→3000及两检查点完整独立评估队列已结束；依据formal_r1_assessment2000/3000.json决定下一步，未自动启动X1。

- 同源1000→3000及2000/3000完整独立评估均已结束：2000固定RMSE .651/.192/.427、1摔，随机13/8/4摔；七指令主要站立、无有效迈步，独立风格仍通过。3000固定RMSE .623/.308/.340、159摔，随机112/112/106摔；风格3.328314/4.451759也未通过。两者均不收敛，不能继续声称仅训练不足，停止原配置盲目续训。证据formal_r1_assessment2000.json/3000.json及原报告；四网络/四优化器/来源审计均通过。
- 参考重置r2只读对比完成：相同128参考帧×0/.05/.1m，0偏移脚link最低.02735m、无link低于地面、首步最大速度1.069m/s且0.4s内无摔倒；加.1m反而产生额外自由落体（第5步平均vz约-.994m/s，0偏移-.376）。未支持严重穿透/冲量假设，保持现有高度，不照搬上游偏移。报告reference_reset_diagnostic_r2.json；首跑脚本广播/UTF8错误已修正，失败日志保留。
- 问题排序：首要为站立局部解/实际迈步数据不足，AMP已接近完全分离（policy约-1、真实style约.003）；普通站立分布世界模型未爆炸、RSI严重穿透假设已排除。下一步先只读分析AMP梯度及尝试参考关节轨迹作为少量真实采样行为，检验能否提供有节律的PhysX迈步数据；actor仍仅由WM可微想象优化，禁止PPO、禁止把逐帧强制root/关节状态写入伪装为真实转移。验证前不改正式训练配置，G1未成功不进入X1。

- 启动G1参考关节行为诊断PID2603625，同128训练参考帧比较actor/静态/连续参考PD/参考PD+速度前馈，真实PhysX只在初始RSI写状态，其余仅关节action；状态logs/amp_g1/reference_behavior_diagnostic.process.json，日志reference_behavior_diagnostic.log，不改变正式训练。

- G1参考关节行为诊断结束，返回码1，报告logs/amp_g1/reference_behavior_diagnostic.json；仅用来判断采样覆盖与AMP信号，不作为正式验收。

- 参考行为诊断首跑因使用Lab3的ObservationManager.compute(update_history=...)参数退出（无有效结果），已核对本机Lab2.1签名改为compute()，原日志保留，使用独立r2记录重跑。GitHub已找到参考项目同症状Issue28：作者确认D饱和并建议降低D更新频率/LR、提高GP；适用于共享判别器部分，不能照搬其PPO更新或奖励尺度，证据github_legged_lab_issue28.json。

- 启动G1参考关节行为诊断PID2605321，同128训练参考帧比较actor/静态/连续参考PD/参考PD+速度前馈，真实PhysX只在初始RSI写状态，其余仅关节action；状态logs/amp_g1/reference_behavior_diagnostic_r2.process.json，日志reference_behavior_diagnostic_r2.log，不改变正式训练。

- G1参考关节行为诊断结束，返回码0，报告logs/amp_g1/reference_behavior_diagnostic_r2.json；仅用来判断采样覆盖与AMP信号，不作为正式验收。

- 决定先做判别器节流的最小修复/独立消融：新增amp_update_interval（默认1保留A1行为），G1新随机首轮采用interval5、lr1e-5、GP40，最终AMP权重.5/任务/数据/验收不变。依据参考项目作者Issue28#issuecomment-4865653000的同症状诊断与缓解；本项目D为每迭代2步而非PPO的20步，只采用判别器优化控制，不移植PPO或其奖励混合尺度。先CPU及真实GPU计数/四优化器更新/CLI恢复验证，再提交并启动新实验；参考行为目前仅诊断，暂不混入正式训练。

- 参考行为r2实际完成：连续参考PD/PD+速度前馈仍在2s内127–128/128摔倒，不作为新采样行为接入；静态参考姿态虽然全摔，D仍约+.996/style≈1，而actor为-.996/style≈.004，D存在姿态捷径。actor状态特征style梯度范数约.99，不能把饱和直接说成完全零梯度。报告reference_behavior_diagnostic_r2.json；先验证判别器节流缓解，不混合参考控制或引入额外策略来源。

- 判别器节流验证队列已启动PID2607604，状态logs/amp_g1/discriminator_throttle_validation.pipeline.json，CPU日志cpu_discriminator_throttle.log；原正式/诊断队列均已结束，勿重启。当前训练器修改尚未提交，源SHA256随验证审计保存。

- G1判别器节流GPU验证启动throttle_smoke_initial，PID2607693，完整命令/状态logs/amp_g1/discriminator_throttle_validation.pipeline.json，日志logs/amp_g1/throttle_smoke_initial.log。

- G1判别器节流GPU验证结束throttle_smoke_initial，返回码0，日志logs/amp_g1/throttle_smoke_initial.log。

- G1判别器节流GPU验证启动throttle_smoke_resume，PID2608238，完整命令/状态logs/amp_g1/discriminator_throttle_validation.pipeline.json，日志logs/amp_g1/throttle_smoke_resume.log。

- G1判别器节流GPU验证结束throttle_smoke_resume，返回码0，日志logs/amp_g1/throttle_smoke_resume.log。

- G1判别器节流GPU验证启动throttle_legacy_resume，PID2608762，完整命令/状态logs/amp_g1/discriminator_throttle_validation.pipeline.json，日志logs/amp_g1/throttle_legacy_resume.log。

- G1判别器节流GPU验证结束throttle_legacy_resume，返回码0，日志logs/amp_g1/throttle_legacy_resume.log。

- G1判别器节流CPU/GPU验证通过：interval5使20→25的D步数3→4，actor16→21/critic36→46/WM20→25；CLI继承interval/GP并生效显式D lr2e-5。旧检查点缺新字段仍interval1、D18→23。审计logs/amp_g1/discriminator_throttle_validation.audit.json；此为接口验证，非收敛。

- 判别器节流已通过CPU50项（48受Git管理+原未跟踪exploration的2项，cpu_discriminator_throttle.log）及原生GPU编译/真实四网络四优化器更新/保存恢复。interval5时20→25的D步数3→4、actor16→21/critic36→46/WM20→25；CLI继承interval/GP，显式D lr2e-5覆盖已保存优化器；旧检查点缺新字段默认interval1，D18→23。证据discriminator_throttle_validation.audit.json及pipeline.json，所有网络继续更新且有限。
- 第二轮正式实验决定：新随机初始化seed0、独立model_0；18432环境及R1全部学习批次/WM预热300/critic200/actor_ramp500/AMP_ramp1000不变，仅D每5迭代更新2步、lr1e-5、GP40，最终AMP权重.5。先训练至3000，保存1000/2000/3000并对三者分别完整速度/步态/留出风格评估；连续三点全过后再最终加噪/录像/实际审计。D再次饱和且学习停滞时提前保存并定位，不无限续训；参考关节行为不接入，正式数据仅真实策略+原有随机探索/RSI。尚未启动新正式队列，启动前提交代码/记录。
