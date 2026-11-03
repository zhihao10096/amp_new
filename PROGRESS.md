# Go2 速度跟踪与步态改进：当前进度

## 当前状态：已完成
- Isaac Lab 迁移已提交 `4ca881b`；原速度收敛验证见 `CONVERGENCE.md`，旧模型 `checkpoints/go2_velocity_converged.pt` 保留。
- 用户本轮要求参考 Unitree Go2 奖励改善小碎步，并提高并行环境数以充分使用 GPU。
- 已实现奖励、扩展世界模型/回放，完成真实 GPU 训练、步态/速度验收及前后录像；所有训练、评估、录像进程已退出。
- 最终模型 `checkpoints/go2_velocity_gait.pt`，元数据 `checkpoints/go2_velocity_gait.json`；SHA-256 `8e261f8b363be540852558c57174bfcd8d82cc28a21b7ba55d36e946c5f42ca6`，与最后微调第1500轮原文件一致。
- 对比视频 `videos/go2_gait_comparison.mp4`，左旧右新、相同(1,0,0)指令/种子42，10秒、25fps、1920×640；已抽帧检查，均零摔倒。
- 本轮修改未提交 Git；用户添加的未跟踪 `reference/` 保持原状，不纳入本项目提交。日志、模型、视频均被忽略。

## 核心实现
- 参考 `reference/unitree_rl_lab/.../go2/velocity_env_cfg.py` 及 `mdp/rewards.py`：增强动作变化/力矩/限位惩罚，增加关节速度/能耗、站立放大关节偏差、腾空/支撑时序方差、足滑和非足接触。
- 额外使用摆脚高度、站立足接触、无外部相位的摆动/支撑时长与对角配合奖励。最终足滑权重 -.3、时长 -8，其余参考/步态权重见 `velocity.py`。
- 环境和想象共用奖励/可微接触计时。模型状态34→63维（加入足端位置/速度/接触），回放另存16维计时器；actor仍225维。
- 检查点v2；v1可评估/--warm-start迁移，保留actor与原动力学子映射，重建critic/优化器。--resume保持原奖励，改奖励用--warm-start。
- 缓存CUDA指令边界，合并奖励日志GPU→CPU回读；新增真实/想象吞吐和stop-file边界保存停止。

## 验收证据
- 原模型1/1.5m/s每足步频6.04/8.71Hz，腾空.044/.035s，摆动离地.0048/.0065m，足滑.256/.418m/s；倒退主要滑行（足滑.871）。
- 最终1/1.5m/s步频 **2.63/2.75Hz**，腾空 **.141/.139s**，离地 **.0193/.0224m**，足滑 **.0889/.1347m/s**，短摆动 **1.25%/2.46%**（原99.8%/100%）。
- 7指令均零摔倒；倒退/侧移足滑.061/.045m/s。站立有少量微接触切换.214Hz，平均离地仅.0145s，低于预定.3Hz标准；未声称绝对零抬脚。
- 最后一轮1000、1500检查点均通过预先记录的全部步态标准，选最新1500。准则/数据见 `GAIT.md`、`logs/gait/gait_report.json`，图 `logs/gait/comparison.png`。
- 原速度标准完整复测：20固定指令×8环境×30s，加160环境×3种子×30s；标准/训练观测噪声各320机器人分钟，合计640分钟零摔倒，全部固定/随机/站立用例达标。
- 随机稳态RMSE：无噪(.0463,.0444,.0426)，带噪(.0509,.0468,.0552)。原始报告 `logs/gait/benchmark_final.json`、`benchmark_final_noisy.json`；判定 `benchmark_criteria.json`。
- 16项CPU测试通过；GPU集成PASS含80次reset、1次强制翻倒、80次指令切换，验证奖励/观测、计时器reset、终止next-state和固定指令。compileall/whitespace通过。

## GPU 扩容与训练
- RTX4070TiSUPER 16GB。相同检查点100轮扫描：1024/WM1024/imag1024约18.3k转移/s、5339MiB；4096/2048/4096约57.6k、9263MiB；8192/4096/8192约94k、14419MiB，约为原配置5.1倍。
- WM8192批次仅73.1k，吞吐下降，排除继续堆大batch。最终采用8192环境、WM4096×4、imag8192、horizon32、buffer256；完整新奖励长跑约75–82k转移/s，GPU均值约80%、峰值97%、显存约14GB。
- 原始扫描 `logs/gait/profile_results.json`，连续GPU采样 `refinement_gpu.csv` / `refinement_continued_gpu.csv`。
- 参考主项训练 `logs/supermimic/2026-11-03_19-26-27_435859_unitree_gait/` 第2000轮，步频降低但站立抬脚、腾空不足。
- 步态补充阶段 `2026-11-03_19-44-24_752291_gait_refinement/`，1002轮边界保存后评估；续训 `2026-11-03_19-53-53_748320_gait_refinement_continued/` 至2500轮，常用速度改善但高速air/足滑未过，未降低标准。
- 最后加重足滑/时长，热启动运行 `logs/supermimic/2026-11-03_20-07-39_561455_gait_slip_refinement/` 至1500轮，前100轮WM、再200轮critic，actor学习率缩放.15。三检查点评估 `logs/gait/slip_refinement_eval.json`。

## 已排除/修复的问题
- 仅在环境加接触奖励无法影响SuperMimic actor梯度：扩展动力学/回放并在想象中计算相同奖励。
- 本机IsaacLab2.1提供quat_rotate_inverse，参考quat_apply_inverse名称不可用：核对源码修正。
- 新可选配置字段导致旧v2原始dict与补默认值后的配置不相等：恢复时规范化后比较，回归测试实际调用Trainer.load并验证奖励不匹配仍拒绝。
- 多检查点评估的inference_mode环境缓存跨作用域reset写入失败：改no_grad；Kit关闭前打印异常以免吞错，三检查点评估验证通过。
- 已检索Unitree GitHub gait相关Issues，主要是PPO标准差/梯度爆炸，不适用于本次SuperMimic步频问题，采用参考源码并以实测迭代。
- ROS注入PYTHONPATH会污染pytest；使用 `env -u PYTHONPATH .venv/bin/python ...`，不改ROS环境。

## 后续
- 本轮授权工作已完成；无运行中训练/评估进程。复现参数、评估标准和局限见 `GAIT.md` / `README.md`。
