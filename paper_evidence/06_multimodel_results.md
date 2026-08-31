# 06 — 多模型家族泛化实验

**Canonical source**：`experiments/v3/results/external300/multimodel/MULTIMODEL_CANONICAL_STATISTICS_v2.json`
**Preregistration**：`MULTIMODEL_PREREGISTRATION_v2.md`（2026-08-25 冻结）
**Verdict**：**MODEL_GENERALIZATION_PASS**（4/4 Δ>0，4/4 CI lower >0）

## 6.1 总体模型表

| Model | KF CVSR | SA CVSR | Δ (pp) | 95% CI | McNemar (b,c) | McNemar p | TF |
|---|---:|---:|---:|---|---|---|---:|
| DeepSeek-V4-Flash | 0.7167 | 0.4800 | +23.67 | [18.33, 29.00] | (77, 6) | <10⁻⁶ | 0 |
| Kimi-K2.6 (Pro) | 0.6733 | 0.4933 | +18.00 | [13.00, 23.33] | (63, 9) | <10⁻⁶ | 0 |
| MiniMax-M2.5 | 0.6067 | 0.3500 | +25.67 | [19.67, 31.67] | (91, 14) | <10⁻⁶ | 1 |
| Qwen3.6-27B | 0.6967 | 0.4800 | +21.67 | [16.67, 26.67] | (69, 4) | <10⁻⁶ | 0 |
| GLM-5.2 | 0.7367 | 0.4933 | +24.33 | [18.33, 30.33] | (88, 15) | <10⁻⁶ | 0 |

Cluster bootstrap（四新模型均值，按 task_id 聚类，2000 resamples）：point +22.42pp，CI95 [17.92, 27.00]——探索性标注。

## 6.2 每模型 task-category CVSR breakdown

| Type | DeepSeek | Kimi | MiniMax | Qwen | GLM | 模式 |
|---|---:|---:|---:|---:|---:|---|
| **rule_repair KF** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | **五模型完全一致** |
| **rule_repair SA** | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | **五模型完全一致** |
| data_binding KF | 1.00 | 0.95 | **0.27** | 1.00 | 0.87 | MiniMax 退化 |
| data_binding SA | 1.00 | 0.97 | 0.22 | 1.00 | 0.82 | MiniMax 退化 |
| memory_query (all) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 全部天花板 |
| scene_construction KF | 0.50 | 0.42 | 0.63 | 0.48 | 0.63 | 模型间差异 |
| scene_construction SA | 0.40 | 0.50 | 0.53 | 0.40 | 0.65 | 模型间差异 |
| asset_routing KF | 0.08 | 0.00 | 0.13 | 0.00 | 0.18 | 普遍低 |
| asset_routing SA | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 全部为零 |

## 6.3 fatal / replay 对比

| Model | KF Fatal | SA Fatal | KF Ev-P | SA Ev-P | KF Replay | SA Replay |
|---|---:|---:|---|---|---|---|
| DeepSeek | 0.000 | 0.250 | 1.000 | 0.947 | 0.808 | 0.455 |
| Kimi | 0.000 | 0.290 | 1.000 | 0.933 | 0.808 | 0.442 |
| MiniMax | 0.003 | 0.293 | 0.990 | 0.957 | 0.798 | 0.475 |
| Qwen | 0.000 | 0.250 | 1.000 | 0.953 | 0.808 | 0.458 |
| GLM | 0.000 | 0.227 | 0.997 | 0.853 | 0.805 | 0.383 |

**Universal pattern**：KF Fatal≈0 / Replay≈0.80 / Ev-P≈1.00 全模型一致；SA Fatal 0.23–0.29 / Bind-F1≤0.20 / Replay 0.38–0.48 全模型一致。

## 6.4 rule_repair

**五模型完全一致的机制性证据**：
- KF rule_repair CVSR = 1.00（5/5 模型）
- SA rule_repair CVSR = 0.00（5/5 模型）
- 这是协议性差异（类型化修复闭环机制），不是模型能力差异

## 6.5 data_binding

**模型依赖的退化现象**：
- MiniMax-M2.5 KF data_binding CVSR = 0.27（其余模型 0.87–1.00）
- 原因未明，如实报告，不剔除
- 即便如此，MiniMax Δ 仍为最大值之一（+25.67pp）

## 6.6 模型间最稳定的现象

1. rule_repair：KF=1.00 / SA=0.00 五模型完全一致
2. memory_query：全部 1.00（天花板）
3. KF Fatal≈0 / SA Fatal 0.23–0.29
4. asset_routing：所有模型 KF≤0.18 / SA=0
5. KF Replay≈0.80 / SA Replay 0.38–0.48

## 6.7 模型间差异

1. MiniMax data_binding 退化（KF 0.27 vs 其余 0.87–1.00）
2. scene_construction 波动（KF 0.42–0.63，SA 0.40–0.65）
3. MiniMax 延迟显著更高（p50 20s / p95 106s，其余 2.5–10s）
4. MiniMax tokens 更高（973K vs 其余 616–650K）
