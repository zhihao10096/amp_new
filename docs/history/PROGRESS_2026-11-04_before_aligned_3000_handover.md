# 进度与恢复入口

最后核实：2026-11-04T12:55:53+08:00。恢复先读GOAL/PLAN/STATUS，再核实commit、pipeline、PID/GPU与产物；不重复启动。详细历史已归档[PROGRESS历史](docs/history/PROGRESS_2026-11-04_before_aligned_result.md)，当前完整配置/模型/PID/命令见STATUS。

- 总目标：Manager/A1已完成；G1仅29DOF平地walk，成功后X1下半身12DOF，禁PPO，SuperMimic世界模型/可微想象。总目标未完成，X1未开始。
- 用户约束：G1无DC转速降额；A1/G1实际参考动作复制且由项目Git管理；X1动作复制后忽略、清单入Git，部署参考reference/AMP，跳过RKNN。
- 历史诊断：Go2课程使旧G1冷启动9000移动但碎步；真实TD0/.5、MPC/动态拟合、AMP61/64/70/四帧均未通过。A1初始actor/WM继承Manager，不能与G1随机起点直接类比。详见全程问题报告和历史记录。
- 控制f32755e：恢复上游隐式PD固定限矩，无证据表明其有缺陷。用户允许IdealPD，已核对本机IsaacLab2.1显式PD/固定限矩实现；如采用须新控制类型/WM谱系。
- 奖励29b1875：16项上游公式/最终混合及oracle通过；终止eee92bb：state84和原生接触、GPU1851次oracle通过；RSI20ad0d3：默认关闭/同帧one-shot、本机counter差异、严格评估及四帧metadata修复。CPU92/原生GPU/编译梯度/四网恢复/旧模型边界/A1三点审计passed。
- 12:39–12:45：唯一driver2915722完成16384/18432完整更新profiling，约46307/50820真实转移/s、峰值22196/23208MiB，选18432（+9.7%）；余量不足未尝试20480，不导入profile权重。
- 12:45–12:50：随机G1 AMP0→1000正常结束，run `logs/supermimic/2026-11-04_12-45-04_890456_g1_aligned_formal_r1`；AMP61四帧/RSI.5同帧对齐/隐式PD/state84/上游奖励。四网更新actor500/critic8400/WM4000/D280，审计passed，峰值23374MiB；最新model1000，无已验收最佳。
- 12:51：独立七指令24项失败，0.6/1m/s步频0/.013Hz、腾空0/.085s，vx RMSE1.387/1.440，严格fall/越界采样608/614（非独立摔倒回合数）。风格距改善约37%不等于行走，不能据此判定隐式PD是根因。
- 当前队列已complete、原driver及全部子进程退出、GPU0%/1MiB；状态 `logs/amp_g1/aligned_baseline_r1.pipeline.json`，核对原进程，勿重复启动。G1三点/加噪/录像/最终审计未完成。
- 下一步先读完整速度/assessment，区分actor实际训练预算和WM/稳定性问题，再决定单变量验证；不盲续旧配置、不做奖励网格、不在运行中切换PD。思路/限制见 `doc/G1_ALIGNED_BASELINE_2026-11-04.md` 和 `doc/G1_IMPLICIT_PD_RESTORE_2026-11-04.md`。

下一条命令：`cat logs/amp_g1/aligned_baseline_r1.pipeline.json`，按其中PID核实ps/GPU，再读取assessment1000。原始日志只保留路径。

- 2026-11-04T12:56:59+08:00 原队列已于2026-11-04T12:54:17.660648+08:00完成并退出，GPU0%/1MiB；1000单点passed=False，步态失败24项、速度失败30项。固定整体RMSE(vx/vy/yaw)=1.293/0.533/0.613，三随机种子vx RMSE1.281–1.300；没有已验收G1最佳模型，X1未开始。本轮未修改训练源码或启动额外实验，IdealPD仍为允许的独立候选，不能将当前失败归因于隐式PD。

- 2026-11-04T12:57:34+08:00 本轮结果/IdealPD备选/精简交接文档已提交 `e969d8f2e61c7b2cfc78e03714b65b494c74bcf0`；受测训练源码仍为20ad0d3。STATUS提交后已写入准确HEAD，未改训练配置或启动实验。

- 2026-11-04T13:00:02+08:00 续接目标：上一轮属于progress（完成新PD1000全套独立评估和审计，非仅状态复述）。已核实HEAD e969d8f/无旧PID或GPU作业。当前优先检验“500次actor更新不足”与“新动力学想象偏差”并存的假设；计划新增冻结G1模型审计，使用当前隐式PD/state84/上游混合/四帧AMP，普通/参考起点分别量测真实多步转移、闭环回报、终止概率及有限策略梯度。不复用历史DC诊断结论，不改控制/奖励或启动权重网格；审计后决定是否同配置续到3000。

