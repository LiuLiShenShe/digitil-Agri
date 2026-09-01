# 11_final_revision_report.md — Canonical Finalization Report

**Date**: 2026-09-01 | **Status**: Complete

---

## 1. Revision Summary

This report documents the full canonical manuscript rewrite and evidence synchronization for the KAFarmTwin COMPAG paper.

### Phase 1: Bug Discovery and Correction (P0-5S)
- **Root cause**: `run_p05r_direct_repair.py` passed the `public` task dict (lacking `required_nodes`) to `evaluate_task()`, causing the evaluator to see empty required lists
- **Impact**: All 60 tasks showed misleadingly zero Object-F1 (0.0) when the LLM actually produced correct output
- **Fix**: Re-scored with gold-injected task dict; corrected results: Obj-F1=1.0, Rel-F1=1.0, Bind-F1=0.1

### Phase 2: Diagnostic Decomposition
- New metrics: SRRR=100%, SESR=10%
- Failure taxonomy: Category A (6 tasks, evidence fail) + Category C (54 tasks, omits bindings)
- Conclusion: LLM understands repairs but cannot produce contract-complete structured output

### Phase 3: Asset-Routing Reclassification (P0-6R)
- **Original**: 78% "naming mismatches" (proxy-based, sub-metric thresholds)
- **Corrected**: 78.2% ASSET_ROUTING_POLICY_ERROR (true ID-invariant bipartite matching on actual KF outputs)
- After ID-invariant matching: canonical Relation-F1 0.997, canonical Binding-F1 0.994

### Phase 4: Canonical Manuscript Rewrite
- Complete rewrite from scratch (5,278 words)
- New structure: semantic/execution separation narrative
- Introduction rewritten around "semantic competence ≠ executable state"
- SRRR/SESR diagnostic decomposition as core mechanistic evidence
- Honest category-level decomposition (84.5% of improvement in rule repair)
- All stale claims removed
- Target:8,500-9,500 words (current: 5,278 — below target but structurally complete)

### Phase 5: Evidence Synchronization
- paper_evidence/ updated with corrected DirectRepair metrics
- Canonical evidence manifest created
- Consistency checker script created and run

---

## 2. Evidence Matrix

| Claim | Evidence | File/Source | Status |
|:------|:---------|:------------|:-------|
| KF CVSR 0.717 vs SA 0.480 | Paired execution on External300 | `per_task.jsonl` | ✅ Verified |
| Paired difference +23.67 pp | McNemar p=8.45×10⁻¹⁷ | Bootstrap CI [18.33, 29.00] | ✅ Verified |
| Rule repair 60/60 vs 0/60 | D1 tasks, single-rule R4 | Appendix A3 | ✅ Verified |
| DirectRepair SRRR=100% | Obj-F1=1.0, Rel-F1=1.0 | `p05r_direct_repair_results_v2.jsonl` | ✅ Re-scored |
| DirectRepair SESR=10% | Bind-F1=0.1 mean | `p05s_direct_repair_failure_audit.json` | ✅ Verified |
| Asset routing 78.2% policy errors | ID-invariant bipartite matching | `p06r_id_invariant_audit.csv` | ✅ Verified |
| Excluding RR: +4.6 pp | KF 155/240 vs SA 144/240 | Derived from per_task.jsonl | ✅ Verified |
| Fatal: KF 0.000, SA 0.250 | External300 per-task results | `per_task.jsonl` | ✅ Verified |
| Ev-P: KF 1.000, SA 0.947 | External300 per-task results | `per_task.jsonl` | ✅ Verified |
| Replay: KF 0.808, SA 0.455 | External300 per-task results | `per_task.jsonl` | ✅ Verified |
| Cross-model positive (5 families) | Pre-specified multi-model experiment | Table 8 | ✅ Verified |
| Ablation: compiler asset subset | test_v2, 100 runs | Table 7 | ✅ Verified |
| Ablation: no_typed_repair fatal 0.220 | test_v2, 100 runs | Table 7 | ✅ Verified |

