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
