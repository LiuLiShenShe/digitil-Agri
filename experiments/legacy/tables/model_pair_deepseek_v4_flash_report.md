# 主实验结果

- 模型：`deepseek-ai/DeepSeek-V4-Flash`
- 运行模式：v2 公平基线均使用同一 schema、对象本体、规则和资产知识；Ours 使用本地 `/sceneApi/semantic/build/plan` 执行工具化闭环。
- 密钥处理：脚本只在内存中读取 API key，不写入结果文件。

| 方法 | Object-F1 | Relation-F1 | Binding-F1 | VR↓ | TFC | ETF |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Direct-LLM + Schema | 0.841 | 0.683 | 0.485 | 0.082 | 0.167 | 0.000 |
| Ours KAFarmTwin | 0.612 | 0.774 | 0.716 | 0.006 | 0.987 | 0.987 |

图文件：`experiments/analysis/model_pair_deepseek_v4_flash_structure_reliability.png` 和 `experiments/analysis/model_pair_deepseek_v4_flash_structure_reliability.pdf`。
