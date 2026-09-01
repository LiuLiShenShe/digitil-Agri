# 02 — Main Results Master Table

论文核心主实验：External300（DeepSeek-V4-Flash，300 任务 × 2 方法，single execution per task×method）

**Canonical source**：`experiments/v3/results/external300/External300_CANONICAL_METRICS.json`

## 主结果

| Method | CVSR ↑ | Obj-F1 ↑ | Rel-F1 ↑ | Bind-F1 ↑ | Crit-Recall ↑ | Fatal ↓ | Ev-Precision ↑ | Replay ↑ | Tokens | Cost $ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| KAFarmTwin-TypedRepair | **0.7167** | 0.6896 | 0.6995 | 0.5939 | **1.000** | **0.000** | **1.000** | **0.8083** | 668,769 | 0.1035 |
| SingleAgent-AllTools | 0.4800 | 0.6351 | 0.3790 | 0.2000 | 0.950 | 0.250 | 0.9467 | 0.4553 | 472,722 | 0.0854 |

## 配对统计

| Statistic | Value | Detail |
|---|---|---|
| Δ (KF − SA) | **+0.2367** | +23.67 percentage points |
| 95% CI | **[0.1833, 0.2900]** | 10,000 bootstraps, seed 20260804 |
| McNemar b (KF wins) | 77 | |
| McNemar c (SA wins) | 6 | |
| McNemar p | **p<10⁻⁶** | exact tail 8.45e-17 |
| Odds ratio | 12.83 | |
| Token ratio (KF/SA) | 1.41× | |
| Cost ratio (KF/SA) | 1.21× | ≤1.5× threshold |

## 延迟（双口径）

| 口径 | KF p50 (s) | KF p95 (s) | KF n | SA p50 (s) | SA p95 (s) | SA n |
|---|---:|---:|---:|---:|---:|---:|
| All tasks | 2.52 | 9.59 | 300 | 2.06 | 12.52 | 300 |
| LLM-invoking tasks | 2.82 | 10.01 | 240 | 6.72 | 15.45 | 180 |

## test_v2 核心对照（辅助证据，非主实验）

**Canonical source**：`experiments/v3/results/v3_summary.json`

| Method | n | CVSR | pass@1 | pass@5 | Obj-F1 | Rel-F1 | Bind-F1 | Fatal | Ev-P | Replay | Cost/run |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| KAFarmTwin | 100 | **0.610** | 0.610 | 0.700 | 0.7997 | 0.5342 | 0.5292 | **0.000** | 1.000 | 1.000 | $0.0003 |
| SingleAgent | 100 | 0.360 | 0.360 | 0.500 | 0.6854 | 0.3911 | 0.1267 | 0.320 | 0.900 | 0.6068 | $0.0003 |
| ReAct | 100 | 0.000 | 0.000 | 0.000 | 0.0000 | 0.0000 | 0.0000 | 0.000 | 0.000 | 0.0000 | $0.0026 |
| GenericMultiAgent | 100 | 0.010 | 0.010 | 0.050 | 0.4613 | 0.1999 | 0.0433 | 0.310 | 0.790 | 0.0000 | $0.0011 |
| GenericRepair | 100 | 0.060 | 0.060 | 0.100 | 0.4566 | 0.2453 | 0.0425 | 0.070 | 1.000 | 1.0000 | $0.0004 |

test_v2 配对统计（KF vs SingleAgent）：Δ=+0.25pp，95% CI [+0.09, +0.44]，n=20 tasks × 5 repeats。

## 主实验支撑的 central claim

**Claim M1**：KAFarmTwin 在 External300 上的完整有效场景率（CVSR 0.717）显著高于 SingleAgent（0.480），配对提升 +23.7pp（p<10⁻⁶）。

**Claim M1-qual**：优势集中于 rule_repair 类（60 of 71 额外成功），所有 rule_repair 任务均为 D1 难度（单条 R4 违规，prompt 中给出明确修复目标）。排除 rule_repair 后，KF-SA 差异缩小至 +4.6pp（KF 0.646 vs SA 0.600，n=240）。

**Claim M1-directrepair**：SingleAgent-DirectRepair（无类型化修复但有修复 prompt）在 60 个 rule_repair 任务上 CVSR=0.000，但 SSPR=100%（语义结构保持率：Obj-F1=1.000, Rel-F1=1.000），SESR=10%（结构化执行成功率：Bind-F1=0.100）。图级别正确性不等于可执行状态完整性——这是 KAFarmTwin typed repair + deterministic executor 的核心价值。

**Claim M2**：优势的核心来源是约束安全性——KF 致命违例率 0.000 对 SA 0.250，证据精确率 1.000 对 0.947，重放成功率 0.808 对 0.455。

**Claim M3**：成本增加可控——token 比 1.41×，精确成本比 1.21×，低于 1.5× 门限。
