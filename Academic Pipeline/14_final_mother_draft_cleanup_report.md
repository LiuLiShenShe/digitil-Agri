# FINAL MOTHER-DRAFT CLEANUP REPORT

**Date:** 2026-09-01 | **Status:** Complete | **Constraint:** NEW_MODEL_EXECUTIONS=0 (no model re-runs)

---

## Summary

23-section cleanup of the KAFarmTwin canonical manuscript (`09_final_paper.md`) and all evidence files, eliminating unsupported claims, correcting terminology, fixing reference metadata, and synchronizing evidence.

---

## A. Terminology Changes

| Before | After | Scope |
|:-------|:------|:------|
| SESR (Structured Execution Success Rate) | **SSCR (Structured Completion Success Rate)** | Paper, manifest MD/JSON, P05S, 02_main_results |
| "Semantic Understanding Rate" | **"Semantic Structure Preservation Rate"** | P05S metrics table |
| "Semantically complete, evidence fail" | **"Structurally complete, evidence fail"** | Paper Table A5, P05S, manifest MD |
| "semantic understanding" (as bottleneck) | **"structure preservation"** | Abstract, §1 Contribution 1, §5.4, §6.1, §8, Appendix A5 |

**Rationale:** The term "semantic understanding" implies latent comprehension that SSPR=1.0 does not demonstrate. "Structure preservation" is operationally defined (Obj-F1=1.0 AND Rel-F1=1.0) and makes no claims about the LLM's internal representations.

---

## B. Paper Wording Changes (§5 of spec)

| Location | Before | After |
|:---------|:-------|:------|
| Abstract (L14) | "not semantic understanding—as the bottleneck" | "not structure preservation—as the bottleneck" |
| Contribution 1 (L43) | "semantic/execution boundary" | "structure-preservation/execution boundary" |
| §5.4 (L239) | "retains the scene's semantic structure" | "retains the scene's structure" |
| §5.4 (L241) | "bottleneck is not semantic understanding" | "bottleneck is not structure preservation" |
| §5.4 (L241) | "KAFarmTwin's typed operators bridge this gap" | "KAFarmTwin's complete constrained repair path—typed operator selection, deterministic parameter instantiation, and execution-trace generation—bridges this gap" |
| §6.1 title | "Semantic competence versus executable state" | "Structure preservation versus executable state" |
| §6.1 body | "The LLM understands the repair semantics" | "The LLM output preserves the repair semantics" |
| §6.1 body | "semantic recognition and contract-complete" | "structure preservation and contract-complete" |
| §8 (L355) | "stochastic semantic interpretation" | "stochastic natural-language interpretation" |
| §8 (L357) | "100% semantic structure preservation but only 10% structured execution success" | "100% structure preservation but only 10% structured completion success" |
| Appendix A5 (L407) | "not semantic understanding" | "not structure preservation" |

---

## C. Table 6 Unit Fix (§11 of spec)

| Before | After |
|:-------|:------|
| `Fatal` column with bare counts (0, 43, 60) | `Fatal, n (%)` with "0 (0%)", "43 (71.7%)", "60 (100%)" |

---

## Causal Attribution Fix (§13 of spec)

| Before | After |
|:-------|:------|
| "KAFarmTwin's typed operators bridge this gap" | "KAFarmTwin's complete constrained repair path—typed operator selection, deterministic parameter instantiation, and execution-trace generation—bridges this gap" |

**Rationale:** Over-attributing to "typed operators alone" ignores the deterministic executor and trace generator. The full constrained repair path is the differentiator.

---

## D. Related Work §2.9 Fixes (§14–16 of spec)

| Issue | Fix |
|:------|:----|
| Dangling "Table 1 positions KAFarmTwin…" reference (Table 1 is rule checkpoints, not a positioning table) | Removed; replaced with prose summary |
| "a combination not present in any single prior system" (universal novelty claim) | Softened to "Prior systems address subsets of this combination" with specific examples |

---

## E. Reference Metadata Fixes (§17 of spec)

| Reference | Before | After |
|:----------|:-------|:------|
| Akroyd et al. 2021 | `e10` | `e14` (DOI suffix .10 ≠ article number e14) |
| Zellers et al. 2018 | `Zellers, R., Zellers, R., Zellers, R., et al., 2018. …pp. 5825–5834` | `Zellers, R., Yatskar, M., Thomson, N., Choi, Y., 2018. …pp. 5831–5840` |
| Qi et al. 2025 | `2025b` (unnecessary suffix) | `2025` (no disambiguation needed) |

---

## F. Orphan Reference Removal (§18 of spec)

Removed 3 bibliography entries with no in-text citations:

| Reference | Status |
|:----------|:-------|
| Kojima et al., 2022 | Removed (zero-shot reasoners — not cited in text) |
| Staab and Studer, 2009 | Removed (Handbook on Ontologies — not cited in text) |
| Wolfert et al., 2017 | Removed (Big data in smart farming — not cited in text) |

Note: `Wolfert, S.` appears as co-author in the verified-correct Verdouw et al. 2021 entry — this is correct and unrelated to the removed orphan.

---

## G. Evidence File Sync (§20 of spec)

| File | Changes |
|:-----|:--------|
| `CANONICAL_EVIDENCE_MANIFEST.md` | SESR→SSCR, Category A rename, cross-tab added (binding_omit×fatal: 43/11), provenance note updated |
| `CANONICAL_EVIDENCE_MANIFEST.json` | `sesr`→`sscr`, cross-tab fields added (binding_omission_fatal, binding_omission_clean, has_bindings_fatal, has_bindings_clean, fatal_r6, fatal_r2) |
| `02_main_results.md` | SESR→SSCR in Claim M1-directrepair |
| `P05S_direct_repair_failure_analysis.md` | "Semantic Understanding Rate"→"Semantic Structure Preservation Rate", "understanding"→"structure preservation" (6 locations), Category A label renamed, SSCR terminology applied |

---

## H. Consistency Scan Results (§21 of spec)

Scanned all 6 files for 17 stale patterns. Results:
- **Paper (`09_final_paper.md`):** CLEAN (1 Wolfert hit is co-author in Verdouw 2021 — correct)
- **Manifest MD/JSON:** CLEAN
- **02_main_results.md:** CLEAN
- **P05S report:** CLEAN (after fixes above)
- **CITATION_VERIFICATION_REPORT.md:** 12 hits are historical documentation of found errors — correct as-is

---

## Governing Scientific Message (§23 of spec)

**Do NOT infer latent "understanding" from SSPR=1.0.** The paper now consistently uses:
- "structure preservation" (operationally defined: Obj-F1=1.0 AND Rel-F1=1.0)
- "structured output production" (the actual bottleneck)
- "structured completion success" (SSCR = Bind-F1 > 0.5 threshold)

No claim in the paper implies the LLM "understands" the domain. SSPR=1.0 demonstrates output-level structural fidelity, not comprehension.

---

## Files Modified

| File | Edits Applied |
|:-----|:-------------|
| `Academic Pipeline/09_final_paper.md` | 19 edits (terminology, wording, tables, references, orphans) |
| `paper_evidence/CANONICAL_EVIDENCE_MANIFEST.md` | 3 edits (SSCR, cross-tab, provenance) |
| `paper_evidence/CANONICAL_EVIDENCE_MANIFEST.json` | 2 edits (sscr, cross-tab) |
| `paper_evidence/02_main_results.md` | 1 edit (SSCR) |
| `Academic Pipeline/05_review/P05S_direct_repair_failure_analysis.md` | 6 edits (terminology, language, Category A) |

**Total: 31 edits across 5 files. Zero model executions.**
