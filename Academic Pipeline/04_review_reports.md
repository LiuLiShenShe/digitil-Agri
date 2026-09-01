# Peer Review Report: KAFarmTwin

**Manuscript:** KAFarmTwin: A Knowledge-Constrained Agent Approach for Traceable Digital Twin Scene Construction in Protected Agriculture

**Journal:** Computers and Electronics in Agriculture (COMPAG)

**Review Date:** 2026-09-01

---

## Review Panel Composition

| Role | Expertise | Focus Area |
|:-----|:----------|:-----------|
| EIC | Editor-in-Chief, Agricultural Informatics | Scope fit, novelty, significance |
| R1 | Reviewer 1, AI/ML Methodology | Experimental design, statistical validity |
| R2 | Reviewer 2, Systems Engineering | Technical depth, reproducibility |
| R3 | Reviewer 3, Academic Writing | Clarity, organization, presentation |
| DA | Devil's Advocate | Worst-case challenges, limitations |

---

## 1. EIC (Editor-in-Chief) — Scope Fit & Novelty Assessment

### Summary Assessment: **Minor Revision**

### Key Strengths

1. **Highly relevant to COMPAG scope.** The paper addresses a genuine bottleneck in agricultural digital twins — the manual, error-prone process of constructing object-graph scenes from natural language. This aligns directly with the journal's focus on electronics and computing applications in agriculture.

2. **Novel integration of knowledge constraints with LLM agents.** The separation of semantic understanding (LLM) from structural constraint satisfaction (deterministic Knowledge Compiler) is a principled design that goes beyond typical RAG or prompt-engineering approaches. The three-stage pipeline (IntentIR → Knowledge Compiler → Typed Repair) offers a clear architectural contribution.

3. **Honest reporting of limitations.** The authors explicitly disclose that test_v2 was consulted during development, External300 was author-reviewed (not independent double-blind), and no state-of-the-art claims are made. This level of transparency is commendable and builds reviewer trust.

4. **Practical agricultural relevance.** The object hierarchy (Greenhouse → Plot → CropRow → Plant → Sensor → Event) maps to real protected-agriculture management needs, making the work grounded in domain reality rather than abstract problem-solving.

### Key Weaknesses

1. **Limited real-world validation.** The system is validated only on synthetic benchmarks (test_v2 and External300), not on actual greenhouse management scenarios with real sensor data streams. The "protected agriculture" framing would benefit from at least one case study involving a real or semi-real deployment context.

2. **Narrow contribution to 3D scene construction.** While the paper claims to address digital twins broadly, the actual contribution is limited to object-graph construction and validation. The 3D visualization layer (Three.js frontend) is mentioned but not evaluated — the paper explicitly states it does not address 3D quality. This narrows the claimed scope.

3. **Benchmark limitations acknowledged but not fully resolved.** The authors correctly identify that neither benchmark constitutes independent external validation. However, the paper still presents results as if they demonstrate generalizable performance, which may mislead readers who skip the limitations section.

4. **Weak positioning relative to existing agricultural digital twin work.** The related work section (Section 2.1) acknowledges that most existing systems focus on monitoring and visualization, but does not adequately contrast KAFarmTwin against specific systems (e.g., Pylianidis et al. 2021, Verdouw et al. 2021) in terms of what each actually delivers.

### Specific Questions/Suggestions

1. Can the authors provide a brief case study or pilot deployment involving a real greenhouse or a semi-real data stream, even if limited in scope? This would substantially strengthen the "protected agriculture" claim.

2. How does KAFarmTwin compare, even qualitatively, to existing agricultural digital twin platforms (e.g., those reviewed in Pylianidis et al. 2021) in terms of the time/effort required to construct a scene?

3. The abstract mentions "traceable" scene construction, but the paper's traceability contribution (execution traces with evidenceId) is relatively thin. Can the authors elaborate on how these traces would be used in a production agricultural context?

### Overall Score: **7/10**

The paper addresses a relevant problem with a principled approach, but the gap between synthetic benchmarks and real-world agricultural deployment weakens the practical impact claim.

---

## 2. R1 (Reviewer 1) — Methodology & Statistical Validity

