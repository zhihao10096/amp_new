# 进度与恢复入口

恢复先读 [STATUS.md](STATUS.md) 并核实Git、进程和产物；目标见 [GOAL.md](GOAL.md)，阶段计划见 [PLAN.md](PLAN.md)。

## 已完成：Manager随机来源收敛（2026-11-04）
- 7000/8000/9000相隔1000迭代，完整速度和7指令步态全部通过；最终9000训练观测噪声复测通过。四轮完整速度评估合计1280机器人分钟零摔倒，三轮步态也零摔倒。
- 实际checkpoint来源/任务/最终奖励/三网络与优化器更新/有限性/SHA256审计通过，converged=true、failures=[]；证据 [MANAGER_CONVERGENCE.md](MANAGER_CONVERGENCE.md)。
- 最终模型checkpoints/go2_manager_converged.pt；9000随机稳态RMSE .04054/.04416/.03648，加噪 .04285/.04726/.05306；1/1.5m/s足滑 .07295/.11357，腾空均.1312s，站立步频0。
- videos/manager_gait_comparison.mp4为左3000/右9000的侧面对照，manager_fast_side.mp4快走、manager_stand.mp4站立；录像均零摔倒，侧面抽帧检查通过。相机副本和命令保存在logs/manager_4090，不改变训练代码。
- 所有项目训练/评估/录像进程结束，监控2381346停止，核实记录logs/manager_4090/final_process_check.json。当前阶段结果提交并建立本地标签manager-converged-20261104；AMP未启动。

## 保留的关键结论
- 用户确认d9eee9b3可收敛；对照该版本和Direct中间基线，发现初期弱正则没有还原平方关节惩罚。修正并随机重训后学会运动，再渐进最终奖励；未经单因素消融，不把改善全部归因于单项。见 [MANAGER_BASELINE.md](MANAGER_BASELINE.md)。
- 初期静止、单纯弱权重和无效溢出轮已排除；周期探索、外部策略、PPO和优先采样未用于正式训练。reference/保持用户原状。
- PhysX patch按32×env扩容；旧16k/24k溢出性能作废。真实完整更新对照后采用32k/collect1，FP32编译约12.5万真实转移/s、显存约21.8GB，TF32严格比较未过故不用。
- CPU31项及原生GPU接口、三网络更新、保存恢复、动态课程/编译梯度一致性此前通过；后续没有训练源码改动。AGENTS保持长期规则和文档入口。

## 下一阶段
- 按GOAL/PLAN，Manager后参考reference/rl_amp接入A1 AMP平地行走，再参考reference/legged_lab做G1平地walk，全程不用PPO。当前任务已完成，尚未启动AMP实验。
- 下一条恢复命令及最新/最佳checkpoint、版本、运行目录和配置见STATUS，避免重复启动。

历史事件及日志依据：[本轮完整过程](docs/history/PROGRESS_2026-11-04_manager.md)、[更早归档](docs/history/PROGRESS_2026-11-03.md)。

## 进入Go2 AMP平地阶段
- 恢复核实HEAD b1f59eb，前阶段记录的训练/评估/监控均已退出，GPU空闲；Manager验收和模型保留，不重复训练。
- 用户明确Go2 AMP也仅平地；G1后续仅平地walk，禁run和其它动作。全程禁止PPO，按阶段提交，总目标仍未完成。
- 已核对reference/rl_amp：43维状态（绝对关节角、局部足端、机体系线/角速度、关节速度、高度）相邻帧LSGAN与专家零中心梯度惩罚。现有63维WM状态足够，拟接入同一纯Torch特征和冻结判别器可微奖励，actor继续世界模型反传，不使用参考PPO训练器。
- A1运动数据为FL/FR/RL/RR逐腿顺序，当前IsaacLab关节顺序及Go2几何必须实测；拟用Go2 FK重算足端和高度，避免A1/Go2几何混入判别标签。先GPU探测，再锁定数据/验收，尚未启动AMP训练。

## 用户范围变更：A1替代Go2 AMP
- 按用户最新要求，将后续Go2 AMP改为A1 AMP平地行走，G1仅平地walk和全程禁PPO保持；已更新GOAL.md和PLAN.md，不能把A1阶段省略或以Go2结果代替。
- 尚未启动Go2几何探测或AMP实验，只有日志目录中的探测脚本草稿；无需停止运行作业。当前HEAD仍b1f59eb，GPU空闲，无最新/最佳AMP checkpoint。
- A1原生IsaacLab资产与reference/rl_amp的mocap_motions_a1对应，优先验证A1 Manager环境、关节顺序和FK，而非继续Go2几何适配。AMP判别器/纯Torch特征与世界模型可微想象方案继续适用。
- 下一条命令：核对UNITREE_A1_CFG、参考A1 URDF与运动库，随后建立A1-AMP-Flat配置和GPU接口验证。

