# 进度索引

当前目标见 [GOAL.md](GOAL.md)，阶段计划见 [PLAN.md](PLAN.md)，恢复必须先读 [STATUS.md](STATUS.md) 并核实进程。
旧的长篇进度已保存在 [历史归档](docs/history/PROGRESS_2026-11-03.md)；历史路径不代表当前开发机存在。

## 2026-11-03 21:56:01 CST：熟悉项目与交接整理
- 已梳理 ManagerBasedRLEnv、共享 Torch 接口、SuperMimic 训练/评估链路和验收标准；代码基线24046e2。
- 核实当前RTX4090D 24GB且无实验进程；logs/checkpoints/videos缺失，旧Manager训练仍无收敛证据。
- 测试基线受缺少pytest阻塞；同时发现mediapy/项目安装元数据缺失、Isaac Sim许可尚未确认。本轮未安装依赖、未接受许可或启动训练。
- 采纳规则：精简AGENTS，维护GOAL/PLAN/STATUS；可直接commit；后续训练根据实测吞吐/显存尽量提高GPU利用率。
- 文档整理及交叉链接/diff检查完成，纳入本次文档提交；当前任务完成。后续实验等待新指示，恢复入口见STATUS。

## 继续Manager实现
- 用户已上传logs/videos并明确继续，暂停约束解除；核实145个日志/模型文件、5视频，Manager model0/1000/2000/2025存在，当前无实验进程。
- 优先解决依赖/仿真可执行性并分析静止策略；不直接假定继续训练即可收敛。
- 依赖安装完成，GPU集成检查已启动PID2336158，日志`logs/manager_4090/integration.log`。
- 总目标明确为Manager收敛后接入Go2 AMP（参考rl_amp，禁用PPO）。CPU23项/GPU集成PASS；8192环境吞吐实验PID2336854运行中。
- 8192env恢复200更新完成，吞吐约54553.0转移/s，真实线速度误差仍约0.69059；启动16384env同起点对照PID2337710。
- 已实现可选训练奖励渐进调度，真实RewardManager/想象同步权重，checkpoint保留最终任务并记录当前调度比例；验收拒绝未到最终权重的模型。CPU结果见logs/manager_4090/curriculum_cpu.log，GPU验证待吞吐实验结束。
- 16384env完成，最终吞吐99421.0转移/s、显存观测17918MiB，误差仍约.69；启动24576env对照PID2339624并连续采样GPU。
- 24576env完整100更新通过，峰值22506.0MiB、吞吐约133888/s；调度GPU检查PID2341954启动。
- 调度GPU一致性PASS，覆盖初始/中间/最终权重；开始32环境真实更新/保存恢复和2秒评估验证。
- 调度验证curriculum_smoke结束，退出码0，日志logs/manager_4090/curriculum_smoke.log。
- 调度验证curriculum_resume结束，退出码0，日志logs/manager_4090/curriculum_resume.log。
- 调度验证curriculum_eval结束，退出码0，日志logs/manager_4090/curriculum_eval.log。
- 调度全部验证通过（CPU25项/GPU三阶段奖励一致/32环境实际更新保存恢复短评估）；准备从Manager model1000的未更新actor起步验证弱正则，最终目标/验收不变。
- 提交6304099；核实model1000 actor网络与model0逐张量相同，已启动24576env/collect1/WM4096×4/imag4096/buffer128从1000至2500的弱正则实验PID2345789，日志logs/manager_4090/curriculum_train.log。
- 重要定位：24576随机actor落地触发PhysX patch buffer overflow（需求>=294912）；已停止PID2345789并作废本轮，优先按环境规模增大物理patch容量，重跑后再评估学习。
- patch默认163840已按32×envs扩至786432；错误进程SIGTERM未退出后核实身份并强制停止，开始24576env实际落地/reset GPU回归PID2349431。
- 复查全部性能日志：logs/manager_4090/profile16384.log, logs/manager_4090/profile24576.log也有物理patch错误，已标记该配置吞吐无效，扩容后须重测；原8192若无错误可保留。
- 扩容后24576env GPU回归PASS：122880reset/221184指令切换，奖励观测/三阶段调度一致，完整日志零PhysX错误。原16k/24k性能结果因初始化溢出作废；下一轮从原model1000重启，不使用错误轮权重。
- 提交917072e；已从原model1000重启修复后的24576env/collect1/imag4096/buffer128实验PID2351410，日志curriculum_fixed.log，持续GPU/物理错误监测；初始错误轮作废。
- 修复调度恢复默认值会意外禁用课程的边界；CPU26项PASS，开始32env省略调度参数的实际CLI恢复回归，主训练继续。
- 新增实际CLI恢复已验证省略参数仍保留调度4/12；model1500已保存，启动7指令运动诊断PID2356116，不把短评估当收敛。
- model1500独立7指令仍近似静止（forward均速约0），尚属早期300actor更新；model2000已保存并启动同标准诊断PID2360644，主训练继续。
- model2000弱正则评估仍静止；本轮至2500完成，启动gait2500诊断PID2363114，世界模型分组误差报告dynamics2000.json待复核；未开始最终约束。
- dynamics2000：现有低速数据单步/32步线速度误差.0032/.0132m/s，接触归一化误差约1；不能把停滞简单归因于已测轨迹预测很差。重点转向运动数据覆盖与闭环想象，暂不增加最终步态惩罚。
- model2500前进仍.00075，转弯约.104；停止同类续跑，转向真实运动覆盖假设。新增仅采样用周期trot生成器（actor仍无phase、无PPO），CPU28项PASS；启动参数物理扫描PID2367897，见trot_exploration_scan.log。
- 周期探索物理扫描结束：slow前进>.2m/s且零摔倒的组0个，报告trot_exploration_scan.json；需核对其它方向与可用状态覆盖再定训练方案。
- 首轮周期动作扫描未得到有效前进组（有-.3～-.65m/s后退覆盖），方向假设待核对；不将其直接当跟踪策略或投入长跑。启动PhysX足端Jacobian测量PID2370099，核对Go2实际关节方向/几何。
- 实测PhysX足端Jacobian确认几何符号基本正确；下一假设是抬腿相位/伺服与接触时序。启动2频率×2幅度×4相位的真实运动扫描PID2371518，日志trot_phase_scan.log；探索尚未接入训练。
- 用户指出d9eee9b3f248e5300e636c433255db2c1c3e086a可收敛；停止扩展未验证探索路线，优先系统对照该基线算法/状态/奖励/数据分布，找迁移差异。周期探索未进入正式训练。

