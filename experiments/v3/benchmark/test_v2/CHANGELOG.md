# test_v2 — Changelog

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