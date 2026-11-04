# 当前状态与恢复入口

## 最新建议复核（2026-11-04）
- 当前HEAD `9b77f254ec6e08bbd3a8dabe556bbb7a18ffa840`，课程公式修复已落地。用户本轮询问实现建议，仅核查并记录[建议报告](docs/experiments/G1_AMP_RECOMMENDATIONS_2026-11-04.md)，未改训练/生产代码；原factory/eval工作树改动及未跟踪文件保留。
- 实际训练PID2741172仍在5000→9000同源续训；运行目录`logs/supermimic/2026-11-04_08-00-37_784295_g1_velocity_cold_start18432_to9000`，本轮核实最新`model_6000.pt`，尚未独立评估。配置18432env、collect1/buffer128、WM4096×4/window8、imag8192/H32、critic3×4、actor_lr_scale=.15、最终奖励、关闭AMP，完整命令见进程及目录config.json。
- 已评估运动候选仍为`logs/supermimic/2026-11-04_07-44-59_766317_g1_velocity_cold_start18432_continue5000/model_5000.pt`：七组零摔倒、0.6/1m/s实际vx=.54958/.93835；但前进步频4.656Hz、腾空.05474s、离地.00450m、足滑.21922m/s，侧移不达标，无通过验收G1最佳模型。真实TD两臂均未形成步态，已结束并停止该修复方向。
- 后续建议优先同源运动checkpoint的无AMP/AMP对照，再单独测运动特征、历史、参考条件与碎步约束；“稳定移动可进入诊断AMP”是建议，未改现有正式入口及最终验收。未解决：动态步态质量和完整速度覆盖。下一命令`tail -n 3 logs/amp_g1/g1_velocity_cold_start18432_to9000.log`并核对PID2741172，勿重启；以实际进程/产物覆盖下方历史状态。

## A1/G1差异诊断复核（2026-11-04，本轮）
- 核实HEAD为`a979f5e7939f174fa1d3a8fb607340d652c6810f`，原真实TD对照driver2689332仍在运行；不重复启动或改变两臂配置。
- 新确认的首要比较混杂：A1正式model_0已加载已收敛Manager actor/WM，七指令步态评估全部零摔倒；1/1.5m/s实际vx=.94146/1.43389m/s、每足步频3.418/3.489Hz。它在AMP迭代0已经能走，但站立步频/快走足滑等尚未满足A1验收。G1 R3 model_0为随机初始化，七组20秒×8环境共806次摔倒、每足步频均0。因此A1的1000轮通过不能解释为从零快速学会行走；证据`logs/amp_a1/formal_r1_baseline_gait.json`、`convergence_report.json`及`logs/amp_g1/formal_r3_baseline_gait.json`。
- CPU离线追查已完成：A1初始actor/WM与Manager逐张量一致；Go2最终模型确证random_initialization/seed0，3000–5000奖励课程。G1冷启动无该课程且关节项始终L1；.01rad每关节局部代价/梯度较Go2初期平方项为60/30倍（非总梯度结论）。R3正常/冻结零速专家特征style=.89035/.87366；静止脚离地项满分且足高梯度0。证据`logs/amp_g1/a1_g1_gap_audit.{py,json,log}`与[综合诊断](docs/experiments/A1_GO2_G1_CONVERGENCE_GAP_2026-11-04.md)。未修改生产代码/训练配置，未证明单一根因或修复。
- 本轮最新进程核实：driver2689332，anchor训练已保存3500并结束，现阶段`real_value_ablation_velocity_anchor`、child2698057；目录`logs/supermimic/2026-11-04_06-31-11_000288_g1_real_value_ablation_anchor`，最新诊断`model_3500.pt`。control3500速度失败19项、步态失败14项、0.6/1m/s步频仍0；anchor完整评估待pipeline。正式最新/最佳结论仍为下文，无通过验收G1。下一命令仍读原pipeline并核对active_pid，不重启。

