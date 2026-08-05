# 主实验结果

- 模型：`step-3.5-flash`
- 运行模式：v2 公平基线均使用同一 schema、对象本体、规则和资产知识；Ours 使用本地 `/sceneApi/semantic/build/plan` 执行工具化闭环。
- 密钥处理：脚本只在内存中读取 API key，不写入结果文件。

| 方法 | Object-F1 | Relation-F1 | Binding-F1 | VR↓ | TFC | ETF |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Direct-LLM + Schema | 0.814 | 0.696 | 0.554 | 0.117 | 0.067 | 0.000 |
| LLM + Ontology/Rules Prompt | 0.835 | 0.725 | 0.533 | 0.119 | 0.027 | 0.000 |
| RAG-Agent + Ontology/Rules | 0.819 | 0.745 | 0.658 | 0.077 | 0.040 | 0.000 |
| Single-Agent + Validator | 0.837 | 0.723 | 0.595 | 0.027 | 0.133 | 0.000 |
| Multi-Agent + Shared Knowledge | 0.827 | 0.727 | 0.625 | 0.053 | 0.973 | 0.000 |
| Ours KAFarmTwin | 0.711 | 0.803 | 0.775 | 0.007 | 1.000 | 1.000 |

图文件：`experiments/analysis/main_experiment_v2_structure_reliability.png` 和 `experiments/analysis/main_experiment_v2_structure_reliability.pdf`。
