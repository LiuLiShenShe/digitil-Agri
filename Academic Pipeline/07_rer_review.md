# Re-Review Verification Report: KAFarmTwin

**Manuscript:** KAFarmTwin: A Knowledge-Constrained Agent Approach for Traceable Digital Twin Scene Construction in Protected Agriculture

**Original Review Date:** 2026-09-01
**Re-Review Date:** 2026-09-01

---

## Verification Checklist

### Priority 1: Critical (Must Address)

#### 1.1 Strengthen agricultural domain connection

**1.1.1 Add case study or pilot deployment involving real or semi-real greenhouse data**

- **Status:** ⚠️ Partially addressed
- **Evidence:** Section 5.8 provides an "Illustrative case study: tomato greenhouse construction" (lines 418-428). However, this is a synthetic scenario from the benchmark set, not real or semi-real greenhouse data. The case study describes a request to "Construct a 30 m × 8 m greenhouse for tomato cultivation" and traces the pipeline execution.
- **Remaining concern:** The case study is illustrative of the method's operation but does not involve real sensor data streams, actual greenhouse environments, or field deployment. The reviewer's request for "real or semi-real greenhouse data" remains unaddressed.

**1.1.2 Justify ontology with reference to real agricultural management needs**

- **Status:** ✅ Addressed
- **Evidence:** Definition 4 (lines 104-108) defines the agricultural object ontology with categories (Greenhouse, Plot, CropRow, Plant, Sensor, Camera, Device, Trait, Event, Asset) and relationship types. The introduction (lines 35-37) grounds the hierarchy in real agricultural management needs: "greenhouse → plot → crop row → plant → sensor → event" relationships are described as necessary for object-level queries, historical tracking, and rule validation.
- **Remaining concern:** None significant. The ontology is justified by domain requirements.

**1.1.3 Address why asset_routing fails so badly (KF CVSR 0.083) with detailed failure analysis**

- **Status:** ✅ Addressed
- **Evidence:** Section 5.7 (lines 407-415) provides a detailed root-cause analysis of the 55/60 failed asset-routing tasks. Three failure modes are identified: (i) asset registry lacks GLB models for 60% of required object types; (ii) Knowledge Compiler's asset policy maps only 8 device types; (iii) LLM's IntentIR occasionally omits asset-policy preferences. The analysis is architectural and honest.
- **Remaining concern:** None. The failure analysis is thorough and transparent.

#### 1.2 Address benchmark validity concerns

**1.2.1 Clarify relationship between test_v2 and External300**

- **Status:** ✅ Addressed
- **Evidence:** Section 5.1 (lines 255-259) clearly states: "External300 (Benchmark B) serves as the primary evidence for directional consistency on a larger task set; test_v2 (Benchmark A) provides supplementary multi-baseline comparison on a smaller set that was consulted during development."
- **Remaining concern:** None. The relationship is clearly delineated.

**1.2.2 Acknowledge rule_repair perfect separation may indicate benchmark design bias**

- **Status:** ⚠️ Partially addressed
- **Evidence:** Section 5.6 (line 401) acknowledges: "KF rule_repair CVSR = 1.00 for all five models; SA = 0.00 for all five. This is a protocol-level difference (typed repair closed-loop mechanism), not a model-capability difference." However, the paper frames this as a protocol difference rather than acknowledging potential benchmark design bias.
- **Remaining concern:** The paper does not explicitly acknowledge that perfect separation may indicate benchmark design favoring the proposed method. The Devil's Advocate concern about benchmark validity remains partially unaddressed.

**1.2.3 Provide sensitivity analysis of bootstrap results across multiple random seeds**

- **Status:** ❌ Not addressed
- **Evidence:** The paper uses seed 20260804 throughout (line 257) but does not provide sensitivity analysis across multiple seeds. The reviewer specifically requested "sensitivity analysis of the bootstrap results across multiple random seeds" and this is absent.
- **Remaining concern:** The statistical stability of results across different random seeds is not demonstrated.

#### 1.3 Add missing technical details

**1.3.1 Formally define scene graph G = (N, E) with node and edge types**

- **Status:** ✅ Addressed
- **Evidence:** Definition 2b (lines 92-93) provides a formal graph-theoretic definition: "The 3D digital-twin scene graph is a typed attributed graph G = (N, E) where each node n ∈ N carries a type τ(n) ∈ C and a set of attributes α(n) ⊆ P; each edge e = (ni, nj) ∈ E carries a relationship type ρ(e) ∈ Ro and optional temporal metadata t(e)."
- **Remaining concern:** None. The definition is formal and complete.

**1.3.2 Provide more detail on Knowledge Compiler conflict resolution mechanism**

- **Status:** ⚠️ Partially addressed
- **Evidence:** Algorithm 1 (lines 134-149) describes the Knowledge Compiler pipeline including "Fold or split object counts that violate identity semantics" (line 137). However, the paper does not provide detailed conflict resolution logic for when LLM candidate objects conflict with ontology classifications.
- **Remaining concern:** The conflict resolution mechanism is mentioned but not detailed. The reviewer's example of a "sensor" classified as "device" is not explicitly addressed.