### Summary Assessment: **Minor Revision**

### Key Strengths

1. **Rigorous paired evaluation protocol.** The use of task-level paired bootstrap (10,000 resamples) with seed fixed for reproducibility, combined with McNemar's exact test, provides appropriate statistical machinery for binary outcome comparison. The 95% CI reporting is complete.

2. **Ablation study design is well-conceived.** The three-component ablation (Knowledge Compiler, Typed Repair, Ontology) cleanly isolates each component's contribution. The honest reporting that A2 (no typed repair) yields *higher* CVSR than full is scientifically responsible — the authors correctly interpret this as evidence that repair contributes safety rather than performance.

3. **Multi-model generalization is pre-registered.** The use of a frozen pre-registration document (MULTIMODEL_PREREGISTRATION_v2.md, frozen 2026-08-25) for the cross-model experiment prevents HARKing (hypothesizing after results are known). The pre-registered verdict MODEL_GENERALIZATION_PASS is applied correctly.

4. **Appropriate gate criteria.** The engineering acceptance criteria (paired difference ≥ 3 pp, CI lower bound > 0, pass@5 strictly higher, etc.) are pre-specified and all met. The authors correctly note that "PASS does not constitute a state-of-the-art claim."

5. **Transparent handling of ceiling effects.** The authors explicitly identify that data_binding and memory_query reach ceiling (1.00 vs. 1.00) and refuse to make relative claims on these categories. This is methodologically sound.

### Key Weaknesses

1. **External300 single execution per task-method.** With only one execution per task-method pair on External300, the paired bootstrap estimates variance across *tasks* but not across *runs*. If LLM stochasticity at temperature 0.2 produces non-trivial per-task variance (as evidenced by the ablation full 0.550 vs. main experiment 0.610 discrepancy), the single-execution protocol may underestimate uncertainty. The paper acknowledges this but does not quantify the potential bias.

2. **Ablation lacks confidence intervals.** The ablation results (Table 9) report point estimates without CIs or significance tests. While the paired flips (22:0 for A2) provide qualitative evidence, a formal confidence interval on the CVSR difference between full and each ablation variant would strengthen the component attribution claims.

3. **test_v2 benchmark contact bias is acknowledged but underweighted.** The paper notes that test_v2 was "consulted during development and drove multiple repair cycles," yet still presents it as a "frozen benchmark" with results in the main text. The dual presentation (test_v2 + External300) may confuse readers about which constitutes the primary evidence. The authors should more clearly delineate test_v2 as supplementary/supportive rather than primary.

4. **Bootstrap seed fixation limits generality.** All bootstrap analyses use seed 20260804. While reproducible, reporting results from multiple seeds (or at minimum, noting sensitivity to seed choice) would provide more robust evidence of statistical stability.

5. **The McNemar test assumption.** The McNemar exact test assumes binary outcomes from paired observations. While appropriate here, the paper should explicitly state this assumption and note that the test is valid because each task-method pair produces a binary (pass/fail) outcome.

### Specific Questions/Suggestions

1. **Can the authors provide a sensitivity analysis of the bootstrap results across multiple random seeds?** Even 3-5 seeds would help assess whether the CI estimates are stable.

2. **For the ablation study, can the authors compute 95% CIs for the CVSR differences between full and each ablation variant?** This would allow formal assessment of whether the component contributions are statistically distinguishable.

3. **The "paired flips" metric (22:0 for A2) is compelling but informal.** Can the authors provide a formal test (e.g., McNemar on the ablation results) to quantify the significance of the fatal-violation increase?

4. **How sensitive are the results to the choice of LLM temperature?** Temperature 0.2 is used throughout, but the paper does not explore whether the advantage holds at temperature 0 (greedy) or temperature 0.5 (higher stochasticity).

5. **The pass@5 metric is computed on test_v2 (5 repeats) but not on External300 (single execution).** Can the authors clarify why pass@k is not reported for External300, and whether the single-execution protocol precludes this metric?

### Overall Score: **8/10**

The statistical methodology is sound and well-applied. The main weakness is the single-execution protocol on External300 and the lack of CIs in the ablation study. These are addressable through minor revisions.

---

