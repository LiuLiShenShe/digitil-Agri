# 主实验结果

- 模型：`deepseek-v4-flash`
- 运行模式：Direct-LLM、Single-Agent、RAG-Agent、Multi-Agent 使用 DeepSeek 结构化 JSON；Ours 使用本地 `/sceneApi/semantic/build/plan`。
- 密钥处理：脚本只在内存中读取 API key，不写入结果文件。

| 方法 | SR | OC | RA | BA | VR↓ | MR↓ | TC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Direct-LLM | 1.000 | 0.600 | 0.352 | 0.296 | 0.100 | 0.000 | 1.000 |
| Single-Agent | 1.000 | 0.629 | 0.372 | 0.316 | 0.150 | 0.000 | 0.787 |
| RAG-Agent | 0.933 | 0.620 | 0.352 | 0.320 | 0.014 | 0.000 | 0.667 |
| Multi-Agent | 1.000 | 0.634 | 0.358 | 0.317 | 0.250 | 0.000 | 1.000 |
| Ours | 0.967 | 0.524 | 0.815 | 0.654 | 0.007 | 0.033 | 1.000 |

图文件：`experiments/analysis/main_experiment_bar.png` 和 `experiments/analysis/main_experiment_bar.pdf`。
