# G1 AMP 足端特征单变量诊断（2026-11-04）

## 假设与范围

已有64维根线速度特征未消除碎步。本次只增加左右踝roll link原点相对骨盆的6维位置，形成`g1_amp_70_feet_v1`；原64维顺序保持为前缀，世界模型状态、奖励、两帧AMP历史、参考split和重置条件均不变。足端位置包含相对骨盆的z，**不是**世界绝对足高或地面净空；不声称它增加了关节角之外的独立物理信息，而是检验显式几何表达能否改善D与actor的学习。

专家、PhysX和想象均从绝对关节角通过同一USD FK计算。该特征不读取WM独立预测的足端位置通道；不改该通道的训练或现有步态奖励。FK脚点为left/right_ankle_roll_link原点、坐标pelvis、米；geometry schema及physics USD SHA256写入checkpoint metadata。61/64维旧metadata保持原样。

GitHub核对MimicKit关键体位置观测，证据logs/amp_g1/github_amp_feet_features_2026-11-04.json；不移植其策略算法。

## 编译问题与验证

初次四元数FK的常量轴张量索引/广播在PyTorch2.5.1 Inductor中生成无效Triton `broadcast_to(constexpr,...)`，原生测试及smoke虽返回0，却无passed报告和最终checkpoint。该次结果失败，日志保留`feet70_integration.log`、`feet70_smoke_initial.log`与`feet70_validation.pipeline.json`。

FK改写为旋转基向量及Python标量几何常量，不改变几何约定，未关闭torch.compile或梯度。相关GitHub搜索记录`github_fk_inductor_broadcast_2026-11-04.json`，不同版本Issue未当成已适配修复。

- CPU61项通过：训练参考世界足端位置、double数值梯度、batch形状、专家/状态特征、D与现有回归，`feet70_r2_cpu.log`。
- 独立CUDA fullgraph，32/8192批量最大位置误差1.79e-7m、梯度误差4.77e-7，`feet70_fk_compile_r2.json`。
- 原生/想象编译通过：65reset、13终止、52超时、356指令切换；原生足端位置max1.73e-6m，专家特征max7.15e-7，返回max1.79e-7，actor梯度max7.28e-12，`feet70_r2_integration.json`。
- 四网实际更新/CLI恢复/A1回归全部通过：actor16→21、critic36→46、WM20→25、D3→4；CLI无显式schema继承70维，61/64旧metadata和D加载精确兼容，`feet70_r2_validation.audit.json`。验证器额外检查passed报告、最终checkpoint和异常日志，不能只检查退出码。

所有日志路径均在logs/amp_g1下。GPU验证已完成；提交代码后才启动以下诊断。

## 匹配试验

从`logs/supermimic/2026-11-04_08-00-37_784295_g1_velocity_cold_start18432_to9000/model_9000.pt`继承actor/WM及归一化，重建critic/D/所有优化器，保存独立model_0。

与64维`2026-11-04_09-09-01_259556_g1_amp_warm9000_velocity64_diag/config.json`逐字段比较，仅run_name和amp_feature_schema变化：18432env，1000迭代，WM4096×4/window8、imag8192/H32、critic3×4、actor_lr_scale=.15、D2048×2/interval5/lr1e-5/GP40/weight.5/ramp1000/RSI.5，OU.6占25%，其余Gaussian.1，compile FP32 highest。

初始审计要求actor/WM等于9000来源；actor/critic/WM与64维model_0逐张量一致，优化器状态均为空。七份实际动作已在项目Git目录中；启动前逐份核对Git追踪及SHA256，不新增参考数据。

保存model_0/1000并做相同七指令20秒×8环境seed42的普通站立reset步态及独立留出风格评估。只根据真实步频、摆动、净空、足滑、速度和稳定性决定是否延长；不同维度schema不直接比较绝对风格距离。本实验是诊断，不能替代正式完整速度、连续三点、加噪、录像和审计。

实现已提交e835835；1000轮训练及model_0/1000独立七指令评估已于09:56全部完成，pipeline stage=complete；原driver2802496/训练2802600/评估2807823均退出，09:57实测GPU无计算进程。目录`logs/supermimic/2026-11-04_09-49-14_815830_g1_amp_warm9000_feet70_diag`。model_0与9000来源actor/WM及64维初始actor/critic/WM逐张量匹配，四优化器初始状态为空，证据`g1_amp_warm9000_feet70_diag.initial_audit.json`；最终四网/优化器审计`g1_amp_warm9000_feet70_diag.audit.json`通过，更新计数actor500/critic8400/WM4000/D280。峰值显存23404MiB、观测GPU峰值92%。

## 最终独立评估与结论

七指令×8env×20s、seed42，model_1000全部零摔倒；这是短程诊断，未执行正式完整速度/连续三点/加噪/录像。

| 指令vx | 实际vx m/s | 每足步频 Hz | 腾空 s | 摆动离地 mm | 接触足滑 m/s |
|---|---:|---:|---:|---:|---:|
| .6 | .5932 | 3.533 | .0815 | 7.13 | .1072 |
| 1.0 | 1.0199 | 3.800 | .0913 | 14.18 | .2087 |

70维自身留出风格距forward 6.58430→5.00757（改善23.95%）、fast 9.56222→7.74379（19.02%）；不能与其他schema绝对距离直接比较。1m/s步频比64维4.350Hz下降，但仍高于2.5Hz，摆动不足.15s、离地不足15mm、快走足滑超过.20m/s；左侧移从初始vy=.2801退化至.1074（指令.3）。因此编译/实现问题已修复，步态问题仍未解决，现有结果不足以支持原配置盲目延长。

原始报告`logs/amp_g1/g1_amp_warm9000_feet70_diag_assessment.json`，训练/评估命令和状态`g1_amp_warm9000_feet70_diag.pipeline.json`。四臂对照见[G1_AMP_WARM9000_COMPARISON_2026-11-04.md](G1_AMP_WARM9000_COMPARISON_2026-11-04.md)；后续将历史、参考条件和辅助奖励分开消融，未启动下一实验。
