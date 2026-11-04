# G1 奖励与 legged_lab 对齐

## 问题、依据与决定

在固定上游 f33a189 的原函数审计中，确认本项目有额外全29DOF运动姿态惩罚、自定义步态项、错误的关节惩罚范围，以及AMP相对任务系数少4倍、站立style被关闭等差异。此前DC模型已在 f32755e 恢复为隐式PD；没有证据证明它就是碎步根因。用户要求优先使用上游已验证奖励，停止权重网格。

本阶段新增明确的`g1_legged_lab_walk_v1`配置：16项任务公式/权重/关节范围按上游；仅平地walk指令和项目归档数据；保留29DOF动作/83维状态。旧`g1_walk`作为历史隐式PD短跑的显式配置保留。Go2/A1行为不变，不恢复DC。

AMP最终组合为`.5*task + .5*(2*dt*style)`，无站立style门控；真实RewardManager、想象返回、真实TD目标和评估重建使用同一混合系数。训练保留已记录的AMP ramp：style混合份额从0到.5时，task份额从1到.5。新G1不再套用旧四足步态课程，以免凭空增加高度等上游没有的惩罚。

## 必要近似与尚未对齐的接口

- 83维状态不含求解器力矩/末子步加速度：真实与想象仍共用固定限矩PD估算、控制周期速度差分；oracle在相同估算输入下核对上游公式，不能声称等于PhysX实际力矩或原生末子步加速度。
- 真实接触为控制周期历史力阈值，接触计时采用共享控制周期计时器，想象使用连续接触松弛。oracle覆盖二值接触端点及公式；真实传感器和控制周期量化差异需GPU记录。
- 当前先保持原任务的高度/倾角终止标准，仍未复制上游torso/pelvis接触终止和minimum_height=.2。上游已关闭倾角终止；此为独立的后续终止接口对照，不隐去差异，不在本阶段同时扩世界模型状态。
- RSI同帧命令对齐尚未实现；旧Lab版本counter差异仍需处理。参考重置高度已有负对照，不盲目加.1m。

## 验证与后续

验证已于2026-11-04完成；`logs/amp_g1/upstream_reward_validation.pipeline.json`为complete，driver2883115与所有子进程均退出；汇总`upstream_reward_validation.audit.json`为passed（以下证据均在`logs/amp_g1/`）。

- CPU82项通过：`upstream_reward_cpu.log`，覆盖分组关节惩罚、站立门控、倾斜坐标、AMP ramp及有限梯度。
- 固定上游原方法oracle：512个float64样本、16项奖励，单项最大误差9.76e-13、任务合计1.95e-14；9组dt/混合组合通过。`upstream_reward_oracle.json`；GitHub固定commit与本地源码SHA256一致，`upstream_reward_github_evidence.json`。
- 新profile真实GPU与想象编译：32env、61维四帧，8个手臂惩罚接触体映射；65次reset/11摔倒/54超时/355次指令切换；真实TD误差4.77e-7、编译返回3.58e-7、actor梯度1.46e-11。`upstream_reward_integration.json`。这些是接口覆盖事件，不是训练行走指标。
- PD末子步估算与端点代理最大相差52.21Nm，末子步关节加速度与控制周期差分最大相差2443.33rad/s²。这些量化差异证实代理不等于原生末子步量，不能把公式oracle解释为完整原生MDP等价；未据此判断它们对学习的因果影响。
- 同隐式PD速度8轮→AMP20轮的actor/WM精确继承、四优化器重建；CLI20→25恢复后actor16→21、critic36→46、WM20→25、D3→4，四网络持续更新且有限；恢复自动继承61维四帧、reward_profile及奖励权重。`upstream_reward_validation.audit.json`。
- 历史隐式PD旧profile原生/编译以及实际旧checkpoint评估通过；A1原生GPU回归通过。`upstream_reward_legacy_integration.json`、`upstream_reward_legacy_checkpoint_gait.json`、`upstream_reward_a1_regression.json`。
- 新profile25轮随机短跑七指令829摔，留出风格距3.81350/3.80468：`upstream_reward_smoke_gait.json`。仅证明评估接口可运行，无步态改善或收敛结论。最新模型`logs/supermimic/2026-11-04_12-03-38_812189_g1_upstream_reward_smoke_resume/model_25.pt`，不是行走候选。
- 七份G1参考动作的Git跟踪与SHA256通过；旧DC模型仍被拒绝。此轮未改变数据、RSI、终止条件、WM状态或G1正式门槛。

本阶段不把源码对齐或短跑当作行走收敛。验证通过后单独提交，再处理剩余终止/RSI接口并确定新PD训练基线；不使用旧DC世界模型。全目标仍为G1成功后X1下半身12DOF，跳过RKNN，数据/部署约束见GOAL。

## 隐式PD与IdealPD的选择

用户允许Isaac Lab IdealPD；它显式计算PD并使用固定力矩上限，同样满足不用DC转速降额的要求。当前保留上游隐式PD：原生驱动与增益检查已通过，尚无其有缺陷的对照证据；世界模型学习状态转移也不要求对PhysX求导。本机Isaac Lab 2.1 `actuators/actuator_pd.py`明确说明隐式PD在较大仿真时间步通常比显式IdealPD积分更准确，这不是本任务行走收益的证明。如后续有控制问题，再用相同增益、固定限矩、时间步和数据比较IdealPD，单独标记执行器类型并从新控制数据训练世界模型，不复用DC动力学。