## 3. R2 (Reviewer 2) — Technical Depth & Reproducibility

### Summary Assessment: **Minor Revision**

### Key Strengths

1. **Clear system architecture with layered implementation.** The backend (Go, Gin, sqlx, MySQL) and frontend (Vue 3, TypeScript, Vite, Three.js, Pinia, Element Plus) are well-specified. The layered implementation for object management, scene binding, memory management, asset governance, and agent orchestration demonstrates engineering maturity.

2. **Deterministic Knowledge Compiler is well-defined.** The six deterministic knowledge modules (Ontology, Constraint, Mapping, Binding Vocabulary, Asset Policy, Unit Registry) are described with sufficient detail to understand the compilation pipeline. The claim of "zero LLM invocations" in the Compiler is verifiable from the algorithm description.

3. **Typed Repair safety property is formally stated.** The key safety property — "any applied patch cannot introduce destructive modifications" — is backed by the ablation evidence (A2 fatal rate 0 → 0.22) and the transactional safety mechanism (deep-copy, apply, re-validate, rollback on new fatal violations).

4. **Budget constraints are transparent.** The shared budget (30 LLM calls, 100 tool calls, 3 repair rounds) across all methods ensures fair comparison. The cost reporting (token ratio 1.41×, cost ratio 1.21×) is grounded in concrete provider pricing.

5. **Execution trace mechanism is documented.** The distinction between declarative traces and execution traces with evidence identifiers (evidenceId, callId) addresses a real problem in agent systems — the risk of model self-narration being mistaken for actual execution evidence.

### Key Weaknesses

1. **Limited implementation detail for the Knowledge Compiler.** The algorithm description (Algorithm 1) is high-level. Key implementation questions remain: How is the ontology loaded and queried? What data structure represents the scene graph? How does the Compiler handle conflicting candidate objects in IntentIR? The paper would benefit from a more detailed technical description or a pointer to the codebase.

2. **No code availability statement.** The paper does not mention whether the implementation will be released as open source. For a systems paper in COMPAG, code availability is important for reproducibility. The evidence files reference internal paths (e.g., `harness/semantic_compiler.py`, `methods/kafarmtwin_typed_repair.py`) but the paper does not disclose whether these will be made public.

3. **The 3D scene graph (G) is under-specified.** Definition 2 defines the output as Y = {G, B, V, T}, where G is the "3D digital-twin scene graph." However, the paper does not specify the graph schema (nodes, edges, attributes) in formal detail. The ontology (Definition 4) defines categories and relationships, but the scene graph G is not formally defined as a graph-theoretic object.

4. **Asset routing policy details are sparse.** The paper mentions "high-fidelity, lightweight GLB, procedural model, or placeholder" asset routing preferences but does not describe how these preferences are determined, how conflicts are resolved, or how the asset registry is populated.

5. **The unit-alias gap in the evaluator is a known limitation that affects result interpretation.** The paper acknowledges that TN22/TN23 fail due to missing unit aliases (°C vs. celsius, klux vs. lux). This means the Bind-F1 scores for all methods are systematically depressed by evaluator limitations, not method limitations. The paper should more clearly distinguish between method performance and evaluator limitations in the results interpretation.

### Specific Questions/Suggestions

1. **Is the implementation available as open source?** If not, what is the plan for code release? COMPAG readers will want to replicate or extend the work.

2. **Can the authors provide more detail on the scene graph schema?** A formal definition of G = (N, E) with node and edge types would strengthen the technical contribution.

3. **How does the Knowledge Compiler handle conflicts in IntentIR?** For example, if the LLM candidate objects include a "sensor" that the ontology classifies as a "device," how is this resolved?

4. **What is the maximum scale of scenes that the prototype system can handle?** The paper mentions "larger-scale crop production data" as future work, but does not provide current scalability bounds (e.g., maximum number of objects, maximum graph depth).

5. **Can the authors provide a concrete example of an execution trace?** A sample trace showing evidenceId, callId, and the validation chain would help readers understand the auditability claim.

### Overall Score: **7/10**

The system is well-engineered and the technical approach is sound. The main weaknesses are underspecified scene graph details, sparse implementation description, and the absence of a code availability statement. These are addressable through minor revisions with supplementary material.

