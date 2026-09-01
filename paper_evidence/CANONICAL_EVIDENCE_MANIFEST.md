# CANONICAL EVIDENCE MANIFEST

**Version:** 2.0 | **Date:** 2026-09-01 | **Paper version:** canonical_rewrite_v2

This document is the single source of truth for all numerical claims in the paper. Every number in the manuscript must trace back to one of the entries below.

---

## 1. Metrics Summary

### 1.1 External300 (DeepSeek-V4-Flash, N=300 tasks)

| Metric | KF | SA | Delta | Source |
|---|---:|---:|---:|---|
| CVSR | 0.717 | 0.480 | +23.67pp | `ext300_formal_20260825/scored/per_task.jsonl` |
| Paired 95% CI | — | — | [18.33, 29.00] | 10,000 task-level bootstraps |
| McNemar p | — | — | 8.45e-17 | b=77 (KF wins), c=6 (SA wins) |
| Fatal Rate | 0.000 | 0.250 | — | `External300_CANONICAL_METRICS.json` |
| Evidence Precision | 1.000 | 0.947 | — | 同上 |
| Replay Success | 0.808 | 0.455 | — | 同上 |

**Provenance:** Sealed under `ext300_formal_20260825/SEAL.json`, SHA-256 `b52f00c4bee3b437...`. Bootstrap seed 20260804. Each task-method pair executed once (single execution protocol).

### 1.2 Rule Repair (D1 difficulty, 60 tasks)

| Metric | KF | SA | DirectRepair | Source |
|---|---:|---:|---:|---|
| CVSR | 1.000 | 0.000 | 0.000 | `External300_CANONICAL_METRICS.json` (by_type) |
| Object-F1 | 1.000 | — | 1.000 | 同上 |
| Relation-F1 | 1.000 | — | 1.000 | 同上 |
| Binding-F1 | 1.000 | — | 0.100 | 同上 |
| SSPR (Semantic Structure Preservation Rate) | 1.000 | — | 1.000 | = 1[Obj-F1=1 ∧ Rel-F1=1]; all 60 tasks preserve structure |
| SSCR (Structured Completion Success Rate) | 1.000 | — | 0.100 | = 1[Obj-F1=1 ∧ Rel-F1=1 ∧ Bind-F1>0.5]; only 6/60 DirectRepair tasks have complete bindings |
| Category A (structurally complete, no execution trace) | — | — | 6 | Correct nodes + edges + bindings; missing execution evidence |
| Category C (correct structure, omits bindings) | — | — | 54 | Correct nodes + edges; empty bindings array → R6 fatal |

**Cross-tab (binding omission × fatal violations):** Of 54 binding-omission tasks, 43 had fatal findings (29 R6, 14 R2) and 11 had no fatal finding. Of 6 tasks with correct bindings, 0 had fatal findings.

**Provenance:** DirectRepair was RE-SCORED ONLY (no new LLM calls). The original runner passed the `public` task dict (lacking `required_nodes`) to `evaluate_task()`, masking correct output. After re-scoring with gold records, Object-F1=1.000, Rel-F1=1.000 confirmed. All values are from canonical statistics after re-scoring. D1 subset = rule_repair tasks only (no D2-D4 difficulty tiers tested).

### 1.3 Asset Routing

| Metric | Value | Source |
|---|---:|---|
| KF CVSR | 0.083 | `External300_CANONICAL_METRICS.json` (by_type) |
| ID-invariant policy error % | 78.2% | ID-invariant audit: canonical asset F1=0.997 but 78.2% of routed assets have wrong physical identity |
| ID-invariant canonical Rel-F1 | 0.997 | 同上 audit |
| ID-invariant canonical Bind-F1 | 0.994 | 同上 audit |

**Provenance:** Asset routing was audited using an ID-invariant evaluation method — the evaluator checks whether the *structure* of the asset binding is correct regardless of which specific asset ID is chosen. This reveals that KF's low CVSR (0.083) comes from policy/routing errors (adding an unrequired device while omitting a required one), not structural binding errors. The high canonical Rel-F1 (0.997) and Bind-F1 (0.994) with 78.2% policy error confirms the bottleneck is asset identification, not scene graph construction.

### 1.4 Excluding Rule Repair (240 tasks: scene + binding + asset + memory)

| Metric | KF | SA | Delta |
|---|---:|---:|---:|
| CVSR | 0.646 | 0.600 | +4.6pp |

**Provenance:** Derived by excluding the 60 rule_repair tasks from External300 totals. KF total correct = 0.717 * 300 = 215.1, rule_repair correct = 60, remaining = 155.1/240 = 0.646. SA: 0.480 * 300 = 144, rule_repair correct = 0, remaining = 144/240 = 0.600.

---

## 2. Claim-Evidence Mapping

