# test_v2 — Changelog

## v2.0-rev2 (2026-08-07) — Annotator 2 review round 2 fixes applied
- **P0-1 Gold leakage**: `test_v2_public_inputs.jsonl` now uses a **whitelist**
  (task_id/task_type/difficulty/prompt/policy_ref/initial_state). No
  required_nodes/edges/bindings/critical/equivalence/fatal/forbidden/variants
  leak to methods. New `test_benchmark_integrity.py::test_public_inputs_have_no_gold_fields`.
- **P0-2 Schema**: `schema.json` rewritten (type-aware). task_id slug pattern
  `^TN[0-9]{2}-v2-(scene|asset|bind|repair|mem)$`; `review_status` unified to
  `{pending, needs_revision, approved, rejected}`; null-able query/answer
  blocks; `allowed_variants` object form; `equivalence_groups` object form;
  `goal_state`/`required_events`/`event_bind` typed. **96 → 0 schema errors.**
- **P0-3 asset bindings**: focus→`focus_asset`, bg→`bg_asset`, light device→
  placeholder `asset_job`. Referential-integrity test added.
- **P0-4 repair disjunctive**: dedicated `rule_repair` adapter accepts
  `replace_asset` OR `set_placeholder`; retained-wrong-binding and no-op both
  fail. Registered in `register_adapters.py`.
- **P1-1 equivalence_groups**: object-structured `{group_id, match_on, members,
  expected_count}`; `node_match` supports both object + legacy string groups.
- **P1-2 data_binding**: initial_state pre-exists the bound objects
  (root/row/sensors/plant) + explicit `relations`.
- **P1-3 memory gold**: ≥3 records/day (real daily_mean), interference records,
  trend with `net_change_direction` + `shape`, TN43 temperature threshold=35°C;
  `query_cvsr` grades `daily_means` + `trend`.
- **P1-4 packets**: T031 control_bind (no ws asset binding), T032 `event_bind`,
  T033 disjunctive repair, T034 enhanced memory gold, T035 referential-clean.
- **P1-5 hash sync**: MANIFEST/DATASHEET/benchmark_manifest re-sealed.
- **Status**: REVISED — re-submitted to Annotator 2 for a second review. All
  tasks still `pending`. Freeze gate remains `BLOCKED_ANNOTATION_REVIEW`.

## v2.0-rev1 (2026-08-05) — Annotator 2 review round 1
- **All 20 tasks revised** per Annotator 2 review (0/20 approved as-is initially).
- **scene_construction** (TN01-TN04): added WeatherStation=1 + Camera=2 to
  required_nodes, containment edges, camera observes target, equivalence groups.
- **asset_routing** (TN11-TN14): fixed prompt wording (N focus plants), added
  missing supplemental-light Device + placeholder asset_job + fatal constraint.
- **data_binding** (TN21-TN24): explicit prompt (crop, 1 key plant, trait,
  timestamp), sensor_bind timestamp, equivalence groups.
- **rule_repair** (TN31-TN34): target asset class device-derived
  (Pump/Irrigation→irrigation, Camera→camera), corrected asset in
  required_nodes, both replace_asset + set_placeholder variants.
- **memory_query** (TN41-TN44): explicit trend field, grounded row relations,
  TN43 temperature (no thermo alias), single canonical Oracle
  (expected_outcome.answer == expected_answer).
- **Status**: REVISED — re-submitted to Annotator 2 for a second review. All
  tasks still `PENDING_HUMAN_REVIEW`. Freeze gate remains `BLOCKED_ANNOTATION_REVIEW`.

## v2.0-candidate (2026-08-05)
- **Created** test_v2 as the frozen candidate replacing invalidated test_v1.
- **Rebuild**: 5 task types × 4 = 20 tasks (was 9 test_v1 tasks with a
  Prompt-Gold contradiction in the 4 memory_query ones).
- **Schema**: unified `task_type`-aware Gold Schema v2 (`benchmark/schema.json`).
- **Memory query**: switched from scene-count gold to Query-Gold
  (`query_spec`/`expected_answer`/`expected_evidence`), where target objects and
  data pre-exist in `initial_state` and gold is Oracle-derived.
- **Evaluators**: added Query-CVSR (`query_cvsr.py`), task-type dispatch
  (`task_types.py`, `register_adapters.py`), static Gold audit
  (`gold_audit.py`).
- **Status**: CANDIDATE. Passes static Gold audit (0 errors); blocked on human
  approval (all `PENDING_HUMAN_REVIEW`). Frozen after approval.

## v1 (superseded)
- Invalidated: memory_query T27-T30 gold demanded scene construction for
  retrieval prompts -> CVSR structurally 0. Archived to
  `benchmark/archive/test_v1_invalid/`.