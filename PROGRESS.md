# 进度与恢复入口

恢复先读GOAL/PLAN/STATUS，再核实HEAD、pipeline和实际进程/GPU；动态覆盖队列已complete，不重复启动。

- 总目标保持：Manager/A1已独立成功 → G1平地walk → X1下半身12DOF AMP；全程禁PPO、WM可微想象，各阶段独立验收提交。G1/X1未成功前总目标未完成。
- G1资产/AMP/原生Manager/真实想象/编译/四网更新恢复通过，CPU50项、A1回归通过。动作七份Walk_B已复制assets/motions/g1并Git管理，新增/替换也须归档提交，哈希复核通过。
- R1/R2/R3全部三点失败。R3仅OU .3→.6，仍0.6m/s步频0；1000/2000/3000固定RMSE(.963,.299,.410)/(.649,.192,.438)/(.630,.240,.390)，摔倒1460/2/63；3000风格改善59.2%/59.0%不能代替行走。R3训练/评估全退出，formal_r3_summary.json；不再盲目加OU或同配置续训。
- 骨架/映射/原动作几何一致；原型与PhysX足端位置max6e-6m，直接FK修正WM足端误差收益很小，暂不改模型结构。kinematics_r3.json。普通复制状态有限差分受接触噪声干扰，不能当梯度错误证据。
- 冻结WM参考MPC存活.779→1.442s、单支撑20.9%→56%，但2s仍16/16全摔，动态一步速度误差.0984m/s；reference_mpc_r3.json；由此开展的动态覆盖验证已完成，结果见下项。
- 动态覆盖诊断已结束：四任务返回码0，pipeline为complete/active_pid=null；2026-11-03T21:35:36+00:00核实原driver/child均退出、GPU无计算进程。日志及完整命令见logs/amp_g1/dynamic_coverage_r3.pipeline.json。
- 补充动态数据后8步留出速度RMSE .29988→.14465（改善51.76%）；同32独立初态MPC存活1.2669→.9331s，两组仍32/32全摔。fit.json及control_baseline/control_refit.json证据位于logs/amp_g1，前缀dynamic_coverage_r3。预测改善未转化控制收益，暂不把MPC或诊断WM接入正式采样，无新正式训练或已收敛G1模型。
- 已明确GOAL/PLAN：所有实际G1动作（含新增/替换）复制assets/motions/g1，文件本体及清单均纳入Git，训练前/提交前核验来源/许可/SHA256/split/默认路径。本次七份动作及两份来源文档逐文件匹配manifest和HEAD，默认路径已复核；证据logs/amp_g1/g1_motion_tracking_recheck_current.json。
- 本次复核起点b44f9e0；本次仅更新目标/计划/恢复文档，当前版本用git rev-parse HEAD核实。正式R3源9bc7115，训练实现仍754e1fd。原未跟踪文件保留。
- Manager/A1勿重训。X1待G1独立成功提交后实施：动作复制后.gitignore忽略、清单Git管理，部署参考reference/AMP，跳过RKNN。

下一步：`sed -n '1,240p' logs/amp_g1/g1_reference_mpc_diagnostic.py`，先核查控制目标/action映射与想象优化，结合已完成成对控制报告提出可验证假设后再设计实验。G1验收标准不变，不以动力学误差下降替代行走。