---

## 4. R3 (Reviewer 3) — Writing Quality & Organization

### Summary Assessment: **Minor Revision**

### Key Strengths

1. **Logical paper structure.** The paper follows a clear progression: problem → related work → method → implementation → experiments → discussion → conclusions. The experimental section structure (setup → main results → safety analysis → ablation → category breakdown → cross-model → validity threats) tells a coherent story.

2. **Honest and transparent tone.** The repeated disclaimers ("this paper does not claim state-of-the-art performance," "results must not be extrapolated to unseen data") are appropriate and build credibility. The explicit disclosure of benchmark deviations (Section 5.8) is a model of research transparency.

3. **Well-defined formal notation.** The paper uses consistent mathematical notation for definitions (Definition 1-8), algorithms (Algorithm 1-2), and statistical tests. The notation is self-contained and does not require external references for interpretation.

4. **Effective use of tables and evidence.** The paper includes 10 tables that are well-organized and support the narrative. The category-level breakdown (Table 6) and the failure taxonomy (Table 8) provide useful diagnostic detail.

5. **Strong abstract.** The abstract is comprehensive, reporting specific numbers (CVSR 0.717 vs. 0.480, +23.7 pp, p < 10^-6) and clearly stating contributions and limitations. It meets the standard for a high-quality journal abstract.

### Key Weaknesses

1. **Dense prose in the method section.** Section 3 (Materials and methods) is long and technical, with multiple definitions, algorithms, and formal notation. While rigorous, it may be challenging for readers without a strong AI/ML background. Consider adding a high-level overview paragraph at the start of Section 3 that summarizes the pipeline in plain language before diving into formal definitions.

2. **Inconsistent use of terminology.** The paper alternates between "knowledge-constrained agent," "knowledge-augmented agent," and "neurosymbolic integration" without clearly distinguishing these terms. While related, they have different connotations. The paper should settle on a primary term and use it consistently.

3. **The related work section (Section 2) is somewhat generic.** Section 2.2 (LLM agents and tool use) surveys general agent research (ReAct, Toolformer, Chain-of-Thought) without clearly connecting these to the specific challenges of digital-twin scene construction. A more targeted discussion of why general agents fail on this specific task would strengthen the motivation.

4. **Some sections are overly self-referential.** The paper repeatedly references its own limitations (e.g., "this paper does not claim state-of-the-art performance" appears in the abstract, introduction, and conclusion). While transparency is valued, excessive repetition may dilute the main contributions. Consider consolidating limitations into a dedicated subsection.

5. **Figure plan is not yet executed.** The evidence files describe a figure plan (Fig 1-5, Fig A1-A2) but the paper text does not include actual figures. The figure descriptions in the plan are useful but the paper would benefit from having these figures (or at least placeholders) in the manuscript.

### Specific Questions/Suggestions

1. **Can the authors add a high-level pipeline overview at the start of Section 3?** A 1-paragraph summary in plain language would improve accessibility.

2. **Can the authors standardize terminology?** Choose one primary term (e.g., "knowledge-constrained agent") and use it consistently throughout.

3. **Can the authors strengthen Section 2.2 by connecting general agent research to the specific failure modes of digital-twin scene construction?** For example, explain why ReAct fails (CVSR 0.000) on this task.

4. **Can the authors reduce the repetition of limitation disclaimers?** Consolidate into Section 5.8 (Threats to validity) and the conclusion, rather than repeating in every section.

5. **Can the authors include the planned figures (or at minimum, figure placeholders) in the manuscript?** Figures would significantly improve readability, especially for the system architecture (Fig 1) and the cross-model forest plot (Fig 4).

### Overall Score: **7/10**

The paper is well-written and organized, with strong formal rigor. The main weaknesses are prose density, terminology inconsistency, and the absence of figures. These are addressable through minor revisions.

---

## 5. Devil's Advocate — Worst-Case Challenges & Limitations

### Summary Assessment: **Major Revision** (minor revision insufficient for all concerns)

### Key Strengths (acknowledged even in worst-case reading)

