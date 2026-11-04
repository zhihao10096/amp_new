# 新隐式PD的G1无AMP基础速度训练

## 假设与范围

旧DC冷启动9000能够移动但碎步，不能将它的世界模型导入新隐式PD。当前隐式PD/state84/上游16项任务奖励下，独立无AMP冷启动尚未正式验证。先关闭AMP、D和RSI，保持任务/控制/采样和SuperMimic，不增加奖励或更换执行器。该实验同时移除了AMP奖励和参考重置，因此与旧AMP比较不能把所有差异归咎D。

源码内核407b091，当前HEAD4d5462f（文档提交）。当前运行目录 `logs/supermimic/2026-11-04_14-43-09_759735_g1_implicit_velocity_cold_r1`，完整配置同目录config.json。18432env、WM4096×4/window8、imag8192/H32、critic3×4、actor_lr_scale.15、WM300/critic200/actor ramp500、FP32 highest/编译；seed0全新随机来源，没有任何旧模型或性能模型导入。固定vx0–1.2/vy±.3/yaw±.8、10%站立，上游16项任务奖励固定，未启用奖励/速度范围课程。

## 容量与更新验证

完整actor反传profiling18432env约59320真实转移/s、峰23170MiB，按余量跳过20480；不是20480 OOM证据。1000轮训练正常结束并保存model0/500/1000，actor/critic/WM更新500/8400/4000，三网络和优化器有限性、实际变化、随机来源审计通过：`logs/amp_g1/implicit_velocity_r1_update_audit.json`。优化过程正常不等于学会行走。

## 1000步态检查

七指令20s×8env、seed42，普通reset/关闭噪声；原生或height<.5/tilt>60越界均累计。falls可对连续越界重复累计，不能解读为独立摔倒回合数。

| 指令 | vx RMSE | 严格fall/越界采样 | 每足步频 Hz | 平均腾空 s | 平均高度 m |
|---|---:|---:|---:|---:|---:|
| stand | 1.2244 | 600 | 0.0260 | 0.0300 | 0.6578 |
| slow | 1.2483 | 605 | 0.0527 | 0.0275 | 0.6550 |
| forward | 1.3703 | 593 | 0.0441 | 0.0321 | 0.6641 |
| fast | 1.4443 | 600 | 0.0331 | 0.0300 | 0.6551 |
| left | 1.2217 | 600 | 0.0468 | 0.0293 | 0.6555 |
| right | 1.2190 | 604 | 0.0267 | 0.0387 | 0.6531 |
| turn | 1.4241 | 596 | 0.2767 | 0.0585 | 0.6568 |

1000未形成稳定行走，不满足预设诊断AMP入口；不能根据少量触地事件称学会迈步。报告 `logs/amp_g1/implicit_velocity_r1_gait0_1000.json`。完整速度评估由原队列继续，未完成前不填造指标。

## 下一阶段

1000总迭代只有500次actor更新，因此先保持同配置、三网/三优化器/计数 `--resume --continue-run` 到3000，保存2000/3000并分别运行完整七指令步态与12固定+3随机速度；不重置预热或从头开同配置，不接AMP、不叠加奖励改动。如果3000仍不移动，再单独验证Go2式奖励渐进；不能用当前profile忽略的schedule参数冒充已启用课程。衔接AMP的预设入口和最终G1验收保持PLAN/G1_CONVERGENCE。

原队列 `logs/amp_g1/implicit_velocity_r1.pipeline.json`；续训脚本已准备但需原评估complete/PID退出后才启动 `logs/amp_g1/implicit_velocity_extension_r1.pipeline.py`。恢复先读取STATUS，禁止重复启动。

核实时间：2026-11-04T14:50:25+08:00。

## 1000完整速度结果与续训

12固定+3随机、30s/96env完成：物理步态失败22项、速度失败30项。固定整体RMSE(vx/vy/yaw)=[1.3285375833511353, 0.33740633726119995, 0.5387760996818542]；三随机vx RMSE为1.3126, 1.2944, 1.3300。均未通过，严格fall仍非0。完整判断 `logs/amp_g1/implicit_velocity_r1_assessment1000.json`，速度 `logs/amp_g1/implicit_velocity_r1_velocity1000.json`。

2026-11-04T14:52:43+08:00：原队列complete且实际PID全部退出，已启动同谱系1000→3000续训driver3020615；状态 `logs/amp_g1/implicit_velocity_extension_r1.pipeline.json`，完整命令/目录/PID与日志以该文件为准，不重复启动。没有修改生产源码或训练配置，不接入AMP。
