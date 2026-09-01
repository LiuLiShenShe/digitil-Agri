# P0-6R: ID-Invariant Asset-Routing Semantic Audit

**Date**: 2026-09-01 | **Status**: Complete | **Rerun Decision**: RERUN_NOT_REQUIRED

---

## 1. Executive Summary

The original P0-6 proxy-based classification (78% "naming mismatches") was based on sub-metric thresholds and NOT on actual scene comparison. The corrected ID-invariant audit loads actual KF scene outputs from raw run records and performs bipartite object matching independent of node identifiers.

**Corrected findings:**
- **78.2% ASSET_ROUTING_POLICY_ERROR** — compiler adds an unrequired device (fogger, fan, or light) while omitting a required node; all edges and bindings otherwise match
- **20.0% ID_ONLY_OR_CANONICALIZATION** — all semantic requirements matched; only node IDs differ
- **1.8% MIXED** — single case with multiple issues
- **0% structural mismatches** — no semantic object-type or relation failures

## 2. Raw Output Verification

**STOP CONDITION: RAW_OUTPUTS_FOUND**

KF scene outputs for all 60 asset_routing tasks exist in:
```
experiments/v3/results/external300/ext300_formal_20260825/raw/runs.jsonl
```

Each record contains: `nodes`, `edges`, `bindings`, `final_state`, `construction_path`, `trace`, etc.

No model rerun was required for the audit.

## 3. Methodology

For each of the 55 failed KF asset_routing tasks:

1. Load KF actual scene (nodes, edges, bindings) from raw runs
2. Load gold required scene (required_nodes, required_edges, required_bindings)
3. Perform bipartite node matching using:
   - Ontology type compatibility (weight 3.0)
   - Role match (weight 1.0)
   - Parent type context (weight 1.5)
   - Threshold: 0.25
4. Remap gold edges/bindings to matched KF node IDs
5. Perform bipartite edge matching (predicate + subject/object type, threshold 0.3)
6. Perform bipartite binding matching (type + asset_key + policy + metric, threshold 0.3)
7. Compute canonical precision/recall/F1 for objects, relations, bindings
8. Classify failure cause

## 4. Results

### Canonical vs Original Metrics (55 failed tasks)

| Metric | Original | Canonical (ID-invariant) | Improvement |
|--------|----------|-------------------------|-------------|
| Object-F1 | 0.406 | 0.810 | +0.404 |
| Relation-F1 | 0.766 | 0.997 | +0.231 |
| Binding-F1 | 0.973 | 0.994 | +0.021 |

### Failure Cause Distribution

| Cause | Count | % | Interpretation |
|-------|------:|--:|:---------------|
| ASSET_ROUTING_POLICY_ERROR | 43 | 78.2% | Extra device added, required node omitted |
| ID_ONLY_OR_CANONICALIZATION | 11 | 20.0% | All semantics match, only IDs differ |
| MIXED | 1 | 1.8% | Multiple independent issues |

### Asset-Routing Policy Error Pattern

All 43 policy errors follow the same template:
- KF adds one extra device (cycling through: fogger, circulation_fan, supplemental_light)
- Gold expects one node that KF omits (named `EAR*_missing_1`)
- All edges match after remapping
- All bindings match after remapping
- Asset keys match

This is a **deterministic policy insertion error** — the compiler's asset routing policy adds a default device that is not required by the task specification.

### ID-Only Failures

All 11 ID-only failures have:
- Canonical Object-F1 = 1.000 (perfect after ID normalization)
- All gold nodes matched
- All edges matched
- All bindings matched
- Only node identifiers differ (e.g., `sensor_1` vs `EAR001_sensor`)

## 5. Corrected Paper Claims

### Removed/Softened
- ❌ "78% are naming mismatches" → Corrected to "78.2% are asset-routing policy errors"
- ❌ "failures are evaluative rather than generative" → Corrected to "failures are policy-level routing decisions"
- ❌ "true algorithmic failure rate is ~22%" → Corrected to "20% are ID-only, 78% are policy errors"
- ❌ "not a fundamental architectural deficiency" → Corrected to "policy error pattern is addressable"

### Retained
- ✅ Original CVSR = 5/60 = 0.083 (authoritative)
- ✅ Critical Recall = 1.000 for all 55 failed tasks
- ✅ Replay Success = 1.000 for all 55 failed tasks
- ✅ Zero fatal violations in all 55 failed tasks

## 6. Output Files

| File | Description |
|------|-------------|
| `p06r_id_invariant_audit.csv` | 60-row per-task audit with canonical metrics |
| `p06r_semantic_audit_summary.json` | Machine-readable summary |
| `analyze_id_invariant_audit.py` | Analysis script (read-only) |
