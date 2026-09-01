# 05 — External300 证据模块

**Canonical source**：`experiments/v3/results/external300/External300_CANONICAL_METRICS.json`
**Seal**：`ext300_formal_20260825/SEAL.json`，raw SHA-256 = `b52f00c4bee3b43723689c3556300e0754a8ab9564b96341d05e88b591d40d91`

## 1. 任务构成

- 300 个任务，5 类各 60：`scene_construction`、`data_binding`、`asset_routing`、`rule_repair`、`memory_query`
- 与 test_v2（20 任务）不同——更大规模、更多类型均衡
- 身份：author-reviewed controlled benchmark（非独立双盲、非 gold standard）

## 2. 执行协议

- 每 task × method 单次正式执行（single execution）
- DeepSeek-V4-Flash，temperature 0.2
- 预算：30 LLM / 100 工具 / 3 修复轮 / 超时 300s
- 任务顺序与 KF/SA 配对：复用 `order_table_v1.json`（seed 20260804，150 KF 先/150 SA 先）

## 3. 主结果表

| Metric | KF | SA | Δ |
|---|---:|---:|---:|
| CVSR ↑ | 0.7167 | 0.4800 | +0.2367 |
| Object-F1 ↑ | 0.6896 | 0.6351 | +0.0545 |
| Relation-F1 ↑ | 0.6995 | 0.3790 | +0.3205 |
| Binding-F1 ↑ | 0.5939 | 0.2000 | +0.3939 |
| Critical Recall ↑ | 1.000 | 0.950 | +0.050 |
| Fatal Rate ↓ | 0.000 | 0.250 | −0.250 |
| Evidence Precision ↑ | 1.000 | 0.9467 | +0.0533 |
| Replay Success ↑ | 0.8083 | 0.4553 | +0.3530 |

## 4. 配对统计

| Test | Value |
|---|---|
| Δ (point estimate) | +0.2367 |
| 95% CI (10,000 bootstraps) | [0.1833, 0.2900] |
| McNemar b (KF wins) | 77 |
| McNemar c (SA wins) | 6 |
| McNemar p | p<10⁻⁶ (exact tail 8.45e-17) |
| Odds ratio | 12.83 |

## 5. 分类型 CVSR

| Type | KF | SA | Δ | 读数 |
|---|---:|---:|---:|---|
| rule_repair | **1.00** | 0.00 | +1.00 | KF 完全修复，SA 完全失败；D1 难度（单条 R4 违规，prompt 给出明确修复目标） |
| data_binding | 1.00 | 1.00 | 0.00 | 天花板效应 |
| memory_query | 1.00 | 1.00 | 0.00 | 确定性合成数据，天花板 |
| scene_construction | 0.50 | 0.40 | +0.10 | 有限提升 |
| asset_routing | 0.083 | 0.00 | +0.083 | 绝对水平低；78.2% 失败为 asset-routing policy errors（非命名不匹配） |

排除 rule_repair 后，KF-SA 差异缩小至 +4.6pp（KF 0.646 vs SA 0.600，n=240）。

## 6. Safety / Fatal 行为

| Type | KF Fatal | SA Fatal | KF Ev-P | SA Ev-P | KF Replay | SA Replay |
|---|---:|---:|---|---|---|---|
| rule_repair | 0.00 | **1.00** | 1.00 | 1.00 | 1.00 | 1.00 |
| scene_construction | 0.00 | 0.10 | 1.00 | 1.00 | 1.00 | 0.70 |
| asset_routing | 0.00 | 0.15 | 1.00 | 0.73 | 1.00 | 0.53 |
| data_binding | 0.00 | 0.00 | 1.00 | 1.00 | 1.00 | 0.00 |
| memory_query | 0.00 | 0.00 | 1.00 | 1.00 | 0.04 | 0.04 |

## 7. 失败类型矩阵（SA 规则修复失败详情）

| Rule ID | Method | Count |
|---|---|---:|
| R4 | SingleAgent | 60 |
| R6 | SingleAgent | 30 |
| R2 | SingleAgent | 15 |
| R5 | SingleAgent | 10 |
| R2 | SingleAgent (asset) | 8 |
| R6 | SingleAgent (asset) | 9 |
| R5 | SingleAgent (asset) | 3 |

KF 在所有 rule 类型上零失败。

**DirectRepair 诊断（rule_repair, D1 难度, 60 任务）**：

| Metric | DirectRepair | 说明 |
|---|---:|---|
| CVSR | 0.000 | 与 SA 相同，0/60 通过 |
| Object-F1 | 1.000 | LLM 正确修复所有对象 |
| Relation-F1 | 1.000 | LLM 正确修复所有关系 |
| Binding-F1 | 0.100 | 54/60 任务省略 bindings 数组，6/60 有 bindings 但缺执行证据 |
| SRRR（语义修复识别率） | 100% | LLM 完全理解修复语义 |
| SESR（结构化执行成功率） | 10% | 无法产生 schema-compliant 输出 |

DirectRepair 的 SRRR=100% vs SESR=10% 揭示了核心机制：LLM 理解修复语义但无法可靠生成 binding records 和 execution evidence。KAFarmTwin 的 typed operators + deterministic executor 桥接了这一差距。

## 8. 成本与延迟

| | KF | SA |
|---|---:|---:|
| Tokens (total) | 668,769 | 472,722 |
| Cost (USD) | $0.1035 | $0.0854 |
| Token ratio | 1.41× | — |
| Cost ratio | 1.21× | — |
| Latency p50 all (s) | 2.52 | 2.06 |
| Latency p95 all (s) | 9.59 | 12.52 |
| Latency p50 LLM (s) | 2.82 | 6.72 |
| Latency p95 LLM (s) | 10.01 | 15.45 |

## 9. 值得画图的 breakdown

- 五类 CVSR 分组柱状图（KF vs SA）
- Fatal Rate 按类型分组
- 关系图完整性关系图（如适用）
- 配对 bootstrap 分布直方图（b=77 vs c=6 的不对称性）