1. **The safety guarantee is real.** The typed repair mechanism's ability to reduce fatal violations from 0.25 (SA) to 0.00 (KF) is robust across five model families. This is a genuine contribution to agent safety.

2. **The ablation is honest.** The authors correctly report that typed repair does not improve CVSR (A2 CVSR 0.58 > full 0.55) and reframe the contribution as safety. This level of honesty is rare and commendable.

3. **The multi-model pre-registration is a strong methodological choice.** Pre-registering the cross-model experiment prevents cherry-picking favorable models.

### Key Weaknesses (worst-case reading)

1. **The benchmarks may be too easy or too synthetic.** External300 tasks are generated and reviewed by the authors themselves. The rule_repair category shows KF = 1.00 and SA = 0.00 across all five models — this perfect separation suggests the benchmark may be designed in a way that favors the proposed method. The scene_construction category (KF 0.50, SA 0.40) shows only marginal improvement, suggesting that when the task is genuinely challenging, the advantage shrinks.

2. **The "protected agriculture" framing is thin.** The paper claims to address protected agriculture, but the agricultural knowledge is encoded in a static ontology and rule set (R1-R10). The system does not learn from real crop data, does not adapt to different greenhouse types, and does not integrate with actual sensor networks. The agricultural domain knowledge is essentially a lookup table, not a learned or adaptive model.

3. **The cost comparison is misleading.** The paper reports a cost ratio of 1.21× (KF/SA), but this compares only token costs. The Knowledge Compiler requires maintaining and updating six deterministic knowledge modules, which has significant development and maintenance costs not captured in the token-based cost metric. The true total cost of ownership may be substantially higher.

4. **The asset_routing CVSR is 0.083 — nearly complete failure.** While the authors honestly report this, it means the Knowledge Compiler fails on 91.7% of asset routing tasks. This is a critical weakness because asset routing is one of the core contributions claimed. The paper should investigate why this category fails so badly and provide a more detailed failure analysis.

5. **The "traceability" claim is weak.** The paper claims to provide "auditable execution traces," but the traces are internal system logs, not independently verifiable evidence. In a real agricultural production context, an auditor would need to verify that the traces are complete and accurate — the paper does not address this verification challenge.

6. **The system is a prototype, not a production system.** The paper explicitly states this, but the implications are significant: the system has not been tested with real users, real sensor data, or real greenhouse environments. The "protected agriculture" application is aspirational, not demonstrated.

7. **The five-model generalization may be overstated.** All five models are served through the same SiliconFlow inference interface. The paper acknowledges this limitation, but the claim of "cross-model-family robustness" should be qualified as "cross-model-family robustness under the same inference interface." Different inference providers may produce different results.

### Specific Questions/Suggestions

1. **Why does asset_routing fail so badly (KF CVSR 0.083)?** Can the authors provide a detailed failure analysis of the 55/60 failed asset routing tasks? Is the failure in the Knowledge Compiler's asset policy, the LLM's intent parsing, or the asset registry coverage?

2. **Can the authors provide evidence that the agricultural ontology (Definition 4) is sufficient for real greenhouse scenarios?** The current ontology has 10 categories and 8 relationship types — is this sufficient for diverse greenhouse configurations (e.g., hydroponic vs. soil-based, different crop types, different sensor deployments)?

3. **How would the system handle a genuinely novel request that falls outside the ontology?** The paper mentions the `ask_user` operator, but does not demonstrate it. Can the authors provide an example of a request that triggers `ask_user` and show how the system handles it?

4. **Can the authors provide a more realistic cost analysis?** The token-based cost metric ignores development, maintenance, and infrastructure costs. What is the estimated total cost of deploying KAFarmTwin for a 100-task agricultural digital twin project?

5. **The "no state-of-the-art claim" disclaimer may be overly modest.** If the paper does not claim SOTA, what is the contribution? The paper should clearly articulate what readers should take away — is it a method, a system, a case study, or a benchmark?

### Overall Score: **5/10**

The Devil's Advocate reading reveals significant concerns about benchmark validity, real-world applicability, and the gap between the "protected agriculture" framing and the actual contribution. While the technical approach is sound, the practical impact claim is weak.

---

## 6. Editorial Decision

### Consolidated Assessment