- 2026-11-04T13:01:46.017105+08:00 冻结G1模型审计启动driver2934344/child2934345；状态logs/amp_g1/aligned_model_audit1000.pipeline.json，输出logs/amp_g1/aligned_model_audit1000.json，当前PD/state84/四帧AMP，不训练。

- 2026-11-04T13:02:03.119536+08:00 冻结G1模型审计结束，阶段complete/returncode0；证据logs/amp_g1/aligned_model_audit1000.json及同名.log。

- 2026-11-04T13:06:30+08:00 冻结新模型审计已完成：普通/参考32步真实与想象bootstrap均值1.09807/1.09826、-.32111/-.28897；actor梯度10.13/4.26且有限、动作无clip，WM实际输入clip极少；参考32步速度预测RMSE.2088，尚未验证物理梯度方向。CPU项目范围92passed；不限定目录pytest误收集第三方logs/reference已排除。思路doc/G1_ALIGNED_MODEL_AUDIT_2026-11-04.md；GitHub独立SuperMimic复现仅作路线/预算参考，不直接移植参数。决定保持当前全部学习配置，1000同谱系续到3000并独立2000/3000评估；尚未启动，先提交工具和证据。

- 2026-11-04T13:08:24+08:00 冻结审计工具/CPU92/GPU结果已提交9fb00b305aea39a71944361b78d0a20cc8a81133。已启动唯一同配置1000→3000续训队列driver2938989，状态logs/amp_g1/aligned_extension_r1.pipeline.json；保持18432env及全部学习参数/新PD/奖励/state84/四帧AMP/RSI，resume四网/四优化器并continue-run，不重计数；保存2000/3000再两点步态与完整速度，G1未成功前不进入X1。

- 2026-11-04T13:08:25.650347+08:00 同配置续训队列启动aligned_extension_train3000，driver2938989/child2939097；配置/命令/状态logs/amp_g1/aligned_extension_r1.pipeline.json，日志logs/amp_g1/aligned_extension_train3000.log，勿重复启动。

- 2026-11-04T13:10:29+08:00 当前原续训driver2938989/child2939097已加载1000并从1001继续；实际run=logs/supermimic/2026-11-04_13-09-39_985939_g1_aligned_formal_r1_to3000，配置同目录config.json；原1000模型仍为最新已保存模型，18432env，未重启预热。

- 2026-11-04T13:11:53+08:00 当前1000冻结D的CPU反事实：4096留出专家序列style均值.90948、同姿态四帧重复且角速度/关节速度清零.89998，差.00950；重复帧保留速度.90961、反向帧保留速度.90652。训练段差.00927。支持“当前D时间/运动敏感性弱”候选，但合成序列不是物理行走，D仅训练280步，不能据此宣称根因；原始logs/amp_g1/aligned_discriminator_sensitivity1000.json，保持当前续训不混改D，后续比较3000。原续训driver2938989/child2939097存活，1200轮实际更新、约54183转移/s、峰值24092MiB，无OOM/PhysX错误。

- 2026-11-04T13:19:13+08:00 2000配置/数据/随机来源/四优化器审计passed；仅CLI网络尺寸list→tuple表示不同，JSON语义比较无超参变化。actor/critic/WM/D步数1500/20400/8000/680；D留出专家/合成静止style=0.89507/0.87263。当前训练不动；原driver内存中的旧审计在3000后会误报此类型差异，已准备修正后仅接续审计/评估，不重复训练。上游另有镜像增强/损失.1和6维朝向，本项目3维重力/480观测，不能照搬525维索引。

- 2026-11-04T13:21:31.283346+08:00 同配置续训队列结束aligned_extension_train3000，returncode0/validTrue；峰值24134MiB，证据logs/amp_g1/aligned_extension_train3000.log。

- 2026-11-04T13:21:31.307033+08:00 同配置续训队列失败AssertionError(['wm_hidden', 'actor_hidden', 'critic_hidden'])，核实原PID及logs/amp_g1/aligned_extension_r1.pipeline.json，不自动重复启动。

- 2026-11-04T13:21:47+08:00 原1000→3000训练已returncode0/validTrue并保存2000/3000；仅旧审计把网络尺寸list/tuple误判而退出，已保留原pipeline状态/脚本并启动仅审计/评估恢复driver2951034。训练未重启、模型/配置未修改，JSON数值比较严格保留超参数差异检测；状态仍logs/amp_g1/aligned_extension_r1.pipeline.json。

- 2026-11-04T13:21:48.475802+08:00 仅恢复完成训练后的配置/四网审计及独立评估，不重新启动训练；网络尺寸list/tuple按相同数值比较，保留原失败记录和检查点。

