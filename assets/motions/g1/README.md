# G1 walk 参考动作

原样复制自 https://github.com/zitongbai/legged_lab ，commit `f33a18904e5209d9aceb95ef78ed82412c5f2072`，源目录 `source/legged_lab/legged_lab/data/MotionData/g1_29dof/amp/walk_and_run/`。仅使用manifest列出的七份 `Walk_B*.pkl`，不使用任何Run/C系列或走跑转换。项目默认从此处加载，不依赖reference目录。

来源README声明MIT（快照UPSTREAM_README.md）；该commit未含独立LICENSE文本，运动文件也未单独声明原始动作授权，故如实保留此状态，不把项目MIT自动套用于第三方运动。参考项目推荐GMR重定向；文件自身没有进一步原始动作来源元数据。

文件SHA256、帧数、dt、权重、四元数WXYZ、Lab关节/关键体顺序见manifest.json及retarget_g1_29dof.yaml。每条动作前80%训练/参考重置、后20%独立时间留出；速度在各split内部差分，采样和插值不跨split/clip/loop。pkl是本项目纳入Git的可信来源文件，加载前核对manifest SHA256。
