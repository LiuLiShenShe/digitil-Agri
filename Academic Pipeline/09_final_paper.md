# KAFarmTwin: A Knowledge-Constrained Agent Approach for Traceable Digital Twin Scene Construction in Protected Agriculture

**Author A**<sup>a</sup>, **Author B**<sup>a,b</sup>, **Author C**<sup>a</sup>

<sup>a</sup> Affiliation 1, City, Country
<sup>b</sup> Affiliation 2, City, Country

**Corresponding author:** Author B (email@university.edu)

---

## Abstract

Digital twins in protected agriculture require greenhouse structures, crops, devices, sensors, 3D assets, and operational data to be organized into a common object graph that is queryable, traceable, and verifiable. Existing scene-construction workflows remain largely manual, whereas unconstrained large language model (LLM) agents can produce incomplete hierarchies, invalid data-binding contracts, mismatched assets, and execution traces that describe rather than prove tool use. This paper presents KAFarmTwin, a knowledge-constrained agent method that separates semantic interpretation from deterministic constraint enforcement. An LLM converts natural-language requests into a compact Intent Intermediate Representation (IntentIR). A deterministic Knowledge Compiler expands the IntentIR using agricultural ontology, binding vocabulary, unit registry, and asset-routing policies. Rule violations trigger typed repair: the LLM selects an admissible operator while a deterministic executor instantiates parameters and commits only when re-validation does not increase fatal violations. We evaluate on a frozen development-contact benchmark (test_v2, 20 tasks) and an author-generated, author-reviewed controlled benchmark (External300, 300 tasks, five categories). On External300, KAFarmTwin achieves a Complete-and-Valid Scene Rate (CVSR) of 0.717 versus 0.480 for SingleAgent (+23.7 pp; McNemar $p = 8.45 \times 10^{-17}$), with the improvement concentrated in rule-repair tasks (60 of 71 additional successes, all D1 single-rule R4 violations). A diagnostic decomposition of the unconstrained repair baseline reveals 100% Semantic Repair Recognition Rate (the LLM correctly repairs all objects and relations) but only 10% Structured Execution Success Rate (the LLM omits bindings in 90% of tasks), isolating structured output production—not semantic understanding—as the bottleneck that typed operators and deterministic execution address. Excluding rule repair, the paired difference narrows to +4.6 pp. Asset routing remains weak (CVSR 0.083), but post-hoc ID-invariant auditing shows 78% of failures are asset-routing policy errors rather than structural construction failures. Four additional model families reproduce the positive KF–SA direction. These results support separating LLM semantic decisions from executable domain constraints for scene and binding construction under controlled conditions, but do not establish open-world generalization or field-deployed performance.

**Keywords:** protected agriculture; digital twin; knowledge-augmented AI; LLM agent; knowledge constraint; typed repair; scene construction


---

**Fig. 1.** KAFarmTwin system architecture. Three-stage pipeline: (a) LLM-based IntentIR parsing, (b) deterministic Knowledge Compilation using ontology, mapping, binding, unit, constraint, and asset-policy modules, (c) validation-triggered typed repair. The LLM handles semantic parsing and repair-operator selection; graph expansion, parameter instantiation, patch application, and re-validation are deterministic. The shaded region marks the stochastic semantic layer; the unshaded region marks the deterministic execution layer.

**Fig. 2.** External300 CVSR by task category. Grouped bar chart: KAFarmTwin (KF) versus SingleAgent (SA) for rule_repair (1.00 vs. 0.00), scene_construction (0.50 vs. 0.40), asset_routing (0.083 vs. 0.00), data_binding (1.00 vs. 1.00), memory_query (1.00 vs. 1.00). Improvement concentrated in rule repair; ceiling effects in data binding and memory query.

**Fig. 3.** Ablation results. (a) CVSR: full 0.550, no_compiler 0.370, no_typed_repair 0.580, no_ontology 0.530. (b) Fatal rate: 0.000, 0.010, 0.220, 0.000. Typed repair contributes safety rather than CVSR.

**Fig. 4.** Cross-model robustness. Point estimates and 95% CI for KF–SA CVSR difference across five families: DeepSeek-V4-Flash (+23.67 pp), Kimi-K2.6 (+18.00 pp), MiniMax-M2.5 (+25.67 pp), Qwen3.6-27B (+21.67 pp), GLM-5.2 (+24.33 pp). All lower bounds positive.

**Fig. 5.** Execution-trace example. Links IntentIR, tool-call identifiers, evidence identifiers, validation findings, selected repair operator, deterministic patch, and post-repair validation. Distinguishes executable evidence from LLM-generated narration.

---

## 1. Introduction

Digital twins create dynamic mappings among virtual models, physical objects, and operational data (Grieves, 2014; Tao et al., 2019; Jones et al., 2020). In protected agriculture, production management spans greenhouse compartments, plots, crop rows, plants, sensors, cameras, irrigation devices, and time-stamped events (Pylianidis et al., 2021; Verdouw et al., 2021; Walter et al., 2017). A 3D digital-twin scene provides a spatial-semantic layer when objects are linked to business objects, sensor streams, and assets rather than treated as visual geometry alone.

