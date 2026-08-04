# pair_deepseek_v4_flash_base_smoke 阻塞记录

- 模型：`deepseek-ai/DeepSeek-V4-Flash`
- 状态：至少一个方法调用失败，脚本未写入正式 `main_experiment_v2_*` 结果表。
- 处理原则：不沿用 v1 结果冒充 v2 公平基线实验。

| 任务 | 方法 | 错误 |
| --- | --- | --- |
| T01 | Direct-LLM + Schema | AttributeError: 'str' object has no attribute 'get' |
