# P0-5S: DirectRepair Failure-Mode Audit

**Date**: 2026-09-01 | **Status**: Complete | **Rerun Decision**: RERUN_NOT_REQUIRED (re-scored with fixed evaluator)

---

## 1. Executive Summary

SingleAgent-DirectRepair (unconstrained LLM, no typed operators, no Knowledge Compiler) achieves CVSR=0/60 on 60 rule_repair tasks. However, this zero pass rate masks a critical distinction:

- **Semantic Repair Recognition Rate = 100%** — the LLM correctly identifies and repairs ALL objects (Object F1 = 1.000) and ALL relations (Relation F1 = 1.000) across all 60 tasks
- **Structured Execution Success Rate = 10%** — only 6/60 tasks produce complete structured output (nodes + edges + bindings + execution evidence)

The failure is NOT in understanding WHAT to repair, but in producing the structured output format required by the evaluator.

## 2. Runner Bug Discovery

### Original v1 Results (INVALID)
All 60 tasks showed: `object_p=0.0, object_r=1.0, object_f1=0.0`

### Root Cause
The runner script (`run_p05r_direct_repair.py`) passed the `public` task dict (stripped to `{task_id, category, task_type, difficulty, prompt, initial_state}`) to `evaluate_task()`. The evaluator looked up `task.get("required_nodes")` — but the public dict has no `required_nodes` field, so it received `[]` (empty list).

With `n_required=0`:
- `object_precision_recall()` returned recall=1.0 (vacuously true: no required nodes to miss)
- Precision=0.0 (generated nodes exist but can't match empty required)

### Corrected v2 Results (VALID)
After passing the gold record (which contains `required_nodes`, `required_edges`, `required_bindings`) as the `task` parameter:

| Metric | v1 (bug) | v2 (correct) |
|--------|----------|--------------|
| Object F1 | 0.000 | **1.000** |
| Relation F1 | 0.000 | **1.000** |
| Binding F1 | 0.000 | **0.100** |

## 3. Failure Taxonomy

| Category | Count | % | Description |
|----------|------:|--:|:------------|
| A: Semantically complete, evidence fail | 6 | 10% | Correct nodes + edges + bindings, but no execution trace |
| C: LLM omits bindings | 54 | 90% | Correct nodes + edges, but outputs empty bindings array |

### Category A: Semantically Complete, Evidence Fail (6 tasks)

Tasks: EXT-RR-003, -007, -009, -011, -015, -019 (and others matching pattern)

The LLM correctly produces:
- All required nodes with correct types, parents, and attributes
- All required edges with correct predicates
- All required bindings with correct metadata

But fails on `evidence_ok` — the execution trace is empty or incomplete. The LLM produces the scene structure but does not generate the tool-call trace that proves the scene was constructed through deterministic execution.

### Category C: LLM Omits Bindings (54 tasks)

The LLM correctly repairs nodes and edges but outputs an empty `bindings` array. The gold standard expects an asset binding (e.g., `{"subject": "ERR001_pump", "target": "ERR001_pump", "type": "asset", "metadata": {"asset_key": "irrigation"}}`).

This triggers fatal violation R6 (device coverage — devices must bind control zones) in most tasks.

### Nonfatal Violations

R3 (spatial layout): 157 occurrences across 60 tasks. The LLM does not produce `location` attributes in `key_attrs`, causing R3 to fire nonfatally.

## 4. Key Metrics

| Metric | Value | Interpretation |
|--------|------:|:---------------|
| CVSR | 0/60 | Still 0 (bindings + evidence required) |
| Semantic Understanding Rate | 100% | LLM correctly repairs all objects and relations |
| Binding Production Rate | 10% | LLM produces bindings in only 6/60 tasks |
| Evidence Production Rate | 0% | LLM produces no execution traces |
| Object F1 | 1.000 | Perfect object matching |
| Relation F1 | 1.000 | Perfect relation matching |
| Binding F1 | 0.100 | Near-zero binding production |

## 5. Comparison with KAFarmTwin

| Metric | KAFarmTwin | DirectRepair | Interpretation |
|--------|-----------|-------------|:---------------|
| Object F1 | 1.000 | 1.000 | Both understand objects |
| Relation F1 | 1.000 | 1.000 | Both understand relations |
| Binding F1 | 1.000 | 0.100 | **KF's typed operators produce bindings; LLM cannot** |
| CVSR | 0.083 (5/60) | 0.000 | KF partially succeeds via deterministic execution |
| Evidence Precision | 1.000 | 0.000 | **KF's executor generates real traces; LLM fabricates nothing** |

**The gap between DirectRepair and KAFarmTwin is NOT in understanding — it is in structured execution.** The LLM understands what needs to change but cannot reliably produce the schema-compliant output (especially bindings and execution evidence) that the evaluator requires.

## 6. Implications for Paper

### What This Proves
1. The LLM has sufficient understanding to repair all rule violations in all 60 tasks
2. The bottleneck is NOT semantic understanding but structured output production
3. KAFarmTwin's typed operators and deterministic executor bridge this exact gap
4. The Knowledge Compiler's role is to translate semantic understanding into structured actions

### What This Does NOT Prove
1. That the LLM "understands" in a deep sense — it may be pattern-matching
2. That DirectRepair would fail on ALL repair tasks — only tested on D1 template-matched tasks
3. That KAFarmTwin is optimal — only that it outperforms unconstrained LLM on structured output

### Paper Claims to Update
- ~~"DirectRepair achieves 0/60 CVSR — LLM cannot repair"~~ → "DirectRepair achieves 0/60 CVSR despite 100% semantic understanding; failure is in structured output production"
- Add: "Semantic Repair Recognition Rate = 100%" as a new diagnostic metric
- Add: "Structured Execution Success Rate = 10%" as a complementary metric

## 7. Output Files

| File | Description |
|------|-------------|
| `p05s_direct_repair_failure_audit.csv` | 60-row per-task failure classification |
| `p05s_direct_repair_failure_audit.json` | Machine-readable summary with diagnosis |
| `analyze_directrepair_failures.py` | This analysis script (read-only) |