Constructing this layer is labor-intensive. A greenhouse scene requires a valid object hierarchy, spatial placement, 3D-asset assignment, sensor–actuator associations, unit and timestamp normalization, and traceable construction records. LLM agents offer a natural-language interface to this problem, but direct generation of the complete scene by a general-purpose agent creates recurrent failure surfaces: omitted hierarchy nodes, invalid data-binding contracts, mismatched assets, and textual traces that claim tool use without carrying machine-verifiable evidence. Critically, these failures are not primarily language-understanding errors. An LLM can correctly identify what a scene should contain—the required objects, their types, and their relationships—while still failing to produce the schema-compliant structured output (bindings, traces, deterministic state) that a digital-twin system requires.

This observation motivates a different architectural boundary. KAFarmTwin separates **semantic repair recognition** from **contract-complete state execution**. The LLM produces a compact IntentIR capturing semantic candidates. A deterministic Knowledge Compiler expands hierarchy, bindings, units, and asset routes. Validation findings trigger typed RepairTickets; the LLM selects an admissible operator, and a deterministic executor instantiates, applies, and validates the patch under a transactional commit criterion. Agricultural knowledge is implemented as executable transformations, not prompt-supplemented prose.

The contributions are:

1. **A semantic/execution boundary for digital-twin scene construction.** IntentIR separates natural-language interpretation from complete scene instantiation, enabling independent analysis of semantic understanding versus structured output production.

2. **A deterministic Knowledge Compiler with typed transactional repair.** The compiler expands ontology, hierarchy, bindings, units, and asset policies. Typed repair operators have explicit applicability and side-effect boundaries; committed repairs satisfy a fatal-violation non-increase property.

3. **A diagnostic decomposition isolating the structured-output bottleneck.** On 60 D1 rule-repair tasks, an unconstrained repair baseline achieves 100% Semantic Repair Recognition Rate but only 10% Structured Execution Success Rate, demonstrating that the LLM understands repairs yet fails to produce contract-complete scene state. KAFarmTwin's typed operators and deterministic execution bridge this gap, achieving 60/60 CVSR on the same tasks. The empirical support is limited to D1 R4 repairs; task homogeneity constrains generalization claims.

## 2. Related work

### 2.1. Agricultural digital twins

Digital-twin research has expanded from manufacturing to agricultural production-process modelling (Tao et al., 2019; Verdouw et al., 2021; Pylianidis et al., 2021). Agricultural applications emphasize sensor-data integration, crop monitoring, and visualization (Liakos et al., 2018; Kamilaris and Prenafeta-Boldú, 2018). Semantic-web resources such as AgroPortal (Jonquet et al., 2018) and SSN/SOSA (Compton et al., 2012; Janowicz et al., 2019) provide vocabularies for sensors and observations. These establish the value of explicit semantics but do not solve scene construction as a graph-and-contract generation problem.

### 2.2. LLM agents and tool-mediated execution

LLM agents extend generation with task decomposition, tool use, and intermediate state (Wang et al., 2023; Xi et al., 2023). ReAct interleaves reasoning and actions (Yao et al., 2023a), Toolformer demonstrates API use (Schick et al., 2023), and chain-of-thought improves decomposition (Wei et al., 2022). Multi-agent approaches divide roles (Li et al., 2023). These improve LLM interaction with external systems, but tool availability does not guarantee domain-contract satisfaction. An agent may invoke correct tools while producing illegal relations, inconsistent assets, or incomplete traces.

### 2.3. Knowledge augmentation and neurosymbolic execution

