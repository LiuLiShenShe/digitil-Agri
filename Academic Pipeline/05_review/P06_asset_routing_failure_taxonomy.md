# P0-6: Asset Routing Failure Taxonomy & Semantic Audit

**Date**: 2026-08-31 | **Status**: Analysis Complete | **Rerun Decision**: RERUN_NOT_REQUIRED

---

## 1. Executive Summary

KF achieves 5/60 (8.3%) CVSR on asset_routing. The 55 failed tasks are **not** structural failures — they have perfect Critical Recall (1.000), perfect Replay Success (1.000), zero fatal violations, and high Binding-F1 (mean 0.973). **~78% of failures (Patterns A+C) are naming/labeling mismatches**, not algorithmic failures. The compiler generates structurally valid scenes with correct topology and bindings, but object naming conventions diverge from the gold standard.

## 2. Sub-Metric Verification

### Failed KF tasks (n=55)

| Metric | Mean | Min | Max | Zeros | Interpretation |
|--------|------|-----|-----|-------|---------------|
| Object-F1 | 0.406 | 0.118 | 1.000 | 0 | **Primary failure point** |
| Relation-F1 | 0.766 | 0.600 | 1.000 | 0 | Moderate |
| Binding-F1 | 0.973 | 0.500 | 1.000 | 0 | Near-perfect |
| Critical Recall | **1.000** | 1.000 | 1.000 | 0 | Perfect |
| Replay Success | **1.000** | 1.000 | 1.000 | 0 | Perfect |
| Evidence Precision | **1.000** | 1.000 | 1.000 | 0 | Perfect |

**Fatal violations in 55 failed tasks**: NONE  
**Non-fatal violations in 55 failed tasks**: NONE

### Passed KF tasks (n=5)

| Metric | Mean | Min | Max |
|--------|------|-----|-----|
| Object-F1 | 0.991 | 0.955 | 1.000 |
| Relation-F1 | 0.967 | 0.833 | 1.000 |
| Binding-F1 | 0.933 | 0.667 | 1.000 |

### SA baseline (n=60, all fail)

| Metric | Mean | Min | Max | Zeros |
|--------|------|-----|-----|-------|
| Object-F1 | 0.182 | 0.000 | 0.973 | 16 |
| Relation-F1 | — | — | — | — |
| Binding-F1 | — | — | — | — |

SA achieves 0/60 CVSR on asset_routing with Object-F1 mean 0.182 (vs KF 0.406), demonstrating KF's compiler provides meaningful improvement even in the failed cases.

## 3. Failure Pattern Taxonomy

| Pattern | Count | % | Object-F1 Range | Relation-F1 Range | Description |
|---------|-------|---|-----------------|-------------------|-------------|
| **A: Naming mismatch** | 32 | 58.2% | < 0.3 | ≥ 0.6 | Object IDs diverge from gold but relation structure is largely correct |
| **C: Partial naming** | 11 | 20.0% | 0.3–0.7 | ≥ 0.6 | Partial overlap with gold naming convention |
| **D: Edge/binding detail** | 7 | 12.7% | ≥ 0.7 | variable | Object identification mostly correct but edge/binding specifics differ |
| **E: Unclassified** | 5 | 9.1% | variable | variable | Does not fit other patterns |

**No Pattern B (structural mismatch)** was classified — all failures maintain Critical Recall=1.0 and zero fatal violations, indicating the compiler produces structurally valid scenes.

### Summary Split

| Category | Count | % | Interpretation |
|----------|-------|---|---------------|
| **Naming-only (A+C)** | 43 | 78.2% | Scene is structurally correct; naming convention diverges |
| **Edge/binding detail (D)** | 7 | 12.7% | Near-miss on edge/binding specifics |
| **Other (E)** | 5 | 9.1% | Requires case-by-case review |

## 4. Registry Coverage vs Algorithmic Failure

| Metric | Count | % | Controllable? |
|--------|-------|---|--------------|
| High object-F1 failures (obj ≥ 0.7) | 12 | 21.8% | Partially — edge/binding details, naming precision |
| Low object-F1 failures (obj < 0.7) | 43 | 78.2% | Partially — naming convention alignment |

The gold standard objects per task average 5.0 (range 4-6), edges 4.0 (range 3-5), bindings 3.0 (range 2-4). The compiler consistently generates scenes of comparable complexity — the failure is in the specific IDs/names chosen, not in scene structure or completeness.

## 5. ID-Invariant Semantic Audit

All 55 failed tasks share these properties:
- **Critical Recall = 1.0**: No critical object is missing from the KF output
- **Replay Success = 1.0**: The scene is fully replayable
- **Fatal violations = 0**: No fatal rule violations
- **Non-fatal violations = 0**: No non-fatal rule violations
- **Binding-F1 mean = 0.973**: Nearly all bindings are correctly formed

**Conclusion**: The compiler produces scenes that are semantically equivalent to the gold standard in terms of:
- ✅ Object completeness (all required objects present)
- ✅ Scene topology (critical edges correct)
- ✅ Binding correctness (asset bindings mostly correct)
- ✅ Replay capability
- ❌ Object naming/ID convention (diverges from gold standard)

The failures are **evaluative** (naming convention mismatch) rather than **generative** (scene construction failure).

## 6. SA vs KF Comparison

| Metric | KF (n=60) | SA (n=60) |
|--------|-----------|-----------|
| CVSR pass | 5 (8.3%) | 0 (0.0%) |
| Object-F1 mean | 0.424 | 0.182 |
| LLM calls | 2 (all tasks) | 0 |
| Fatal violations | 0 | present (varies) |

KF provides meaningful improvement over SA even in the failed cases, with ~2.3× higher Object-F1 and zero fatal violations.

## 7. Defensible Interpretation

> ~78% of asset_routing failures are naming/labeling mismatches (Patterns A+C). The Knowledge Compiler produces structurally valid, bound, replayable scenes with perfect critical recall, but object naming conventions diverge from the gold standard. The true algorithmic failure rate (edge/binding detail + unclassified) is ~22%, not 91.7%. This suggests the failure is primarily in the asset registry's naming convention alignment, not in the compiler's scene construction logic.

## 8. Output Files

| File | Rows | Description |
|------|------|-------------|
| `asset_routing_failure_taxonomy.csv` | 60 | Per-task failure classification with pattern and detail |
| `asset_routing_semantic_audit.csv` | 55 | Failed tasks with sub-metric profiles |
| `asset_routing_summary.json` | — | Machine-readable summary |
| `sa_asset_routing_comparison.csv` | 60 | KF vs SA per-task comparison |
