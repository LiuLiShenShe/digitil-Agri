# 09 — Statistical Evidence Inventory

## 统计方法清单

| Claim | Unit of analysis | N | Statistic | CI / Test | Canonical script / source |
|---|---|---:|---|---|---|
| test_v2 KF > SA (CVSR) | task-level paired | 20 tasks × 5 repeats | mean Δ = +0.25pp | 95% CI [+0.09, +0.44] | `run_sota_gate.py` paired bootstrap (seed 20260804, 10000 iter) |
| External300 KF > SA (CVSR) | task-level paired | 300 tasks | mean Δ = +0.2367 | 95% CI [0.1833, 0.2900] | `External300_CANONICAL_METRICS.json` → 10,000 bootstraps |
| External300 McNemar | task-level discordant pairs | b=77, c=6 | p<10⁻⁶ (8.45e-17) | Exact binomial tail | `External300_CANONICAL_METRICS.json` |
| Multimodel Δ (Kimi) | task-level paired | 300 tasks | Δ = +0.1800 | 95% CI [0.1300, 0.2333] | `MULTIMODEL_CANONICAL_STATISTICS_v2.json` |
| Multimodel Δ (MiniMax) | task-level paired | 300 tasks | Δ = +0.2567 | 95% CI [0.1967, 0.3167] | 同上 |
| Multimodel Δ (Qwen) | task-level paired | 300 tasks | Δ = +0.2167 | 95% CI [0.1667, 0.2667] | 同上 |
| Multimodel Δ (GLM) | task-level paired | 300 tasks | Δ = +0.2433 | 95% CI [0.1833, 0.3033] | 同上 |
| Multimodel cluster bootstrap | task-level clustered | 300 tasks × 4 models | mean Δ = +22.42pp | 95% CI [17.92, 27.00] | `multimodel_canonical_stats.py` 2000 resamples |
| Ablation A1 (compiler) | task-method grouped | 100 runs (20×5) | CVSR 0.550→0.370 | Descriptive (no CI) | `ablation_results.csv` |
| Ablation A2 (repair) | task-method grouped | 100 runs (20×5) | Fatal 0→0.22 | Paired flips 22:0 | `v3_ablation_summary.json` |

## 关键统计说明

1. **test_v2 和 ablation**：每配置 5 repeats，n=20 tasks × 5 = 100 runs per method
2. **External300 和 multimodel**：每 task×method 单次执行，n=300 tasks per method
3. **Bootstrap**：均使用 task-level paired bootstrap，不将 repeats 视为独立样本
4. **McNemar**：仅对 discordant pairs（b+c）做精确二项检验，不用近似
5. **跨模型聚合**：cluster bootstrap by task_id（300 任务被五个模型复用，非 1500 独立样本）
6. **bootstrap seed**：全部使用 20260804，可复现