## 目标、版本和目录
- 开发机权威目录`/pfs/user/learning/amp_new`，SSH `ssh -p 9205 root@118.196.87.69`。恢复先读GOAL/PLAN/STATUS/PROGRESS，再核实HEAD、实际进程和产物，避免重复启动。
- 当前实现/文档版本以`git rev-parse HEAD`核实；当前实验实现commit`fa93cabff98ec9870c971cf155009a29506c022e`；后续仅文档提交以HEAD为准。新增可选真实TD critic目标，源码SHA256及全部验证见real_value_validation.audit.json；正式R3来源仍`9bc7115a082eafc403d5f8fb2947d10e3cac38b2`。原未跟踪reference/、exploration.py、explore_eval.py、dynamics_eval.py、test_exploration.py及R3历史文件保留，勿误提交。
- Manager/A1已独立成功 → 当前G1平地walk → 成功提交后X1下半身12DOF AMP；全程WM可微想象、禁PPO。G1动作Git管理；X1动作复制后.gitignore忽略、清单入Git，部署参考reference/AMP、跳过RKNN。

## 当前进程、配置与目录
- 当前真实TD短程消融driver PID2689332；active_pid/阶段以`logs/amp_g1/real_value_ablation.pipeline.json`及实际ps为准，勿重复启动。运行目录项目根，代码commit`fa93cabff98ec9870c971cf155009a29506c022e`；无新正式训练。
- 两臂control=0/anchor=.5，同源正式R3 model_3000，分别继续500迭代到3500；18432env/collect1/buffer128，WM4096×4/window8、imag8192/H32、critic3×4、D2048×2/interval5/lr1e-5/GP40及其余任务/批次完全相同。仅critic_real_fraction/run_name/stop_file变化，critic总样本预算固定；保存初始3000及3250/3500，初始四网四优化器精确审计。
- 初始源`logs/supermimic/2026-11-04_04-51-38_136861_g1_amp_formal_r3_exploration/model_3000.pt`，新运行目录/最新模型/来源SHA256/实际命令/日志/GPU峰值都写pipeline。两臂各做完整速度和七指令步态/独立风格，报告real_value_ablation_velocity_*.json/gait_*.json。此为诊断续训，不作为正式成功声明；无收益则停止，不自动无限续训。
- 实现验证已全过：CPU55、G1终止/超时/命令与真实TD、编译/四网20→25/CLI继承.5/旧默认/A1、CUDA RNG精确恢复、默认0更新与1be9b27逐位一致；real_value_validation.audit.json。验证driver2683870已退出，短跑步态失败不算收敛。

## 最新/最佳检查点与最近指标
- G1最新正式`logs/supermimic/2026-11-04_04-51-38_136861_g1_amp_formal_r3_exploration/model_3000.pt`；无通过验收的最佳/已收敛G1模型。R3配置18432env、collect1/buffer128、WM4096×4/window8/hidden512×3、imag8192/H32、critic3×4、actor/critic512,256,128、actor_lr_scale.15、WM预热300+critic200/actor_ramp500、FP32 highest/compile；D2048×2/interval5/lr1e-5/GP40/weight.5/ramp1000/RSI.5，25%OU .6/其余Gaussian .1。训练GPU峰值23124MiB、利用率约86%、约5.75万真实转移/s。
- R3完整1000/2000/3000固定RMSE(.963,.299,.410)/(.649,.192,.438)/(.630,.240,.390)，摔倒1460/2/63；0.6m/s每足步频全部0，3000留出风格改善59.2%/59.0%仍原地站立。四网络/四优化器/随机来源审计通过，汇总logs/amp_g1/formal_r3_summary.json及对应assessment/audit；不能把风格改善当行走成功。
- R2同样三点失败，3000固定RMSE(.637,.226,.410)、52摔、步频0，style改善41.8%/46.5%；R1三点也失败。两轮目录/详细失败见历史，均勿作成功或热启动来源。
- A1完成归档checkpoints/a1_amp_converged.pt（3000，SHA256 09a16f5f8bc4bcbf64a1c2dfd80010d3756b5c09224cc706d9a717b155a533ed），三点/加噪/录像/审计通过，固定RMSE .0498/.0524/.0385，风格改善36.3%/40.7%；AMP_CONVERGENCE.md及logs/amp_a1/convergence_report.json。Manager完成checkpoints/go2_manager_converged.pt，证据MANAGER_CONVERGENCE.md。两者勿重训。