| Reviewer | Assessment | Score |
|:---------|:-----------|:------|
| EIC | Minor Revision | 7/10 |
| R1 | Minor Revision | 8/10 |
| R2 | Minor Revision | 7/10 |
| R3 | Minor Revision | 7/10 |
| DA | Major Revision | 5/10 |

### Editorial Decision: **Minor Revision**

The paper makes a genuine contribution to knowledge-constrained agent design for digital-twin scene construction. The technical approach is principled, the experiments are rigorous, and the honest reporting of limitations is commendable. However, several issues must be addressed before publication.

### Consolidated Revision Roadmap (Prioritized)

#### Priority 1: Critical (Must Address)

1. **Strengthen the agricultural domain connection.**
   - Add a case study or pilot deployment involving real or semi-real greenhouse data
   - Justify the ontology (Definition 4) with reference to real agricultural management needs
   - Address why asset_routing fails so badly (KF CVSR 0.083) with a detailed failure analysis

2. **Address benchmark validity concerns.**
   - Clarify the relationship between test_v2 and External300 — which is the primary evidence?
   - Acknowledge that rule_repair's perfect separation (KF=1.00, SA=0.00) may indicate benchmark design bias
   - Provide a sensitivity analysis of bootstrap results across multiple random seeds

3. **Add missing technical details.**
   - Formally define the scene graph G = (N, E) with node and edge types
   - Provide more detail on the Knowledge Compiler's conflict resolution mechanism
   - Clarify the unit-alias gap's impact on Bind-F1 scores

#### Priority 2: Important (Should Address)

4. **Improve reproducibility.**
   - Include a code availability statement (open source or otherwise)
   - Add confidence intervals to the ablation study results
   - Include the planned figures (Fig 1-5) in the manuscript

5. **Strengthen the writing.**
   - Add a high-level pipeline overview at the start of Section 3
   - Standardize terminology (choose one primary term)
   - Reduce repetition of limitation disclaimers
   - Connect general agent research (Section 2.2) to specific failure modes

6. **Clarify the cost analysis.**
   - Acknowledge that token-based cost ignores development and maintenance costs
   - Provide a more realistic total cost of ownership estimate

#### Priority 3: Minor (Nice to Have)

7. **Enhance the related work section.**
   - Contrast KAFarmTwin against specific agricultural digital twin systems (Pylianidis et al. 2021, Verdouw et al. 2021)
   - Strengthen the connection between general agent research and digital-twin scene construction

8. **Address the "traceability" claim.**
   - Provide a concrete example of an execution trace (Fig 5 or supplement)
   - Discuss how traces would be verified in a production agricultural context

9. **Clarify the "no state-of-the-art" disclaimer.**
   - Articulate clearly what readers should take away from the paper
   - Position the contribution as a method/system/case study, not an SOTA claim

### Expected Outcome After Revision

If the authors address Priority 1 and Priority 2 items, the paper should be suitable for publication in COMPAG. The technical contribution is sound, the experiments are rigorous, and the honest reporting of limitations is a strength. The main gap is the connection to real-world agricultural deployment, which can be partially addressed through a case study or pilot deployment.

---

## Appendix: Cross-Paper Tension Inventory

No cross-paper tensions were assessed because this review evaluates a single manuscript. The tension inventory is not applicable.

---

## Appendix: Evidence Quality Summary

| Evidence Type | Quality Level | Assessment |
|:-------------|:-------------|:-----------|
| External300 main results | Level II (controlled experiment) | Strong — large sample, pre-specified metrics, paired analysis |
| test_v2 multi-baseline | Level III (controlled, small sample) | Moderate — small sample (n=20), benchmark contact bias |
| Ablation study | Level III (controlled) | Strong — clean component isolation, honest reporting |
| Cross-model generalization | Level II (pre-registered) | Strong — pre-registered, 4 new model families |
| Safety/failure analysis | Level IV (diagnostic) | Strong — consistent across models, mechanistic explanation |
| Implementation details | Level V (descriptive) | Moderate — sufficient for understanding, insufficient for replication |

---

*Review completed 2026-09-01. This review represents the independent assessments of five simulated reviewers and does not constitute an official editorial decision.*
