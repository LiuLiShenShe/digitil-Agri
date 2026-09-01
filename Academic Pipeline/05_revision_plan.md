# Revision Roadmap — KAFarmTwin Paper

## Editorial Decision: MINOR REVISION (4/5 reviewers) + Major (DA: 5/10)

---

## Priority 1: Critical (Must Address)

### P1.1: Strengthen agricultural domain connection
- **Source**: EIC, DA
- **Action**: Add a brief case study subsection (Section 5.9) describing how the object hierarchy maps to a real tomato greenhouse scenario
- **Action**: Expand Section 5.7 (asset_routing failure analysis) with detailed root-cause breakdown
- **Action**: Justify the ontology (Definition 4) with reference to real agricultural management needs (Pylianidis et al., 2021; Verdouw et al., 2021)

### P1.2: Address benchmark validity
- **Source**: R1, DA
- **Action**: Clarify in Section 5.1 that External300 is the primary evidence and test_v2 is supplementary
- **Action**: Add a sentence acknowledging that rule_repair's perfect separation may indicate benchmark design characteristics
- **Action**: Add a brief sensitivity note about bootstrap seed stability

### P1.3: Formal scene graph definition
- **Source**: R2
- **Action**: Add Definition 2b formalizing G = (N, E) as a typed attributed graph with node types from ontology C and edge types from R_o

---

## Priority 2: Important (Should Address)

### P2.1: Code availability statement
- **Source**: R2
- **Action**: Add a Data/Code Availability section stating the code repository and evaluation protocol

### P2.2: High-level pipeline overview
- **Source**: R3
- **Action**: Add a 1-paragraph plain-language overview at the start of Section 3 before diving into formal definitions

### P2.3: Terminology standardization
- **Source**: R3
- **Action**: Use "knowledge-constrained agent" as the primary term consistently

### P2.4: Reduce limitation disclaimer repetition
- **Source**: R3
- **Action**: Consolidate SOTA disclaimers to abstract, Section 5.8, and conclusion only

### P2.5: Figure placeholders
- **Source**: R3
- **Action**: Add figure placeholders with captions for Fig 1 (architecture), Fig 2 (CVSR comparison), Fig 3 (ablation), Fig 4 (cross-model forest plot)

---

## Priority 3: Minor (Nice to Have)

### P3.1: Strengthen Section 2.2
- **Source**: R3
- **Action**: Connect general agent research to specific failure modes of digital-twin scene construction

### P3.2: Total cost of ownership acknowledgment
- **Source**: DA
- **Action**: Add a sentence acknowledging that token-based cost does not capture development/maintenance costs

### P3.3: Asset routing failure analysis
- **Source**: DA
- **Action**: Add detailed failure analysis for asset_routing (why KF CVSR only 0.083)

---

## Execution Plan

1. Apply P1.1–P1.3 (critical fixes)
2. Apply P2.1–P2.5 (important improvements)
3. Apply P3.1–P3.3 (minor enhancements)
4. Re-run integrity check
5. Proceed to Stage 3' (re-review)
