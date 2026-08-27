# 多模型泛化预注册 v2（MULTIMODEL PREREGISTRATION v2）

日期：2026-08-25（CST）｜ 状态：**PREREGISTERED_AWAITING_SMOKE_APPROVAL — 在收到 `MULTIMODEL_SMOKE_APPROVED` 前不发出任何付费请求**

本文件为 v1（`MULTIMODEL_PREREGISTRATION.md`，保留不动）的正式预注册升级版。机器可读镜像见 `model_matrix_config_v2.json`；模型目录与价格证据见 `model_catalog_snapshot.json`、`price_snapshot.json`。

## 0. 背景

DeepSeek-V4-Flash 主实验已冻结：`ext300_formal_20260825`，raw SHA-256 `b52f00c4bee3b43723689c3556300e0754a8ab9564b96341d05e88b591d40d91`（600 记录）。**不得重跑或覆盖。** 本预注册新增四个硅基流动模型家族，各运行完整 External300（300 任务 × KF/SA = 600 条），共新增 2,400 条；加冻结 DeepSeek 共 3,000 条方法—任务记录。

## 1. 冻结的模型清单（精确 ID，禁止替换/近似/改大小）

| 区块顺序（seed=20260825 预生成） | catalog ID | 档位 |
|---|---|---|
| 1 | `Pro/moonshotai/Kimi-K2.6` | Pro |
| 2 | `MiniMaxAI/MiniMax-M2.5` | 标准 |
| 3 | `Qwen/Qwen3.6-27B` | 标准 |
| 4 | `zai-org/GLM-5.2` | 标准 |

- 四个 ID 已于 2026-08-25 经非计费 `GET /v1/models` 核对存在（见 catalog snapshot）。
- **任一精确 ID 运行时不可用 → 立即停止并报告，禁止自动替换。**
- API：`https://api.siliconflow.cn/v1`（OpenAI 兼容 `/chat/completions`）。
- 结论只能表述**跨模型家族泛化**；五模型均经同一硅基流动接口，**不得宣称跨 provider 泛化**。
- API key 只经环境变量/`.env` 读入内存；绝不打印、写入代码、配置、日志、manifest 或报告。

## 2. 冻结的任务集、顺序与配对

- public inputs：`external300_public_inputs.jsonl`，SHA-256 `0ede96ecb3c7e49c33e591c9d21c729db287dd5bd17148e7ca2d815f72d0e3d7`；
- gold：`external300_gold_draft.jsonl`，SHA-256 `a07964f6d3cc03f2561d51a9d097596ad52fd3345cde2e0ef317001c87c88891`；
- 任务顺序与任务内 KF/SA 配对顺序：复用冻结 `order_table_v1.json`（文件 SHA-256 `fceca2f6818c117327c12baf2d569fe49072ab0d8fc61cb2d7f30da6267bfa39`，内嵌 self-SHA `1e36c935…2650`；150 KF 先 / 150 SA 先），所有模型区块使用同一 schedule；
- 不修改任务、gold、public prompt、evaluator、阈值、方法预算与评分口径。

## 3. 冻结的生成参数与预算

- `temperature=0.2`；每调用 `max_tokens=1200`；
- 预算同冻结主实验：30 LLM 调用 / 100 工具调用 / 3 修复轮 / 单任务超时 300s / 请求超时 180s / max_tokens 预算 500k；
- 同一模型上 KF 与 SA 使用**逐字节相同**的模型级参数；
- thinking/reasoning 类专有开关策略：先查硅基流动当前文档——该模型有公开 OpenAI 兼容字段则在 smoke 前把实际值写入附录并冻结；无则使用 provider default 并记录；**禁止为提高某模型成绩单独调参**。冻结 DeepSeek 运行曾用顶层 `enable_thinking=false`（网关行为，见 harness/llm.py 注释），该开关对新模型的可用性不做假设。

## 4. 冻结的代码指纹（SHA-256，完整值见 model_matrix_config_v2.json）

