# test_v2 — Annotator 2 Review Status (F-014 revision round)

**Review date**: 2026-08-05
**Annotator 2**: user
**Final status per reviewer recommendation**: `needs_revision` (NO batch approval)

## Verdict
The reviewer concluded 0/20 test_v2 tasks and 0/5 T031-T035 packets can be
approved as-is. The freeze gate remains **BLOCKED_ANNOTATION_REVIEW**.

Per the reviewer's recommended status writing, annotator_2 status fields are
recorded here (NOT stamped into task `review_status`, which stays
`PENDING_HUMAN_REVIEW` until a clean revision round):

```json
{"annotator_2_status": "needs_revision", "final_status": "pending_revision"}
```

## Systemic issues (accepted by annotator 1)
1. scene gold omits WeatherStation/Camera required by the prompt
2. asset gold omits the missing-lighting placeholder task
3. binding gold injects unobservable arbitrary details (crop/trait/timestamp)
4. repair gold does not encode the corrected asset/placeholder as a gradable goal
5. memory gold: trend not graded, associated_row lacks evidence, TN43
   temperature/thermo contradiction
6. expected_answer and expected_outcome are not one canonical Oracle output

## Revision plan (annotator 1)
- scene: add WS/Cam + containment edges + camera observes + equivalence groups
- asset: fix prompt wording + add placeholder/asset_job + fatal no-silent-omit
- binding: explicit prompt details OR constrained trait/time variants +
  equivalence matching
- repair: target asset class = irrigation/pump (crop-independent), encode
  corrected binding, add replace_asset + set_placeholder variants
- memory: explicit trend field, row relation evidence, fix TN43 alias,
  single canonical Oracle shape
- T031-T035: apply the same fixes to the review packets

## Next
After all revisions: regenerate test_v2, recompute SHA-256, re-run gold audit
(0 errors), then re-submit the SAME batch for a second independent review.

---

## Round 2 (2026-08-07) — revision resubmitted for review

Annotator 1 applied the round-2 P0/P1 fixes (all documented in CHANGELOG
v2.0-rev2):

- **P0-1** public inputs now whitelist-only (no gold leakage) — verified by
  `test_public_inputs_have_no_gold_fields`.
- **P0-2** schema rewritten: 96 → 0 errors; task_id slug pattern,
  `review_status` unified to `{pending, needs_revision, approved, rejected}`.
- **P0-3** asset bindings fixed to focus/bg assets + placeholder job.
- **P0-4** repair is disjunctive (`replace_asset` OR `set_placeholder`);
  retained-wrong-binding and no-op both fail.
- **P1-1** equivalence_groups object-structured.
- **P1-2** data_binding initial_state pre-exists bound objects + relations.
- **P1-3** memory gold enhanced: ≥3 records/day, interference records, trend
  `net_change_direction`+`shape`, TN43 threshold=35°C; query_cvsr grades them.
- **P1-4** T031-T035 packets revised (control_bind / event_bind / disjunctive
  repair / enhanced memory / referential-clean).
- **P1-5** MANIFEST / DATASHEET / benchmark_manifest hashes re-sealed.

Checks passed before resubmission:
- `pytest tests/` → **53 passed** (incl. new `test_benchmark_integrity.py`).
- `gold_audit test_v2_gold.jsonl` → **0 errors** (20 warnings = all still
  `pending`), now including JSON Schema validation.
- memory_query Oracle self-consistency → all 4 sealed tasks + T034 pass
  Query-CVSR (no Prompt-Gold contradiction).
- repair gold → both branches gradeable on TN31-TN34.

**Status**: `review_status` stays `pending`; gate remains
**BLOCKED_ANNOTATION_REVIEW** until Annotator 2 approves.
