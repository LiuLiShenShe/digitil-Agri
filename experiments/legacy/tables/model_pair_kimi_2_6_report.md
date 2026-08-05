# 主实验结果

- 模型：`Pro/moonshotai/Kimi-K2.6`
- 运行模式：v2 公平基线均使用同一 schema、对象本体、规则和资产知识；Ours 使用本地 `/sceneApi/semantic/build/plan` 执行工具化闭环。
- 密钥处理：脚本只在内存中读取 API key，不写入结果文件。

| 方法 | Object-F1 | Relation-F1 | Binding-F1 | VR↓ | TFC | ETF |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Direct-LLM + Schema | 0.851 | 0.749 | 0.597 | 0.026 | 0.033 | 0.000 |
| Ours KAFarmTwin | 0.680 | 0.804 | 0.794 | 0.000 | 1.000 | 1.000 |

图文件：`experiments/analysis/model_pair_kimi_2_6_structure_reliability.png` 和 `experiments/analysis/model_pair_kimi_2_6_structure_reliability.pdf`。
