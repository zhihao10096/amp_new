# 进度与恢复入口

- 2026-11-04 09:40:07 +0800 用户要求的全程Markdown复盘已完成：docs/experiments/G1_AMP_ISSUES_AND_SOLUTIONS_2026-11-04.md（11节），覆盖移植/归档、R1-R3、RSI/PD/几何/探索、WM响应/MPC/真实TD、Go2课程突破、warm9000三臂、奖励可导边界、OOM/错误续训及70维编译失败；已核对核心原始报告，提交b2343e1，本地artifacts保存同名副本。当前70维验证终态failed，没有1000轮新训练；下一步改写FK常量广播并补GPU编译/四网更新恢复，保留失败产物。总目标仍未完成，X1未启动。

- 2026-11-04T09:26:16 关键决定：以已完成64维诊断为对照，新增可选70维schema，仅追加左右踝roll link原点在骨盆坐标系的6维位置；专家/真实/想象统一由绝对关节角经已核对USD几何FK计算，不改变WM状态或奖励，不叠加历史/RSI条件变量。现有几何证据logs/amp_g1/kinematics_r3.json及g1_kinematics_reference_consistency.json；GitHub MimicKit关键体观测检索存logs/amp_g1/github_amp_feet_features_2026-11-04.json。先CPU梯度/训练split几何及GPU接口、编译更新/恢复验证，再提交并从同model_9000做1000轮单变量筛选；是否续训仅由真实步态收益决定。当前无训练进程。

- 2026-11-04 09:24:07 +0800 状态核查与64维评估收尾：HEAD e375093；64维model_0/1000独立七指令评估完整，三臂均零摔倒，但64维0.6m/s步频3.477Hz、腾空.0836s、离地6.05mm，1m/s步频4.350Hz，未解决碎步/抬脚。无AMP/61维对照亦未通过；不能跨schema直接比较绝对风格距离，也不能把无AMP臂的共同退化全部归因于AMP。报告[G1_AMP_WARM9000_COMPARISON_2026-11-04.md](docs/experiments/G1_AMP_WARM9000_COMPARISON_2026-11-04.md)。实查无GPU训练/评估进程、GPU0%/1MiB，不重复启动或按原配置盲续；下一步先核查局部足端动态特征的一致坐标/FK，再单变量验证。旧STATUS归档到docs/history/STATUS_2026-11-04_before_velocity64_result.md，现STATUS已压缩为可直接接手的当前事实。G1未成功，X1尚未开始；本轮未修改生产代码。

- 2026-11-04实现建议复核：HEAD9b77f25，真实TD0/.5已结束且两臂无迈步；新G1基础5000已七组零摔倒并前向移动，但碎步/低抬脚/足滑及侧移未达标。PID2741172继续既有5000→9000，核实最新6000、无独立评估。已记录[建议报告](docs/experiments/G1_AMP_RECOMMENDATIONS_2026-11-04.md)：同源无AMP/AMP对照→运动特征/历史→参考条件/碎步约束，必要时参考跟踪辅助。建议未改生产、训练或正式验收，不重复启动。

- 2026-11-04 A1/Go2/G1综合诊断完成：[报告](docs/experiments/A1_GO2_G1_CONVERGENCE_GAP_2026-11-04.md)。Go2从零但使用弱初期平方正则及3000–5000步态课程，A1继承其完整actor/WM，G1从零无对应启动课程。CPU确认G1风格运动区分不足、静止脚离地项满分/高度梯度0，并记录参考覆盖和RSI指令独立采样差异；均不冒充闭环因果结论。脚本/报告/日志`logs/amp_g1/a1_g1_gap_audit.*`，不改生产或原0/.5对照，Manager/A1不重训。control3500仍无迈步，anchor已进入完整评估，以pipeline为准。

- 2026-11-04 A1/G1原因追查：初始评估确认A1 model_0继承Manager actor/WM，七组全部零摔倒，1/1.5m/s实际速度.941/1.434、每足步频3.418/3.489Hz；G1随机model_0七组806次摔倒且步频0。A1快速AMP达标包含既有行走能力，必须先纠正起点不一致，再分析G1站立局部解。原真实TD对照driver2689332继续，未重启实验或修改配置；详见STATUS及后续诊断报告。

