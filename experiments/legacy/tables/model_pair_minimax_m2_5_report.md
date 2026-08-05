# 主实验结果

- 模型：`MiniMaxAI/MiniMax-M2.5`
- 运行模式：v2 公平基线均使用同一 schema、对象本体、规则和资产知识；Ours 使用本地 `/sceneApi/semantic/build/plan` 执行工具化闭环。
- 密钥处理：脚本只在内存中读取 API key，不写入结果文件。

| 方法 | Object-F1 | Relation-F1 | Binding-F1 | VR↓ | TFC | ETF |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Direct-LLM + Schema | 0.870 | 0.765 | 0.606 | 0.025 | 0.000 | 0.000 |
| Ours KAFarmTwin | 0.670 | 0.819 | 0.741 | 0.007 | 0.993 | 0.993 |

图文件：`experiments/analysis/model_pair_minimax_m2_5_structure_reliability.png` 和 `experiments/analysis/model_pair_minimax_m2_5_structure_reliability.pdf`。
