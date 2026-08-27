# MULTIMODEL SMOKE REPORT v2（第六节执行记录）

日期：2026-08-25（CST）｜ 授权：用户回复"同意"，记为 `MULTIMODEL_SMOKE_APPROVED`（2026-08-25）
规模：4 模型 × 2 DEV 任务（DEV-XX-001 scene 结构化输出、DEV-XX-003 rule_repair 修复路径）× KF/SA = **16 次方法运行**
数据：`tests/fixtures/external300_dev_fixture/`（status=DEV_FIXTURE_NOT_A_BENCHMARK，不属于 External300）
结果文件：`smoke_results_v2.json`｜**不入论文主结果，不用于调正式提示词**

## 1. 兼容性核验结果（逐项）

| 核验项 | Kimi-K2.6 | MiniMax-M2.5 | Qwen3.6-27B | GLM-5.2 |
|---|---|---|---|---|
| HTTP 兼容（7 请求全 200） | ✅ | ✅ | ✅ | ✅ |
| usage 字段 | ✅ | ✅ | ✅ | ✅ |
| content 解析/结构化输出 | ✅（nodes=4） | ✅（nodes=8） | ✅（nodes=4-6） | ✅（nodes=4） |
| finish_reason | stop | stop | stop | stop |
| 返回 model id 与请求一致 | ✅ 精确 ID 原样返回 | ✅ | ✅ | ✅ |
| 缓存字段 | ✅ cached=1984 | 无缓存命中 | 0 | 0 |
| reasoning_content | 无 | **有（reasoning_tokens=5208）** | 无 | 无 |
| tool_calls 路径 | 经 proxy 正常 | 正常 | 正常 | 正常 |
| 技术失败 | 0 | 0 | 0 | 0 |

- **harness 兼容修复：无需要**。现有 `llm.py`（OpenAI 公共字段）对四模型全部开箱即用。
- thinking 开关观测：payload 中的顶层 `enable_thinking=false` 被四模型全部接受（无 400），但 MiniMax-M2.5 仍输出 reasoning_content——该模型走 provider default（开关无效或语义不同）。按预注册 §3 记录为 provider default，不为任何模型单独调参；同一模型 KF/SA 参数保持逐字节相同。
- 实测单次成本（价格快照计价）：Kimi ¥0.072、MiniMax ¥0.065、Qwen ¥0.047、GLM ¥0.076，smoke 合计 **≈¥0.26**。

## 2. 按 smoke 实测比例重算正式实验费用

实测 output 占比：Kimi 18.6%、MiniMax 53.2%（推理 token 计入输出）、Qwen 21.1%、GLM 15.7%。
Token 量基线仍用 DeepSeek 冻结区块 1,141,491 tokens（新模型用量未知，安全系数兜底）：

| 模型 | 期望（实测配比） | 安全 ×1.5 |
|---|---:|---:|
| Kimi-K2.6 (Pro) | ≈¥11.8 | ¥17.7 |
| MiniMax-M2.5 | ≈¥6.2 | ¥9.3 |
| Qwen3.6-27B | ≈¥7.0 | ¥10.6 |
| GLM-5.2 | ≈¥12.7 | ¥19.1 |
| **四模型合计** | **≈¥37.7 ($5.59)** | **≈¥56.7 ($8.41)** |

区间对照（预注册时的盲估）：期望 ¥246 / 安全 ¥369 —— 实测后收窄至约 1/6~1/6.5，主要因除 MiniMax 外各模型输出占比 <21%。风险提示：正式任务 prompt 远长于 DEV fixture，输入占比可能进一步升高（费用更低方向）；MiniMax 的推理 token 是最大不确定性（其延迟也显著更高：KF 单 run 79.5s vs 其他 12-50s）。原建议 `MAX_TOTAL_CNY=500` 维持不变即可覆盖。

## 3. Smoke 结论

四个精确 ID 全部兼容、可用、可解析、可计量。**满足进入正式运行的条件**。

等待授权字符串：`MULTIMODEL_RUN_APPROVED MAX_TOTAL_CNY=<人民币上限>`
