# External300 最终报告 v1（canonical，2026-08-25）

数据源：`ext300_formal_20260825/raw/runs.jsonl`（SEAL SHA `b52f00c4bee3b43723689c3556300e0754a8ab9564b96341d05e88b591d40d91`），
全部指标由 `recompute_external300_canonical.py` 从封存 raw 独立重算，一致性门 12/12 PASS。

## 身份声明（必读）
External300 为 **author-generated / author-reviewed controlled benchmark**
（human_review_mode=author_confirmation，审核人数=1，非独立、非双盲、非 gold standard）。
本报告不得用于宣称 independent external validation / double-blind / private held-out / SOTA。
协议偏离与作废-重跑链见 PROTOCOL_DEVIATION_EXTERNAL300.md。

## 主结果（300 配对任务）
| 指标 | KF-TypedRepair | SA-AllTools |
|---|---|---|
| Overall CVSR | 0.7167 | 0.48 |
| Object-F1 | 0.6896 | 0.6351 |
| Relation-F1 | 0.6995 | 0.379 |
| Binding-F1 | 0.5939 | 0.2 |
| Critical Recall | 1.0 | 0.95 |
| Fatal violation rate | 0.0 | 0.25 |
| Evidence Precision | 1.0 | 0.9467 |
| Replay Success | 0.8083 | 0.4553 |

配对统计：Δ=+0.2367（23.67 pp），95% CI [0.1833, 0.29]；
McNemar exact b=77 / c=6，p<1e-6 (exact tail 8.45e-17, b=77, c=6)。

## 分类型 CVSR
| 类型 | KF | SA |
|---|---|---|
| asset_routing | 0.0833 | 0.0 |
| data_binding | 1.0 | 1.0 |
| memory_query | 1.0 | 1.0 |
| rule_repair | 1.0 | 0.0 |
| scene_construction | 0.5 | 0.4 |

分类型诚实解读：rule_repair（1.00 vs 0.00）是主要提升来源；scene_construction 提升有限
（0.50 vs 0.40）；asset_routing 绝对性能仍很低（0.083 vs 0）；data_binding 与 memory_query
双方均 1.00（天花板效应，无可宣称的相对提升）。repair 类仅覆盖单一错误族；memory 时间序列
为确定性合成数据——两者均限制外推。

## 成本 / Token / 延迟
- KF：tokens 668,769，cost $0.1035，all_tasks p50=2.52s / p95=9.59s (n=300)；llm_invoking p50=2.82s / p95=10.01s (n=240)
- SA：tokens 472,722，cost $0.0854，all_tasks p50=2.06s / p95=12.52s (n=300)；llm_invoking p50=6.72s / p95=15.45s (n=180)
- token ratio（KF/SA）= 1.4147；cost ratio = 1.2119
- 延迟双口径说明：all_tasks 含无 LLM 调用的确定性任务（近零延迟也计入）；
  llm_invoking_tasks 仅计 llm_calls>0 的任务。分位数算法 nearest-rank。
- 勘误：AUDIT_REPORT §8 曾写 SA p50=3.7/p95=14.0，系沿用已作废的 20260824 运行数字；
  canonical 口径以本报告为准（SA all_tasks p50=2.06s /
  p95=12.52s）。
