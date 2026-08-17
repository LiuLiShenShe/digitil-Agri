# test_v2 — Datasheet

**Benchmark version**: test_v2 (candidate, awaiting human approval + freeze)
**Created**: 2026-08-05
**Generator**: `benchmark/test_v2_tasks.py`
**Status**: CANDIDATE — passes static Gold audit (0 errors) AND JSON Schema
validation (0 errors); all tasks `pending` until the user (annotator 2) approves.

## Motivation & composition
test_v2 replaces invalidated test_v1 (Prompt-Gold contradiction, see
`benchmark/archive/test_v1_invalid/INVALIDATION_REPORT.md`). It is a
**task-type-aware** benchmark: each task declares a `task_type`, and gold is
gradeable by the matching adapter — never a single object-graph CVSR for a
retrieval task.

## Composition (20 tasks, 4 per type)

| task_type            | count | task ids                    |
|----------------------|-------|-----------------------------|
| scene_construction   | 4     | TN01,TN02,TN03,TN04 (-v2-scene) |
| asset_routing        | 4     | TN11,TN12,TN13,TN14 (-v2-asset) |
| data_binding         | 4     | TN21,TN22,TN23,TN24 (-v2-bind)  |
| rule_repair          | 4     | TN31,TN32,TN33,TN34 (-v2-repair)|
| memory_query         | 4     | TN41,TN42,TN43,TN44 (-v2-mem)   |

## Uniqueness / anti-collision
All object/node ids are prefixed with a per-task tag (e.g. `N01_lettuce_gh`),
guaranteeing no collision with train/dev ids. Crops, sensor metrics, time
windows, counts, and data values differ from train/dev.

## Deterministic fixtures & Oracle
memory_query tasks embed a deterministic `initial_state`
(objects/timeseries_records/events) from which `expected_answer` and
`expected_evidence` are **Oracle-derived** (see `memory_fixtures.py`). The
agent queries pre-existing state; it does NOT build the scene.

## Access control
- `test_v2_public_inputs.jsonl` — public prompt/task_type only, given to methods.
- `test_v2_gold.jsonl` — full gold (required_nodes / query_spec / expected_answer /
  expected_evidence). **Never passed to methods**; only the scorer reads it.

## Evaluation adapters
Routing via `evaluators/task_types.py`: memory_query -> Query-CVSR
(`query_cvsr.py`); graph types -> object-graph CVSR.

## Files
- `test_v2_public_inputs.jsonl` sha256 `8321ed3dddaff902277f565c5dfa30d8652a929b9fa10b45516d10ba4fee6c9c`
- `test_v2_gold.jsonl`         sha256 `01d4eb6903809f1fc6bed3259aa11bdf86198e76f9254e0c96b7d7cd0dadf306`

See `MANIFEST.sha256` for the authoritative set.

## Freeze state (per F-014)
- **Evaluator / method freeze**: PENDING — `experiments/v3/` is currently untracked
  (not committed). Per spec, `EVALUATOR_FREEZE_COMMIT` and `METHOD_FREEZE_COMMIT`
  must be recorded at HEAD once the evaluator and methods are committed.
- **Base HEAD**: `0055d5cbbe8a80ac836eabbf27b018ec43fceb13`
- **test_v2 freeze**: BLOCKED — round 2 of Annotator 2 review. Round-1 issues
  (P0-1..P0-4, P1-1..P1-3) and packet revisions (P1-4) applied; hash sync (P1-5)
  in progress. Still `pending`; gate stays `BLOCKED_ANNOTATION_REVIEW` until the
  second review approves and the freeze commits are recorded.