- 恢复核实HEAD8029aaa、周期扫描已结束且GPU空闲。d9eee9b3是MuJoCo chase/dodge基线；同时用已收敛Isaac Lab Direct作中间对照。Manager迁移本身未改变WM/actor损失。发现此前弱正则仅复用权重，joint_deviation仍为L2范数/站立5倍，而已收敛速度阶段为平方和，且undesired_contacts仍为-1；需用数学一致的初期奖励作受控验证。
- 已实现初期奖励与已收敛速度阶段的数学对齐：关节平方惩罚渐变至最终范数、初期关闭非足接触惩罚；真实manager/想象共享有效训练配置，最终任务不变。CPU29项通过；GPU原生接口回归PID2377737，日志logs/manager_4090/baseline_reward_integration.log。GitHub源码检索因开发机外网超时，已有本地原始提交可直接验证平方惩罚定义；不引入未验证外部方案。
- 修正后的GPU原生manager回归PASS（80reset/1强制翻倒/144指令重采样/初中末奖励一致）；开始32env实际WM/actor/critic更新和保存烟测PID2378486，日志logs/manager_4090/baseline_reward_smoke.log。

- 烟测完成，model20=logs/supermimic/2026-11-03_23-10-31_076350_baseline_reward_smoke/model_20.pt，真实WM/actor/critic更新及保存成功；恢复CLI验证PID2379347（20→24，省略调度参数），日志logs/manager_4090/baseline_reward_resume.log。

