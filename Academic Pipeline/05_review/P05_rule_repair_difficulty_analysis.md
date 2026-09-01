# P0-5: Rule Repair Task Difficulty & Baseline Applicability Analysis

**Date**: 2026-08-31 | **Status**: Analysis Complete | **Rerun Decision**: RERUN_NOT_REQUIRED

---

## 1. Executive Summary

All 60 rule_repair tasks are **D1 difficulty** (single-rule, single-step, deterministic, explicit fix target in prompt). The 60/60 vs 0/60 result proves "repair loop present > absent" and "typed operator selection works for template-matched single-rule R4 violations" — but does **not** prove general repair capability. The baseline comparison is asymmetric by design: SA has no repair loop.

## 2. SA llm_calls=0 Investigation

| Field | Value |
|-------|-------|
| SA rule_repair records | 60 |
| SA llm_calls | **0 for all 60** |
| SA tokens | **0 for all 60** |
| SA CVSR | **False for all 60** |
| SA fatal violations left in scene | R4: 60, R6: 30, R2: 15 |

**Root cause**: `single_agent.py` lines 40-53 explicitly route rule_repair tasks to `construction_path: "bare_seed_no_repair"`, which returns the broken scene unchanged. This is **by design** — SA has no repair loop.

**Baseline applicability label**: `A_BASELINE_INCAPABLE_BY_DESIGN`

**Verification**: Source code confirmed at `/data/fj/数字孪生-paper-work/experiments/v3/methods/single_agent.py:40-53`. No implementation bug found.

## 3. Task Template Analysis

| Template | Count | % | Violation Rule |
|----------|-------|---|---------------|
| Pump → irrigation asset fix | 15 | 25.0% | R4 |
| Irrigation → irrigation asset fix | 15 | 25.0% | R4 |
| Camera → camera asset fix | 15 | 25.0% | R4 |
| Sensor → sensor asset fix | 15 | 25.0% | R4 |

**All 60 tasks** are R4 (asset_type_mismatch) violations. No other rule is tested.

## 4. Difficulty Tier Classification

| Tier | Count | Description |
|------|-------|-------------|
| D1 | **60/60 (100%)** | Single rule, single step, deterministic, prompt contains explicit fix target |

**Key properties of all 60 tasks**:
- Explicit fix target in prompt: 60/60 (100%)
- Semantic reasoning required: 0/60
- Ontology reasoning required: 0/60
- Multiple valid repairs: 0/60
- Repair steps required: 1 (all tasks)

**D1-D4 taxonomy** (for reference):
- **D1**: Single rule, explicit fix target → deterministic single step
- **D2**: Single rule, fix target requires semantic inference → single LLM call
- **D3**: Multi-rule, cascading violations → sequential repair
- **D4**: Ambiguous/multiple valid repairs → requires disambiguation

## 5. KF Performance

| Metric | Value |
|--------|-------|
| CVSR pass | 60/60 (100%) |
| LLM calls per task | 1 (all tasks) |
| Tokens per task | ~1,200–1,500 |
| Fatal violations after repair | 0 (all tasks) |

KF makes exactly 1 LLM call per task to select from `candidate_actions_for("R4")`, which returns deterministic patch operators (`replace_asset`, `set_placeholder`, `ask_user`). The executor applies the selected operator transactionally.

## 6. Decomposed External300 Contribution

| Metric | All 300 | Excl. Rule Repair (240) |
|--------|---------|------------------------|
| KF CVSR | 215/300 = 0.717 | 155/240 = 0.646 |
| SA CVSR | 144/300 = 0.480 | 144/240 = 0.600 |
| Delta | **+23.7 pp** | **+4.6 pp** |

**Per-category breakdown**:

| Category | KF | SA | Δ | Net KF wins |
|----------|-----|-----|---|-------------|
| scene_construction | 30/60 | 24/60 | +10.0 pp | +6 |
| asset_routing | 5/60 | 0/60 | +8.3 pp | +5 |
| data_binding | 60/60 | 60/60 | +0.0 pp | 0 |
| rule_repair | 60/60 | 0/60 | **+100.0 pp** | **+60** |
| memory_query | 60/60 | 60/60 | +0.0 pp | 0 |

**Net KF-only wins**: 71 tasks (60 rule_repair + 6 scene_construction + 5 asset_routing).  
**Net SA-only wins**: 0 tasks.

## 7. Defensible Interpretation

The 60-task rule_repair subset is a **controlled mechanism test** demonstrating that KAFarmTwin's typed repair path can reliably execute supported single-step R4 corrections when the repair target is unambiguous. The 60/60 vs 0/60 comparison primarily measures:

1. ✅ Presence of an explicit repair loop vs an execution path that performs no repair
2. ✅ Typed operator selection correctness for template-matched single-rule violations
3. ❌ NOT general repair capability across diverse rules (D2-D4 difficulty)
4. ❌ NOT multi-rule cascading repair
5. ❌ NOT ambiguous repair scenarios

## 8. Output Files

| File | Rows | Description |
|------|------|-------------|
| `rule_repair_task_audit.csv` | 60 | Per-task audit with difficulty tier, template, properties |
| `rule_repair_baseline_applicability.csv` | 60 | SA baseline applicability classification (all A_BASELINE_INCAPABLE_BY_DESIGN) |
| `rule_repair_summary.json` | — | Machine-readable summary with all findings |
| `external300_decomposed_metrics.json` | — | Decomposed External300 metrics (all categories) |