恢复先读GOAL/PLAN/STATUS，再核实HEAD、ps/GPU和pipeline；勿重复启动。

- 总目标：Manager/A1已独立成功 → G1仅平地walk → 成功提交后X1下半身12DOF AMP；禁PPO、WM可微想象，各阶段独立验收提交。G1/X1未成功前总目标未完成。
- 当前版本用git rev-parse HEAD核实；本次实现可选critic_real_fraction（默认0），固定critic样本预算混合真实一步TD/想象TD(λ)，actor仍WM更新。使用终止前状态/gait，摔倒不bootstrap、超时bootstrap，跳过非终止命令切换，独立真实采样RNG保存恢复。
- CPU55、G1原生13摔/52超时/356命令切换及真实TD误差1.19e-7、编译梯度/真实四网20→25/CLI继承.5/旧模型默认0/A1回归全部通过。CUDA RNG精确恢复、默认0单次更新与1be9b27逐位一致；real_value_validation.audit.json。短跑步态仍失败，不算成功；验证driver2683870已退出，当前无正式训练。
- 诊断依据：普通/参考真实TD RMSE .03271/.09694，policy_value_r3_td_residual.json；32步参考真实/想象bootstrap 1.123/.866。此前动态拟合/响应约束降低预测/响应误差，但冷启动和统一预热MPC均无稳定性收益；不接入当前MPC，详见docs/experiments/G1_DYNAMICS_RESPONSE_2026-11-04.md。
- 进行0/.5短程消融：同R3 model_3000四网/四优化器初值，18432env、原R3全部批次/任务相同、固定critic样本总量，各续500步到3500，保存3000/3250/3500并完整速度/步态/风格评估。仅诊断续训，无收益停止；状态logs/amp_g1/real_value_ablation.pipeline.json，当前driver PID2689332已启动，代码fa93cab；按pipeline跟进，勿重启。
- 最新正式仍R3 model_3000，完整路径/配置/R1–R3失败指标及Manager/A1完成归档见STATUS；无通过验收的G1最佳模型。Manager/A1勿重训，原未跟踪reference及诊断文件保留。
- G1全部实际动作（含新增/替换）复制assets/motions/g1，文件及清单Git管理，训练前/提交前核验来源/许可/SHA256/split/默认路径。X1动作复制后.gitignore忽略、清单入Git，部署参考reference/AMP，跳过RKNN，待G1独立成功后实施。

下一条命令：cat logs/amp_g1/real_value_ablation.pipeline.json，再核对active_pid实际进程并跟进训练/完整评估，勿重复启动。接口通过不证明迈步收益，G1三点/加噪/录像/审计标准不变。

- 真实TD短程对照启动real_value_ablation_train_control，driver PID2689332、child PID2689497；配置/命令/峰值/log见logs/amp_g1/real_value_ablation.pipeline.json，勿重复启动。

- 真实TD短程对照control初始审计通过：四网/四优化器逐项匹配同一R3模型；任务/数据split不变，仅实验开关不同，属诊断续训，不是正式G1成功来源。

- G1动作归档要求已再次明确写入PLAN第7阶段，训练前及新增/替换后核验；本轮复核七份动作、manifest和来源许可文件均受Git管理、SHA256吻合且默认路径位于项目内，证据logs/amp_g1/g1_motion_plan_recheck_2026-11-04.json。
- 用户关注A1能迈步而人形G1失败：解释须区分已证实的站立局部解与待验证根因，不能只以人形更难作结论；既有诊断排除/负结果见G1_CONVERGENCE和动作响应报告。当前同源真实TD对照继续，不重复启动训练。

- 真实TD短程对照结束real_value_ablation_train_control，返回码0，日志logs/amp_g1/real_value_ablation_train_control.log。

- 真实TD短程对照启动real_value_ablation_velocity_control，driver PID2689332、child PID2692200；配置/命令/峰值/log见logs/amp_g1/real_value_ablation.pipeline.json，勿重复启动。

- A1/G1具体实现差异已核对：A1的43维AMP特征含机身线速度、足端位置和高度，G1的61维仅角速度/关节角/关节速度；G1参考配置四帧而当前两帧。结合静态参考姿态高D分数，列为风格信号偏姿态的待验假设，不能据此宣称根因或修复成功；原0/.5价值对照保持不变。

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