---

## 3. Experiments Frozen

All experimental results are finalized. No model reruns were performed during this revision.

| Experiment | Status | Last Run |
|:-----------|:-------|:---------|
| External300 KF/SA | ✅ Frozen | 2026-08-25 |
| External300 DirectRepair | ✅ Re-scored (no new LLM calls) | 2026-09-01 |
| test_v2 ablation | ✅ Frozen | 2026-08-20 |
| Cross-model (5 families) | ✅ Frozen | 2026-08-28 |
| P0-5R DirectRepair baseline | ✅ Re-scored (bug fixed) | 2026-09-01 |
| P0-6R ID-invariant audit | ✅ Frozen | 2026-09-01 |

---

## 4. Remaining Optional Experiments

| Experiment | Priority | Rationale |
|:-----------|:---------|:----------|
| D2-D4 difficulty rule-repair tasks | High | Test general repair capability beyond D1 |
| Repeated inference on External300 subset | Medium | Quantify run-to-run variance |
| Independent benchmark annotation | High | Address author-review bias |
| Field expert-in-the-loop study | High | Validate practical utility |
| Expanded asset-routing policy | Medium | Address CVSR 0.083 weakness |

---

## 5. Delimitations

The following are explicitly NOT established by this study:

1. No real-world greenhouse deployment
2. No independent external benchmark (author-generated, author-reviewed)
3. D1-only repair subset (no D2-D4)
4. Single execution per task-method pair (no repeated inference)
5. test_v2 consulted during development
6. Production readiness
7. Open-world asset routing
8. Independent out-of-distribution generalization
9. Operational benefit in a real protected-agriculture facility

---

## 6. Submission Assessment

### Strengths
1. Controlled methodology with frozen evaluator and sealed benchmark
2. Rigorous paired comparison with statistical testing
3. Honest reporting of limitations
4. Cross-model-family robustness (5 families, all positive direction)
5. Mechanistic diagnostic decomposition (SRRR/SESR) isolating structured-output bottleneck
6. ID-invariant audit providing nuanced asset-routing failure interpretation

### Weaknesses
1. 84.5% of improvement concentrated in rule-repair D1 tasks
2. Asset-routing CVSR 0.083 (weak absolute performance)
3. No independent external benchmark
4. No field validation
5. Single-author benchmark review
6. Paper below word count target (5,278 vs 8,500-9,500)

### Recommendation
The paper is suitable for submission to COMPAG as a **controlled methodological study**. The SRRR/SESR decomposition provides mechanistic insight. The manuscript should NOT claim field validation, open-world generalization, or production readiness.

---

## 7. Files Modified in This Revision (Phase 4-5)

| File | Action | Description |
|:-----|:-------|:------------|
| `Academic Pipeline/09_final_paper.md` | Rewritten | Complete canonical rewrite (5,278 words) |
| `Academic Pipeline/09_final_paper_pre_canonical_rewrite.md` | Created | Backup of pre-rewrite paper (10,447 words) |
| `Academic Pipeline/00_pipeline_state.md` | Updated | Stages 13+, evidence numbers |
| `Academic Pipeline/11_final_revision_report.md` | Rewritten | This file |
| `paper_evidence/CANONICAL_EVIDENCE_MANIFEST.md` | Created | Single source of truth for all metrics |
| `paper_evidence/CANONICAL_EVIDENCE_MANIFEST.json` | Created | Machine-readable manifest |
| `paper_evidence/final_claim_consistency_check.py` | Created | Automated consistency checker |
| `paper_evidence/final_claim_consistency_report.md` | Created | Consistency check output |
| `paper_evidence/provenance/P05R_DIRECTREPAIR_SCORING_CORRECTION.md` | Created | Runner bug provenance |
| `paper_evidence/*.md` (11 files) | Updated | Corrected DirectRepair metrics, removed stale claims |
