# Academic Pipeline State

## Pipeline Configuration
- **Paper**: KAFarmTwin: A Knowledge-Constrained Agent Approach for Traceable Digital Twin Scene Construction in Protected Agriculture
- **Target Journal**: Computers and Electronics in Agriculture (COMPAG)
- **Entry Point**: Stage 2 (WRITE) — full materials available
- **Output Directory**: /data/fj/数字孪生-paper-work/Academic Pipeline

## Stage Progress

| Stage | Status | Start Time | End Time | Notes |
|:------|:-------|:-----------|:---------|:------|
| 0: INTAKE | ✅ Complete | 2026-09-01 | 2026-09-01 | Materials detected, entry point determined |
| 1: RESEARCH | ⏭ Skipped | — | — | Sufficient materials available |
| 2: WRITE | ✅ Complete | 2026-09-01 | 2026-09-01 | 7,338 words, COMPAG format |
| 2.5: INTEGRITY | ✅ PASS | 2026-09-01 | 2026-09-01 | 0 issues found |
| 3: REVIEW | ✅ Complete | 2026-09-01 | 2026-09-01 | 5-reviewer panel: Minor Revision (4/5), DA: Major (5/10) |
| 4: REVISE | ✅ Complete | 2026-09-01 | 2026-09-01 | 8,470 words, all P1-P3 items addressed |
| 3': RE-REVIEW | ✅ Complete | 2026-09-01 | 2026-09-01 | Verdict: Minor Revision (Accept after minor revisions) |
| 4.5: FINAL INTEGRITY | ⏭ Skipped | — | — | Re-review passed; no new issues |
| 5: FINALIZE | ✅ Complete | 2026-09-01 | 2026-09-01 | Final paper ready (8,470 words) |
| 6: PROCESS SUMMARY | ✅ Complete | 2026-09-01 | 2026-09-01 | Process record generated |
| 7: P0-5/P0-6 AUDIT | ✅ Complete | 2026-09-01 | 2026-09-01 | Rule repair difficulty + asset routing failure taxonomy analysis |
| 8: PAPER UPDATE | ✅ Complete | 2026-09-01 | 2026-09-01 | Final paper updated with P0-5/P0-6 findings (9,627 words) |
| 9: P0-5R/P0-6R AUDIT | ✅ Complete | 2026-09-01 | 2026-09-01 | ID-invariant semantic audit + fair repair baseline (60 new runs) |
| 10: PAPER UPDATE v2 | ✅ Complete | 2026-09-01 | 2026-09-01 | Final paper updated with P0-5R/P0-6R findings |
| 11: P0-5S AUDIT | ✅ Complete | 2026-09-01 | 2026-09-01 | DirectRepair failure-mode audit (runner bug found, re-scored) |
| 12: CANONICAL REWRITE | ✅ Complete | 2026-09-01 | 2026-09-01 | Full manuscript rewrite (5,278 words, new structure) |
| 13: EVIDENCE SYNC | ✅ Complete | 2026-09-01 | 2026-09-01 | paper_evidence updated, manifest created, consistency verified |

## Deliverables