- 真实TD=0/.5短程对照已完整结束：同一R3 model_3000续训500步到3500，control固定整体RMSE(.6422,.2238,.3938)、53摔，anchor(.6335,.2406,.3831)、58摔；两臂七指令步态步频均0，style forward/fast分别control 1.2943/1.3792、anchor 1.2683/1.4213。anchor没有真实迈步收益，停止把真实TD锚定作为当前修复方向；证据logs/amp_g1/real_value_ablation.pipeline.json及对应velocity/gait JSON，均为诊断续训，不是G1成功。
- 已按Go2从零收敛流程新增G1冷启动基础任务：`G1-Velocity-Flat`共享G1平地资产、PD、奖励和SuperMimic接口但关闭AMP；修复G1 reward对`joint_deviation_gait_fraction`的忽略，使初期可使用平方关节惩罚并在最终阶段回到现有L1 walk惩罚。新增CPU测试`tests/test_g1_reward.py`与既有课程测试共5项通过，三处源码py_compile及git diff --check通过。
- 下一步：提交冷启动任务与记录后，先运行G1-Velocity-Flat 32env短跑/保存恢复，确认无接口错误；再按Go2课程从G1随机初始化训练基础行走，独立评估有真实步态后warm-start G1 AMP。

- 对照Go2 Manager进一步核实：Go2随机训练model_0→3000先使用弱初期奖励，随后在3000→5000逐步引入最终步态项；G1此前虽有通用课程接口，但G1特有`flight`/`feet_distance`未参与课程，且G1奖励忽略`joint_deviation_gait_fraction`，因此实际没有复现Go2初期平方关节惩罚。已修复：G1特有项在fraction=0为0并随课程插值，G1关节偏移从平方项插值到最终L1项；课程过滤对Go2保持兼容。提交`9b77f25`，CPU6项通过。
- 下一步运行G1-Velocity-Flat冷启动性能/训练：先以18432与更大无AMP并行数做短profiling，选择不OOM且吞吐最高配置；从随机model_0训练至3000（reward curriculum 3000→5000，保存1000/2000/3000），独立检查速度/步态后再续到5000并决定是否warm-start G1 AMP。

- G1-Velocity-Flat性能profiling完成：24576env运行80迭代稳定，末段真实转移吞吐约1.19e5/s；32768env出现PhysX GPU allocator 50331648-byte分配失败、场景损坏和大量CUDA错误，虽进程返回0但后段指标失真，结果作废。后续冷启动固定24576env，避免以异常吞吐作结论。证据目录logs/supermimic/2026-11-04_06-53-35_966382_g1_velocity_profile24576与logs/supermimic/2026-11-04_06-56-37_971059_g1_velocity_profile32768，原始错误保留于Kit日志。

- G1基础冷启动已启动：PID2711249，task G1-Velocity-Flat，24576env，随机seed0，iterations3000，reward curriculum start=3000/end=5000，WM4096×4/window8，imag8192/H32，actor_lr_scale=.3，compile FP32；日志由当前训练进程stdout及run目录记录，勿重复启动。

- G1-Velocity-Flat冷启动24576正式更新在iteration500 actor想象阶段CUDA OOM：申请16MiB时仅余9MiB，进程返回1；model_0已保存但该运行无有效训练结论，目录logs/supermimic/2026-11-04_07-00-05_640293_g1_velocity_cold_start作废。24576仅warmup profiling约1.19e5/s，不能据此作为完整更新容量。结合G1 AMP 18432完整actor峰值约23.1GiB，后续冷启动固定18432env并保持WM/imag批次。

- G1冷启动重启：PID2713582，run_name g1_velocity_cold_start18432，18432env，随机model_0，iterations3000，reward curriculum 3000→5000，完整actor/critic/WM更新，勿重复启动。24576 OOM已作废。

