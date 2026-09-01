# P0-5R + P0-6R Final Decision Report

**Date**: 2026-09-01

---

## Part D: Required Final Decisions

```
P0-5 ORIGINAL RESULT:
VALID_AS_MECHANISM_TEST

P0-5 FAIR_REPAIR_BASELINE:
COMPLETED (60 new DirectRepair executions; 0/60 CVSR)

P0-6 PROXY_TAXONOMY:
DESCRIPTIVE_ONLY (renamed to PROFILE_* labels)

P0-6 TRUE_SEMANTIC_AUDIT:
COMPLETED (RAW_OUTPUTS_FOUND; 60 KF asset_routing raw records loaded)
```

## Model Executions Performed

```
MODEL_EXECUTIONS_PERFORMED:
60 new SingleAgent-DirectRepair executions on rule_repair tasks only
No reruns of existing KF or SA results
No reruns of other 240 External300 tasks
```

## Files Modified

| File | Change |
|------|--------|
| 09_final_paper.md | Updated Abstract, 5.3, 5.4, 5.7, Threats#5, Conclusions, Appendix A4 |
| experiments/v3/methods/single_agent_direct_repair.py | NEW: DirectRepair method |
| experiments/v3/scripts/run_p05r_direct_repair.py | NEW: DirectRepair runner |
| experiments/v3/results/external300/p05r_direct_repair/ | NEW: 60 scored results + summary |

## Files Created

| File | Description |
|------|-------------|
| 05_review/P05R_fair_repair_baseline.md | P0-5R analysis report |
| 05_review/P06R_id_invariant_audit.md | P0-6R analysis report |
| 05_review/p06r_id_invariant_audit.csv | 60-row ID-invariant audit |
| 05_review/p06r_semantic_audit_summary.json | Audit summary |
| 05_review/analyze_id_invariant_audit.py | Audit script |

## Paper Claims Changed

1. **Abstract**: Added DirectRepair finding; corrected asset-routing claim
2. **Section 5.3**: Added Table 8b (3-column comparison)
3. **Section 5.7**: Replaced "naming mismatch" with "asset-routing policy error"
4. **Threats #5**: Updated with ID-invariant audit results
5. **Conclusions**: Added DirectRepair finding; corrected asset-routing description
6. **Appendix A4**: Replaced proxy taxonomy with ID-invariant audit results