**1.3.3 Clarify unit-alias gap's impact on Bind-F1 scores**

- **Status:** ✅ Addressed
- **Evidence:** Section 5.7 (lines 413-414) explicitly states: "TN22's standard unit °C versus the method's celsius, and TN23's klux/light versus lux/light_intensity, have no mappings in the frozen evaluator's unit-alias table. Even a perfectly correct method cannot score." The impact on Bind-F1 is clearly distinguished from method limitations.
- **Remaining concern:** None. The evaluator limitation is clearly separated from method performance.

### Priority 2: Important (Should Address)

#### 2.1 Improve reproducibility

**2.1.1 Include code availability statement**

- **Status:** ✅ Addressed
- **Evidence:** "Data and code availability" section (lines 456-458) states: "The evaluation protocol, frozen evaluator (evaluator_v2.3, source fingerprint logged with each run), configurations, and result files are available in the accompanying code repository."
- **Remaining concern:** The statement does not explicitly specify whether the code is open source or provide a URL. However, it confirms availability.

**2.1.2 Add confidence intervals to ablation study results**

- **Status:** ❌ Not addressed
- **Evidence:** Table 9 (lines 366-373) reports point estimates for ablation variants without confidence intervals. The paper provides paired flips (22:0 for A2) but no formal CIs for CVSR differences between full and ablation variants.
- **Remaining concern:** The ablation study lacks statistical uncertainty quantification.

**2.1.3 Include planned figures (Fig 1-5) in manuscript**

- **Status:** ⚠️ Partially addressed
- **Evidence:** Figure captions are included (lines 20-28) but actual figures are not present in the markdown manuscript. The captions describe what each figure would show.
- **Remaining concern:** The manuscript contains figure descriptions but not actual figures. For a journal submission, figures must be included.

#### 2.2 Strengthen writing

**2.2.1 Add high-level pipeline overview at start of Section 3**

- **Status:** ✅ Addressed
- **Evidence:** Section 3 begins with an "Overview" paragraph (lines 73-74) that summarizes the pipeline in plain language before diving into formal definitions.
- **Remaining concern:** None. The overview is clear and accessible.

**2.2.2 Standardize terminology**

- **Status:** ✅ Addressed
- **Evidence:** The paper primarily uses "knowledge-constrained agent" consistently throughout (title, abstract, introduction, method). The term "knowledge-augmented AI" appears in related work (Section 2.3) but is distinguished as a broader category. "Neurosymbolic integration" is discussed in related work as a theoretical foundation.
- **Remaining concern:** Terminology appears reasonably standardized with appropriate distinctions.

**2.2.3 Reduce repetition of limitation disclaimers**

- **Status:** ⚠️ Partially addressed
- **Evidence:** The disclaimer "This paper does not make state-of-the-art claims" appears in the abstract (line 14), gate criteria (line 239), and conclusion (line 450). The paper consolidates limitations in Section 5.9 (Threats to validity).
- **Remaining concern:** Some repetition remains, though it is less excessive than before.

**2.2.4 Connect general agent research to specific failure modes**

- **Status:** ✅ Addressed
- **Evidence:** Section 2.2 (line 61) explicitly connects general agent research to failure modes: "Empirically, we find that the ReAct baseline achieves CVSR 0.000 on our frozen benchmark—all 20 tasks fail—demonstrating that unconstrained free-form reasoning is insufficient for structured scene construction."
- **Remaining concern:** None. The connection is clear and evidence-based.

#### 2.3 Clarify cost analysis

**2.3.1 Acknowledge token-based cost ignores development and maintenance costs**

- **Status:** ✅ Addressed
- **Evidence:** Section 5.9 (line 442) explicitly states: "The token-based cost metric does not capture development, maintenance, and infrastructure costs of the six deterministic knowledge modules; the total cost of ownership for deploying KAFarmTwin in a production greenhouse management system would be higher than the per-task token cost suggests."
- **Remaining concern:** None. The limitation is clearly acknowledged.

**2.3.2 Provide more realistic total cost of ownership estimate**

- **Status:** ❌ Not addressed
- **Evidence:** The paper acknowledges the limitation but does not provide an estimate of total cost of ownership. The reviewer requested "estimated total cost of deploying KAFarmTwin for a 100-task agricultural digital twin project."
- **Remaining concern:** No realistic cost estimate is provided.

### Priority 3: Minor (Nice to Have)

#### 3.1 Enhance related work section

**3.1.1 Contrast against specific agricultural digital twin systems**

- **Status:** ⚠️ Partially addressed
- **Evidence:** Section 2.1 (lines 56-57) contrasts KAFarmTwin against general agricultural DT systems: "These studies demonstrate the value of digital twins for agricultural state awareness, yet most systems treat the scene primarily as a data dashboard or visualization layer, lacking computable semantic relationships among objects." However, the contrast is general rather than against specific systems like Pylianidis et al. 2021 or Verdouw et al. 2021.
- **Remaining concern:** The contrast remains general rather than specific to named systems.

