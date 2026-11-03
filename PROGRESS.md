# 进度与恢复入口

恢复先读STATUS/GOAL/PLAN并核实HEAD、进程、GPU与产物；全程禁PPO。

- Manager随机来源7000/8000/9000完整速度/步态及最终加噪/录像/实际模型审计通过，完成提交b1f59eb；模型checkpoints/go2_manager_converged.pt，无需重训。
- A1原生Manager/运动库/参考重置/相邻帧LSGAN/可微想象奖励/四网络优化器更新及保存恢复完成；四份动作与来源/许可/SHA256已纳入assets/motions/a1，提交52b35b6。CPU43项和真实GPU/编译梯度一致通过。
- A1接触正则、USD/URDF几何差异、零权重日志、编译夹具重采样均已修复。32k critic预热OOM根因是无actor更新仍保留完整想象图；关闭对应梯度后不减batch，约11万真实转移/s、峰值20GB，训练就绪提交a909cd2。
- 正式A1由已验收Manager actor/WM明确跨机器人热启动，critic/D/四优化器新建并保存model_0。1000/2000/3000三个检查点全部通过锁定的完整速度/步态/独立留出风格，最终3000加噪及实际来源/四网络四优化器更新审计通过，全部零摔倒。证据logs/amp_a1/convergence_report.json。
- 3000固定总体RMSE=.04982/.05242/.03852，随机约.045/.035/.026，加噪=.05178/.05494/.05499。1/1.5m/s风格距=.47081/.63290，相对初始改善36.3%/40.7%。各步态指标见AMP_CONVERGENCE.md。
- 三段站立/正常走/快走10秒录像生成并人工查看2秒连续步态及6–9秒后段，未见明显异常。证据logs/amp_a1/visual_review.json；模型已归档checkpoints/a1_amp_converged.pt并核对SHA256，已单独提交37b6b58。A1训练/验收/录像进程已全部退出，GPU空闲，禁止重复启动。
- G1所用参考动作同样必须复制进项目Git管理的assets/motions/g1等目录，随代码提交来源commit/许可/SHA256/划分，默认读取项目内副本，GOAL/PLAN已明确。G1预查默认flat包含run/转换，后续显式walk白名单/plane；29DOF、四元数及速度待原生GPU验证，尚无G1实验。

下一步：实现G1平地walk；先数据/资产与许可证核对、原生状态和AMP接口设计，正式训练前锁定独立验收标准。详细配置、进程、产物和下一条命令见STATUS。历史过程见docs/history/；仅保留日志路径与结论。

- 阶段切换交接：A1结果提交37b6b58；G1只读核对确认pkl可pickle读取、四元数WXYZ、29维关节为Lab顺序，参考实现面向Lab v3而本机为2.1，后续须原生验证。未启动新实验；当前任务的数据入库要求已在PLAN第7阶段和GOAL同步明确。恢复commit使用标签a1-amp-handoff-20261104核实。
