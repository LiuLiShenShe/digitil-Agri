# test_v2 — Annotation Report

**Date**: 2026-08-05
**Annotator 1 (implementer)**: generated test_v2 candidate tasks (20 tasks, 5 types × 4)
**Annotator 2 (user)**: PENDING — all 20 tasks are `PENDING_HUMAN_REVIEW`
**Freeze gate**: BLOCKED until annotator 2 approves all gold (changes `review_status` from `PENDING_HUMAN_REVIEW` to `approved`), after which the Gold audit passes with 0 errors, 0 warnings.

## Annotation process

1. **Annotator 1** generates draft gold:
   - Graph tasks (scene_construction/asset_routing/data_binding/rule_repair): gold via `test_v2_tasks.py`, deterministic `required_nodes/edges/bindings/critical_objects` from crop/sensor/asset-type parameters. No hand-picking.
   - memory_query tasks: gold via Oracle (`memory_fixtures.oracle_environment_summary`): deterministic from `initial_state` timeseries. `expected_answer` and `expected_evidence` are computed, not written by hand.

2. **Gold audit** (`evaluators/gold_audit.py`): all 20 tasks pass with 0 errors. The audit specifically checks: task_type consistency, memory_query must not carry scene gold, all task types must have a gradable outcome, annotation_version == v2.

3. **Oracle self-consistency**: all 4 memory_query tasks pass Query-CVSR with the Oracle answer (metric_recall=1.0, evidence_precision=1.0).

4. **Annotator 2** reviews: the user reviews each task's gold, rationale, and review_items. Tasks where annotator 2 identifies issues are revised (with changelog). Once all tasks are `approved`, they are sealed with final SHA-256.

## Review packet locations
All task gold packets are in:
```
benchmark/test_v2/test_v2_gold.jsonl
```
Each line is a full gold dict (task_type + gold block + oracle output + review_status).

## Approval requirements
- Annotator 2 must set `review_status = "approved"` for each task.
- After approval, MANIFEST.sha256 is regenerated and frozen.
- Once frozen: no changes to gold, test split, scorer, or budget without bumping test_v2 → test_v3.
