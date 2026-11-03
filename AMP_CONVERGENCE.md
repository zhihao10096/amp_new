# A1 AMP 平地行走：范围与预先记录的验收

用户已将Go2 AMP改为A1 AMP。Manager阶段保留已完成的Go2验收，不重新定义或放宽。
当前实现参考 `reference/rl_amp`，使用Isaac Lab原生A1和ManagerBasedRLEnv平地环境；
actor沿SuperMimic的冻结世界模型/判别器可微想象路线更新，critic用TD(λ)，不使用PPO。
后续G1只做平地walk，不训练run或其它动作。两个AMP阶段均需独立训练、评估、录像及git提交。

## 数据和接口

- 数据限定项目Git管理的 `assets/motions/a1/{trot1,pace1,left_turn1,right_turn1}.txt`，
  原样复制自rl_amp commit `b4666fa99066ac5c8006b700bf7cc6bc2471232b` 的
  `datasets/mocap_motions_a1/`；来源/许可/SHA256见同目录README及manifest.json。
  来源retarget_config中的dog_walk03、dog_walk00、dog_walk09；不使用canter或dog_run04的trot2。
- 每条运动前80%用于训练/参考重置，后20%作为独立时间留出；相邻帧间隔严格为控制dt=.02秒，
  插值支撑点与整个transition不能跨split、clip末尾或loop首尾。文件SHA256、帧数、dt和split保存在checkpoint。
- 43维AMP特征：绝对关节角12、局部足端12、机体系线速度3/角速度3、关节速度12、高度1；
  判别器输入相邻两帧86维，LSGAN专家+1/策略-1，专家零中心梯度惩罚。
- 原生USD与reference URDF有毫米级差异。专家和策略均用原生A1 FK重算足端；
  hip_x/hip_y/hip_lateral/thigh/calf=(.1805,.047,.0838,.2,.2)，1280个PhysX状态验证残差max2.11e-6m。
  证据 `logs/amp_a1/geometry_fit.json`；不用形态差异训练判别器。
- 真实RewardManager与想象共享AMP奖励 `max(1-(D-1)^2/4,0)`，站立指令(norm≤.1)关闭style项。
  配置amp_weight为每秒权重，真实/想象均且仅乘一次控制dt；初期逐步提高至最终权重。
- 参考运动重置和普通站立重置混合训练；独立评估禁用参考重置，始终普通站立起步。
- 可从已验收Manager actor/世界模型热启动，A1阶段重新计数并保存model_0；
  明确记录跨机器人来源，判别器/critic及优化器新建，不把Manager成绩当作A1成绩。

## 在正式训练前锁定的标准

1. A1仅plane。训练指令vx=[0,1.5]、vy=[-.3,.3]、yaw=[-1,1]，10%站立，6–10秒切换；
   不训练跑步数据、粗糙地形或其它动作。
2. 完整速度：`amp_validation.A1_FIXED_CASES`的12指令×8环境×30秒，
   另96环境分别seed42/123/2026各30秒，剔除切换/reset首秒。
   各固定RMSE≤(.30,.25,.25)，站立≤(.10,.10,.10)，每随机组≤(.20,.15,.15)，全部零摔倒。
3. 步态：`A1_GAIT_CASES`七指令×8环境×20秒，seed42，七组零摔倒、各轴RMSE≤(.20,.15,.15)；
   1/1.5m/s每足步频≤4.5Hz、平均腾空≥.10s、平均摆动离地≥.012m、
   短摆动(<.08s)占比<50%、接触足滑<.15m/s，站立步频<.3Hz。
4. AMP风格独立指标：真实相邻状态对到留出专家对的标准化最近邻平方距离，
   采用专家训练段统计量（std下限.05），参考对限制平均vx距指令<.35m/s。
   固定seed1701，至少128策略对/128留出参考对，比较同数据/配置的A1初始model_0；
   1和1.5m/s的距离均至少改善10%。该指标不用训练中判别器的分数作结论。
5. 连续三个相隔1000训练迭代的A1 AMP检查点全部通过上述速度、步态和风格指标。
   最终检查点另做训练观测噪声下的完整速度复测，以及站立/正常走/快走侧面录像检查。
6. 证据需包含原生manager/reset/终止/真实与想象奖励一致、CUDA编译返回/actor梯度一致、
   真实WM/actor/critic/discriminator与四个优化器更新、保存/CLI恢复；
   实际checkpoint核实robot=a1、plane任务、来源、最终AMP权重、数据split/SHA256和有限性。
   模型、报告、原始日志和视频保留；实现与本阶段最终证据提交后才进入G1。

## 预算与当前状态

没有用户指定的硬时间/费用上限。先32环境真实更新/恢复和短评估，再实测并行数、
吞吐与显存，增加环境数有效时尽量利用4090D；不因短跑或吞吐好而宣称学习成功。
无效实验及时停止。当前进程、配置、checkpoint、指标和下一条命令始终见STATUS.md。

## 正式训练前的配置决定（2026-11-04）

8k/16k/32k实测的稳定真实转移吞吐约3.46万/6.22万/11.04万每秒；
32k显存峰值20258MiB、GPU峰值97%，未缩减学习批次或回放。证据
`logs/amp_a1/performance_summary.json`。原32k在critic预热时保留了不使用的actor图而OOM；
只在不更新actor的滚动中关闭梯度后，完整100次四网络更新与保存通过，CPU43项通过。

正式首轮采用32768env/collect1/buffer128，WM4096×4/window8/hidden512×3，
imag8192/H32，AMP2048×2/weight.5/ramp1000/参考重置.5；
actor_lr_scale=.15，WM预热300、critic预热200、actor渐进500，FP32 highest/compile。
从已验收Manager actor/WM明确跨机器人热启动，其余网络/优化器新建；
保存独立A1 model_0，先到1000迭代完整评估，再按原锁定标准推进。
性能实验模型不作为正式训练来源，以上配置决定不改变验收阈值。
