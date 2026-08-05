# Regression Set — Re-annotated T27-T30 (F-011)

These are the four memory_query tasks from **test_v1** re-annotated to the v2
Query-Gold Schema (F-008). They are **NOT** a hidden test set — test_v2
supersedes them.

## Why they moved here

test_v1's T27-T30 gold required *scene construction* (20 Plant nodes) for
*retrieval* prompts — a Prompt-Gold contradiction (see
`benchmark/archive/test_v1_invalid/INVALIDATION_REPORT.md`). Under that gold,
CVSR was structurally 0 for every method (0/40), which is not evidence of
method failure.

## What changed

Each task now:
- declares `task_type: "memory_query"`
- provides a deterministic `initial_state` (objects/timeseries/events/
  daily_reports/traits) that the agent **queries over** — target objects exist
  up front, the agent does NOT re-build them
- `expected_answer` and `expected_evidence` are **Oracle-derived** from the
  fixture (deterministic), not hand-picked scene counts
- `forbidden_side_effects` include `create_scene`/`add_object`/`delete_object`/
  `modify_timeseries`/`invent_record`

## Validation

Self-consistency: feeding the Oracle answer through Query-CVSR passes on all 4
tasks (metric_recall=1.0, evidence_precision=1.0, aggregation=1.0). This
confirms the new gold is computable and internally consistent (unlike test_v1).

## Uses

- scoring/method regression testing
- memory-tool real-query verification
- paper case studies

| task | original | new query target | difficulty |
|------|----------|------------------|-----------|
| T27-reg | env summary (7d) | greenhouse_01 env telemetry | easy |
| T28-reg | plant P15 state | height/F2DMAS/stage/traits | medium |
| T29-reg | camera C02 coverage | observes + inspection + row3 | medium |
| T30-reg | daily production report | env/device/irrigation/alerts | easy |