- A1原生资产/关节/FK实测开始PID2474180，运行目录/pfs/user/learning/amp_new，命令logs/amp_a1/geometry_probe.process.json，日志geometry_probe.log；无AMP训练，HEAD f3abed8。

- A1 AMP纯Torch模块新增6项CPU测试全部通过，覆盖URDF零角FK/关节顺序、专家/真实特征一致、时间采样与留出边界、四元数反向同表示、冻结判别器状态梯度及LSGAN/GP更新。AMP训练尚未启动。原生A1几何探测PID2474180仍存活但停在sim启动后，正在采集栈定位，未重复启动。

- A1探测首轮栈证实在异常后的SimulationApp.close挂住（set_device/render/_app_control_on_stop）；补显式traceback后已停止旧PID2474180，重启仅诊断PID2477500，日志geometry_probe_v2.log，记录geometry_probe_v2.process.json。GitHub搜索#4365/#7361版本不适用，#7152支持先dump栈诊断，未盲目升级依赖。

- 重要定位：A1构造失败源于Go2专用非足接触正则Head_.*在A1资产不存在（有trunk），IsaacLab要求每个正则匹配。v2 traceback完整定位，不是资产缺失或CUDA问题；将非足接触pattern作为机器人配置，A1使用trunk/hip/thigh/calf，保留Go2原配置。两轮探测无有效样本，均不用于训练。

- 已实现A1-AMP-Flat原生Manager配置（plane/A1资产/独立接触pattern）、可选参考帧reset及原生AMP奖励term。Go2默认配置不变。重新启动A1 GPU探测PID2479004，日志geometry_probe_v3.log，记录geometry_probe_v3.process.json；新增源尚未提交，需全量CPU和GPU接口验证。

- A1原生任务GPU探测v3已完成，关节顺序为FL/FR/RL/RR的hip四项、thigh四项、calf四项；原生USD与reference URDF有2.5mm髋x、1.25mm侧向差异。1280真实状态拟合得到(.1805,.047,.0838,.2,.2)，残差max2.11e-6m/RMSE3.38e-7m，证据logs/amp_a1/geometry_{probe,fit}.json；专家/策略统一以原生FK重算足端，避免形态差异成为判别标签。
- 已接入A1 Manager配置、RSI重置、原生AMP奖励term、WM想象中的AMP梯度、判别器真实pair训练和checkpoint保存/恢复；新增纯Torch模块与7项AMP测试（新增编译/actor梯度覆盖），全量CPU运行中logs/amp_a1/cpu.log，尚未真实更新/保存恢复，因此尚未提交实现或启动正式训练。
- 当前HEAD f3abed8，未提交文件见git diff；本地编辑镜像/home/user/Desktop/dream_codex_workspace/amp_new_src，开发机为运行权威。下一步CPU结果→tests/check_amp_isaaclab.py真实接口→32env更新保存CLI恢复→锁定正式AMP验收→吞吐/正式训练。

- 全量CPU38项PASS（logs/amp_a1/cpu.log）。开始A1真实GPU接口/参考与站立reset/翻倒终止/指令切换/AMP真实想象奖励/本体FK和CUDA编译actor梯度验证PID2486508，完整命令logs/amp_a1/integration.process.json，日志integration.log；正式训练未开始。

- GPU首轮原生接口/RSI及站立reset/翻倒/指令切换/真实AMP奖励/FK断言通过，编译返回比较未过（max .205），尚不能启用正式编译训练。定位验证夹具用了即将过期的真实指令时间，两次滚动触发不同随机重采样；改为同一固定10s指令窗口，保留原返回/梯度阈值重新验证PID2490890，日志integration_v2.log；旧PID2486508已结束，无重复进程。
- checkpoint感知A1评估与独立留出风格距离已接入，预先标准AMP_CONVERGENCE.md已写入，正式训练尚未启动。新增评估/判定测试后全量CPU重跑PID2490891，日志cpu_v2.log；HEAD仍f3abed8，实现未提交。
