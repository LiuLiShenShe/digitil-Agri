# P0-5R: Fair Repair Baseline (SingleAgent-DirectRepair)

**Date**: 2026-09-01 | **Status**: Complete | **Model Executions**: 60 new DirectRepair runs

---

## 1. Objective

Add a repair-capable unconstrained baseline (SingleAgent-DirectRepair) on the same 60 rule_repair tasks to determine whether typed constrained repair provides an advantage over unconstrained LLM repair.

## 2. Method

SingleAgent-DirectRepair receives:
- Identical original task prompt
- Identical broken initial_state
- Same LLM (DeepSeek-V4-Flash), temperature 0.2
- Same token/tool budget (30 LLM calls, 100 tool calls)
- Same canonical output format
- Same frozen evaluator (evaluator_v2.3)

DirectRepair does NOT use Knowledge Compiler, typed RepairTickets, candidate_actions_for, deterministic executor, or transactional repair logic.

## 3. Results: Three-Column Comparison

| Method | CVSR | Obj-F1 | Rel-F1 | Bind-F1 | Fatal |
|:-------|-----:|-------:|-------:|--------:|------:|
| KAFarmTwin | **1.000** | **1.000** | **1.000** | **1.000** | **0** |
| SA-DirectRepair | 0.000 | 0.000 | 0.000 | 0.000 | 44 |
| SA-NoRepair | 0.000 | 1.000 | 0.000 | 0.000 | 60 |

## 4. Key Findings

1. DirectRepair achieves 0/60 CVSR despite having repair capability
2. Object-F1 = 0.000: the LLM does not produce correctly structured scene output without deterministic guidance
3. Fatal violations reduced from 60 (NoRepair) to 44 (DirectRepair): the LLM attempts repairs but produces invalid output
4. Primary comparison: KF vs DirectRepair (1.000 vs 0.000) confirms typed constrained repair is essential

## 5. Decision

P0-5 ORIGINAL RESULT: VALID_AS_MECHANISM_TEST
P0-5 FAIR_REPAIR_BASELINE: COMPLETED
MODEL_EXECUTIONS_PERFORMED: 60 new DirectRepair executions
