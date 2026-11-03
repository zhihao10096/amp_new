# A1 AMP 参考动作

当前A1平地行走实际使用的四份动作以原始字节复制并由本项目Git管理，
默认训练/评估读取此目录，无需未跟踪的reference目录。

来源：[fan-ziqi/rl_amp](https://github.com/fan-ziqi/rl_amp)，
commit `b4666fa99066ac5c8006b700bf7cc6bc2471232b`，目录`datasets/mocap_motions_a1/`。
该项目参考[AMP_for_hardware](https://github.com/Alescontrela/AMP_for_hardware)；
原始关键点来自[AI4Animation](https://github.com/sebastianstarke/AI4Animation)。
四份txt未修改；运行时统一使用原生Isaac Lab A1 FK重算足端。

| 文件 | 帧数 | 原始帧间隔 | 来源关键点 |
| --- | ---: | ---: | --- |
| trot1.txt | 147 | 0.01677秒 | dog_walk03 |
| pace1.txt | 199 | 0.01677秒 | dog_walk00 |
| left_turn1.txt | 100 | 0.01677秒 | dog_walk09 |
| right_turn1.txt | 110 | 0.01677秒 | dog_walk09 |

数据来源的许可声明为CC BY-NC 4.0，原文保存在[LICENSE.ai4animation](LICENSE.ai4animation)；
rl_amp仓库的Apache 2.0许可原文保存在[LICENSE.rl_amp](LICENSE.rl_amp)。
本项目代码的MIT许可不替代上述动作数据的许可。

[manifest.json](manifest.json)记录来源commit、各文件SHA256、帧数、dt与采样权重。
训练使用每条动作前80%，后20%为独立时间留出；采样间隔为控制dt=.02秒，
插值支撑点和相邻状态对均不得跨越训练/留出边界或clip/loop边界。
不包含canter、trot2或run数据。完整任务和验收见[AMP_CONVERGENCE.md](../../../AMP_CONVERGENCE.md)。
