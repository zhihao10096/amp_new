# 当前状态与恢复入口

核实时间：2026-11-04T12:55:53+08:00。权威目录 `/pfs/user/learning/amp_new`；SSH `ssh -p 9205 root@118.196.87.69`。
恢复先读 GOAL/PLAN/本文件，再核实 HEAD、pipeline、PID 和 GPU，避免重复启动。

## 版本、范围和决定

- 当前 HEAD `9fb00b305aea39a71944361b78d0a20cc8a81133`（新增冻结审计工具；训练内核哈希保持20ad0d3）；训练受测源码 `20ad0d3a2490b0c2771b6c8d0b8748674832e0cf`，23份源码SHA256一致。控制f32755e、奖励29b1875、终止eee92bb、RSI/严格评估/四帧审计20ad0d3。
- Manager/A1已独立完成；G1仅29DOF/平地/walk，SuperMimic世界模型与可微想象，禁PPO。G1成功后才做X1下半身12DOF，跳过RKNN，部署参考reference/AMP；总目标未完成。
- 控制 `g1_implicit_pd_v1`，固定限矩88/139/25/5Nm，无DC转速降额；用户允许IdealPD备选，已核对其显式PD/固定限矩源码。当前无隐式PD故障证据，保持与legged_lab一致；切换执行器须独立类型/新WM谱系，不直接续用旧动力学。
- state `g1_state84_base_contact_v1`（WM84/critic125/actor480）；旧DC/83维WM禁止训练复用，旧隐式PD actor可独立评估。reward `g1_legged_lab_walk_v1`，16项及最终R=.5task+dtstyle。
- 训练height<.2/torso或pelvis接触终止；独立评估保留height<.5/tilt>60°，`fall_definition=native_or_height05_tilt60_v1`。严格越界采样可连续累计，不等于独立摔倒回合数。
- G1七份动作 `assets/motions/g1/` Git/SHA256复核7/7通过。A1/G1实际动作须由项目Git管理，X1复制后按GOAL忽略。

## 唯一队列、运行目录和配置

- 当前唯一队列 `logs/amp_g1/aligned_extension_r1.pipeline.json`，driver `2938989`/active PID `2939097`，阶段 `aligned_extension_train3000`。旧baseline1000和冻结审计均退出，不重复启动。
- 当前正式run `logs/supermimic/2026-11-04_13-09-39_985939_g1_aligned_formal_r1_to3000`；配置同目录 `config.json`；训练日志 `logs/amp_g1/aligned_extension_train3000.log`；完整命令/PID见pipeline.jobs。1000来源为旧aligned_formal_r1。
- profiling16384/18432完整反传通过：约46307/50820真实转移/s、峰值22196/23208MiB；选四网更新且无OOM/PhysX错误的18432。按余量跳过20480，不代表已OOM。汇总 `logs/amp_g1/aligned_performance_summary.json`。
- 正式18432env/随机seed0/model0→1000，不继承profile权重；WM512×3/batch4096×4/window8，actor/critic512,256,128，imag8192/H32，critic3×4，buffer128/collect1，FP32最高精度/编译。
- AMP61维四帧，D512,256/2048×2/lr1e-5/GP40/interval5/AMP ramp1000；RSI.5/同帧命令对齐True，评估关闭。OU.3/25%+Gaussian.1，actor_lr_scale.15；WM预热300/critic200/actor ramp500。

## 最新/最佳模型和评估

- 最新 `logs/supermimic/2026-11-04_13-09-39_985939_g1_aligned_formal_r1_to3000/model_2000.pt`；初始对照仍是 `logs/supermimic/2026-11-04_12-45-04_890456_g1_aligned_formal_r1/model_0.pt`。无已验收G1最佳/收敛模型。
- 1000训练正常退出，actor/critic/WM/D更新500/8400/4000/280，四网/优化器有限且参数变化，随机来源审计通过，峰值23374MiB；1000总迭代包含500轮预热，actor仅更新500次。证据 `logs/amp_g1/aligned_formal_r1_update_audit.json`。
- 独立七指令20s×8env共24项失败：0.6/1m/s每足步频0/.013Hz、腾空0/.085s，vx RMSE1.387/1.440；严格fall/越界采样608/614。风格距4.204→2.648、4.210→2.634（约37%改善），仍未学会稳定行走。原始 `logs/amp_g1/aligned_formal_r1_gait0_1000.json`。
- 完整速度30s/96env/12固定+3随机已完成，单点passed=False：速度30项失败、步态24项失败；固定整体RMSE(vx/vy/yaw)=1.293/.533/.613，三随机vx RMSE1.281–1.300。完整速度输出 `logs/amp_g1/aligned_formal_r1_velocity1000.json`；单点结论 `logs/amp_g1/aligned_formal_r1_assessment1000.json`，以pipeline阶段为准。不能代替三连续点、加噪、录像和最终审计。
- 已完成接口回归：CPU92、原生GPU/编译梯度、四网保存恢复、RSI/严格评估/四帧metadata、旧DC/schema拒绝及A1三点审计passed，见 `logs/amp_g1/rsi_alignment_validation.audit.json`。本轮仅文档变更，不重跑GPU训练。
- 已完成模型 `checkpoints/go2_manager_converged.pt`、`checkpoints/a1_amp_converged.pt` 保留，无需重训。

