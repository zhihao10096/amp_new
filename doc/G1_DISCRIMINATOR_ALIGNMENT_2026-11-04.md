# G1判别器组件对齐与当前冷启动

## 问题与决定

新隐式PD/state84随机AMP3000只站立，D对动态/冻结参考的区分弱。先对照固定上游legged_lab f33a189，发现现有D512/256 LeakyReLU、专家+策略联合统计、clip10和统一weight decay，偏离上游1024/512 ELU、仅策略统计、epsilon .01、无clip、1e8冻结、优化后更新统计和独立输出层decay .1。此偏差是待验候选，不能先认定根因。

新增独立 `legged_lab_v1` profile，G1新CLI训练默认选取，上游隐藏层默认1024/512；旧模型缺profile时按legacy加载，A1保持原行为。新旧profile不能直接resume。奖励混合、PD/命令/RSI/参考动作不随此改动调整；本轮不执行AMP权重网格。正常梯度经冻结D输入流入想象状态，保留SuperMimic路线，不运行上游策略算法。

## 验证

- 全工作树CPU95项通过，其中含既有未跟踪exploration的2项；本次提交的测试不包含这些探索文件。日志 `logs/amp_g1/discriminator_alignment_cpu.log`。
- 固定上游D和RSL-RL v5.4.1 normalization源码独立CPU oracle，两帧/四帧各4步：loss最大误差1.19e-7、梯度3.87e-7、参数3.73e-9、归一化9.54e-7；风格奖励一致。代码/结果/上游URL和SHA256见 `logs/amp_g1/discriminator_alignment_oracle.py/.json` 及 `discriminator_alignment_github.json`。
- 原生GPU物理/终止/reset/命令/编译回报与actor梯度通过，结果 `logs/amp_g1/discriminator_alignment_integration.json`。
- 同隐式PD速度8轮→新D AMP20轮→CLI恢复25轮：actor/critic/WM/D更新16/36/20/3→21/46/25/4；warm-start精确继承actor/WM、重建4优化器，恢复profile/归一化count及输出decay通过。旧profile加载、A1 GPU回归通过。完整审计 `logs/amp_g1/discriminator_alignment_validation.audit.json`，命令/PID/配置和模型路径见同前缀pipeline.json。
- 首次额外gait smoke设置2s×2，无法提供style要求的128对有效转移，退出码0但日志含异常，被runner正确拒绝。保留 `.failed.json` 和失败日志；改为20s×8，仅恢复评估，训练未重跑。短跑随机模型没有步态结论。
- 七份实际G1动作Git追踪及SHA256通过，仍从assets/motions/g1加载。

## 冷启动历史纠正与下一步

旧DC/g1_walk冷启动9000和同源AMP诊断都已结束：能移动但碎步。先前“从未冷启动”的表述错误，已纠正；不能将旧WM导入新隐式PD。当前隐式PD/state84/上游16项任务奖励下，速度任务仅完成接口smoke，还缺正式无AMP基础运动实验。

下一队列 `logs/amp_g1/implicit_velocity_r1.pipeline.py/.json`：关闭AMP、D和RSI，保持新PD/上游16项任务奖励/固定命令范围，先完整反传容量profiling，再另起随机1000，保存0/500/1000；0/1000七指令20s×8和1000完整速度30s/96env/3随机种子独立检查。profile模型不作训练来源，无自动AMP warm-start。此实验不评价新D收益，也不启用被当前profile忽略的奖励schedule；若仍站立，再单独检验Go2式奖励课程。最终G1三点/加噪/录像/审计及后续X1范围不变。

核实时间：2026-11-04T14:39:27+08:00。
