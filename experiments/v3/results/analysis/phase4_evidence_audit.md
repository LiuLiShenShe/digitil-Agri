# Phase 4 — Evidence Audit (2026-08-23)

**Auditor scope**: recompute every headline number from raw per-run JSONL records;
separate three judgments (CODE_GATE / OPTIMIZATION_GUARD / PAPER_READINESS); correct
Phase-3 reporting errors. No benchmark, gold, scorer, gate-threshold, budget, or frozen
result was modified. All numbers below are recomputed from raw records at commit
`89757530855e2334cad4f816e45c65c797f2666a`.

---

## 1. Recomputed main-gate metrics (v3_runs.jsonl, 500 runs, raw per-run costs)

| method | n | CVSR | pass@5¹ | ObjF1 | CritR | RelF1 | BindF1 | Fatal | EvidP | Replay | cost (exact) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| KAFarmTwin-TypedRepair | 100 | 0.610 | 0.700 | 0.800 | 1.000 | 0.534 | 0.5292 | 0.000 | 1.000 | 1.000 | $0.0003401 |
| SingleAgent-AllTools | 100 | 0.360 | 0.500 | 0.685 | 0.900 | 0.391 | 0.1267 | 0.320 | 0.900 | 0.607 | $0.0002747 |
| GenericMultiAgent | 100 | 0.010 | 0.050 | 0.461 | 0.800 | 0.200 | 0.0433 | 0.310 | 0.790 | 0.000 | $0.0010974 |
| GenericRepair-AllTools | 100 | 0.060 | 0.100 | 0.457 | 0.800 | 0.245 | 0.0425 | 0.070 | 1.000 | 1.000 | $0.0004391 |
| ReAct-AllTools | 100 | 0.000 | 0.000 | 0.000 | 0.400 | 0.000 | 0.0000 | 0.000 | 0.000 | 0.000 | $0.0026311 |

¹ pass@k recomputed with the repository's own `pass_k` grouping convention (`metrics.py:304`,
consecutive i//k runs per task-method): KF pass@1=0.610 pass@3=0.735 pass@5=0.700; SA
pass@1=0.360 pass@3=0.500 pass@5=0.500.

### Paired comparison (KF − SingleAgent), gate-authoritative estimator