- 2026-11-04 Go2流程复现阶段：G1-Velocity-Flat随机冷启动18432 env已完成3000迭代，model_0/1000/2000/3000均已保存，进程退出且无OOM；24576正式更新因actor阶段OOM作废。下一步补齐G1-Velocity checkpoint评估并检查是否形成真实步态，未评估前不启动G1 AMP warm-start。
- 2026-11-04：为冷启动checkpoint补齐G1-Velocity-Flat评估配置，CPU6项、编译和diff检查通过；已启动四个checkpoint的独立速度/步态评估，结果决定是否进入同机器人G1 AMP warm-start。
- 冷启动评估首次尝试因未传headless卡在GUI/zenity初始化，已kill并确认GPU残留清理；不计模型结论，改headless重跑。
- 冷启动四点评估完成：model_2000/3000已站立但步频全0，model_3000前进均速约0.016m/s、forward RMSE约0.597，未形成基础行走；不能warm-start G1 AMP。headless评估PID2727520退出，首次GUI卡死已排除。下一步同一谱系续训3000→5000。
- G1冷启动续训第一次命令遗漏continue-run，加载model_3000后从0重计数，已在约200轮kill并作废；不计训练结论。恢复逻辑已核对，下一次加continue-run从iteration3000续到5000。
- G1冷启动正确续训3000→5000完成，model_4000/5000已保存且无仿真错误；5000训练统计linear_error约.237、falls/min约1.76。已启动下一步model_4000/5000独立七指令步态评估，评估通过后才warm-start AMP。
- 冷启动model_4000/5000评估完成：5000已出现真实移动但为高频碎步（4.656Hz、腾空.055s、离地.0045m、足滑.219m/s），未通过G1步态标准，不能warm-start。按Go2最终奖励后段继续5000→9000，actor_lr_scale改为.15，随后评估6000/7000/8000/9000。
- 已读取G1_AMP_RECOMMENDATIONS：后续若进入AMP，必须同源速度对照、actor/WM继承且critic/D/优化器重建，新增动态特征/历史/参考筛选/辅助步态约束逐项消融，保持split/Git归档与闭环验收；当前5000→9000不改变量。当前model_6000已保存，PID2741172继续运行。
- G1冷启动同谱系最终奖励续训已完成9000，PID2741172退出，model_6000/7000/8000/9000保存且无仿真错误；按建议文档先做四点独立步态评估，未通过前不进入AMP。
- 6000/7000/8000/9000独立评估完成：9000最稳，前进.601/快走.999且零摔倒，但步频3.672/4.258Hz、腾空.087/.093、离地.0072/.0141仍不达正式walk阈值。按G1_AMP_RECOMMENDATIONS允许从稳定运动候选做诊断AMP；将继承model_9000 actor/WM，重建critic/D/优化器，先测既有AMP特征改善碎步，不宣称正式成功。
- 诊断AMP warm9000跑至约1700后停止：AMP风格分数提高，但真实falls约2.5–3/min、linear_error约.23–.27，较9000来源退化；保留model_0/1000，不把此队列作为正式结果。下一步独立步态评估model_0/1000确认是否有碎步改善，再按建议文档选择单变量方向。
- 诊断AMP model_0/1000评估完成：model_1000风格距离下降但步频/腾空/离地仍不达标，零摔倒；AMP尚未显示步态收益。按建议文档启动同model_9000、同探索/预算的无AMP速度对照，区分AMP与网络重建/训练时长。
- 同源无AMP1000轮对照完成，训练退化与AMP臂同量级；将独立评估control model_0/1000与AMP报告逐项对比，避免把重建网络影响归因于AMP。
- 64维根线速度AMP特征已按建议实现并提交e375093；默认61维兼容、旧R3 metadata精确匹配，CPU58项通过。下一步从model_9000启动同预算1000轮velocity64 AMP短程筛选，比较既有61维AMP和无AMP对照的步态指标。
- 64维根线速度AMP短程1000轮完成：style比61维高但训练falls/min约3.4、linear_error约.274；已启动独立model_0/1000步态评估，比较碎步指标后再决定下一变量。

- 70维足端特征验证启动feet70_integration，driver PID2790233、child PID2790320；配置/命令/log见logs/amp_g1/feet70_validation.pipeline.json，勿重复启动。

- 70维足端特征验证结束feet70_integration，返回码0，日志logs/amp_g1/feet70_integration.log。

- 70维足端特征验证启动feet70_smoke_initial，driver PID2790233、child PID2791858；配置/命令/log见logs/amp_g1/feet70_validation.pipeline.json，勿重复启动。

- 70维足端特征验证结束feet70_smoke_initial，返回码0，日志logs/amp_g1/feet70_smoke_initial.log。

- 70维足端验证失败FileNotFoundError(2, 'No such file or directory')，核对原pipeline及日志后修复，不启动训练。

