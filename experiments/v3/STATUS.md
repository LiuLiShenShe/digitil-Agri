# v3 SOTA Rebuild — STATUS

## Branch
`paper/knowledge-agent-experiments`

## Frozen A+ Protocol
**Overriding constraint:** on the frozen `test_v2` test set under
fair/reproducible/no-leak/same-tool/same-model/same-budget conditions, KAFarmTwin
must statistically significantly beat the strongest fair baseline:

  - Mean CVSR delta ≥ **3pp** over the strongest fair baseline
  - Paired-bootstrap 95% CI lower bound **> 0**
  - ALL absolute guardrails satisfied

**Until PASS: NO declaring success. NO modifying thresholds. NO deleting failed
tasks. NO gaming test set / gold / scorer / baseline budget.**

## Sealed Test Set — INTACT
`test_v2` frozen (20 tasks × 5 types), gold SHA `61a48f61...` matches sealed
`benchmark_manifest.json` after all scorer-side fixes.

## P0 Progress

| P0 | Description | Status |
|----|-------------|--------|
| P0-1 | Trace chain + forbid vacuous evidence | ✅ FIXED (+ residual honest clamp) |
| P0-2 | Repair chain (R4 asset_key, final_state bindings, R9/R10) | ✅ FIXED |
| P0-3 | Repair target states (TN31-34) | ✅ FIXED |
| P0-4 | Asset gold (TN11-14) | ✅ FIXED |
| P0-5 | Data binding (TN21-24) | ✅ FIXED |
| P0-6 | LLM call/token/latency/cost (single source) | ✅ FIXED |
| P0-7 | Run all 5 baselines+KF for real | ✅ DONE — 500-run formal test_v2 complete |
| P0-8 | SOTA Gate (bootstrap CI + per-task repeats + guardrails) | ✅ MECHANISM COMPLETE — **GATE FAIL (honest)** |

## SOTA GATE — FAIL (honest, 2026-08-18)
Formal 500-run frozen test_v2 (20 tasks × 5 methods × 5 runs, real DeepSeek-V4-Flash)
target_objectives. `SOTA_GATE=FAIL` (6 conditions):

| condition | result | bar | status |
|-----------|--------|-----|--------|
| paired bootstrap CI | point Δ=0.000, CI[0.00,0.00] | ≥3pp & lb>0 | ❌ |
| pass5 | 0.200 vs SingleAgent 0.200 | strictly > | ❌ |
| critical_recall | 0.600 | ≥0.95 | ❌ |
| fatal_rate | 0.220 | ≤0.01 | ❌ |
| evidence_precision | 1.000 | ≥0.95 | ✅ |
| replay_success | 0.800 | ≥0.95 | ❌ |
| cost_ratio | 1.75 | ≤1.5 | ❌ |

Evidence table (100 runs each):
```
method                  CVSR  pass5  ObjF1  CritR  RelF1  BindF1  Fatal  EvidP  Cost
KAFarmTwin-TypedRepair  0.200 0.200  0.712  0.600  0.315  0.000   0.220  1.000  $0.0007
SingleAgent-AllTools    0.200 0.200  0.692  0.600  0.300  0.000   0.450  0.990  $0.0004
GenericRepair-AllTools  0.010 0.050  0.489  0.450  0.257  0.010  0.080  1.000  $0.0004
GenericMultiAgent       0.000 0.000  0.499  0.600  0.205  0.000  0.350  0.840  $0.0009
ReAct-AllTools          0.000 0.000  0.000  0.400  0.000  0.000  0.000  0.000  $0.0024
```

## Deep root-cause (task-level bimodal distribution)
CVSR=0.20 is **entirely from the 4 memory_query tasks** (TN41-44, both SA & KF 5/5 —
deterministic). The **16 non-memory tasks (scene/asset/bind/repair ×4 each) score 0/5 for
every method** — a method-agnostic ceiling requiring exact graph-structure + binding-contract
satisfaction that neither method reaches. Hence paired CI is exactly [0.00, 0.00]:
20 tasks, 19 ties, 1 near-tie, no KF advantage anywhere.

## Honest position
- KAFarmTwin does **NOT** statistically significantly beat the best fair baseline (SingleAgent)
  on frozen test_v2. **GATE FAIL, reported truthfully.**
- No thresholds modified, no failed tasks deleted, no test-set/gold/scorer/baseline-budget gamed.
- Next: make methods genuinely solve the 16 non-memory graph+binding tasks (not just
  deterministic memory retrieval); KAFarmTwin's structural advantage, if real, will then
  surface as >3pp CVSR delta naturally.

## Test suite
**68/68 pass** (incl. honesty tests for broken-work-trace vacuous evidence).