## 关键结论、排除方案与未解决问题
- 首要未解决：真实闭环仍不能walk。动态补数据让8步预测误差改善51.76%，成对响应约束另让独立响应分数.35463→.23847、8步速度RMSE .0767→.0317；仍未转化控制收益。冷启动原/普通拟合/响应约束存活1.3288/1.2813/1.1663s、均15/16摔；统一预热后.9550/.9725/.9013s、均16/16摔。不接入MPC或诊断WM，不盲目继续此方向。
- 正式策略32步校准：普通reset初始V3.399、真实/想象bootstrap 3.038/3.089；参考RSI V1.001、真实/想象1.123/.866。128步RSI真实/想象生存.2969/.1210，未支持整体收益过度乐观；动态状态价值尾项偏保守仅为下一假设，未证明真实价值锚定能改善控制。细节/限制见docs/experiments/G1_DYNAMICS_RESPONSE_2026-11-04.md。
- 骨架/映射已核对：原型与PhysX足端位置max6.03e-6m、link速度max2.71e-5m/s；WM32步足端/关节几何差3.74mm，直接FK收益小，暂不投影。原型link与runtime COM速度语义已区分；kinematics_r3.json。站立复制状态的有限差分受接触噪声干扰；本轮预热后零对照明显小于动作信号。
- 已排除：R1/R2/R3同配置盲续训、继续仅加OU、严重RSI穿透/直接加.1m高度、普通站立WM整体爆炸、原样参考PD/前馈或当前MPC作为可靠采样行为。D姿态捷径和风格改善不能代替真实步行；响应/预测分数下降也不能替代闭环稳定性。
- 真实TD可选实现验证完成：CPU55；原生13摔倒/52超时/356命令切换，TD目标与实际奖励最大误差1.19e-7；编译返回/actor梯度一致。四网20→25继续更新，CLI继承.5、独立CUDA RNG精确恢复/后续随机数一致；旧模型缺字段默认0恢复及A1 GPU回归通过。默认0的一次actor/critic/优化器更新与1be9b27逐位一致。短跑步态未通过，不能称G1成功；审计logs/amp_g1/real_value_validation.audit.json。
- G1七份Walk_B与manifest在assets/motions/g1，USD在assets/robots/g1；前80%训练/RSI、后20%独立专家时间留出，不跨clip/split差分或插值。新增/替换动作必须复制并Git提交；本次manifest/SHA256/HEAD/追踪与默认路径复核通过，g1_motion_tracking_recheck_current.json。源f33a189的README MIT与LICENCE Apache-2.0冲突原文已保留，动作独立授权未明示。
- RTX4090D24GB；.venv Python3.10/Torch2.5.1+cu124/Lab2.1/Sim4.5。仿真清PYTHONPATH，OMNI_KIT_ACCEPT_EULA=YES、OMNI_KIT_ALLOW_ROOT=1、TORCHINDUCTOR_COMPILE_THREADS=4；Kit后中文文件显式UTF-8。无rg/系统python，用.venv/bin/python。

## 下一条命令
`cat logs/amp_g1/real_value_ablation.pipeline.json`，然后用active_pid核对ps及对应job.log；跟进同一driver训练/评估，勿重启。当前0/.5同源短程消融尚未得到闭环结论，不把接口通过当行走成功。G1三点/加噪/录像/审计全部通过前不进入X1。

本轮证据：[动作响应/控制/价值校准报告](docs/experiments/G1_DYNAMICS_RESPONSE_2026-11-04.md)。历史R1/R2/R3见G1_CONVERGENCE.md及docs/history。X1只读预查logs/amp_x1/reference_prereview.json（6189ae4），尚未实施，待G1独立成功提交。