- 2026-11-04T09:35:24 重要问题定位：70维CPU61项通过，但原生/短跑编译均遇PyTorch2.5.1/Inductor生成Triton的constexpr broadcast_to错误。Kit退出返回0不能代表验证通过：缺feet70_integration.json与model_20.pt，driver2790233已failed，正式1000轮未启动。原始日志logs/amp_g1/feet70_integration.log、feet70_smoke_initial.log，完整状态feet70_validation.pipeline.json；先修复FK编译表达并要求产物/通过标志，不能用退出码声称成功。

- 2026-11-04T09:42:23 70维FK编译修复：原验证driver2790233已退出、GPU空闲。原日志表明常量轴表广播生成tl.broadcast_to(constexpr,...)；GitHub检索存github_fk_inductor_broadcast_2026-11-04.json，未将不同版本Issue当作直接修复。FK现改为旋转基向量和Python标量几何常量，保留坐标/单位/关节顺序；正在CPU61及32/8192样本CUDA fullgraph值/梯度检查（会话12949，日志feet70_r2_cpu.log与feet70_fk_compile_r2.log）。新GPU验证使用r2 ID，要求报告passed、模型产物及无异常，保留原失败日志；1000轮训练尚未启动。

- 70维FK改写后CPU61及独立CUDA fullgraph通过：32/8192批量位置max1.79e-7m、梯度max4.77e-7；feet70_fk_compile_r2.json。完整原生/编译/四网更新恢复验证driver PID2797838已启动，状态logs/amp_g1/feet70_r2_validation.pipeline.json；原失败r1保留，勿重复启动。

- 70维足端特征验证启动feet70_r2_integration，driver PID2797838、child PID2797944；配置/命令/log见logs/amp_g1/feet70_r2_validation.pipeline.json，勿重复启动。

- 70维足端特征验证结束feet70_r2_integration，返回码0，日志logs/amp_g1/feet70_r2_integration.log。

- 70维足端特征验证启动feet70_r2_smoke_initial，driver PID2797838、child PID2799145；配置/命令/log见logs/amp_g1/feet70_r2_validation.pipeline.json，勿重复启动。

- 2026-11-04T09:45:10 70维完整原生/想象编译验证通过：65reset/13摔倒/52超时/356命令切换，专家特征max7.15e-7、原生足端位置max1.73e-6m、返回max1.79e-7、actor梯度max7.28e-12；feet70_r2_integration.json。当前driver2797838，阶段feet70_r2_smoke_initial，child2799145；继续四网更新/CLI恢复/A1回归，未启动1000轮。

- 70维足端特征验证结束feet70_r2_smoke_initial，返回码0，日志logs/amp_g1/feet70_r2_smoke_initial.log。

- 70维足端特征验证启动feet70_r2_smoke_resume，driver PID2797838、child PID2799919；配置/命令/log见logs/amp_g1/feet70_r2_validation.pipeline.json，勿重复启动。

- 70维足端特征验证结束feet70_r2_smoke_resume，返回码0，日志logs/amp_g1/feet70_r2_smoke_resume.log。

- 70维足端特征验证启动feet70_r2_a1_regression，driver PID2797838、child PID2801271；配置/命令/log见logs/amp_g1/feet70_r2_validation.pipeline.json，勿重复启动。

- 70维足端特征验证结束feet70_r2_a1_regression，返回码0，日志logs/amp_g1/feet70_r2_a1_regression.log。

- 70维足端特征验证全部通过：CPU61、参考训练段几何/梯度、原生接口/终止/命令/reset、编译返回/actor梯度、四网四优化器20→25/CLI schema恢复、61/64维旧模型metadata与D加载、A1回归；证据logs/amp_g1/feet70_r2_validation.audit.json。短跑不算收敛；下一步先提交实现，再启动同源1000轮诊断。

- 2026-11-04T09:47:30+08:00 关键验证完成：70维CPU61、独立CUDA fullgraph、完整原生/想象编译、四网四优化器20→25及CLI自动schema恢复、61/64旧metadata/D加载、A1 GPU回归全部通过，feet70_r2_validation.audit.json。FK常量广播编译问题已修复；短跑不证明收敛。准备提交可选70维实现后，从同9000模型/与64维同配置做1000轮诊断。