**3.1.2 Strengthen connection between general agent research and digital-twin scene construction**

- **Status:** ✅ Addressed
- **Evidence:** Section 2.2 provides a detailed discussion connecting general agent research to digital-twin scene construction challenges, including why ReAct fails and why multi-agent approaches without knowledge constraints are insufficient.
- **Remaining concern:** None.

#### 3.2 Address traceability claim

**3.2.1 Provide concrete example of execution trace**

- **Status:** ⚠️ Partially addressed
- **Evidence:** Figure 5 is described as "Execution trace example" (line 28) showing "evidence identifiers (evidenceId), tool call sequences, and validation outcomes." However, the actual trace example is not included in the manuscript text.
- **Remaining concern:** The trace example is described but not shown.

**3.2.2 Discuss how traces would be verified in production agricultural context**

- **Status:** ❌ Not addressed
- **Evidence:** The paper discusses traceability mechanisms but does not address how traces would be verified in a real agricultural production context.
- **Remaining concern:** The verification challenge in production contexts remains unaddressed.

#### 3.3 Clarify "no state-of-the-art" disclaimer

**3.3.1 Articulate clearly what readers should take away**

- **Status:** ✅ Addressed
- **Evidence:** The conclusion (lines 446-452) clearly articulates the contribution: a knowledge-constrained agent method with specific performance characteristics and limitations. The paper positions the work as a method/system contribution with honest boundaries.
- **Remaining concern:** None.

**3.3.2 Position contribution as method/system/case study, not SOTA claim**

- **Status:** ✅ Addressed
- **Evidence:** The paper consistently frames contributions as methodological (IntentIR → Knowledge Compiler → Typed Repair pipeline) and system-level (prototype implementation), explicitly stating "This paper does not make state-of-the-art claims."
- **Remaining concern:** None.

---

## Overall Re-Review Verdict

**Verdict: Minor Revision**

The revised paper addresses most of the original review concerns effectively. The technical contributions are well-supported, the failure analysis is thorough, and the limitations are honestly reported. However, several items remain partially or completely unaddressed.

---

## Remaining Issues That Still Need Attention

### Critical (Must be addressed before publication):

1. **Sensitivity analysis across multiple random seeds** (Priority 1.2.3): The paper uses a single bootstrap seed (20260804) without demonstrating statistical stability across different seeds. This is a methodological gap that should be addressed.

2. **Ablation study confidence intervals** (Priority 2.1.2): The ablation study lacks CIs for CVSR differences between variants, making it difficult to assess whether component contributions are statistically distinguishable.

3. **Real-world deployment evidence** (Priority 1.1.1): The case study is illustrative but synthetic. While a full pilot deployment may be beyond scope, at minimum the paper should acknowledge this gap more explicitly and discuss what real-world validation would entail.

### Important (Should be addressed):

4. **Actual figures in manuscript** (Priority 2.1.3): The paper includes figure captions but not actual figures. For journal submission, figures must be included.

5. **Total cost of ownership estimate** (Priority 2.3.2): The paper acknowledges token-based cost limitations but provides no alternative estimate.

6. **Knowledge Compiler conflict resolution details** (Priority 1.3.2): The conflict resolution mechanism is mentioned but not detailed.

### Minor (Nice to have):

7. **Benchmark design bias acknowledgment** (Priority 1.2.2): The paper could more explicitly acknowledge that perfect rule_repair separation may indicate benchmark design favoring the proposed method.

8. **Execution trace example in text** (Priority 3.2.1): A concrete trace example would strengthen the traceability claim.

9. **Trace verification in production** (Priority 3.2.2): Discussion of how traces would be verified in real agricultural contexts would strengthen practical impact.

---

## Final Recommendation

The revised paper represents a significant improvement over the original submission. The technical approach is principled, the experiments are rigorous, and the limitations are honestly reported. The paper makes a genuine contribution to knowledge-constrained agent design for digital-twin scene construction.

**Recommendation:** Accept after minor revisions addressing the critical issues (sensitivity analysis, ablation CIs, and clearer real-world deployment discussion). The remaining important and minor issues can be addressed in a subsequent revision or as part of camera-ready preparation.

**Key strengths of the revision:**
1. Thorough failure analysis of asset_routing weaknesses
2. Clear delineation of benchmark relationships (test_v2 vs. External300)
3. Formal scene graph definition
4. Honest acknowledgment of evaluator limitations
5. Pre-registered cross-model generalization study

**Key weaknesses remaining:**
1. Lack of sensitivity analysis across random seeds
2. Missing ablation confidence intervals
3. Synthetic case study without real-world data
4. Figures described but not included in manuscript

The paper is suitable for publication in Computers and Electronics in Agriculture after addressing the critical methodological gaps.