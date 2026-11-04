# G1速度冷启动：历史与当前阶段

本记录修正上一轮将历史与当前动力学混淆的结论。核实时间：2026-11-04T14:28:59+08:00。

## 已完成的旧冷启动

`logs/supermimic/2026-11-04_08-00-37_784295_g1_velocity_cold_start18432_to9000/model_9000.pt` 来自G1随机初始化的3000→5000→9000速度冷启动。采用历史DC执行器、旧状态和g1_walk奖励，经历弱初期正则→最终步态课程。5000/9000可以移动但有高频低抬脚；从9000进行无AMP/61/64/70维与四帧对照也未通过。证据：`docs/experiments/G1_AMP_WARM9000_COMPARISON_2026-11-04.md`、`logs/amp_g1/g1_velocity_cold_start_4000_5000_assessment.json`及各同源对照JSON。不能将这部分工作写成尚未进行。

用户现已禁止DC；旧9000不能作为当前隐式PD世界模型来源。拒绝恢复旧WM的实际验证保存在 `logs/amp_g1/implicit_pd_validation.audit.json`。

## 当前尚缺的实验

隐式PD/state84/上游16项奖励下，G1速度任务只有8轮接口smoke：`logs/supermimic/2026-11-04_12-31-58_139599_g1_rsi_alignment_velocity_smoke`。新PD随机AMP3000只站立，不能据此认为当前无AMP基础速度任务已经失败。

先在当前动力学从新随机model_0运行G1-Velocity-Flat，关闭AMP、判别器和RSI，固定上游16项奖励及命令范围，1000轮后做0/1000独立速度与步态检查。保持SuperMimic及禁PPO、平地、walk范围。当前profile不使用Go2奖励渐进；命令范围也不扩张。WM/critic预热与actor ramp属于优化时序，不能称为已启用奖励/速度范围课程。

## 后续判断

无AMP基础运动成功后，继承同机器人actor/WM，重建critic/D/优化器，再独立验收AMP。若仍站立，优先检验新的基础速度→最终奖励课程，保留旧Go2/旧G1成功移动证据，分开诊断，不做AMP权重网格。最终G1三点、加噪、录像、审计不变；G1成功后才进入X1。

## 本轮验证入口

CPU `logs/amp_g1/discriminator_alignment_cpu.log`；新D GPU验证及新PD冷启动状态将写入STATUS。新D不参与无AMP冷启动，其效果不能由该训练推断。