- 用户再次明确G1实际参考动作须复制至项目Git管理目录，已在PLAN第7阶段列为训练前必要任务。七份动作、manifest及来源许可文件均已提交且SHA256吻合，默认路径为assets/motions/g1；本轮复核证据logs/amp_g1/g1_motion_plan_recheck_2026-11-04.json。
- A1能迈步而G1失败的差异仍待因果定位：G1当前是站立局部解，独立风格改善不等于动态步态；骨架映射/严重RSI穿透等假设未获支持。当前真实TD对照仅检验动态价值保守这一假设，未证明修复成功，继续跟进原driver。

- 真实TD短程对照结束real_value_ablation_train_control，返回码0，日志logs/amp_g1/real_value_ablation_train_control.log。

- 真实TD短程对照启动real_value_ablation_velocity_control，driver PID2689332、child PID2692200；配置/命令/峰值/log见logs/amp_g1/real_value_ablation.pipeline.json，勿重复启动。

- A1/G1具体实现差异已核对：A1的43维AMP特征含机身线速度、足端位置和高度，G1的61维仅角速度/关节角/关节速度；G1参考配置四帧而当前两帧。结合静态参考姿态高D分数，列为风格信号偏姿态的待验假设，不能据此宣称根因或修复成功；原0/.5价值对照保持不变。
- 本轮恢复核实：driver PID2689332，阶段`real_value_ablation_velocity_control`，child PID2692200；当前诊断运行目录`logs/supermimic/2026-11-04_06-23-45_439174_g1_real_value_ablation_control`，最新诊断checkpoint`logs/supermimic/2026-11-04_06-23-45_439174_g1_real_value_ablation_control/model_3500.pt`。正式来源与最佳模型结论不变；动态更新以pipeline及实际ps为准。

- 真实TD短程对照结束real_value_ablation_velocity_control，返回码0，日志logs/amp_g1/real_value_ablation_velocity_control.log。

- 真实TD短程对照启动real_value_ablation_gait_control，driver PID2689332、child PID2694072；配置/命令/峰值/log见logs/amp_g1/real_value_ablation.pipeline.json，勿重复启动。

- A1/G1来源差异核实：logs/amp_a1/convergence_report.json的training_origin.kind=warm_start，actor/WM来源checkpoints/go2_manager_converged.pt（SHA256 07fc3f6e0e6801a3e60ab591be25dbeb3071c930809f847dd14284477dbfa9dd）；G1 R1–R3是随机初始化。A1成功不能单独证明当前G1冷启动能形成步态。待当前0/.5对照结束，若无真实迈步收益，优先诊断从零步态启动/动态数据覆盖，再决定分阶段基础行走预训练；维持WM/AMP、禁PPO、正式随机来源及原验收。

- 真实TD短程对照结束real_value_ablation_gait_control，返回码0，日志logs/amp_g1/real_value_ablation_gait_control.log。

- 真实TD短程对照control完整速度/步态评估结束，速度失败19项、步态失败14项；只证明本次诊断结果，不是正式三点验收。

- 真实TD短程对照启动real_value_ablation_train_anchor，driver PID2689332、child PID2694577；配置/命令/峰值/log见logs/amp_g1/real_value_ablation.pipeline.json，勿重复启动。

- 真实TD短程对照anchor初始审计通过：四网/四优化器逐项匹配同一R3模型；任务/数据split不变，仅实验开关不同，属诊断续训，不是正式G1成功来源。

- 进一步核实A1初始model_0已具备迈步：formal_r1_baseline_gait.json在1/1.5m/s指令下实际vx=.94146/1.43389、步频3.4181/3.4889Hz、零摔倒；G1随机model_0约115–116摔且步频0。来源差异比单凭机器人类别更直接。
- 修正旧诊断表述：reference_behavior_diagnostic_r2的hold是固定参考关节目标，不是完全静止状态；其平均vx=.501、2秒128/128摔倒而style=.99978。它证明高风格分数不保证稳定步行，不能单独证明D只看静态姿态。

- 真实TD短程对照结束real_value_ablation_train_anchor，返回码0，日志logs/amp_g1/real_value_ablation_train_anchor.log。

- 真实TD短程对照启动real_value_ablation_velocity_anchor，driver PID2689332、child PID2698057；配置/命令/峰值/log见logs/amp_g1/real_value_ablation.pipeline.json，勿重复启动。