- Point Δ CVSR = **+0.250** (+25pp over SA's 0.360)
- Paired bootstrap 95% CI = **[+0.090, +0.440]** (20 tasks, 10 000 bootstraps,
  recomputed via `run_sota_gate.paired_bootstrap_ci`, seed-matched to the formal run)
- pass@5: 0.700 vs 0.500 (strictly greater ✅)
- Fatal flips vs SA: KF 0/100 fatal runs vs SA 32/100

## 2. Cost ratio — CORRECTED (rounding artifact in Phase-3 report)

`evaluators/metrics.py:351` rounds `cost_mean` to **4 decimal places**, so the summary
shows $0.0003 for both methods and the Phase-3 report printed "≈1.0×". Recomputed from
raw unrounded per-run costs:

| quantity | value |
|---|---|
| KF exact mean cost/run | **$0.0003401** |
| SingleAgent exact mean cost/run | **$0.0002747** |
| **exact cost ratio (KF/SA)** | **1.238×** |

The "≈1.0×" claim was a rounding artifact and is **retracted**. The honest statement is:
cost ratio ≈ **1.24× ≤ 1.5× bar** → the cost-ratio condition still PASSES, but the margin
is ~0.26×, not parity. All documents have been corrected.

## 3. CVSR regression Phase 2 → Phase 3 — CORRECTED (guard violated)

- Phase-2 frozen KF CVSR = 0.650 (`v3_runs_phase2_frozen.jsonl`)
- Phase-3 optimized KF CVSR = 0.610 (`v3_runs.jsonl`)
- Regression = **−4.00 pp**, which is **> the 3 pp tolerance** of the original Phase-3
  optimization guard ("CVSR drop < 3pp"). The Phase-3 report's phrase "within the 3 pp
  quality tolerance" was wrong and has been removed.
- Note: the gate code itself contains **no** regression-vs-previous-phase condition —
  the guard exists only in the Phase-3 task spec, not in `run_sota_gate.py`. Hence:

## 4. Three separate judgments

### 4.1 CODE_GATE: **PASS**

Judged strictly by conditions implemented in `run_sota_gate.py` at HEAD
(`KAFARMTWIN_CVSR_MIN_DELTA_PP=0.03`, CI lb > 0, pass@5 strictly greater,
critical_recall ≥0.95, fatal ≤0.01 AND ≤ baseline, evidence_precision ≥0.95,
replay ≥0.95, cost_ratio ≤1.5×):

| condition | value | verdict |
|---|---|---|
| paired Δ + CI | +0.250, CI [+0.09,+0.44] | PASS |
| pass@5 | 0.70 > 0.50 | PASS |
| critical_recall | 1.000 | PASS |
| fatal_rate | 0.000 | PASS |
| evidence_precision | 1.000 | PASS |
| replay_success | 1.000 | PASS |
| cost_ratio (exact) | **1.238 ≤ 1.5** | PASS |

CODE_GATE = PASS on exact (unrounded) numbers — no condition depends on the rounding.

### 4.2 OPTIMIZATION_GUARD: **FAIL**

The original Phase-3 spec requires optimized CVSR drop < 3pp relative to the Phase-2
frozen run: actual drop = 0.650→0.610 = **4.0 pp > 3 pp**. The optimization achieved its
cost target (2.22×→1.24×) but exceeded the quality-retention tolerance. This is a real
guard violation and must not be papered over: the paper reports the optimized run with
its −4pp regression stated explicitly.

### 4.3 PAPER_READINESS: **CONDITIONAL PASS** (after Phase-4 corrections)

Ready once the corrections in this audit are applied everywhere (they now are):
(a) cost ratio reported as 1.24×, never ≈1.0×; (b) −4pp CVSR regression reported as a
guard violation with the trade-off stated; (c) ablation framing follows §5 below;
(d) test_v2 described only as a frozen evaluation benchmark developed against during
the engineering loop, never as hidden/blind/independent; (e) D2 described as
"LLM selects typed repair operators; a knowledge-constrained deterministic executor
instantiates and applies admissible parameters".

## 5. Ablation audit (n=100 per variant, independent runs)

Recomputed from raw records:

| variant | n | CVSR | ObjF1 | BindF1 | CritR | Fatal | cost (exact) |
|---|---|---|---|---|---|---|---|
| full | 100 | 0.550 | 0.796 | 0.5292 | 1.000 | 0.000 | $0.0003314 |
| A1 no compiler | 100 | 0.370 | 0.721 | 0.3292 | 0.950 | 0.010 | $0.0004431 |
| A2 no typed repair | 100 | 0.580 | 0.798 | 0.3292 | 1.000 | **0.220** | $0.0001797 |
| A3 no ontology | 100 | 0.530 | 0.796 | 0.4525 | 1.000 | 0.000 | $0.0005162 |

Required honesty points:

1. **A2 CVSR (0.580) is HIGHER than full (0.550).** Typed repair must NOT be credited
   with any CVSR gain — there is none. Its contribution is safety/recoverability:
   removing repair makes the repair-category fatal rate jump 0→**0.220** overall, and
   **TN31–34 flip to 5/5 fatal in every A2 run (20/20 pairs)** while full is 0/5 on all
   four tasks (paired flips: A2-fatal/full-clean = 22, A2-clean/full-fatal = 0).
2. **full (ablation) vs main-gate KAFarmTwin are INDEPENDENT stochastic runs**
   (0.550 vs 0.610). They share code/benchmark/budget but not random draws; they must
   never be presented as a paired comparison. The gap is LLM sampling variance under
   temperature 0.2.
3. Knowledge compiler: decisive on asset category (TN11 full/A1 CVSR 1.00/0.00;
   TN11 ObjF1 0.996→0.655). A1 also degrades CritR to 0.950 and introduces fatal=0.01.
4. Ontology: bind F1 0.4525 (A3) → 0.5292 (full); no fatal cost.

## 6. Binding failure status (unchanged by this audit; verified)

- TN21/TN24: method-side fix validated live (BindF1 0.333/0.25 → 1.0), preserved.
- TN22/TN23: blocked by FROZEN evaluator `_UNIT_CANONICAL` alias gaps (`°C`, `klux`,
  `light_intensity`) — benchmark/evaluator contract limitation, not method-prefectible
  under the freeze.

## 7. Corrections applied by this audit

| location | before | after |
|---|---|---|
| phase3_final_report.md §3 / STATUS.md | "≈1.0× ($0.0003/$0.0003)" | exact ratio **1.24×** (KF $0.0003401 / SA $0.0002747) |
| phase3_final_report.md §3 / STATUS.md | "−4pp, within the 3 pp quality tolerance" | "**−4.0 pp > 3 pp tolerance → OPTIMIZATION_GUARD FAIL**" |
| phase3_final_report.md §4 | asset ObjF1 "0.701→0.800" | TN11 ObjF1 **0.655 (A1) → 0.996 (full)** (n=5 each) |
| phase3_final_report.md §4 / STATUS.md | implied CVSR credit for typed repair | explicit "A2 ≥ full on CVSR; contribution is fatal elimination/safety" |
| all docs | SOTA-adjacent phrasing | gate logic only; no SOTA claim anywhere |

## 8. Provenance & tests

- `provenance/phase3_manifest.yaml` created: git HEAD, environment, SHA-256 of
  evaluator/method/harness/scripts/raw-results files, model disclosure (served catalog
  id only — immutable model snapshot NOT exposed by provider: marked uncertain),
  experiment design, exact commands, fresh test result.
- Tests re-run at current HEAD on 2026-08-23: **101 passed** (`pytest experiments/v3/tests/ -q`,
  57.96 s) — freshly executed, not inherited.
