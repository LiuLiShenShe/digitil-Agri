# Table Plan — COMPAG KAFarmTwin Paper

## Main Paper Tables

| Table | Content | Section | Status |
|:------|:--------|:--------|:-------|
| Table 1 | Rule checkpoints R1-R10 | 3.7 | In paper |
| Table 2 | External300 task composition | 5.1 | In paper |
| Table 3 | Baseline method definitions | 5.1 | In paper |
| Table 4 | Main results on test_v2 | 5.2 | In paper |
| Table 5 | External300 main results (KF vs SA) | 5.3 | In paper |
| Table 6 | External300 CVSR by task category | 5.3 | In paper |
| Table 7 | Latency quantiles | 5.3 | In paper |
| Table 8 | SingleAgent rule findings in rule_repair | 5.4 | In paper |
| Table 8b | Fair repair comparison (KF vs DirectRepair vs NoRepair) | 5.4 | UPDATED this revision |
| Table 9 | Component ablation results | 5.5 | In paper |
| Table 10 | Cross-model-family robustness | 5.6 | In paper |

## Appendix Tables

| Table | Content | Section | Status |
|:------|:--------|:--------|:-------|
| Table A3 | Rule-repair task difficulty classification | A3 | In paper |
| Table A4 | Asset-routing ID-invariant semantic audit | A4 | In paper |
| Table A5 | DirectRepair failure-mode decomposition | A5 | NEW this revision |

## Key Changes in This Revision

### Table 8b (Updated)
- DirectRepair metrics corrected: Obj-F1 0.000 -> 1.000, Rel-F1 0.000 -> 1.000, Bind-F1 0.000 -> 0.100
- Added two new columns: SRRR (Semantic Repair Recognition Rate) and SESR (Structured Execution Success Rate)
- KAFarmTwin: SRRR=1.000, SESR=1.000
- DirectRepair: SRRR=1.000, SESR=0.100
- Interpretation: LLM understands repair (SRRR=100%) but cannot produce structured output (SESR=10%)

### Table A5 (New)
- DirectRepair failure taxonomy: 6 tasks Category A (evidence fail), 54 tasks Category C (omits bindings)
- Comparison with KAFarmTwin on all metrics
- Demonstrates semantic understanding vs structured execution gap
