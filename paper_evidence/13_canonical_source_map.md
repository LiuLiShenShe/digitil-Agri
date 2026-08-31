# 13 — Canonical Source Map

论文写作时，每个数字必须来自唯一 canonical source。以下为映射关系。

## External300 (DeepSeek)

| 数据 | Canonical source | 不可引用 |
|---|---|---|
| KF/SA 总体 CVSR, F1, Fatal, Replay | `results/external300/External300_CANONICAL_METRICS.json` | `overall_summary.json`（中间产物，口径一致但 canonical 以 JSON 为准）|
| 分类型 CVSR/F1 | 同上 `by_type` 字段 | — |
| 配对 Δ, CI, McNemar | 同上 `paired_statistics` | — |
| 延迟 p50/p95 | 同上 `latency` | — |
| 成本 ratio | 同上 `token_ratio_kf_over_sa`, `cost_ratio_kf_over_sa` | — |
| 失败类型矩阵 | 同上 `failure_matrix` | — |
| Seal SHA | `ext300_formal_20260825/SEAL.json` | 任何手动计算的 SHA |
| Frozen baseline SHA | `b52f00c4bee3b437…` (preregistration frozen) | — |

## Multimodel

| 数据 | Canonical source | 不可引用 |
|---|---|---|
| 四新模型全部指标 | `results/external300/multimodel/MULTIMODEL_CANONICAL_STATISTICS_v2.json` | `smoke_results_v2.json`（仅诊断，非正式） |
| 模型 delta/CI/McNemar | 同上 `paired` 字段 | — |
| 分类型 CVSR | 同上 `by_type_cvsr` | — |
| Cluster bootstrap | 同上 `cross_model_aggregate_exploratory` | — |
| 判定 | 同上 `generalization_verdict` | — |
| 价格快照 | `price_snapshot.json` | 任何实时价格 |
| 预注册 | `MULTIMODEL_PREREGISTRATION_v2.md` | `MULTIMODEL_PREREGISTRATION.md`（v1 历史版） |

## Ablation

| 数据 | Canonical source | 不可引用 |
|---|---|---|
| full/A1/A2/A3 CVSR, F1, Fatal | `results/analysis/ablation_results.csv` | `v3_ablation_summary.json`（镜像，CSV 为 canonical） |
| 详细指标 | `results/v3_ablation_summary.json` | — |
| 原始运行 | `results/archive_ablation_v1/v3_runs_ablation_*.jsonl` | — |

## test_v2

| 数据 | Canonical source | 不可引用 |
|---|---|---|
| 五方法 CVSR/pass/F1 | `results/v3_summary.json` | `v3_summary.csv`（镜像） |
| Phase2 frozen 对照 | `results/v3_summary_phase2_frozen.json` | — |

## 论文旧版 claim-evidence

| 数据 | 位置 | 状态 |
|---|---|---|
| 旧 claim-evidence matrix | `results/analysis/paper_claim_evidence_matrix.csv` | 参考但不引用（手工维护，可能过期） |

## 已废弃/归档（禁止引用）

- `results/archive_formal_20260817*` — 首次正式运行（已作废重跑）
- `results/archive_stale_20260817*` — 污染数据
- `results/archive_phase2_frozen*` — Phase2 版本（已被 Phase3 替代）
- `results/archive/dev_20260808*` — 开发期数据
- `results/archive/F015_*` — 早期实验
- `results/backup_*` — 备份
- `results/dev_mock.jsonl` — mock 数据