- 恢复验证PASS：model24三网络/优化器均更新且有限，CLI继承4/12调度和最终公式；开始32env/2秒评估PID2380247，日志logs/manager_4090/baseline_reward_eval.log；证据baseline_reward_regression.json。
- 修正初期奖励的全链路验证完成：CPU29项、原生GPU接口、实际三网络更新/保存/CLI恢复及32env短评估均PASS，全日志零PhysX/CUDA错误；短评估仅证明可执行，不作收敛依据。准备提交修复后以8192env/collect4/WM4096×4/imag8192/buffer256从Manager随机初始化重训。
- 修复提交a3ea68e；新正式来源从Manager随机初始化启动PID2381345（不resume/不warm-start），8192env/collect4/WM4096×4/imag8192/buffer256，300WM预热+200critic预热，首段至3000、每500保存。初期奖励保持至6000、9000达最终；先观察速度，不提前套最终约束。日志logs/manager_4090/baseline_squared_train.log，GPU监控PID2381346。
- 已复核上一周期相位扫描112组：有7组前进>.2m/s且零摔倒；最佳1/1.5m/s指令实际vx约.389/.588，抬腿相位3π/2。该结果仅证明采样覆盖，不证明策略学习或跟踪收敛；保留为后备，当前先完成奖励基线对照，不混入训练。新随机来源model0已保存于2026-11-03_23-14-56_505712_manager_baseline_squared，训练初始化零物理错误。
- 新随机训练到600：model500已保存，actor从501开始更新；WM预热约18.8万样本/s，actor阶段约6.08万样本/s、1.86迭代/s。当前速度误差约.697，仅早期更新，尚不能判定学习成功；下一阶段监测1500/2000及真实运动。
- 针对4090D actor阶段平均GPU约44%的瓶颈，参考d9eee9b3的编译想象单步，新增默认关闭的compile_imagination选项。CPU30项通过，含AOT编译前后返回/轨迹/actor梯度一致；启动独立小批CUDA比较PID2386070，日志logs/manager_4090/compiled_imagination_cuda.log。正式训练仍运行a3ea68e的非编译实现，不受文件修改影响。

- 编译GPU比较首轮在TF32 high下返回最大差约6.4e-4，严格一致性未通过；尚未用于正式训练。CPU AOT一致，当前检验FP32 highest是否消除累计舍入差，PID2388047，日志logs/manager_4090/compiled_imagination_fp32.log。正式训练model1000已保存，linear_error约.695。

- FP32 highest下CUDA编译一致性PASS：actor梯度最大绝对差4.84e-8，128batch/H8单步链暖运行.0753→.0147秒（仅微基准，不代表训练加速）。编译仅在固定奖励阶段启用，课程插值期自动用普通路径避免逐轮重编译。启动真实32env更新/保存及课程切换烟测PID2388957，日志logs/manager_4090/compiled_imagination_smoke.log；最终CPU复验PID2388958。

- 编译32env真实更新/课程切换/保存PASS、CPU30项PASS；恢复验证PID2391480，日志logs/manager_4090/compiled_imagination_resume.log。已请求当前非编译主训练在迭代边界保存停止，准备对比8192×4与16384×2采样配置（每轮真实样本同为32768）及编译吞吐，然后从同一随机来源继续。

- 非编译主训练已在边界保存停止，最新checkpoint=logs/supermimic/2026-11-03_23-14-56_505712_manager_baseline_squared/model_1522.pt；启动7指令×4env×8秒早期真实步态诊断PID2392032，日志logs/manager_4090/baseline_squared_early_gait.log。该模型仅初期奖励，不作最终验收。
- 编译实现完整验证通过：CPU30项、CUDA FP32前后返回/梯度一致、真实32env三网络更新与课程切换、保存及恢复20→24；无PhysX/CUDA错误。准备提交后按相同model1522比较完整训练的并行配置，编译初次耗时单独记录。

- model1522早期7指令诊断结束，前进1m/s实际vx=0.00453，还未恢复有效前进；报告baseline_squared_early_gait.json。编译实现已提交8cb89bb，开始8192env/collect4/FP32编译完整100次更新吞吐实验PID2393181，日志compiled_profile8192.log，从model1522同起点对比。

- 8192编译100更新完成：稳定约10.4万真实样本/s、3.16迭代/s；零PhysX/CUDA错误，model1622保存，原非编译8192约6.1万/1.86。开始同model1522起点16384env/collect2对比PID2395620，日志logs/manager_4090/compiled_profile16384.log，其余WM/imag/buffer和每轮32768采样不变。