| Claim | Key Number | Manifest Entry | Strength |
|---|---|---|---|
| C01: KF CVSR significantly exceeds SA on External300 | 0.717 vs 0.480, p=8.45e-17 | `external300.kf_cvsr`, `external300.sa_cvsr`, `external300.mcnemar_p` | Directly supported |
| C02: Advantage stems from constraint safety (Fatal down, Ev-P up, Replay up) | Fatal 0 vs 0.25, Replay 0.808 vs 0.455 | `external300.kf_fatal`, `external300.sa_fatal`, `external300.kf_replay`, `external300.sa_replay` | Directly supported |
| C03: Cost increase is manageable (<=1.5x) | Token ratio 1.41x, Cost ratio 1.21x | `External300_CANONICAL_METRICS.json` cost fields | Directly supported |
| C04: Knowledge compiler is decisive for the frozen test_v2 asset ablation subset | A1 asset CVSR 0.95 -> 0.00 | `03_ablation_results.md` A1 breakdown | Supported (test_v2 subset only; External300 asset CVSR remains 0.083) |
| C05: Typed repair contributes safety, not CVSR | Fatal 0 -> 0.22 (A2), CVSR 0.58 > full 0.55 | `03_ablation_results.md` A2 | Directly supported |
| C06: Ontology constraint improves binding correctness | Bind-F1 0.529 -> 0.453 (A3) | `03_ablation_results.md` A3 | Supported (moderate effect) |
| C07: Positive KF–SA directional robustness reproduced across evaluated model families under common inference interface | 4/4 models delta > 0, CI lower > 0 | `MULTIMODEL_CANONICAL_STATISTICS_v2.json` | Directly supported (not provider-independent generalization) |
| C08: D1 R4 rule repair subset showed identical KF/SA direction across five evaluated model families | 5/5 models identical | `05_external300_results.md` + `06_multimodel_results.md` | Supported (D1 subset only; no D2-D4 tested) |
| C09: Asset routing absolute level remains low | KF asset CVSR <= 0.18 across 5 models | `08_category_results.md` asset_routing | Directly supported (honest limitation) |

---

## 3. Provenance Notes

### 3.1 DirectRepair Runner Bug Fix (RE-SCORING ONLY; NO MODEL RERUN)
The DirectRepair baseline (single-agent with repair prompt but no typed repair loop) was initially scored with a bug: the runner passed the `public` task dict (lacking `required_nodes`) to `evaluate_task()`, causing empty required lists and misleadingly zero Object-F1. **Existing DirectRepair outputs were loaded and RE-SCORED with gold records. No new LLM calls were made.** The corrected values show DirectRepair CVSR = 0.000 on rule_repair (same as SA), but Object-F1 = 1.000 and Rel-F1 = 1.000 — confirming that DirectRepair preserves structure but fails on structured output production (SSCR = 10%). Typed repair's value is in the *type system and deterministic executor*, not just having a repair loop.

### 3.2 ID-Invariant Audit for Asset Routing
Asset routing CVSR is extremely low for both methods (KF 0.083, SA 0.000). To understand whether the failure is in structural binding or asset identification, an ID-invariant evaluation was conducted:
- Canonical Rel-F1 = 0.997 and Bind-F1 = 0.994 (structure is correct)
- But 78.2% of routed assets have wrong physical identity (policy error)
- Conclusion: the bottleneck is asset identification/routing, not scene graph construction

### 3.3 Statistical Methods
- All bootstrap CIs use task-level paired resampling (10,000 iterations, seed 20260804)
- McNemar test uses exact binomial tail on discordant pairs (not normal approximation)
- Cluster bootstrap for cross-model aggregation uses 2,000 resamples by task_id
- Repeats (5x) in test_v2/ablation are NOT treated as independent samples

---

## 4. Delimitations

| # | Delimitation | Impact |
|---|---|---|
| 1 | No real-world greenhouse deployment | Results reflect simulated environments only |
| 2 | Author-generated and author-reviewed benchmarks | Not independently curated; potential bias in task design |
| 3 | D1-only repair subset (no D2-D4) | Rule repair difficulty analysis limited to easiest tier |
| 4 | Single execution per task-method pair (External300) | No within-method variance estimate for External300 results |
| 5 | test_v2 consulted during development | Potential data leakage for hyperparameter tuning |

---

## 5. Canonical Source Registry

| Experiment | Canonical Source File | Seal/Commit |
|---|---|---|
| External300 | `External300_CANONICAL_METRICS.json` | `ext300_formal_20260825/SEAL.json` |
| Multimodel | `MULTIMODEL_CANONICAL_STATISTICS_v2.json` | Same seal |
| Ablation | `ablation_results.csv` + `v3_ablation_summary.json` | Preregistered protocol |
| test_v2 | `v3_summary.json` | Consulted during dev (delimitation #5) |
| Source map | `13_canonical_source_map.md` | This manifest supersedes all prior claim-evidence docs |

**Do NOT cite:** `overall_summary.json` (intermediate), `smoke_results_v2.json` (diagnostic only), any `archive_*` directories, `v3_summary.csv` (mirror of JSON).