- 2026-11-04T13:21:48.527841+08:00 同配置续训队列启动aligned_extension_gait，driver2951034/child2951152；配置/命令/状态logs/amp_g1/aligned_extension_r1.pipeline.json，日志logs/amp_g1/aligned_extension_gait.log，勿重复启动。

- 2026-11-04T13:22:27+08:00 两点四网更新/配置/数据/随机来源完整审计passed，2000/3000步数actor1500/2500、critic20400/32400、WM8000/12000、D680/1080。原恢复评估driver2951034/child2951152运行；另起独立只读3000冻结审计driver2951902，两小评估共卡不与训练并发，峰值不作训练容量证据。D3000留出专家/合成静止style=0.87623/0.85001；配置无变化，尚无walk结论。

- 2026-11-04T13:22:27.974932+08:00 冻结G1模型审计启动driver2951902/child2951903；状态logs/amp_g1/aligned_model_audit3000.pipeline.json，输出logs/amp_g1/aligned_model_audit3000.json，当前PD/state84/四帧AMP，不训练。

- 2026-11-04T13:22:47.225646+08:00 冻结G1模型审计结束，阶段complete/returncode0；证据logs/amp_g1/aligned_model_audit3000.json及同名.log。

- 2026-11-04T13:22:58.210595+08:00 同配置续训队列结束aligned_extension_gait，returncode0/validTrue；峰值11468MiB，证据logs/amp_g1/aligned_extension_gait.log。

- 2026-11-04T13:22:58.211870+08:00 2000/3000步态独立评估结束，失败项计数{2000: 22, 3000: 15}；继续完整速度，不以style判成功。

- 2026-11-04T13:22:58.216761+08:00 同配置续训队列启动aligned_extension_velocity，driver2951034/child2952473；配置/命令/状态logs/amp_g1/aligned_extension_r1.pipeline.json，日志logs/amp_g1/aligned_extension_velocity.log，勿重复启动。

- 2026-11-04T13:25:49+08:00 3000独立步态六组零严格fall，转弯16个终止/越界采样；先前口头“七组全零”已更正。0.6/1m/s步频/腾空/净空均0，vx RMSE.596/.996；稳定站立，未迈步。风格距.612/.796仍明显改善。新冻结审计普通32步实际/想象bootstrap3.297/2.297、梯度norm170.97；参考.826/.318、梯度29.26。下一项冻结成对首动作梯度检验：复制物理起点并共同接触预热，沿32步想象回报动作梯度做±小扰动，后续同actor闭环，比较实际与模型回报和零对照；不训练/MPC，不改PD或奖励。

- 2026-11-04T13:28:08+08:00 当前新PD3000冻结物理回报方向审计启动driver2956933；32起点×10分支，8步共同预热，首动作沿H32回报梯度全关节/腿部±.1/.3 RMS，之后同actor闭环，含两个零对照。状态logs/amp_g1/aligned_return_direction3000.pipeline.json；完整速度原队列继续，两只读小仿真共卡，不启动训练或MPC。

- 2026-11-04T13:28:08.563281+08:00 冻结G1模型审计启动driver2956933/child2956934；状态logs/amp_g1/aligned_return_direction3000.pipeline.json，输出logs/amp_g1/aligned_return_direction3000.json，当前PD/state84/四帧AMP，不训练。

- 2026-11-04T13:28:24.517415+08:00 冻结G1模型审计结束，阶段complete/returncode0；证据logs/amp_g1/aligned_return_direction3000.json及同名.log。

- 2026-11-04T13:28:34.430471+08:00 同配置续训队列结束aligned_extension_velocity，returncode0/validTrue；峰值11412MiB，证据logs/amp_g1/aligned_extension_velocity.log。

- 2026-11-04T13:28:34.431314+08:00 同配置1000→3000续训及两点完整独立评估结束，单点通过[False, False]；三点/加噪/录像/审计仍需独立完成。

- 2026-11-04T13:33:57+08:00 恢复核实：extension及direction队列均complete、旧PID退出、GPU0%/1MiB；model3000为最新，无已验收最佳。2000/3000完整速度失败30/19项、步态22/15项；3000前进实际vx约.004m/s、步频/腾空/净空0。H32首动作配对方向ordinary(.1全关节)真实/模型斜率.231/2.751，但+相对零对照仅+.00106、零对照RMS.00294；reference为.131/.335，+收益-.00164、零对照RMS.00597。该统计余弦为跨样本斜率向量余弦，不能解释为完整动作梯度夹角；接触预热后物理起点仍有差异，未排除配对噪声/critic偏差。决定不盲续、不切PD，先完成证据归档与配对审计方法复核；IdealPD保留为用户允许的独立固定限矩候选，非已验证修复。