- 真实TD短程对照结束real_value_ablation_velocity_anchor，返回码0，日志logs/amp_g1/real_value_ablation_velocity_anchor.log。

- 真实TD短程对照启动real_value_ablation_gait_anchor，driver PID2689332、child PID2700038；配置/命令/峰值/log见logs/amp_g1/real_value_ablation.pipeline.json，勿重复启动。

- 真实TD短程对照结束real_value_ablation_gait_anchor，返回码0，日志logs/amp_g1/real_value_ablation_gait_anchor.log。

- 真实TD短程对照anchor完整速度/步态评估结束，速度失败20项、步态失败15项；只证明本次诊断结果，不是正式三点验收。

- 真实TD短程0/.5对照全部结束；按real_value_ablation.pipeline.json及velocity/gait报告判断是否有实际迈步收益，无收益则停止此轮，不盲目续训；G1未独立成功前不进入X1。

- 关键决定（2026-11-04）：用户指出Go2可从零收敛，G1应复用其训练过程。已新增`G1-Velocity-Flat`同机器人平地冷启动任务（共享G1奖励/动力学，关闭AMP），计划先从随机初始化验证基础行走，再用同机器人actor/世界模型warm-start G1 AMP；critic/判别器/优化器重新创建。当前真实TD对照仍按pipeline跟进，完成前不重启或叠加正式训练。
- 当前代码增加冷启动任务但尚未提交/训练；校验通过py_compile与git diff --check。待现有real_value_ablation pipeline终止后，先提交此实现，再做32env smoke，随后按GPU容量启动G1-Velocity-Flat冷启动。

- 真实TD=0/.5短程对照已完整结束：同一R3 model_3000续训500步到3500，control固定整体RMSE(.6422,.2238,.3938)、53摔，anchor(.6335,.2406,.3831)、58摔；两臂七指令步态步频均0，style forward/fast分别control 1.2943/1.3792、anchor 1.2683/1.4213。anchor没有真实迈步收益，停止把真实TD锚定作为当前修复方向；证据logs/amp_g1/real_value_ablation.pipeline.json及对应velocity/gait JSON，均为诊断续训，不是G1成功。
- 已按Go2从零收敛流程新增G1冷启动基础任务：`G1-Velocity-Flat`共享G1平地资产、PD、奖励和SuperMimic接口但关闭AMP；修复G1 reward对`joint_deviation_gait_fraction`的忽略，使初期可使用平方关节惩罚并在最终阶段回到现有L1 walk惩罚。新增CPU测试`tests/test_g1_reward.py`与既有课程测试共5项通过，三处源码py_compile及git diff --check通过。
- 当前正式/诊断进程已退出；真实TD pipeline stage=complete，最新诊断checkpoint为logs/supermimic/2026-11-04_06-31-11_000288_g1_real_value_ablation_anchor/model_3500.pt。
- 下一步：提交冷启动任务与记录后，先运行G1-Velocity-Flat 32env短跑/保存恢复，确认无接口错误；再按Go2课程从G1随机初始化训练基础行走，独立评估有真实步态后warm-start G1 AMP。

- 对照Go2 Manager进一步核实：Go2随机训练model_0→3000先使用弱初期奖励，随后在3000→5000逐步引入最终步态项；G1此前虽有通用课程接口，但G1特有`flight`/`feet_distance`未参与课程，且G1奖励忽略`joint_deviation_gait_fraction`，因此实际没有复现Go2初期平方关节惩罚。已修复：G1特有项在fraction=0为0并随课程插值，G1关节偏移从平方项插值到最终L1项；课程过滤对Go2保持兼容。提交`9b77f25`，CPU6项通过。
- 下一步运行G1-Velocity-Flat冷启动性能/训练：先以18432与更大无AMP并行数做短profiling，选择不OOM且吞吐最高配置；从随机model_0训练至3000（reward curriculum 3000→5000，保存1000/2000/3000），独立检查速度/步态后再续到5000并决定是否warm-start G1 AMP。
- 当前HEAD应核实为9b77f25；无运行中的训练进程。最近GPU smoke/resume：G1-Velocity-Flat 32env model_20保存、model_20→25恢复成功，日志目录logs/supermimic/2026-11-04_06-48-21_171420_g1_velocity_smoke及...06-48-57_604456_g1_velocity_smoke_resume。

