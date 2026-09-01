# Provenance: DirectRepair Scoring Correction (P0-5S)

**Date**: 2026-09-01 | **Author**: Automated audit | **Status**: Resolved

## Bug Description

The script `experiments/v3/scripts/run_p05r_direct_repair.py` passed the **public task dict** (`task=task`) to `evaluate_task()` instead of the **gold record** (`task=g`). The public dict does not contain `required_nodes`, `required_edges`, or `required_bindings` fields.

### How the bug manifested

```python
# BEFORE (buggy):
evaluate_task(task=task, method=method, nodes=nodes, edges=edges, bindings=bindings)

# AFTER (fixed):
# CRITICAL: pass the GOLD record as 'task' so evaluate_task can access required_nodes/required_edges/required_bindings
evaluate_task(task=g, method=method, nodes=nodes, edges=edges, bindings=bindings)
```

### Evaluator behavior with missing required_nodes

In `experiments/v3/evaluators/metrics.py` line 76:
```python
required = task.get("required_nodes") or []
```

When `required_nodes` is absent (public dict), `required` becomes `[]`. Then:
- `n_required = 0`
- `recall = tp / n_required if n_required > 0 else (1.0 if tp == 0 else 1.0)` (node_match.py line 310)
- With `n_required=0`, recall defaults to 1.0 vacuously
- This masked the actual failure mode, making all tasks appear to have Object-F1=0.000

## Impact

| Metric | Before (Buggy) | After (Corrected) |
|:-------|----------------:|-------------------:|
| Object-F1 (mean) | 0.000 | **1.000** |
| Relation-F1 (mean) | 0.000 | **1.000** |
| Binding-F1 (mean) | 0.000 | **0.100** |
| CVSR | 0/60 | **0/60** (unchanged) |
| SRRR | N/A | **1.000** (100%) |
| SESR | N/A | **0.100** (10%) |

The CVSR remained 0/60, but the interpretation changed fundamentally: the LLM correctly produces all required objects and relations (SRRR=100%) but fails to produce contract-complete structured output including bindings (SESR=10%).

## Fix Procedure

1. Ran `experiments/v3/scripts/run_p05r_rescore.py` with gold-injected evaluator
2. Gold records loaded from `external300_gold_draft.jsonl`
3. For each of 60 rule_repair tasks: loaded existing DirectRepair output, re-scored with gold record as `task=` argument
4. Results written to `p05r_direct_repair_results_v2.jsonl` and `p05r_direct_repair_v2_summary.json`

## No Reruns Performed

The fix involved **re-scoring only** — no new LLM calls were made. The DirectRepair method output was preserved from the original run; only the evaluation inputs were corrected.

## Downstream Effects

- Table 8b in paper updated with corrected DirectRepair metrics
- Appendix A5 added with failure-mode decomposition
- SRRR/SESR diagnostic introduced as core mechanistic evidence
- Abstract and Conclusions updated with new framing

## Files

| File | Description |
|:-----|:------------|
| `experiments/v3/scripts/run_p05r_direct_repair.py` | Original script (bug at line 121-124) |
| `experiments/v3/scripts/run_p05r_rescore.py` | Re-scoring script with gold injection |
| `experiments/v3/results/external300/p05r_direct_repair/p05r_direct_repair_results_v2.jsonl` | Corrected per-task results |
| `experiments/v3/results/external300/p05r_direct_repair/p05r_direct_repair_v2_summary.json` | Corrected summary |
| `Academic Pipeline/05_review/p05s_direct_repair_failure_audit.csv` | 60-row failure classification |
| `Academic Pipeline/05_review/p05s_direct_repair_failure_audit.json` | Machine-readable summary |
| `Academic Pipeline/05_review/P05S_direct_repair_failure_analysis.md` | Full analysis report |