## 已排除方向、未解决问题和下一步

- 历史增加OU/节流D/真实TD/MPC/补动态拟合/61→64→70/四帧未通过walk；旧Go2课程使G1移动但碎步。历史DC9000不能导入新PD WM。严重骨架错配/RSI穿透无证据支持；A1/G1随机命令冲突约55%是共有现象。
- RSI本机counter1/2差异、默认关闭/同帧命令、严格评估及四帧审计均已修复。接口通过不证明训练收益，1000早期点失败也不证明隐式PD是根因。
- 仍需区分仅500次actor更新与稳定性/WM梯度问题；先读完整速度/checkpoint报告，再决定有证据的单变量验证，不开权重网格或盲切IdealPD。
- 已知差异：端点力矩/控制周期加速度与接触计时代理、yaw-rate而非heading、混合RSI、D512/256 LeakyReLU及统一decay（上游1024/512 ELU/输出decay.1）；尚无独立因果结论。
- 历史已归档 `docs/history/PROGRESS_2026-11-04_before_aligned_result.md`、`docs/history/STATUS_2026-11-04_before_aligned_result.md`；本轮思路/结果 `doc/G1_ALIGNED_BASELINE_2026-11-04.md`，PD候选 `doc/G1_IMPLICIT_PD_RESTORE_2026-11-04.md`，正式标准 `G1_CONVERGENCE.md` 不变。

下一条命令：

```bash
cd /pfs/user/learning/amp_new
git rev-parse HEAD
cat logs/amp_g1/aligned_extension_r1.pipeline.json
ps -p 2938989 -o pid,ppid,etime,stat,args
nvidia-smi
```

当前仅跟进已启动的 `logs/amp_g1/aligned_extension_r1.pipeline.json`，核对driver/active PID、run目录与最新checkpoint；勿重复启动。冻结审计已完成，结论和CPU92证据见doc/G1_ALIGNED_MODEL_AUDIT_2026-11-04.md。

- 2026-11-04T12:56:59+08:00 原队列已于2026-11-04T12:54:17.660648+08:00完成并退出，GPU0%/1MiB；1000单点passed=False，步态失败24项、速度失败30项。固定整体RMSE(vx/vy/yaw)=1.293/0.533/0.613，三随机种子vx RMSE1.281–1.300；没有已验收G1最佳模型，X1未开始。本轮未修改训练源码或启动额外实验，IdealPD仍为允许的独立候选，不能将当前失败归因于隐式PD。

- 2026-11-04T13:00:02+08:00 续接目标：上一轮属于progress（完成新PD1000全套独立评估和审计，非仅状态复述）。已核实HEAD e969d8f/无旧PID或GPU作业。当前优先检验“500次actor更新不足”与“新动力学想象偏差”并存的假设；计划新增冻结G1模型审计，使用当前隐式PD/state84/上游混合/四帧AMP，普通/参考起点分别量测真实多步转移、闭环回报、终止概率及有限策略梯度。不复用历史DC诊断结论，不改控制/奖励或启动权重网格；审计后决定是否同配置续到3000。

- 2026-11-04T13:01:46.016999+08:00 冻结G1模型审计启动driver2934344/child2934345；状态logs/amp_g1/aligned_model_audit1000.pipeline.json，输出logs/amp_g1/aligned_model_audit1000.json，当前PD/state84/四帧AMP，不训练。

- 2026-11-04T13:02:03.119460+08:00 冻结G1模型审计结束，阶段complete/returncode0；证据logs/amp_g1/aligned_model_audit1000.json及同名.log。