- 16384env/collect2编译100更新完成，约11.9万样本/s、3.65迭代/s，比8192编译约快15%，峰值17.5GB且零物理错误。继续测试32768env/collect1/buffer128（回放总容量及每轮32768真实样本与16k相同，单环境回放缩至2.56s），PID2397992，日志logs/manager_4090/compiled_profile32768.log；根据实测效率及学习质量选配置。
- 32768env/collect1/buffer128完整100更新零物理错误，稳定约12.5万样本/s、3.82迭代/s、峰值21728MiB，较非编译8192约2.1倍；三个配置对照报告compiled_profiles.json。采用32k继续同Manager随机来源model1622至3000，PID2401448，日志logs/manager_4090/baseline_squared_fast.log；单环境回放2.56秒，实际学习效果仍须验证。
- 主训练继续期间，按d9eee9b3中已存在的接触优先/稀有窗口存档准备下一项受控对照：新增默认关闭的WM采样选项及有容量上限的archive，尚未用于正式训练；当前32k主进程仍是已提交8cb89bb均匀采样。CPU验证日志priority_cpu.log，若3000仍停滞，再完成GPU验证并决定是否试用，不混改正在评估的训练。
- 新平方奖励/编译32k训练2100：真实linear_error从1700的.699降到.610，出现首次明显改善，model2000已保存；尚无新独立速度评估，保持单一训练路线至3000。候选接触优先/存档CPU33项通过但不启用；避免混入新因素影响判断。

- 到2300，真实linear_error已降至.402（2100为.610），说明当前路线开始学习运动。为保持实验单一，已将未启用的接触优先采样候选移出源码，备份logs/manager_4090/priority_candidate/priority.patch及测试；CPU33项仅为候选验证，正式代码恢复为8cb89bb（原CPU30项）。不启用额外采样方案。
- 初期平方奖励路线至3000完成，最后训练linear_error=.16393/yaw=.12427，零PhysX/CUDA错误，恢复运动学习；checkpoint=2026-11-03_23-40-16_677008_manager_baseline_squared_fast/model_3000.pt。启动完整速度20固定+3随机种子/30秒及7指令8重复20秒步态评估，进程见baseline_squared_eval3000.process.json；本轮奖励比例0，尚不能最终验收。
- model3000完整7指令步态评估完成：各轴速度RMSE全达标、各组零摔倒，1m/s实际vx=.99854；仍小碎步（步频6.087Hz、腾空.0422秒、离地.00664m、足滑.2857m/s），明确下一阶段是渐进最终步态奖励。完整20固定+3随机种子速度评估仍在运行，不能宣布最终收敛。
- 为避免2000次渐进权重阶段退回非编译执行，已将可选编译路径的奖励系数/关节公式混合比例改为GPU张量参数；真实manager仍读取同一当期浮点配置。新增CPU验证5个课程比例的返回/梯度与普通路径一致且只编译一张图，日志dynamic_reward_cpu.log。该实现尚未提交/用于正式训练，需CUDA及真实更新/恢复验证。
- model3000完整速度评估velocity_failures=[]：20固定+3随机种子全部阈值通过，随机稳态平均RMSE约(.0566,.0701,.0561)，随机摔倒1/2/0次，仍需最终步态及连续三检查点验收。GPU张量奖励实现CPU初次仅图数量断言失败（实际初始seed不带梯度、后续状态带梯度有两个合法图；返回/梯度已一致），改为检验各课程比例不增加编译图。启动CUDA中间比例一致性与真实32env更新/课程切换，进程见dynamic_reward.process.json。

- GPU张量奖励系数验证：CPU31项PASS，5个课程比例返回/梯度一致且复用同一组梯度输入图；CUDA中间比例actor梯度最大差2.98e-8；真实32env初中末课程更新/保存PASS。开始CLI恢复20→24 PID2417071，日志logs/manager_4090/dynamic_reward_resume.log。完成后提交并从model3000按3000→5000渐进最终权重、actor_scale=.15继续训练。
- 动态GPU奖励参数验证完成：CPU31项、CUDA中间比例返回/梯度一致、真实32env课程前中后更新/保存及CLI恢复20→24通过，全日志零物理/CUDA错误。计划提交后从Manager model3000开始3000→5000最终步态课程，actor_scale降至.15，保持32k/WM4096×4/imag8192/H32/FP32编译。
