# 主实验结果

- 模型：`Pro/zai-org/GLM-5.1`
- 运行模式：v2 公平基线均使用同一 schema、对象本体、规则和资产知识；Ours 使用本地 `/sceneApi/semantic/build/plan` 执行工具化闭环。
- 密钥处理：脚本只在内存中读取 API key，不写入结果文件。

| 方法 | Object-F1 | Relation-F1 | Binding-F1 | VR↓ | TFC | ETF |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Direct-LLM + Schema | 0.751 | 0.537 | 0.551 | 0.065 | 0.000 | 0.000 |
| Ours KAFarmTwin | 0.661 | 0.805 | 0.761 | 0.007 | 1.000 | 1.000 |

图文件：`experiments/analysis/model_pair_glm_5_1_structure_reliability.png` 和 `experiments/analysis/model_pair_glm_5_1_structure_reliability.pdf`。