- G1-Velocity-Flat性能profiling完成：24576env运行80迭代稳定，末段真实转移吞吐约1.19e5/s；32768env出现PhysX GPU allocator 50331648-byte分配失败、场景损坏和大量CUDA错误，虽进程返回0但后段指标失真，结果作废。后续冷启动固定24576env，避免以异常吞吐作结论。证据目录logs/supermimic/2026-11-04_06-53-35_966382_g1_velocity_profile24576与logs/supermimic/2026-11-04_06-56-37_971059_g1_velocity_profile32768，原始错误保留于Kit日志。
- 下一步命令：启动`G1-Velocity-Flat`随机冷启动24576env、迭代3000、reward curriculum 3000→5000、保存1000/2000/3000；当前无训练进程。

- G1基础冷启动已启动：PID2711249，task G1-Velocity-Flat，24576env，随机seed0，iterations3000，reward curriculum start=3000/end=5000，WM4096×4/window8，imag8192/H32，actor_lr_scale=.3，compile FP32；日志由当前训练进程stdout及run目录记录，勿重复启动。

- G1-Velocity-Flat冷启动24576正式更新在iteration500 actor想象阶段CUDA OOM：申请16MiB时仅余9MiB，进程返回1；model_0已保存但该运行无有效训练结论，目录logs/supermimic/2026-11-04_07-00-05_640293_g1_velocity_cold_start作废。24576仅warmup profiling约1.19e5/s，不能据此作为完整更新容量。结合G1 AMP 18432完整actor峰值约23.1GiB，后续冷启动固定18432env并保持WM/imag批次。
- 当前无训练进程；下一条命令重启G1-Velocity-Flat随机冷启动18432env、同reward课程和批次，勿使用作废24576目录。

- G1冷启动重启：PID2713582，run_name g1_velocity_cold_start18432，18432env，随机model_0，iterations3000，reward curriculum 3000→5000，完整actor/critic/WM更新，勿重复启动。24576 OOM已作废。


## Go2流程复现：G1冷启动完成（2026-11-04，本轮）
- 随机初始化冷启动已正常完成3000迭代，进程已退出，无需恢复或重复启动；当前HEAD为9b77f254ec6e08bbd3a8dabe556bbb7a18ffa840。
- 运行目录：logs/supermimic/2026-11-04_07-04-43_790158_g1_velocity_cold_start18432；配置见该目录/config.json。18432 env、seed0、reward curriculum 3000→5000、关闭AMP、WM/imag/critic完整更新；checkpoint为model_0.pt、model_1000.pt、model_2000.pt、model_3000.pt，当前最佳候选为model_3000.pt，尚未完成独立速度/步态评估。
- 24576 env正式更新因actor想象阶段OOM作废；32768 profiling因PhysX allocator错误作废。18432运行无该错误并产出完整三点checkpoint。
- 下一条执行命令：补齐G1-Velocity-Flat的checkpoint-aware评估入口，然后对上述四个checkpoint运行独立速度/步态评估；只有确认基础行走后，才从同机器人checkpoint warm-start G1 AMP并重新创建critic/判别器/优化器。