runner `run_external300.py`、`harness/llm.py`、`harness/budget.py`、`harness/semantic_compiler.py`、KF 方法 `kafarmtwin_typed_repair.py`、SA 方法 `single_agent.py`、全部 evaluator 与注入每次调用的 `ONTOLOGY_NOTE` 提示词文本哈希，均在 config v2 中固化。执行前重算比对，不一致即停止。

## 5. 执行政策

- 每模型 600 条唯一记录，每 task×method 一次逻辑执行；
- 技术失败仅 retries=2 指数退避（429/5xx/超时同路径）；逻辑失败绝不重试；耗尽记 `technical_failure=true` 零分保留；
- 断点续跑依 ledger 跳过已完成且哈希一致的 (task_id, method) 对，成功记录绝不重复采样；
- 运行期只看完成数/错误数/费用/技术状态，**封存前不看 CVSR 等性能指标**；
- **禁止按性能中止或选择性重跑**；费用不足只能在下一模型区块开始前暂停并将整个研究标 `INCOMPLETE`；
- 每模型完成即：关闭 raw 写入 → 计算 SHA-256 → seal → manifest → 离线评分；
- 无论结果好坏全部记录保留并报告；四模型未齐不得写"五模型泛化成立"。

## 6. 统计与泛化判定（预注册）

每模型分别报告 CVSR、pass@5、Object/Relation/Binding-F1、Critical Recall、Fatal rate、Evidence Precision、Replay、token/人民币成本/延迟 p50/p95、KF−SA 配对差、10,000 次 task-level paired bootstrap 95% CI、McNemar exact、五类分层结果与技术失败数。

跨模型汇总：300 个任务是重复使用的同一批，**不得当 1,500 个独立样本**；聚合用按 task_id 聚类的 cluster bootstrap（保留全部模型结果）或明确标注探索性。

判定（预注册，事后不得更换主要指标；Fatal/Binding-F1/成本作为独立结果报告）：

- `MODEL_GENERALIZATION_PASS`：四新模型 KF−SA CVSR 差值均 >0，且 ≥3 个模型 95% CI 下界 >0；
- `MODEL_GENERALIZATION_PARTIAL`：≥3 个新模型差值 >0 但不满足 PASS；
- `MODEL_GENERALIZATION_FAIL`：≥2 个新模型差值 ≤0。

PASS/PARTIAL/FAIL 无论哪种都完整保存并报告。禁 SOTA、第三方排行榜成绩、private held-out 表述。

## 7. Smoke 测试计划（先于正式运行，需单独授权）

门槛：用户明确回复 `MULTIMODEL_SMOKE_APPROVED`。规模上限 16 次方法运行 = 4 模型 × 2 个 DEV fixture 任务（明确标记 DEV 且不属于 External300，覆盖结构化输出与修复路径）× KF/SA。核验项：HTTP 兼容、结构化输出解析、content/reasoning_content/tool_calls、usage 字段、finish_reason、超时限流、返回 model id、缓存字段、单次成本。结果不入论文主结果、不用于调正式提示词。只允许修模型无关的 harness 兼容性问题，每个修复须补测试并披露。Smoke 后重算正式费用并再次停止，等待：

```
MULTIMODEL_RUN_APPROVED MAX_TOTAL_CNY=<人民币上限>
```

未获授权或上限不足时不得开始正式运行。

## 8. 冻结基线对照（token 分布，来自 sealed raw 重算）

KF 总 token 668,769（514 次 LLM 调用）；SA 总 token 472,722（388 次）。分类型分布见 PREFLIGHT_REPORT_v2.md。**拆分可得性披露**：冻结 raw 仅存 total tokens，prompt/completion/reasoning/cached 拆分未落盘（全文扫描 0 命中）；费用估算因此以区间给出（乐观全输入价 → 保守 2:1 输入输出比），smoke 实测 usage 形状后可收窄。