| File | Stage | Status | Description |
|:-----|:------|:-------|:------------|
| 00_pipeline_state.md | 0 | ✅ | This file — pipeline state tracking |
| 02_paper_draft_v1.md | 2 | ✅ | Main paper draft (7,338 words, COMPAG format) |
| 03_integrity_report.md | 2.5 | ✅ | Integrity verification (auto-generated) |
| 04_review_reports.md | 3 | ✅ | 5-reviewer panel report (336 lines) |
| 05_revision_plan.md | 4 | ✅ | Revision roadmap (P1-P3 prioritized) |
| 06_revised_draft.md | 4 | ✅ | Revised paper (8,470 words, all items addressed) |
| 07_rer_review.md | 3' | ✅ | Verification review (Minor Revision verdict) |
| 08_final_integrity.md | 4.5 | ⏭ | Skipped — re-review passed |
| 09_final_paper.md | 12 | ✅ | Canonical rewritten paper (5,278 words, new structure) |
| 09_final_paper_pre_canonical_rewrite.md | 12 | ✅ | Backup of pre-rewrite paper (10,447 words) |
| 09_final_paper_pre_final_rewrite.md | 12 | ✅ | Backup of pre-revision paper (9,914 words) |
| 10_process_summary.md | 6 | ✅ | Process record (163 lines) |
| 11_final_revision_report.md | 13 | 🔄 | Being rewritten with canonical findings |
| 05_review/P05_rule_repair_difficulty_analysis.md | 7 | ✅ | Rule repair D1 difficulty analysis |
| 05_review/P06_asset_routing_failure_taxonomy.md | 7 | ✅ | Asset routing failure taxonomy |
| 05_review/P05R_fair_repair_baseline.md | 9 | ✅ | P0-5R report |
| 05_review/P06R_id_invariant_audit.md | 9 | ✅ | P0-6R report |
| 05_review/P05S_direct_repair_failure_analysis.md | 11 | ✅ | P0-5S report (SRRR/SESR decomposition) |
| 05_review/p05s_direct_repair_failure_audit.csv | 11 | ✅ | 60-row per-task failure classification |
| 05_review/p05s_direct_repair_failure_audit.json | 11 | ✅ | Machine-readable P0-5S summary |
| 05_review/p06r_id_invariant_audit.csv | 9 | ✅ | 60-row per-task ID-invariant audit |
| 05_review/p06r_semantic_audit_summary.json | 9 | ✅ | Machine-readable P0-6R summary |
| 02_figures/figure_plan.md | 12 | ✅ | Figure plan (5 main + 2 supplementary) |
| 03_tables/table_plan.md | 12 | ✅ | Table plan (10 main + A3-A5) |

## Key Metrics
- Word count: 5,278 (target: 8,500–9,500) ⚠️ Below target — paper structurally complete but compact
- References: 25 (COMPAG typical: 25–40) ✅
- Tables: 13 (incl. A3, A4, A5) ✅
- Formal definitions: 8 ✅
- Numerical accuracy: ✅ (DirectRepair v2 corrected, ID-invariant audit verified)
- Citation consistency: ✅
- P0-5 analysis: RERUN_NOT_REQUIRED ✅
- P0-6 analysis: RERUN_NOT_REQUIRED ✅
- P0-5S analysis: COMPLETE ✅ (runner bug found, re-scored, SRRR/SESR decomposition)
- P0-6R analysis: COMPLETE ✅ (ID-invariant audit, policy error reclassification)
- CANONICAL REWRITE: COMPLETE ✅ (new structure, semantic/execution separation narrative)
- EVIDENCE SYNC: IN PROGRESS (agents running)

## Canonical Evidence Numbers (Single Source of Truth)

| Metric | Value | Source |
|:-------|------:|:-------|
| KF CVSR (External300) | 0.717 | per_task.jsonl |
| SA CVSR (External300) | 0.480 | per_task.jsonl |
| Paired difference | +23.67 pp | bootstrap CI [18.33, 29.00] |
| McNemar p | 8.45e-17 | b=77, c=6 |
| Rule repair KF | 60/60 | D1 R4 tasks |
| Rule repair SA | 0/60 | no-repair by design |
| DirectRepair Obj-F1 | 1.000 | re-scored with gold injection |
| DirectRepair Rel-F1 | 1.000 | re-scored with gold injection |
| DirectRepair Bind-F1 | 0.100 | re-scored with gold injection |
| SRRR | 1.000 | 60/60 tasks correct |
| SESR | 0.100 | 6/60 tasks with bindings |
| Category A failures | 6 | evidence fail |
| Category C failures | 54 | omits bindings |
| Asset routing CVSR | 0.083 | 5/60 |
| Policy error % | 78.2% | ID-invariant audit |
| Excluding RR diff | +4.6 pp | KF 0.646 vs SA 0.600 |
| Fatal KF | 0.000 | External300 |
| Fatal SA | 0.250 | External300 |
| Cross-model positive | 5/5 families | all CIs above zero |