## G1冷启动基础行走评估启动（2026-11-04）
- 已补齐checkpoint-aware的G1-Velocity-Flat评估支持，CPU测试6项通过，py_compile与git diff --check通过；尚未提交，待评估结果一起提交。
- 当前无训练进程；评估仅使用冷启动目录logs/supermimic/2026-11-04_07-04-43_790158_g1_velocity_cold_start18432中的model_0/1000/2000/3000。
- 当前运行：将执行四点速度/步态独立评估；日志与报告保存至logs/amp_g1/g1_velocity_cold_start_assessment.*。评估结束后先检查真实迈步，再决定G1 AMP warm-start。
- 评估尝试2723124已终止：未加headless导致Isaac Sim GUI初始化在zenity缺失处卡住，未产生仿真指标；该尝试不计入模型结论。GPU残留已清理。
- 下一条命令：使用headless重新运行同一四checkpoint评估，保留新日志并核对PID。
- 冷启动四点评估已完成，报告logs/amp_g1/g1_velocity_cold_start_assessment.json。model_0/1000大多摔倒；model_2000/3000稳定站立但7指令步频均0。model_3000前进均速约0.0158m/s、forward RMSE约0.5968、3摔，未形成基础行走，不能warm-start AMP。
- 评估headless重跑PID2727520已退出；首次GUI卡死尝试不计结果。按Go2同一随机谱系继续model_3000到5000，使用checkpoint保存的3000→5000奖励课程和18432 env；训练结束再评估，必要时继续到Go2同等最终阶段。
- 续训尝试PID2730565已作废并终止：命令遗漏continue-run，虽加载model_3000权重但从iteration0重新计数，约到200即停止，目录logs/supermimic/2026-11-04_07-42-23_379560_g1_velocity_cold_start18432_to5000及其model_0不作为结果。
- 下一条命令：同一model_3000使用continue-run，从checkpoint iteration3000正确续到5000；新目录和PID以实际日志为准。

## G1冷启动3000到5000完成（2026-11-04，本轮）
- 正确continue-run已完成model_3000到model_5000，训练目录logs/supermimic/2026-11-04_07-44-59_766317_g1_velocity_cold_start18432_continue5000；进程已退出，无OOM/PhysX错误。model_4000/5000已保存，5000为当前最佳候选但尚未独立验收。
- 训练末段5000：reward curriculum fraction=1，linear_error约0.237、yaw_error约0.503、falls_per_minute约1.76，真实转移吞吐约5.55万/s；这些是训练统计，不能代替独立步态评估。
- 下一步命令：headless运行model_4000和model_5000的G1七指令20秒×8步态评估；若真实步频/摔倒达标，再以model_5000作为同机器人G1 AMP warm-start来源并重新创建critic/判别器/优化器。
- model_4000/5000独立步态评估已完成，报告logs/amp_g1/g1_velocity_cold_start_4000_5000_assessment.json。model_4000仍站立；model_5000前进/快走真实移动且零摔倒，但前进步频4.656Hz、腾空0.055s、摆动离地0.0045m、足滑0.219m/s，超过频率/足滑且低于腾空/离地阈值，未通过G1基础步态标准，不能warm-start AMP。
- 决定按Go2后续流程沿model_5000同一谱系继续最终奖励到9000；5000后奖励已为最终值，actor_lr_scale降为0.15以复现Go2后段，保持18432 env和其余学习批次，保存6000/7000/8000/9000。
- 下一条命令：使用continue-run从model_5000续到9000，完成后对四个检查点做独立速度/步态评估；未通过前不进入G1 AMP。
- 已读取并纳入后续约束docs/experiments/G1_AMP_RECOMMENDATIONS_2026-11-04.md：当前5000只作为真实运动候选，不能称walk；后续AMP诊断需与速度对照同源、继承actor/WM、重建critic/D/优化器并逐项验证新增特征/历史，参考数据必须保持split与Git归档；不把D分数/WM loss替代闭环指标。当前5000→9000仍按原命令运行，不中途改变量。
- 续训当前核实PID2741172仍存活，目录logs/supermimic/2026-11-04_08-00-37_784295_g1_velocity_cold_start18432_to9000，model_6000已保存；训练末指标尚非独立验收。

## G1冷启动5000到9000完成，四点评估启动（2026-11-04）
- 同谱系最终奖励续训已完成9000，PID2741172已退出，目录logs/supermimic/2026-11-04_08-00-37_784295_g1_velocity_cold_start18432_to9000，model_6000/7000/8000/9000已保存；训练过程无OOM/PhysX错误。末段训练统计约linear_error .13-.16、yaw_error .39、falls_per_minute .3-.7，仅作训练信号。
- 当前无训练进程；headless评估将读取6000/7000/8000/9000，输出logs/amp_g1/g1_velocity_cold_start_6000_9000_assessment.json。评估前不启动AMP。