- 2026-11-04T13:06:30+08:00 冻结新模型审计已完成：普通/参考32步真实与想象bootstrap均值1.09807/1.09826、-.32111/-.28897；actor梯度10.13/4.26且有限、动作无clip，WM实际输入clip极少；参考32步速度预测RMSE.2088，尚未验证物理梯度方向。CPU项目范围92passed；不限定目录pytest误收集第三方logs/reference已排除。思路doc/G1_ALIGNED_MODEL_AUDIT_2026-11-04.md；GitHub独立SuperMimic复现仅作路线/预算参考，不直接移植参数。决定保持当前全部学习配置，1000同谱系续到3000并独立2000/3000评估；尚未启动，先提交工具和证据。

- 2026-11-04T13:08:24+08:00 冻结审计工具/CPU92/GPU结果已提交9fb00b305aea39a71944361b78d0a20cc8a81133。已启动唯一同配置1000→3000续训队列driver2938989，状态logs/amp_g1/aligned_extension_r1.pipeline.json；保持18432env及全部学习参数/新PD/奖励/state84/四帧AMP/RSI，resume四网/四优化器并continue-run，不重计数；保存2000/3000再两点步态与完整速度，G1未成功前不进入X1。

- 2026-11-04T13:08:25.650252+08:00 同配置续训队列启动aligned_extension_train3000，driver2938989/child2939097；配置/命令/状态logs/amp_g1/aligned_extension_r1.pipeline.json，日志logs/amp_g1/aligned_extension_train3000.log，勿重复启动。

- 2026-11-04T13:10:29+08:00 当前原续训driver2938989/child2939097已加载1000并从1001继续；实际run=logs/supermimic/2026-11-04_13-09-39_985939_g1_aligned_formal_r1_to3000，配置同目录config.json；原1000模型仍为最新已保存模型，18432env，未重启预热。

- 2026-11-04T13:11:53+08:00 当前1000冻结D的CPU反事实：4096留出专家序列style均值.90948、同姿态四帧重复且角速度/关节速度清零.89998，差.00950；重复帧保留速度.90961、反向帧保留速度.90652。训练段差.00927。支持“当前D时间/运动敏感性弱”候选，但合成序列不是物理行走，D仅训练280步，不能据此宣称根因；原始logs/amp_g1/aligned_discriminator_sensitivity1000.json，保持当前续训不混改D，后续比较3000。原续训driver2938989/child2939097存活，1200轮实际更新、约54183转移/s、峰值24092MiB，无OOM/PhysX错误。

- 2026-11-04T13:19:13+08:00 2000配置/数据/随机来源/四优化器审计passed；仅CLI网络尺寸list→tuple表示不同，JSON语义比较无超参变化。actor/critic/WM/D步数1500/20400/8000/680；D留出专家/合成静止style=0.89507/0.87263。当前训练不动；原driver内存中的旧审计在3000后会误报此类型差异，已准备修正后仅接续审计/评估，不重复训练。上游另有镜像增强/损失.1和6维朝向，本项目3维重力/480观测，不能照搬525维索引。

- 2026-11-04T13:21:31.283225+08:00 同配置续训队列结束aligned_extension_train3000，returncode0/validTrue；峰值24134MiB，证据logs/amp_g1/aligned_extension_train3000.log。

- 2026-11-04T13:21:31.306927+08:00 同配置续训队列失败AssertionError(['wm_hidden', 'actor_hidden', 'critic_hidden'])，核实原PID及logs/amp_g1/aligned_extension_r1.pipeline.json，不自动重复启动。

- 2026-11-04T13:21:47+08:00 原1000→3000训练已returncode0/validTrue并保存2000/3000；仅旧审计把网络尺寸list/tuple误判而退出，已保留原pipeline状态/脚本并启动仅审计/评估恢复driver2951034。训练未重启、模型/配置未修改，JSON数值比较严格保留超参数差异检测；状态仍logs/amp_g1/aligned_extension_r1.pipeline.json。

- 2026-11-04T13:21:48.475716+08:00 仅恢复完成训练后的配置/四网审计及独立评估，不重新启动训练；网络尺寸list/tuple按相同数值比较，保留原失败记录和检查点。

- 2026-11-04T13:21:48.527735+08:00 同配置续训队列启动aligned_extension_gait，driver2951034/child2951152；配置/命令/状态logs/amp_g1/aligned_extension_r1.pipeline.json，日志logs/amp_g1/aligned_extension_gait.log，勿重复启动。