Knowledge-augmented AI incorporates retrieval, knowledge graphs, and rule systems (Lewis et al., 2020; Gao et al., 2023; Hogan et al., 2021). Neurosymbolic research separates neural interpretation from symbolic constraint checking (d'Avila Garcez and Lamb, 2023). KAFarmTwin follows this separation at the execution level: agricultural knowledge is compiled into deterministic transformations, not appended to prompts.

### 2.4. Traceability and execution provenance

Long-term-memory research highlights persistent state (Park et al., 2023; Shinn et al., 2023). Protected-agriculture digital twins additionally require temporal provenance. A language model can narrate tool use without corresponding calls; KAFarmTwin distinguishes declarative text from executable trace evidence, making trace completeness part of scene validity.

## 3. Materials and methods

### 3.1. Problem formulation

Let the construction input be $Q = (q, D_s, A, M_t, R, K)$, where $q$ is the natural-language request, $D_s$ the available data, $A$ the asset registry, $M_t$ optional memory, $R$ the validation-rule set, and $K$ the deterministic knowledge modules.

The output state is $Y = (G, B, V, T)$, where $G = (N, E)$ is a typed attributed scene graph, $B$ the data and asset bindings, $V$ the validation result, and $T$ the executable trace.

For each node $n \in N$, $\tau(n) \in C$ denotes its ontology type and $\alpha(n)$ its attributes. For each edge $e = (n_i, n_j) \in E$, $\rho(e) \in R_o$ denotes its relationship type. Let $\{\phi_r\}_{r \in R}$ be rule predicates with $\phi_r(Y) = 1$ when satisfied. The fatal-violation count is $F(Y) = \sum_{r \in R_f} \mathbb{1}[\phi_r(Y) = 0]$.

The fully valid output set is $\mathcal{F}(Q) = \{Y \mid \phi_r(Y) = 1, \forall r \in R_{\text{required}}\}$. CVSR is $\frac{1}{|\mathcal{T}|} \sum_{i=1}^{|\mathcal{T}|} \mathbb{1}[Y_i \in \mathcal{F}(Q_i)]$.

### 3.2. Agricultural ontology and executable knowledge

The ontology is $K_o = (C, R_o, P, I_o)$, where $C$ contains object categories (Greenhouse, Plot, CropRow, Plant, Sensor, Camera, Device, Trait, Event, Asset), $R_o$ contains relationship types, $P$ contains attribute schemas, and $I_o$ contains instantiated entities.

Domain knowledge is represented as six deterministic modules: (1) Ontology—admissible types and hierarchy; (2) Constraint—device defaults, asset classes, rule-linked restrictions; (3) Mapping—parent resolution and child lookup; (4) Binding vocabulary—canonical metrics and binding records; (5) Asset policy—object-type and crop-specific routing; (6) Unit registry—canonical units and metric mappings.

### 3.3. Intent Intermediate Representation

The LLM maps request $q$ to $I = f_\theta(q) = (O_{\text{cand}}, E_{\text{cand}}, B_{\text{cand}}, P_{\text{cand}})$, containing candidate objects, relations, bindings, and preferences. IntentIR preserves semantic information while reducing instance-level stochastic generation. Required hierarchy, canonical bindings, and asset routes are supplied downstream by deterministic modules.

### 3.4. Deterministic Knowledge Compiler

The compiler is a deterministic mapping $\mathcal{C}_K: I \rightarrow (G_0, B_0, A_0)$, with $\mathcal{C}_K = \mathcal{C}_{\text{asset}} \circ \mathcal{C}_{\text{bind}} \circ \mathcal{C}_{\text{graph}}$.

**Algorithm 1.** Knowledge Compiler
1. **Graph expansion.** Resolve types, insert hierarchy nodes, normalize multiplicities, assign deterministic IDs.
2. **Binding compilation.** Map metrics to canonical vocabulary, normalize units, create binding records.
3. **Asset-route compilation.** Resolve object-type and crop policy, select route, attach asset keys.
4. Return compiled state.

For identical IntentIR and knowledge snapshot, the compiler produces identical output.

### 3.5. Typed repair with transactional commit

Validation produces violations $\mathcal{V}(Y) = \{v_j = (r_j, s_j, z_j, m_j)\}$. Each repair operator $a = (\text{name}_a, \text{pre}_a, \text{schema}_a, \text{scope}_a, \text{effect}_a)$ has applicability, parameter constraints, writable scope, and permitted mutation class. For violation $v$, the admissible set is $\mathcal{A}(v) = \{a \in \mathcal{A} \mid \text{pre}_a(v) = 1\}$.

The LLM selects $a^* = \pi_\theta(v, \mathcal{A}(v))$, but the deterministic executor applies the mutation:

$$Y_{t+1} = \begin{cases} \tilde{Y}_{t+1}, & F(\tilde{Y}_{t+1}) \leq F(Y_t) \land \text{policy}(\tilde{Y}_{t+1}, a^*) = 1, \\ Y_t, & \text{otherwise.} \end{cases}$$

This yields **transactional non-degradation**: $F(Y_{t+1}) \leq F(Y_t)$ for committed repairs. It is not convergence.

### 3.6. Data binding and trace evidence

A binding $b = (o_i, d_j, r_{ij}, u_j, t_j, m_j)$ links a target object to a data source with relationship, unit, and temporal contract. The binding compiler normalizes metrics and rejects absent object references.

The trace records actual tool calls, evidence identifiers, validation findings, repair selections, and commit/rollback events. A textual claim such as "validation passed" is insufficient without a recorded validator call.

### 3.7. Rule validation

The validator implements ten checkpoint groups (Table 1): hierarchy (R1), binding (R2), spatial (R3), asset consistency (R4), camera (R5), device coverage (R6), trace completeness (R7), memory queries (R8), asset fallback (R9), and correctability (R10). Fatal findings contribute to $F(Y)$ and prevent CVSR satisfaction.

**Table 1.** Rule checkpoints R1–R10.

| Rule | Description |
|:----:|:------------|
| R1 | Object hierarchy legality |
| R2 | Data binding legality |
| R3 | Spatial layout legality |
| R4 | Asset type consistency |
| R5 | Camera legality |
| R6 | Device coverage legality |
| R7 | Execution-trace completeness |
| R8 | Memory-query legality |
| R9 | Missing-asset non-interruption |
| R10 | Error correctability |

### 3.8. Statistical evaluation

For paired task $i$, $\Delta = \frac{1}{|\mathcal{T}|} \sum (s_i^{\text{KF}} - s_i^{\text{SA}})$. A 95% CI uses 10,000 paired bootstrap resamples (Efron and Tibshirani, 1993). For McNemar's test (McNemar, 1947), with discordant counts $b$ (KF only) and $c$ (SA only), the two-sided exact p-value is $p = \min(1, 2 \sum_{k=0}^{\min(b,c)} \binom{X}{k} (1/2)^X)$.

External300 uses one execution per task-method pair; bootstrap intervals quantify task-sampling uncertainty, not inference-run variance.

## 4. System implementation

KAFarmTwin is a prototype validating that the knowledge-constrained pipeline can be realized as an invocable scene-construction service. The frontend uses Vue 3, TypeScript, Three.js, and Element Plus for 3D display, object tree, and trace visualization. The backend uses Go, Gin, sqlx, and MySQL for object management, binding, memory, asset governance, and agent orchestration. The experimental harness (experiments/v3) implements a shared Python framework: unified tool registry, budget controller, trace proxy, canonicalized output layer, and frozen evaluator (evaluator_v2.3), ensuring all methods compare under identical budget and scoring.

The prototype validates object-graph construction, typed repair, data binding, and trace mechanisms. It is not a production-grade agricultural control platform.

## 5. Results

### 5.1. Experimental setup

Five research questions guide the evaluation: **RQ1** overall KF–SA comparison; **RQ2** component contributions (ablation); **RQ3** fatal-violation and replay effects; **RQ4** latency and cost; **RQ5** cross-model robustness.

**Benchmarks.** test_v2 (20 tasks, five categories, five repeats, consulted during development) and External300 (300 tasks, five categories, one execution, author-generated and author-reviewed). Neither is an independent external test set.

**Table 2.** External300 task composition.

| Category | Count | Capability tested |
|:---------|------:|:-------------------|
| scene_construction | 60 | Hierarchy, spatial layout, relation completeness |
| asset_routing | 60 | Asset-policy routing, fallbacks, object-asset consistency |
| data_binding | 60 | Binding contracts: metrics, units, timestamps |
| rule_repair | 60 | Violation handling, typed repair, post-repair validation |
| memory_query | 60 | Pre-placed retrieval, answer boundaries, no side effects |

**Baselines.** All methods receive identical public task fields, vocabularies, rule text, tools, and budget limits (Table 3).

**Table 3.** Baseline definitions.

| Method | Purpose |
|:-------|:--------|
| SingleAgent-AllTools (SA) | Primary shared-tool baseline; no typed repair loop |
| GenericMultiAgent | Role decomposition without closed-loop enforcement |
| GenericRepair | Untyped generic repair without deterministic instantiation |
| ReAct | Reasoning-acting alternation without structured construction |
| **KAFarmTwin** | IntentIR → Knowledge Compiler → typed repair (proposed) |

### 5.2. Overall performance: External300

**Table 4.** External300 main results (300 task-method executions).

| Method | CVSR | Obj-F1 | Rel-F1 | Bind-F1 | Crit-Rec | Fatal | Ev-P | Replay | Cost |
|:-------|-----:|-------:|-------:|--------:|---------:|------:|-----:|-------:|-----:|
| KAFarmTwin | **0.717** | 0.690 | 0.700 | 0.594 | **1.000** | **0.000** | **1.000** | **0.808** | $0.104 |
| SingleAgent | 0.480 | 0.635 | 0.379 | 0.200 | 0.950 | 0.250 | 0.947 | 0.455 | $0.085 |

KF succeeds on 215/300, SA on 144/300. Paired difference: **+23.67 pp** (95% CI [+18.33, +29.00]; McNemar $p = 8.45 \times 10^{-17}$; $b = 77$, $c = 6$). Cost ratio 1.21×.

### 5.3. Category-level decomposition

**Table 5.** External300 CVSR by task category.

| Category | KF | SA | $\Delta$ | Notes |
|:---------|---:|---:|----------:|:------|
| rule_repair | **1.00** | 0.00 | +1.00 | Dominant source of net improvement |
| scene_construction | 0.50 | 0.40 | +0.10 | Modest improvement |
| asset_routing | 0.083 | 0.00 | +0.083 | Weak absolute performance |
| data_binding | 1.00 | 1.00 | 0.00 | Ceiling; no comparative evidence |
| memory_query | 1.00 | 1.00 | 0.00 | Ceiling; no comparative evidence |

Of 71 additional KF successes, 60 (84.5%) come from rule repair. **Excluding rule repair, the paired difference narrows to +4.6 pp** (KF 155/240 = 0.646, SA 144/240 = 0.600). The aggregate result is therefore heavily concentrated in the repair category.

Post-hoc analysis (Appendix A3) confirms all 60 rule-repair tasks are D1 difficulty: single-rule R4 violations with explicit fix targets, requiring one deterministic repair step. SingleAgent routes these to `bare_seed_no_repair` by design (source: `single_agent.py:40–53`). The 60/60 vs 0/60 comparison measures repair-loop presence versus absence, not general repair reasoning.

### 5.4. Fair repair comparison

To assess whether the typed repair advantage persists when the baseline also has repair capability, we ran SingleAgent-DirectRepair: same LLM, same budget, but without Knowledge Compiler, typed RepairTickets, or deterministic executor. DirectRepair receives the broken scene and a free-form repair instruction.

**Table 6.** Three-way repair comparison on rule_repair ($n = 60$).

| Method | CVSR | Obj-F1 | Rel-F1 | Bind-F1 | Fatal | Ev-P | Replay | SRRR | SESR |
|:-------|-----:|-------:|-------:|--------:|------:|-----:|-------:|-----:|-----:|
| KAFarmTwin | **1.000** | **1.000** | **1.000** | **1.000** | **0** | **1.000** | **1.000** | 1.000 | **1.000** |
| DirectRepair | 0.000 | 1.000 | 1.000 | 0.100 | 43 | 0.000 | 0.000 | **1.000** | 0.100 |
| NoRepair | 0.000 | 1.000 | 0.000 | 0.000 | 60 | — | 1.000 | — | — |

SRRR = Semantic Repair Recognition Rate: fraction of tasks where the LLM output contains correct required objects and relations (Obj-F1 = 1.0 AND Rel-F1 = 1.0). SESR = Structured Execution Success Rate: fraction of tasks where the output satisfies all structural components including bindings (Obj-F1 = 1.0 AND Rel-F1 = 1.0 AND Bind-F1 > 0.5).

**The critical finding is the gap between SRRR and SESR for DirectRepair.** The LLM correctly recognizes and produces the required repair in all 60 tasks (SRRR = 100%): Object-F1 = 1.000 and Relation-F1 = 1.000 demonstrate that the LLM understands what to fix and preserves the scene's object and relation structure. However, the LLM fails to produce contract-complete structured output in 90% of tasks: in 54/60 tasks the bindings array is omitted entirely (Binding-F1 = 0.000, triggering R6 fatal violations), and in the remaining 6 tasks bindings are correct but execution evidence is absent. The **Structured Execution Success Rate is only 10%**.

This decomposition establishes that the bottleneck is not semantic understanding but structured output production. KAFarmTwin's typed operators bridge this gap: the LLM selects a bounded repair action, while deterministic code produces the binding records and execution evidence that unconstrained LLM output cannot reliably generate.

### 5.5. Ablation study

**Table 7.** Component ablation (test_v2, 100 runs per variant).

| Variant | Removed | CVSR | Bind-F1 | Fatal |
|:--------|:--------|-----:|--------:|------:|
| full | — | 0.550 | 0.529 | **0.000** |
| A1 no_compiler | Knowledge Compiler | 0.370 | 0.329 | 0.010 |
| A2 no_typed_repair | Typed repair loop | 0.580 | 0.329 | **0.220** |
| A3 no_ontology | Ontology constraint | 0.530 | 0.453 | 0.000 |

The `full` variant and main-experiment KF result (0.610) are independent samples. Component interpretation is within the ablation family only.

**Knowledge Compiler.** Removing the compiler reduces CVSR by 18 pp and Binding-F1 from 0.529 to 0.329. On the asset subset, CVSR falls from 0.95 to 0.00. The compiler is required for this subset; it does not solve general asset routing (External300 CVSR 0.083).

**Typed repair.** Removing repair does not reduce CVSR (0.580 vs 0.550) but raises fatal violations from 0.000 to 0.220. Typed repair acts as a safety mechanism.

**Ontology.** Removing ontology reduces Binding-F1 from 0.529 to 0.453 with no fatal effect. Point estimates from 20 task templates; effect-size uncertainty requires larger follow-up.

### 5.6. Cross-model robustness

**Table 8.** Cross-model KF–SA difference on External300.

| Model | KF | SA | $\Delta$ (pp) | 95% CI | McNemar $p$ |
|:------|---:|---:|--------------:|:-------|:------------|
| DeepSeek-V4-Flash | 0.717 | 0.480 | +23.67 | [+18.33, +29.00] | < 10$^{-6}$ |
| Kimi-K2.6 | 0.673 | 0.493 | +18.00 | [+13.00, +23.33] | < 10$^{-6}$ |
| MiniMax-M2.5 | 0.607 | 0.350 | +25.67 | [+19.67, +31.67] | < 10$^{-6}$ |
| Qwen3.6-27B | 0.697 | 0.480 | +21.67 | [+16.67, +26.67] | < 10$^{-6}$ |
| GLM-5.2 | 0.737 | 0.493 | +24.33 | [+18.33, +30.33] | < 10$^{-6}$ |

All four additional families satisfy the directional criterion (positive difference, lower bound above zero). This supports cross-model-family robustness under the common inference interface, not provider-independent generalization. KF fatal rates remain near zero; SA remains 0.23–0.29.

### 5.7. Asset-routing ID-invariant audit

KF achieves CVSR 0.083 (5/60) on asset routing. A post-hoc ID-invariant audit loads actual KF scene outputs and performs bipartite matching independent of node identifiers (Appendix A4).

**Table 9.** Asset-routing failure taxonomy (55 failed KF tasks).

| Failure cause | Count | % |
|:--------------|------:|--:|
| Asset-routing policy error | 43 | 78.2% |
| ID-only / canonicalization | 11 | 20.0% |
| Mixed | 1 | 1.8% |

After ID-invariant alignment: canonical Relation-F1 = 0.997, canonical Binding-F1 = 0.994. The dominant failure is a policy-level routing error—adding an unrequired device while omitting a required one—rather than a structural construction deficiency. Scene topology and binding construction are substantially more reliable than open-world asset selection.

### 5.8. Latency

**Table 10.** Latency (nearest-rank quantiles).

| Scope | KF p50 (s) | KF p95 (s) | SA p50 (s) | SA p95 (s) |
|:------|-----------:|-----------:|-----------:|-----------:|
| All tasks | 2.52 | 9.59 | 2.06 | 12.52 |
| LLM-invoking | 2.82 | 10.01 | 6.72 | 15.45 |

SA has lower overall p50 because 120/300 SA tasks are deterministic zero-LLM executions. Among LLM-invoking tasks, KF has lower latency, consistent with moving structural work to deterministic compilation.

### 5.9. Illustrative worked example

This is a controlled benchmark example, **not** a field validation study. Request: "Construct a 30 m × 8 m greenhouse for tomato cultivation with 4 crop rows of 10 plants each, temperature sensors, humidity sensors, a camera, and drip-irrigation devices."

The LLM emits an IntentIR; the Knowledge Compiler inserts the Greenhouse → Plot → CropRow → Plant hierarchy, deterministic IDs, asset routes, and canonical binding contracts. Validation reports an R5 camera violation; the repair controller exposes admissible actions; the LLM selects `fill_observes`; the deterministic executor resolves the target, applies the patch, re-validates, and commits under the non-decrease criterion. The trace records IntentIR, compiler calls, validator result, repair selection, deterministic patch, and post-repair validation with evidence identifiers.

## 6. Discussion

### 6.1. Semantic competence versus executable state

The DirectRepair diagnostic (Section 5.4) provides the paper's central mechanistic evidence: an unconstrained LLM achieves SRRR = 1.0 (correct objects and relations) but SESR = 0.1 (complete structured output). The LLM understands the repair semantics yet cannot reliably produce the binding records and execution evidence that the scene-construction protocol requires. This gap between semantic recognition and contract-complete execution is the primary justification for the KAFarmTwin architecture.

### 6.2. Why deterministic knowledge compilation helps

The Knowledge Compiler eliminates the need for the LLM to rediscover hierarchy, binding schema, and asset policy for every request. Ablation shows the compiler is required for asset-subset success and substantially improves binding consistency. However, the compiler's asset-routing policy remains weak (CVSR 0.083), demonstrating that deterministic compilation does not uniformly solve all construction sub-problems.

### 6.3. Why typed repair helps

Typed repair does not improve CVSR in the ablation sample but eliminates fatal violations (0.000 vs 0.220). The mechanism is bounded state mutation: the LLM selects from an admissible operator set while deterministic code handles instantiation and validation. This is a safety control, not a reasoning enhancement.

### 6.4. Why asset routing remains difficult

Open-world asset selection requires coverage of diverse crop types, equipment configurations, and routing policies. The current registry handles a limited set; 78% of failures are policy errors (adding an unrequired device while omitting a required one). Expanding the policy vocabulary is a targeted engineering improvement, not an architectural change.

### 6.5. What External300 establishes

The benchmark provides controlled methodological evidence for the semantic/execution separation on the tested task distributions. The paired comparison, ablation, and cross-model experiments support the architectural rationale. The aggregate +23.7 pp result must be interpreted by category, with 84.5% concentrated in D1 rule repair.

### 6.6. What it does not establish

The study does not establish: (1) open-world asset routing; (2) general repair capability beyond D1 R4 tasks; (3) independent out-of-distribution generalization; (4) operational benefit in a real protected-agriculture facility; (5) production readiness. These are addressed in Section 7 (Limitations) and left to future work.

## 7. Limitations

1. **No real-world deployment.** Experiments evaluate controlled scene-construction tasks, not operating greenhouses. No independent operator requests, physical device inventory, live sensor bindings, or expert acceptance study is included.

2. **Author-constructed benchmarks.** test_v2 was consulted during development. External300 is larger but author-generated and author-reviewed with single-author confirmation. Neither is independent external validation.

3. **D1-only repair subset.** All 60 rule-repair tasks are single-rule R4 violations with explicit fix targets. Performance on D2–D4 difficulty levels is untested.

4. **Asymmetric baseline design.** SingleAgent routes rule-repair tasks to no-repair by design. The 60/60 vs 0/60 comparison measures repair-loop presence, not general repair superiority.

5. **DirectRepair limited scope.** The failure-mode decomposition applies only to D1 R4 rule-repair tasks. DirectRepair performance on other task types or difficulty levels is unknown.

6. **Weak asset routing.** Asset-routing CVSR is 0.083. The paper demonstrates policy-constrained routing architecture more strongly than practically adequate open-world asset assignment.

7. **Single-run stochasticity.** External300 uses one execution per task-method pair. Bootstrap intervals quantify task-sampling uncertainty, not inference-run variance. Repeated inference on an independent subset is needed.

8. **Ontology and task scope.** The agricultural ontology and task templates do not cover every crop, facility, or equipment configuration.

9. **Cost scope.** Reported costs use provider token pricing and exclude engineering, knowledge-base curation, and infrastructure.

## 8. Conclusions

KAFarmTwin addresses protected-agriculture digital-twin scene construction by separating stochastic semantic interpretation from deterministic structural enforcement. Natural-language requests are reduced to IntentIR; a Knowledge Compiler expands hierarchy, bindings, units, and asset routes; typed repair enables bounded, transactionally safe state mutations.

On test_v2, KF achieves CVSR 0.610 vs 0.360 (SA), pass@5 0.700 vs 0.500, zero fatal violations. On External300, KF achieves CVSR 0.717 vs 0.480 (+23.67 pp), concentrated in D1 rule-repair tasks. A diagnostic decomposition reveals that the unconstrained repair baseline achieves 100% semantic repair recognition but only 10% structured execution success, confirming that the bottleneck is structured output production. Asset routing remains weak (CVSR 0.083), with 78% of failures being policy-level routing errors. Four model families reproduce the positive KF–SA direction.

The present evidence supports a specific claim: **encoding agricultural knowledge as deterministic compilation and bounded state transitions can improve scene-construction validity and execution safety relative to shared-tool LLM agents on controlled task distributions.** Semantic correctness alone is insufficient for executable digital-twin construction. The study does not establish open-world generalization, independent out-of-distribution performance, or operational benefit in a real protected-agriculture facility.

Future work should prioritize: independently collected greenhouse requests, repeated inference for stochastic stability, blinded benchmark annotation, and expert-in-the-loop validation of scene quality and construction effort.

---

## Data and code availability

The evaluation protocol, frozen evaluator (evaluator_v2.3, source fingerprint logged per run), configurations, task-generation scripts, and result records will accompany the manuscript in the project repository **[repository URL to be inserted]**. The External300 run is sealed (SHA-256: `b52f00c4bee3b43723689c3556300e0754a8ab9564b96341d05e88b591d40d91`). External300 tasks are author-generated and author-reviewed; this provenance is part of the released metadata.

## Appendix A: Supplementary analysis

### A3. Rule-repair task difficulty analysis

**Table A3.** Rule-repair difficulty classification.

| Property | Value |
|:---------|:------|
| Total tasks | 60 |
| Violation rule | R4 (asset-type mismatch) |
| Difficulty tier | D1 — all tasks |
| Explicit fix in prompt | 60/60 (100%) |
| Repair steps required | 1 |
| Template families | 4 × 15 (Pump→irrigation, Irrigation→irrigation, Camera→camera, Sensor→sensor) |

The D1–D4 taxonomy: D1 = single rule, explicit target; D2 = single rule, inference needed; D3 = multi-rule cascading; D4 = ambiguous/multiple valid repairs. All 60 tasks are D1.

### A4. Asset-routing ID-invariant audit

**Table A4.** Audit results (55 failed KF asset-routing tasks).

| Failure cause | Count | % |
|:--------------|------:|--:|
| Asset-routing policy error | 43 | 78.2% |
| ID-only / canonicalization | 11 | 20.0% |
| Mixed | 1 | 1.8% |

Canonical metrics after ID-invariant matching: Object-F1 0.810, Relation-F1 0.997, Binding-F1 0.994. Full node match: 12/55. No structural relation or object-type mismatches found.

### A5. DirectRepair failure decomposition

**Table A5.** Failure-mode decomposition ($n = 60$).

| Category | Count | Description |
|:---------|------:|:------------|
| A: Semantically complete, evidence fail | 6 | Correct nodes + edges + bindings, no execution trace |
| C: LLM omits bindings | 54 | Correct nodes + edges, empty bindings array |

The LLM produces correct objects (Object-F1 = 1.0) and relations (Relation-F1 = 1.0) in all 60 tasks but omits bindings in 54 tasks (triggering R6 fatal violations) and lacks execution evidence in the remaining 6. This confirms that the failure is in structured output production, not semantic understanding.

---

## References

Compton, M., Barnaghi, P., Bermudez, L., et al., 2012. The SSN ontology of the W3C semantic sensor network incubator group. J. Web Semant. 17, 25–32.

d'Avila Garcez, A., Lamb, L.C., 2023. Neurosymbolic AI: the 3rd wave. Artif. Intell. Rev. 56 (11), 12387–12406.

Efron, B., Tibshirani, R.J., 1993. An Introduction to the Bootstrap. Chapman & Hall/CRC, New York.

Gao, Y., Xiong, Y., Gao, X., et al., 2023. Retrieval-augmented generation for large language models: a survey. arXiv preprint arXiv:2312.10997.

Grieves, M., 2014. Digital Twin: Manufacturing Excellence through Virtual Factory Replication. White paper.

Hogan, A., Blomqvist, E., Cochez, M., et al., 2021. Knowledge graphs. ACM Comput. Surv. 54 (4), 1–37.

Janowicz, K., Haller, A., Cox, S.J.D., et al., 2019. SOSA: a lightweight ontology for sensors, observations, samples, and actuators. J. Web Semant. 56, 1–10.

Jones, D., Snider, C., Nassehi, A., et al., 2020. Characterising the digital twin: a systematic literature review. CIRP J. Manuf. Sci. Technol. 29, 36–52.

Jonquet, C., Toulet, A., Arnaud, E., et al., 2018. AgroPortal: a vocabulary and ontology repository for agronomy. Comput. Electron. Agric. 144, 126–143.

Kamilaris, A., Prenafeta-Boldú, F.X., 2018. Deep learning in agriculture: a survey. Comput. Electron. Agric. 147, 70–90.

Kojima, T., Gu, S.S., Reid, M., et al., 2022. Large language models are zero-shot reasoners. NeurIPS 35, 22199–22213.

Lewis, P., Perez, E., Piktus, A., et al., 2020. Retrieval-augmented generation for knowledge-intensive NLP tasks. NeurIPS 33, 9459–9474.

Li, G., Hammoud, H., Itani, H., et al., 2023. CAMEL: communicative agents for mind exploration of large language model society. NeurIPS 36, 51991–52008.

Liakos, K.G., Busato, P., Moshou, D., et al., 2018. Machine learning in agriculture: a review. Sensors 18 (8), 2674.

McNemar, Q., 1947. Note on the sampling error of the difference between correlated proportions or percentages. Psychometrika 12, 153–157.

Park, J.S., O'Brien, J., Cai, C.J., et al., 2023. Generative agents: interactive simulacra of human behavior. UIST, pp. 1–22.

Pylianidis, C., Osinga, S., Athanasiadis, I.N., 2021. Introducing digital twins to agriculture. Comput. Electron. Agric. 184, 105942.

Schick, T., Dwivedi-Yu, J., Dessi, R., et al., 2023. Toolformer: language models can teach themselves to use tools. NeurIPS 36, 68539–68551.

Shinn, N., Cassano, F., Gopinath, A., et al., 2023. Reflexion: language agents with verbal reinforcement learning. NeurIPS 36, 8634–8652.

Staab, S., Studer, R. (Eds.), 2009. Handbook on Ontologies. Springer, Berlin.

Tao, F., Zhang, H., Liu, A., Nee, A.Y.C., 2019. Digital twin in industry: state-of-the-art. IEEE Trans. Ind. Inform. 15 (4), 2405–2415.

Verdouw, C., Tekinerdogan, B., Beulens, A., Wolfert, S., 2021. Digital twins in smart farming. Agric. Syst. 189, 103046.

Walter, A., Finger, R., Huber, R., Buchmann, N., 2017. Smart farming is key to developing sustainable agriculture. Proc. Natl. Acad. Sci. 114 (24), 6148–6150.

Wang, L., Ma, C., Feng, X., et al., 2023. A survey on large language model based autonomous agents. arXiv preprint arXiv:2308.11432.

Wei, J., Wang, X., Schuurmans, D., et al., 2022. Chain-of-thought prompting elicits reasoning in large language models. NeurIPS 35, 24824–24837.

Wolfert, S., Ge, L., Verdouw, C., et al., 2017. Big data in smart farming: a review. Agric. Syst. 153, 69–80.

Xi, Z., Chen, W., Guo, X., et al., 2023. The rise and potential of large language model based agents: a survey. arXiv preprint arXiv:2309.07864.

Yao, S., Zhao, J., Yu, D., et al., 2023a. ReAct: synergizing reasoning and acting in language models. ICLR.

Yao, S., Yu, D., Zhao, J., et al., 2023b. Tree of thoughts: deliberate problem solving with large language models. NeurIPS 36, 11809–11822.