## G1冷启动9000四点评估完成，诊断AMP准备（2026-11-04）
- 报告logs/amp_g1/g1_velocity_cold_start_6000_9000_assessment.json：6000/7000/8000/9000均七指令零摔倒且能前进；9000前进vx=.601、fast vx=.999，步频3.672/4.258Hz、腾空.087/.093s、摆动离地.0072/.0141m、足滑.076/.197m/s。频率/腾空/离地仍未达G1正式阈值，故9000仅为稳定运动诊断来源，不是基础walk验收或正式G1 AMP成功来源。
- 依据G1_AMP_RECOMMENDATIONS，下一实验从同一model_9000 warm-start现有G1 AMP特征：继承actor/WM及归一化，重建critic/D/优化器，AMP interval5、D lr1e-5、GP40、探索OU .6，18432 env、其余学习批次不变；保存独立model_0/1000/2000/3000，监测碎步指标。正式G1连续三点、加噪、录像和审计标准保持不变。
- 下一条命令：启动诊断G1-AMP-Flat warm-start model_9000，当前无训练进程。
- 诊断AMP队列PID2754624已在约1700迭代终止并保留目录logs/supermimic/2026-11-04_08-29-51_887706_g1_amp_warm9000_diag的model_0/1000。训练期真实falls约2.5-3/min、linear_error约.23-.27，均较model_9000速度来源明显退化；D/AMP风格分数上升不能视为闭环收益。该队列是诊断消融，不是正式G1来源。
- 下一步命令：独立评估诊断AMP model_0/1000的七指令步态，并与model_9000报告逐项比较；若无步态收益，停止当前AMP特征/参数方向，按建议文档转向成对速度对照或特征/参考数据单变量实验。
- 诊断AMP独立评估已完成，报告logs/amp_g1/g1_amp_warm9000_diag_assessment.json。model_0复现9000来源；model_1000风格距离forward 7.45→5.36、fast 10.88→8.37，但前进步频3.754Hz、腾空.087s、摆动离地.0068m、足滑.072m/s，仍不达正式阈值；七指令零摔倒。风格改善不能替代步态改善。
- 下一步执行同model_9000、18432 env、同探索OU .6、同1000轮预算的G1-Velocity无AMP对照；控制臂与AMP臂初始actor/WM相同，均warm-start并重建critic/优化器。
- 同源无AMP对照已完成1000轮，目录logs/supermimic/2026-11-04_08-45-32_585067_g1_velocity_warm9000_control1000，model_0/1000保存；训练期model_1000约3.0 falls/min、linear_error .255，与诊断AMP同量级，提示warm-start后重建critic/训练分布是混杂因素。
- 下一步命令：headless评估无AMP对照model_0/1000，完成与AMP model_0/1000的逐项步态比较；报告只作诊断，不替代正式G1验收。
- 64维根线速度AMP特征实现已提交commit e375093（默认61维兼容，新增schema=g1_amp_64_velocity_v1；真实/参考/想象统一body-frame根线速度，metadata携带schema；G1 checkpoint-aware评估同步）。CPU unit tests/test_*.py共58项通过，相关子集31项通过；默认MotionLibrary metadata与旧R3 G1 checkpoint逐字一致。
- 下一条命令：从稳定运动model_9000启动同预算1000轮的64维AMP短程筛选，其他AMP参数与旧warm9000诊断一致；输出logs/amp_g1/g1_amp_warm9000_velocity64_diag.*。新实验仅作单变量诊断，不替代G1正式验收。
- 64维根线速度AMP短程已完成，PID2775303退出，目录logs/supermimic/2026-11-04_09-09-01_259556_g1_amp_warm9000_velocity64_diag，model_0/1000保存。末训练1000约falls/min3.40、linear_error .274、AMP style .382，不能代替独立步态。
- 下一步命令：headless评估64维AMP model_0/1000，报告logs/amp_g1/g1_amp_warm9000_velocity64_diag_assessment.json；与61维AMP及无AMPcontrol逐项比较。