- 2026-11-04T13:22:27+08:00 两点四网更新/配置/数据/随机来源完整审计passed，2000/3000步数actor1500/2500、critic20400/32400、WM8000/12000、D680/1080。原恢复评估driver2951034/child2951152运行；另起独立只读3000冻结审计driver2951902，两小评估共卡不与训练并发，峰值不作训练容量证据。D3000留出专家/合成静止style=0.87623/0.85001；配置无变化，尚无walk结论。

- 2026-11-04T13:22:27.974844+08:00 冻结G1模型审计启动driver2951902/child2951903；状态logs/amp_g1/aligned_model_audit3000.pipeline.json，输出logs/amp_g1/aligned_model_audit3000.json，当前PD/state84/四帧AMP，不训练。

- 2026-11-04T13:22:47.225570+08:00 冻结G1模型审计结束，阶段complete/returncode0；证据logs/amp_g1/aligned_model_audit3000.json及同名.log。

- 2026-11-04T13:22:58.210486+08:00 同配置续训队列结束aligned_extension_gait，returncode0/validTrue；峰值11468MiB，证据logs/amp_g1/aligned_extension_gait.log。

- 2026-11-04T13:22:58.211810+08:00 2000/3000步态独立评估结束，失败项计数{2000: 22, 3000: 15}；继续完整速度，不以style判成功。

- 2026-11-04T13:22:58.216690+08:00 同配置续训队列启动aligned_extension_velocity，driver2951034/child2952473；配置/命令/状态logs/amp_g1/aligned_extension_r1.pipeline.json，日志logs/amp_g1/aligned_extension_velocity.log，勿重复启动。

- 2026-11-04T13:25:49+08:00 3000独立步态六组零严格fall，转弯16个终止/越界采样；先前口头“七组全零”已更正。0.6/1m/s步频/腾空/净空均0，vx RMSE.596/.996；稳定站立，未迈步。风格距.612/.796仍明显改善。新冻结审计普通32步实际/想象bootstrap3.297/2.297、梯度norm170.97；参考.826/.318、梯度29.26。下一项冻结成对首动作梯度检验：复制物理起点并共同接触预热，沿32步想象回报动作梯度做±小扰动，后续同actor闭环，比较实际与模型回报和零对照；不训练/MPC，不改PD或奖励。

- 2026-11-04T13:28:08+08:00 当前新PD3000冻结物理回报方向审计启动driver2956933；32起点×10分支，8步共同预热，首动作沿H32回报梯度全关节/腿部±.1/.3 RMS，之后同actor闭环，含两个零对照。状态logs/amp_g1/aligned_return_direction3000.pipeline.json；完整速度原队列继续，两只读小仿真共卡，不启动训练或MPC。

- 2026-11-04T13:28:08.563205+08:00 冻结G1模型审计启动driver2956933/child2956934；状态logs/amp_g1/aligned_return_direction3000.pipeline.json，输出logs/amp_g1/aligned_return_direction3000.json，当前PD/state84/四帧AMP，不训练。

- 2026-11-04T13:28:24.517335+08:00 冻结G1模型审计结束，阶段complete/returncode0；证据logs/amp_g1/aligned_return_direction3000.json及同名.log。

- 2026-11-04T13:28:34.430362+08:00 同配置续训队列结束aligned_extension_velocity，returncode0/validTrue；峰值11412MiB，证据logs/amp_g1/aligned_extension_velocity.log。

- 2026-11-04T13:28:34.431257+08:00 同配置1000→3000续训及两点完整独立评估结束，单点通过[False, False]；三点/加噪/录像/审计仍需独立完成。

- 2026-11-04T13:33:57+08:00 恢复核实：extension及direction队列均complete、旧PID退出、GPU0%/1MiB；model3000为最新，无已验收最佳。2000/3000完整速度失败30/19项、步态22/15项；3000前进实际vx约.004m/s、步频/腾空/净空0。H32首动作配对方向ordinary(.1全关节)真实/模型斜率.231/2.751，但+相对零对照仅+.00106、零对照RMS.00294；reference为.131/.335，+收益-.00164、零对照RMS.00597。该统计余弦为跨样本斜率向量余弦，不能解释为完整动作梯度夹角；接触预热后物理起点仍有差异，未排除配对噪声/critic偏差。决定不盲续、不切PD，先完成证据归档与配对审计方法复核；IdealPD保留为用户允许的独立固定限矩候选，非已验证修复。
