# KAFarmTwin: A Knowledge-Constrained Agent Approach for Traceable Digital Twin Scene Construction in Protected Agriculture

**Author A**<sup>a</sup>, **Author B**<sup>a,b</sup>, **Author C**<sup>a</sup>

<sup>a</sup> Affiliation 1, City, Country
<sup>b</sup> Affiliation 2, City, Country

**Corresponding author:** Author B (email@university.edu)

---

## Abstract

Digital twins in protected agriculture require organizing greenhouses, crops, devices, and sensors into queryable, traceable, and verifiable object networks, yet existing scene construction pipelines rely heavily on manual modelling and configuration. Although large language model (LLM) agents can generate candidate digital-twin scenes from natural-language requests, they frequently produce outputs with missing object hierarchies, invalid binding contracts, mismatched 3D assets, and unauditable execution traces, rendering the results unsuitable for object-level monitoring, fault localization, and production review. This paper presents KAFarmTwin, a knowledge-constrained agent method for protected-agriculture digital-twin scene construction. The approach decomposes the task into three stages: (i) the LLM parses natural-language requirements into a compact Intent Intermediate Representation (IntentIR); (ii) a deterministic Knowledge Compiler expands the IntentIR into a scene graph constrained by an agricultural object ontology, binding vocabulary, and asset routing policies; (iii) when validation detects constraint violations, the LLM selects repair operators from a typed action space, while a deterministic executor instantiates and applies admissible parameters, guaranteeing that no destructive patches are introduced. We evaluate KAFarmTwin on two benchmarks: a frozen benchmark test_v2 (20 tasks across five categories, 5 repeats per task-method pair) and a larger author-reviewed controlled benchmark External300 (300 tasks, five categories of 60 each, single execution per task-method pair). On External300, KAFarmTwin achieves a Complete-and-Valid Scene Rate (CVSR) of 0.717 versus 0.480 for the strongest fair baseline (SingleAgent), a paired improvement of +23.7 percentage points (95% CI [+18.3, +29.0]; McNemar exact test *p* < 10<sup>−6</sup>), with a fatal-violation rate of 0.000 versus 0.250. Ablation studies demonstrate that the Knowledge Compiler is decisive for asset construction (asset-category CVSR drops from 0.95 to 0.00 when removed), typed repair contributes safety rather than overall CVSR (removing it raises fatal violations from 0 to 0.22), and ontology constraints improve binding quality (Binding-F1 drops from 0.529 to 0.453 when disabled). Cross-model-family generalization experiments on four additional model families show a consistent direction: paired KF–SA differences of +18.0 to +25.7 percentage points with all 95% CI lower bounds positive. We do not claim state-of-the-art performance; both benchmarks have known limitations, and results must not be read as generalization to unseen data.

**Keywords:** protected agriculture; digital twin; knowledge-augmented AI; LLM agent; knowledge constraint; typed repair; scene construction

---

## 1. Introduction

Digital twins create dynamic mappings between virtual models, physical objects, and operational data, providing a critical technical pathway for state awareness, process analysis, and decision support in complex systems (Grieves, 2014; Tao et al., 2019; Jones et al., 2020). In protected agriculture, greenhouse production management is evolving from environment-level monitoring toward object-level, process-oriented, and traceable management (Pylianidis et al., 2021; Verdouw et al., 2021; Walter et al., 2017). Traditional monitoring systems typically centre on indicators such as temperature, humidity, light intensity, and device status, which can describe local production environments but cannot uniformly represent the spatial, semantic, and temporal relationships among greenhouses, plots, crop rows, individual plants, sensors, cameras, irrigation equipment, phenotypic metrics, and production events. Three-dimensional (3D) digital twins provide a shared spatial vehicle for these objects, enabling sensor data, phenotypic records, irrigation events, and historical states to be bound to specific agricultural objects, thereby supporting object-level queries, anomaly localization, and production process review (Liakos et al., 2018; Kamilaris and Prenafeta-Boldú, 2018).

However, existing agricultural digital-twin and 3D visualization systems primarily emphasize monitoring, display, and data aggregation (Pylianidis et al., 2021; Drury et al., 2019). Scene construction remains heavily dependent on manual modelling, drag-and-drop configuration, and manual assignment of data interfaces, asset models, and spatial positions. This process is inefficient, difficult to reuse, and prone to broken object relationships. For example, the same sensor may exist as a model object in the 3D scene, a device object in the business system, and a data-source object in the time-series database; without a unified object graph and binding rules, downstream question-answering or decision systems cannot determine which greenhouse, crop row, or plant the data belongs to.

LLM-based agents offer new automation possibilities for digital-twin scene construction. An agent can understand natural-language requirements such as "construct a 30 m × 8 m tomato greenhouse with crop rows, sensors, cameras, and drip-irrigation equipment" and generate object lists, 3D layouts, and data bindings through tool calls (Wei et al., 2022; Yao et al., 2023a,b; Wang et al., 2023; Xi et al., 2023). Nevertheless, directly deploying general-purpose LLMs or unconstrained agents still faces three critical challenges:

1. **Object-graph structural integrity.** The model may omit intermediate layers such as plots or crop rows, or generate semantically incorrect *contains*, *monitors*, and *controls* relationships.
2. **Consistent binding of 3D assets, business objects, and runtime data.** For example, binding a water-pump asset to a plant model, or generating phenotypic metrics without units, timestamps, or object attribution.
3. **Auditable execution evidence.** Declarative execution traces can describe that validation was performed, but cannot prove which tools were actually invoked, which knowledge was used, or whether rule checks truly passed.

To address these challenges, this paper proposes KAFarmTwin, a knowledge-constrained agent method for protected-agriculture digital-twin scene construction. The core insight is to separate *semantic understanding* (where LLMs excel) from *structural constraint satisfaction* (where deterministic code excels). The LLM performs semantic understanding and candidate generation through a compact Intent Intermediate Representation (IntentIR); a deterministic Knowledge Compiler expands the IntentIR into a scene graph constrained by agricultural ontology, binding vocabulary, and asset policies; when validation detects violations, the LLM selects repair operators from a typed action space, while a deterministic executor instantiates and applies admissible parameters, guaranteeing safety convergence. The main contributions are:

1. A formal representation of the protected-agriculture digital-twin object graph and a rule system (R1–R10), with the method pipeline of *IntentIR → Knowledge Compilation → Typed Repair*. IntentIR carries semantic candidates; the Knowledge Compiler deterministically expands them into ontology-legal object graphs and binding plans; typed repair enforces safe convergence through the division of "LLM selects operators, deterministic executor instantiates parameters."
2. A knowledge-constrained scene-construction closed loop, integrating agricultural object ontology, binding vocabulary, multi-fidelity asset metadata, and rule sets into the planning, layout, asset routing, data binding, and validation pipeline, with evidence-numbered execution traces for auditability.
3. Two-level evaluation evidence: (a) a frozen benchmark test_v2 (20 tasks × 5 methods × 5 repeats) yielding a paired CVSR difference of +25 percentage points (95% CI [+9, +44]) and an exact cost ratio of 1.24× relative to the strongest fair baseline; (b) a larger author-reviewed controlled benchmark External300 (300 tasks × 2 methods) yielding CVSR 0.717 versus 0.480 (paired +23.7 pp, McNemar *p* < 10<sup>−6</sup>). Ablation studies isolate the independent contributions of the Knowledge Compiler (decisive for asset construction), typed repair (safety guarantee), and ontology constraints (binding quality).

This paper does not claim state-of-the-art performance. test_v2 was consulted during development and is a frozen benchmark rather than a hidden test set. External300 was generated and reviewed by the authors themselves (single-author confirmation, not independent double-blind review). Neither constitutes independent external validation, and results must not be extrapolated to unseen data.

The remainder of this paper is organized as follows. Section 2 reviews related work on agricultural digital twins, LLM agents, knowledge-augmented AI, and traceable reasoning. Section 3 details the KAFarmTwin method. Section 4 describes the system implementation. Section 5 presents experiments and analysis. Section 6 concludes with a summary and future directions.

## 2. Related work

### 2.1. Agricultural digital twins and 3D scene construction

Digital-twin research has gradually expanded from manufacturing into agricultural production process modelling and smart farm management (Tao et al., 2019; Verdouw et al., 2021; Pylianidis et al., 2021). In agricultural contexts, related work typically focuses on sensor data aggregation, crop state monitoring, machinery or greenhouse equipment management, and 3D visualization (Liakos et al., 2018; Drury et al., 2019; Kamilaris and Prenafeta-Boldú, 2018). These studies demonstrate the value of digital twins for agricultural state awareness, yet most systems treat the scene primarily as a data dashboard or visualization layer, lacking computable semantic relationships among objects, business entities, and historical events. For the multi-level object relationships of "greenhouse → plot → crop row → plant → sensor → event," if 3D models exist only as display elements, they cannot support object-level queries, historical tracking, or rule validation. This paper therefore focuses not on 3D visualization quality itself, but on automatically constructing digital-twin object graphs that include object hierarchies, data bindings, asset provenance, and rule validation results.

### 2.2. LLM agents and tool use

LLM agents extend single-turn text generation to interactive task execution by combining language understanding, task decomposition, tool use, and result aggregation (Wang et al., 2023; Xi et al., 2023). The ReAct framework alternates reasoning and acting (Yao et al., 2023a); Toolformer demonstrates that language models can learn to invoke external tools (Schick et al., 2023); chain-of-thought prompting, zero-shot reasoning, and tree-of-thoughts search further enhance problem decomposition and candidate exploration (Wei et al., 2022; Kojima et al., 2022; Yao et al., 2023b); multi-agent research discusses role assignment, task scheduling, and collaborative execution (Li et al., 2023; CAMEL). For digital-twin scene construction, agents can invoke model retrieval, layout solving, object querying, data binding, and rule validation tools to convert natural-language requirements into executable configurations. The problem is that general-purpose agents typically lack the domain-specific object hierarchies and business rules of protected agriculture, and may generate scenes that appear structurally complete but are semantically invalid. Merely increasing agent count does not naturally guarantee correctness; erroneous objects and bindings may propagate across multiple agents. Multi-agent collaboration must therefore be combined with executable knowledge constraints and re-entrant validation mechanisms.

### 2.3. Knowledge augmentation and neurosymbolic integration

Knowledge-augmented AI introduces symbolic knowledge into neural model reasoning through retrieval-augmented generation (RAG), knowledge graphs, ontologies, rule systems, and external memory (Lewis et al., 2020; Gao et al., 2023). RAG can mitigate model knowledge deficiency, but retrieved documents do not automatically become executable constraints. Knowledge graphs and ontologies can explicitly represent concepts, properties, and relationships, making them suitable for describing the object hierarchies, device control relationships, and data attribution relationships in protected agriculture (Hogan et al., 2021; Staab and Studer, 2009; Jonquet et al., 2018). The SSN/SOSA ontology provides a standardized representation for sensors, observations, samples, and actuators (Compton et al., 2012; Janowicz et al., 2019). Neurosymbolic integration further emphasizes that neural models can handle perception, language understanding, and candidate generation, while symbolic knowledge can enforce structural constraints, rule validation, and error correction (d'Avila Garcez and Lamb, 2023). This paper implements this principle in digital-twin object-graph construction, integrating knowledge not merely as prompts or retrieval materials but into the full pipeline of planning, layout, asset routing, binding, and validation.

### 2.4. Long-term memory and traceable reasoning

Research on long-term memory and interpretability examines whether model outputs possess trackable evidence, auditable processes, and explicit applicability boundaries (Park et al., 2023; Shinn et al., 2023). In protected agriculture, plant growth, environmental states, irrigation events, equipment maintenance, and anomaly alerts all carry temporal attributes. If a system generates only static 3D scenes, it cannot answer questions such as "how has the third row of tomatoes grown over the past 7 days" or "has the water pump been abnormal in the last 24 hours." Traceable reasoning requires recording which knowledge the agent used at each step, which tools were invoked, what outputs were produced, and whether validation passed. This paper incorporates object-level memory and agent execution traces into the digital-twin construction pipeline, distinguishing between declarative traces and execution traces carrying evidence identifiers (evidenceId) or call identifiers (callId), to prevent mistaking model self-narration for actual execution evidence.

## 3. Materials and methods

### 3.1. Problem formulation

We formalize protected-agriculture digital-twin scene construction as a knowledge-constrained object-graph generation task.

**Definition 1 (Input).** Given a natural-language user request, existing sensor and phenotypic data, a 3D asset library, object-level long-term memory, and an agricultural rule set, the input is:

$$Q = \{q, D_s, A, M_t, R\}$$

where $q$ denotes the natural-language request, $D_s$ denotes available sensor data, phenotypic data, and production events, $A$ denotes the 3D asset library (including existing GLB models, high-fidelity plant assets, 3D generation tasks, procedural models, and placeholder assets), $M_t$ denotes object-level long-term memory, and $R$ denotes the agricultural rule set (R1–R10).

**Definition 2 (Output).** The output is a digital-twin scene:

$$Y = \{G, B, V, T\}$$

where $G$ denotes the 3D digital-twin scene graph, $B$ denotes binding relationships between objects and assets, data, events, and business objects, $V$ denotes rule validation results, and $T$ denotes the agent execution trace.

**Definition 3 (Complete-and-Valid Scene Rate).** A run is counted as successful if and only if all of the following hold simultaneously: all critical objects are present, no fatal rule violations exist, all binding contracts are valid (including unit canonicalization and timestamp matching), and the execution trace passes validation. The Complete-and-Valid Scene Rate (CVSR) is defined as:

$$\text{CVSR} = \frac{1}{|{\mathcal{T}}|} \sum_{i=1}^{|{\mathcal{T}}|} \mathbb{1}[\text{valid}(Y_i)]$$

where $\mathcal{T}$ is the task set and $\text{valid}(Y_i) = 1$ iff all the above conditions hold for task $i$.

### 3.2. Agricultural object ontology

We represent agricultural domain knowledge as a formal ontology:

**Definition 4 (Agricultural Ontology).** The agricultural object ontology is defined as:

$$K_o = (C, R_o, P, I)$$

where $C$ is the set of object categories (Greenhouse, Plot, CropRow, Plant, Sensor, Camera, Device, Trait, Event, Asset), $R_o$ is the set of relationship types (*contains*, *belongs_to*, *monitors*, *observes*, *controls*, *has_asset*, *has_trait*, *has_event*), $P$ is the set of attribute schemas, and $I$ is the set of instances. The hierarchy constraint requires: Greenhouse *contains* Plot, Plot *contains* CropRow, CropRow *contains* Plant.

### 3.3. Intent Intermediate Representation (IntentIR)

The LLM's first responsibility is to parse the natural-language request into a structured IntentIR.

**Definition 5 (IntentIR).** The Intent Intermediate Representation is:

$$I = \{O_{\text{cand}}, E_{\text{cand}}, B_{\text{cand}}, P_{\text{cand}}\}$$

where $O_{\text{cand}}$ denotes candidate objects (type, count, key attributes), $E_{\text{cand}}$ denotes candidate hierarchy and monitoring relationships, $B_{\text{cand}}$ denotes candidate bindings (metrics, units), and $P_{\text{cand}}$ denotes asset and layout preferences.

IntentIR carries only semantic candidates without committing to legality—this is the critical design point separating *understanding* from *guarantee*. The LLM outputs a compact intent description (far below the ~1200-token output limit) rather than generating complete object instances, hierarchies, and IDs, which resolves the fundamental output-truncation problem in stepwise construction approaches.

### 3.4. Knowledge Compiler

The Knowledge Compiler deterministically expands IntentIR into a construction plan without invoking the LLM and without randomness—identical IntentIR always produces identical plans, making asset-class construction paths reproducible and cost-fixed.

**Algorithm 1.** Knowledge Compiler (`knowledge_compiler.build_scene_from_intent`)

---

**Input:** IntentIR $I = \{O_{\text{cand}}, E_{\text{cand}}, B_{\text{cand}}, P_{\text{cand}}\}$

**Output:** Constrained scene graph $G = (N, E)$ with bindings $B$

1. **Expand graph** ($\texttt{expand\_graph}$):
   - For each candidate object in $O_{\text{cand}}$, look up the ontology $K_o$ to determine its type, required parent, and attributes.
   - Insert missing intermediate hierarchy nodes (Greenhouse → Plot → CropRow → Plant) according to $K_o$.
   - Fold or split object counts that violate identity semantics.
   - Assign unique node identifiers.

2. **Bind scene** ($\texttt{bind\_scene}$):
   - Map candidate bindings $B_{\text{cand}}$ to the binding vocabulary's canonical metric names and units.
   - Generate sensor bindings with standardized units via the unit registry.
   - Generate asset bindings via the asset policy.

3. **Compile asset routes** ($\texttt{compile\_asset\_routes}$):
   - For each object type, look up the asset policy to determine the routing preference (high-fidelity, lightweight GLB, procedural model, or placeholder).
   - Assign asset keys from the asset registry.

---

The Compiler integrates six deterministic knowledge modules: (1) the **Ontology** module (object types, hierarchy, root identity); (2) the **Constraint** module (device defaults, asset classes, aggregatable types); (3) the **Mapping** module (identity-type detection, parent resolution, child finding); (4) the **Binding Vocabulary** module (sensor/asset binding construction, canonical metrics); (5) the **Asset Policy** module (type-to-asset mapping, crop policy); and (6) the **Unit Registry** module (metric-to-unit mapping, canonical unit normalization). All six modules are pure deterministic code with zero LLM invocations.

### 3.5. Typed Repair: LLM selects operators, deterministic executor instantiates

When the validator detects constraint violations according to rules R1–R10, each violation is annotated with a rule identifier, severity level (fatal/warning), and affected objects. The repair process enforces strict division of responsibilities:

**Definition 6 (Repair Action Space).** The typed action space $\mathcal{A}_r$ for rule $r$ is:

$$\mathcal{A}_r = \{\texttt{replace\_asset}, \texttt{attach\_to\_root}, \texttt{set\_placeholder}, \texttt{attach\_all\_rootless}, \texttt{fill\_observes}, \ldots, \texttt{ask\_user}\}$$

Each operator has explicit preconditions and effect types. The `ask_user` operator is reserved for ambiguous cases that cannot be mechanically mapped.

**Algorithm 2.** Typed Repair Loop

---

**Input:** Violated scene $G = (N, E)$ with bindings $B$, rule set $R$

**Output:** Repaired scene $G'$ or rollback record

1. Classify conflicts and prioritize by severity (fatal before warning).
2. For each fatal violation in priority order:
   a. Compute candidate actions: $\mathcal{A}_{\text{cand}} = \texttt{candidate\_actions\_for}(r)$
   b. **LLM call:** Select one action $a^* \in \mathcal{A}_{\text{cand}}$ based on the structured RepairTicket.
   c. **Deterministic execution:**
      - If $a^*$ is mechanically instantiable: $G' = \texttt{apply\_action}(a^*, r, \text{violation}, N, E, B)$
      - If $a^* = \texttt{ask\_user}$: LLM generates a full patch (1 additional LLM call).
   d. **Transactional safety:** Deep-copy $G$; apply patch; re-validate; if new fatal violations introduced, rollback.
3. **Early stopping:** If consecutive rounds yield identical warning-only signatures, terminate.
4. Return $G'$ with trace.

---

The key safety property is: any applied patch cannot introduce destructive modifications (such as deleting critical objects or writing illegal types). The ablation study (Section 5.6) confirms this: removing typed repair raises the fatal-violation rate from 0 to 0.22 in the rule-repair category, demonstrating that the mechanism contributes safety rather than scene-pass-rate improvement.

### 3.6. Object-level long-term memory and data binding

Facility agriculture digital-twin objects are not merely 3D models but also state memory units.

**Definition 7 (Object Memory).** The memory of object $o_i$ is:

$$M(o_i) = \{P_i, S_i^t, E_i^t, A_i, T_i\}$$

where $P_i$ denotes static attributes, $S_i^t$ denotes dynamic state at time $t$, $E_i^t$ denotes event records, $A_i$ denotes associated assets, and $T_i$ denotes operation records.

**Definition 8 (Data Binding).** A data binding is defined as:

$$B = \{(o_i, d_j, r_{ij}, t)\}$$

where $o_i$ is the target object, $d_j$ is the data source, $r_{ij}$ is the binding relationship type, and $t$ is the timestamp. History-query tasks require answers to be bounded by object, metric, time range, and event type, with the pre-placed retrieval store as the sole evidence source; query processes must not produce side effects on scene state.

### 3.7. Rule validation and agent execution traces

The rule set contains ten categories of rules covering object hierarchy, data binding, spatial layout, asset types, cameras, device coverage, execution traces, memory queries, missing assets, and error correction. Table 1 defines the rule checkpoint system.

**Table 1.** Rule checkpoints R1–R10.

| Rule | Description |
|:----:|:------------|
| R1 | Object hierarchy legality: greenhouse contains plots, plots contain crop rows, crop rows contain plants. |
| R2 | Data binding legality: sensors, phenotypic data, and events must have bound objects, units, and timestamps. |
| R3 | Spatial layout legality: objects do not float or exceed boundaries; crop rows lie within plot boundaries. |
| R4 | Asset type consistency: object type matches GLB model, high-fidelity asset, 3D generation task, procedural or placeholder asset policy. |
| R5 | Camera legality: cameras must have pose, observation target, and field-of-view coverage. |
| R6 | Device coverage legality: irrigation, fertigation, supplemental-lighting, and ventilation devices must bind control zones or service targets. |
| R7 | Agent execution trace completeness: must record planning, layout, asset routing, data binding, and validation steps. |
| R8 | Memory query legality: historical queries must constrain object, metric, time range, event type, and result count. |
| R9 | Missing-asset non-interruption: when GLB models are missing, placeholder objects and asset generation tasks must be created. |
| R10 | Error correctability: rule conflicts must output conflict type, triggering rule, and correction plan. |

Fatal sub-items of R4, R5, etc. are counted as fatal violations; the remainder count as warnings. CVSR requires zero fatal violations; the repair loop prioritizes fatal violations. Inspired by research on traceable agent execution (Park et al., 2023; Shinn et al., 2023), tools are classified as read-only, controlled-write, and prohibited; high-risk operations are blocked and logged as policy violations in the trace summary. Execution traces are scoring objects rather than supplementary logs: if critical steps are missing or the evidence chain breaks, the corresponding guardrail metrics (evidence precision, replay success) degrade.

### 3.8. Statistical evaluation protocol

**Paired comparison.** For each task $i$, let $s_i^{\text{KF}}$ and $s_i^{\text{SA}}$ denote binary success indicators (1 = complete-and-valid scene) for KAFarmTwin and SingleAgent, respectively. The paired difference is:

$$\Delta = \frac{1}{|\mathcal{T}|} \sum_{i=1}^{|\mathcal{T}|} (s_i^{\text{KF}} - s_i^{\text{SA}})$$

The 95% confidence interval is obtained by 10,000 paired bootstrap resamples of the task-level differences.

**McNemar's exact test.** Let $b$ denote the number of tasks where only KF succeeds, and $c$ the number where only SA succeeds. Under the null hypothesis of equal success probabilities:

$$X = b + c, \quad p = 2 \cdot \sum_{k=\min(b,c)}^{X} \binom{X}{k} \cdot 0.5^X$$

**Pass@k.** For each task, pass@k equals 1 if at least one of $k$ independent runs succeeds:

$$\text{pass@}k = \frac{1}{|\mathcal{T}|} \sum_{i=1}^{|\mathcal{T}|} \mathbb{1}\left[\sum_{j=1}^{k} s_i^{(j)} \geq 1\right]$$

**Gate criteria.** Acceptance requires: paired difference ≥ 3 pp with CI lower bound > 0; pass@5 strictly higher; Critical Recall ≥ 0.95; Fatal ≤ 0.01 and not exceeding the baseline; Evidence Precision ≥ 0.95; Replay ≥ 0.95; cost ratio ≤ 1.5×. This gate is engineering acceptance logic; its PASS does not constitute a state-of-the-art claim.

## 4. System implementation

KAFarmTwin is implemented as a prototype system for validating that the knowledge-constrained pipeline can be realized as an invocable scene-construction service. The system frontend is built on Vue 3, TypeScript, Vite, Three.js, Pinia, and Element Plus, responsible for 3D scene display, object tree, property panel, natural-language input, acceptance console, Agent Trace, and asset routing result display. The system backend is built on Go, Gin, sqlx, and MySQL, providing agricultural object management, scene object binding, object-level memory, asset metadata, asset quality auditing, asset routing, semantic construction, and acceptance aggregation interfaces.

The backend service adopts layered implementation for object management, scene binding, memory management, asset governance, and agent orchestration. The agent orchestration service extends the SceneBuilderAgent compatible entry to FarmTwinOrchestrator, exposing planning, layout, asset routing, data binding, and validation step evidence in trace.steps; the tool strategy classifies tools into read-only, controlled-write, and prohibited categories, with prohibited operations blocked and logged as policy violations. The experimental evaluation (experiments/v3) implements a shared harness in Python: a unified tool registry, budget controller (LLM calls / tool calls / repair-round limits), trace proxy, canonicalized output layer, and versioned evaluator, ensuring all methods compare under the same budget and scoring protocol.

The prototype system validates object-graph construction, typed repair, data binding, and trace mechanisms; it is not equivalent to a complete production-grade agricultural control platform. Real device closed-loop control, long-term operational stability, and larger-scale crop data will be extended in future work.

## 5. Results and discussion

### 5.1. Experimental setup

Experiments address four research questions: (RQ1) Does KAFarmTwin significantly outperform the strongest fair baseline on frozen benchmarks, and what is the magnitude and statistical confidence? (RQ2) What does each of the Knowledge Compiler, typed repair, and ontology constraint contribute independently? (RQ3) Is the cost overhead within an acceptable range? (RQ4) Does the advantage maintain directional consistency on a larger, more diverse task set?

**Benchmarks.** Two independent benchmarks are used:

*Benchmark A: test_v2.* A frozen benchmark of 20 tasks across five categories (4 per category), each run 5 times per method (LLM temperature 0.2, fixed random seed 20260804). The base model is DeepSeek-V4-Flash (SiliconFlow access). All methods share the same model access layer, budget constraints (30 LLM calls, 100 tool calls, 3 repair rounds per run), output schema, and rule text. The gold standard is held only by the frozen evaluator (evaluator_v2.3); its source fingerprint is logged with each run record. **Note:** test_v2 was consulted during development and is a frozen benchmark rather than a hidden test set or independent external test.

*Benchmark B: External300.* An author-reviewed controlled benchmark of 300 tasks across five categories of 60 each, with single execution per task-method pair (DeepSeek-V4-Flash, temperature 0.2). The generation, review, and unsealing protocol had deviations from the original plan (original plan: independent dual review + third-party adjudication; actual: single-author unified confirmation); complete disclosure is in Section 5.8 and project-internal `REVIEW_PROVENANCE_CORRECTION.md` / `PROTOCOL_DEVIATION_EXTERNAL300.md`.

**Table 2.** External300 task composition.

| Task Category | Count | Key Capability Tested |
|:-------------|------:|:-----------------------|
| scene_construction | 60 | Object hierarchy, spatial layout, relation-graph completeness |
| asset_routing | 60 | Knowledge-compiler-guided asset selection, placeholders, binding |
| data_binding | 60 | Sensor/device/phenotype binding contracts: metrics, units, timestamps |
| rule_repair | 60 | Violation detection, typed repair operator selection, safe convergence |
| memory_query | 60 | Pre-placed retrieval, answer boundaries, no side effects |

**Baseline methods.** To avoid the unfair comparison of a complete engineering system against a bare LLM, all methods receive identical public task fields, output structure, object types, relationship predicates, and R1–R10 rule text, and run within the same budget (Table 3).

**Table 3.** Baseline method definitions.

| Method | Setting | Purpose |
|:-------|:--------|:--------|
| SingleAgent-AllTools (SA) | Single agent with all shared tools, no repair loop | Strongest fair baseline (primary control) |
| GenericMultiAgent-AllTools | Multi-role division, shared knowledge, no closed-loop correction | Tests upper bound of role division without closed loop |
| GenericRepair-AllTools | Single agent + untyped generic repair | Tests effect of "having repair" without typed operators/deterministic executor |
| ReAct-AllTools | Reasoning-acting alternation, no structured output constraint | Weak baseline, exposes free-form execution failure modes |
| **KAFarmTwin-TypedRepair (Ours)** | IntentIR → Knowledge Compiler → Typed Repair → Ontology-constrained execution | Proposed method |

### 5.2. Main results: test_v2

Table 4 presents the main results from 500 runs (20 tasks × 5 methods × 5 repeats) on test_v2.

**Table 4.** Main results on test_v2 (100 runs per method).

| Method | CVSR ↑ | pass@5 ↑ | Obj-F1 ↑ | Crit-Recall ↑ | Rel-F1 ↑ | Bind-F1 ↑ | Fatal ↓ | Ev-P ↑ | Replay ↑ | Cost/run |
|:-------|-------:|---------:|---------:|--------------:|---------:|----------:|--------:|-------:|---------:|---------:|
| KAFarmTwin (Ours) | **0.610** | **0.700** | 0.800 | **1.000** | 0.534 | **0.529** | **0.000** | **1.000** | **1.000** | $0.00034 |
| SingleAgent | 0.360 | 0.500 | 0.685 | 0.900 | 0.391 | 0.127 | 0.320 | 0.900 | 0.607 | $0.00027 |
| GenericMultiAgent | 0.010 | 0.050 | 0.461 | 0.800 | 0.200 | 0.043 | 0.310 | 0.790 | 0.000 | $0.00110 |
| GenericRepair | 0.060 | 0.100 | 0.457 | 0.800 | 0.245 | 0.043 | 0.070 | 1.000 | 1.000 | $0.00044 |
| ReAct | 0.000 | 0.000 | 0.000 | 0.400 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | $0.00263 |

KAFarmTwin achieves a paired CVSR difference of **+25 percentage points** over SingleAgent (95% CI [+9, +44] pp; 20-task paired bootstrap, 10,000 resamples); pass@5 is 0.700 versus 0.500. All guardrail metrics pass: Critical Recall 1.000, Fatal 0.000 (SingleAgent 0.320), Evidence Precision 1.000, Replay 1.000. Cost: exact cost ratio 1.24×, below the 1.5× threshold. ReAct achieves CVSR 0.000 across all 20 tasks, confirming that unconstrained free-form execution fails entirely on structured scene-construction tasks.

### 5.3. Main results: External300

Table 5 reports directional-consistency results on the larger External300 benchmark.

**Table 5.** External300 main results (300 task executions per method).

| Method | CVSR ↑ | Obj-F1 ↑ | Rel-F1 ↑ | Bind-F1 ↑ | Crit-Recall ↑ | Fatal ↓ | Ev-P ↑ | Replay ↑ | Total Cost | Total Tokens |
|:-------|-------:|---------:|---------:|----------:|--------------:|--------:|-------:|---------:|-----------:|-------------:|
| KAFarmTwin (Ours) | **0.717** | 0.690 | 0.700 | 0.594 | **1.000** | **0.000** | **1.000** | **0.808** | $0.1035 | 668,769 |
| SingleAgent | 0.480 | 0.635 | 0.379 | 0.200 | 0.950 | 0.250 | 0.947 | 0.455 | $0.0854 | 472,722 |

The paired CVSR difference is **+23.67 pp** (95% CI [+18.33, +29.00] pp; 300-task paired bootstrap, 10,000 resamples); McNemar exact test: *b* = 77, *c* = 6, *p* < 10<sup>−6</sup> (exact tail 8.45 × 10<sup>−17</sup>). The odds ratio is 12.83. Cost: token ratio 1.41×, exact cost ratio 1.21×, below the 1.5× threshold.

**Category-level breakdown (Table 6).**

**Table 6.** External300 CVSR by task category.

| Category | KF | SA | Interpretation |
|:---------|---:|---:|:---------------|
| rule_repair | **1.00** | 0.00 | Primary improvement source: typed repair eliminates all fatal violations |
| scene_construction | 0.50 | 0.40 | Limited improvement |
| asset_routing | 0.083 | 0.00 | Absolute performance remains low; KF marginally better via placeholder mechanism |
| data_binding | 1.00 | 1.00 | Ceiling effect: both at maximum, no relative improvement |
| memory_query | 1.00 | 1.00 | Ceiling effect: deterministic synthetic data, both at maximum |

The advantage concentrates in rule_repair (1.00 vs. 0.00). scene_construction shows only limited improvement (0.50 vs. 0.40). asset_routing absolute performance remains low (0.083 vs. 0). data_binding and memory_query both reach ceiling (1.00 vs. 1.00), leaving no room for relative claims.

**Latency.** Reported at two granularities (Table 7):

**Table 7.** Latency (nearest-rank quantiles).

| Granularity | KF p50 (s) | KF p95 (s) | SA p50 (s) | SA p95 (s) |
|:-----|-----------:|-----------:|-----------:|-----------:|
| All tasks (*n* = 300) | 2.52 | 9.59 | 2.06 | 12.52 |
| LLM-invoking tasks | 2.82 | 10.01 | 6.72 | 15.45 |

In the all-tasks granularity, SA's median latency is lower because 120/300 SA tasks are deterministic zero-LLM tasks counted as near-zero. In the LLM-invoking-tasks granularity (comparing only tasks that truly call the model), KF is actually faster (p50 2.82 s vs. 6.72 s), consistent with the knowledge-compiled path reducing LLM burden.

### 5.4. Safety and failure analysis

The central mechanism chain is:

> Knowledge constraint (Knowledge Compiler + Ontology + Typed Repair) → Fewer illegal/inexecutable actions → Fewer fatal violations → Higher replay success → Higher CVSR

**Arrow 1: Knowledge constraint → Fatal↓ (strong support).** External300 DeepSeek: KF Fatal = 0.000, SA Fatal = 0.250. Ablation A2: removing typed repair raises Fatal from 0 to 0.22 (paired flips 22:0). Five-model generalization: KF Fatal all ≤ 0.003, SA Fatal all 0.23–0.29.

**Arrow 2: Fatal↓ → Replay↑ (supported).** External300: KF Replay 0.808 vs. SA 0.455. All 0.25 fatal tasks in SA are non-replayable. Ablation A2: removing repair reduces Replay from 1.00 to 0.80, consistent with fatal increase.

**Arrow 3: Replay↑ → CVSR↑ (supported but not sole factor).** Replay is a necessary condition for CVSR (non-replayable tasks cannot be complete-and-valid) but not sufficient—asset_routing has KF Replay = 1.00 yet CVSR only 0.083, indicating other failure factors (knowledge compiler path limitations).

**SA failure taxonomy on External300 rule repair (Table 8).**

**Table 8.** SA failure counts by rule type (External300 rule_repair category, *n* = 60).

| Rule | Meaning | SA Failures |
|:----:|:--------|------------:|
| R4 | Asset-type constraint violation (fatal) | 60 |
| R6 | Incomplete device coverage | 30 |
| R2 | Invalid data binding | 15 |
| R5 | Camera logic inconsistency | 10 |

KF achieves zero failures across all rule types. The dominance of R4 (asset-type constraint) failures in SA confirms that the Knowledge Compiler's deterministic asset routing is the primary differentiator.

### 5.5. Ablation study

Ablation is conducted under the v3 frozen protocol: 20 tasks × 5 repeats = 100 runs per variant, DeepSeek-V4-Flash, temperature 0.2. The full variant and the main-experiment KAFarmTwin are **independent random runs** (different samples under temperature 0.2); their CVSR difference (0.550 vs. 0.610) reflects inter-run variance, and they must not be compared as pairs. All contribution attribution is within the ablation family.

**Table 9.** Component ablation results (100 runs per variant).

| Variant | Removed Component | CVSR | Obj-F1 | Bind-F1 | Crit-Recall | Fatal ↓ | Cost/run |
|:--------|:------------------|-----:|-------:|--------:|------------:|--------:|---------:|
| full | (none) | 0.550 | 0.796 | 0.529 | 1.000 | **0.000** | $0.00033 |
| A1 (no_compiler) | Knowledge Compiler | 0.370 | 0.721 | 0.329 | 0.950 | 0.010 | $0.00044 |
| A2 (no_typed_repair) | Typed repair loop | 0.580 | 0.798 | 0.329 | 1.000 | **0.220** | $0.00018 |
| A3 (no_ontology) | Ontology constraint | 0.530 | 0.796 | 0.453 | 1.000 | 0.000 | $0.00052 |

The three components make independent, non-substitutable contributions:

**(1) Knowledge Compiler: decisive for asset construction.** Under A1, asset-category CVSR drops from 0.95 to **0.00** (all 4 asset tasks fail across all repeats); overall CVSR drops by 18 pp; Critical Recall degrades from 1.00 to 0.95. The Compiler is the critical path for deterministically expanding IntentIR into ontology-legal asset scenes.

**(2) Typed Repair: contributes safety, not CVSR.** Critically, A2's CVSR (0.580) is slightly *higher* than full (0.550); therefore, we cannot claim that repair improves scene pass rate. Its true value is safety: removing repair raises the fatal-violation rate from 0 to 0.22 (paired flips A2-fatal/full-clean = 22, reverse = 0). This confirms the "LLM selects operators, deterministic executor instantiates parameters" division as a *unidirectional safety guarantee*.

**(3) Ontology Constraint: improves binding quality.** A3's Binding-F1 drops from 0.529 to 0.453, while Critical Recall and Fatal remain unchanged. The ontology constraint trades within the type and side-effect policy boundary for more correct bindings.

### 5.6. Cross-model-family generalization

To test whether the method's advantage depends on a single model family, we conducted a pre-registered multi-model experiment (`MULTIMODEL_PREREGISTRATION_v2.md`, frozen 2026-08-25). Four additional model families—Kimi-K2.6 (Pro), MiniMax-M2.5, Qwen3.6-27B, and GLM-5.2—each run the complete External300 (300 tasks × KF/SA, single execution), totalling 2,400 method-task records across the four new models, plus the frozen DeepSeek-V4-Flash baseline.

**Table 10.** Cross-model-family generalization: External300 main metrics and paired statistics.

| Model Family | KF CVSR | SA CVSR | Δ (pp) | 95% CI | McNemar (*b*, *c*) | *p* |
|:-------------|--------:|--------:|-------:|:-------|:-------------------|:----|
| DeepSeek-V4-Flash (baseline) | 0.717 | 0.480 | +23.67 | [+18.33, +29.00] | (77, 6) | < 10<sup>−6</sup> |
| Kimi-K2.6 | 0.673 | 0.493 | +18.00 | [+13.00, +23.33] | (63, 9) | < 10<sup>−6</sup> |
| MiniMax-M2.5 | 0.607 | 0.350 | +25.67 | [+19.67, +31.67] | (91, 14) | < 10<sup>−6</sup> |
| Qwen3.6-27B | 0.697 | 0.480 | +21.67 | [+16.67, +26.67] | (69, 4) | < 10<sup>−6</sup> |
| GLM-5.2 | 0.737 | 0.493 | +24.33 | [+18.33, +30.33] | (88, 15) | < 10<sup>−6</sup> |

The pre-registered verdict is **MODEL_GENERALIZATION_PASS** (4/4 Δ > 0, 4/4 CI lower bound > 0, exceeding the required ≥ 3).

**Universal safety pattern across models.** KF Fatal ≈ 0, Evidence Precision ≈ 1.00, Replay ≈ 0.80 across all five models. SA Fatal 0.23–0.29, Binding-F1 ≤ 0.20, Replay 0.38–0.48 across all five models. The safety benefit of typed repair is model-agnostic.

**rule_repair: five-model perfect consistency.** KF rule_repair CVSR = 1.00 for all five models; SA = 0.00 for all five. This is a protocol-level difference (typed repair closed-loop mechanism), not a model-capability difference.

**Known anomaly: MiniMax-M2.5 data_binding.** KF data_binding CVSR = 0.27 on MiniMax (0.87–1.00 on other models). The cause is unknown; we report it honestly without exclusion. Even so, MiniMax achieves one of the largest Δ values (+25.67 pp), indicating the overall framework still provides substantial benefit despite this category-specific degradation.

**Scope boundary.** All five models are served through the same SiliconFlow inference interface; the experiment supports only *cross-model-family robustness*, not cross-provider generalization.

### 5.7. Binding failure analysis

Data-binding tasks represent the most transparent failure surface of the current method. Root causes have been identified and classified into two categories during development:

**Method-side defect (fixed, TN21/TN24).** The shared scene binding constructor initially omitted the timestamp field from its output template, while the public prompt explicitly declared the binding timestamp contract and the frozen evaluator enforced it—causing sensor binding mismatches due to missing timestamps. The fix deterministically writes the ISO-8601 timestamp declared in the public prompt into each binding's metadata (reading only the public prompt, not the gold standard). After fixing, TN21/TN24 Binding-F1 rose from 0.333/0.25 to **1.000**.

**Evaluator unit-alias gap (TN22/TN23).** TN22's standard unit °C versus the method's celsius, and TN23's klux/light versus lux/light_intensity, have no mappings in the frozen evaluator's unit-alias table. Even a perfectly correct method cannot score. This is a known benchmark/evaluator contract limitation (the evaluator cannot be modified during the frozen period); we report it as an honest capability boundary.

### 5.8. Threats to validity

1. **Benchmark contact bias.** test_v2 was repeatedly consulted during development and drove multiple repair cycles (including the method-side fix in Section 5.7). It is a *frozen benchmark rather than a hidden test set or independent external test*; results characterize the method's behaviour on a known task distribution. The current work lacks a truly private held-out external test, which is the most significant open threat.

2. **External300 review identity and protocol deviation.** External300 was generated and reviewed by the authors themselves: the original plan required independent dual review with third-party adjudication before unsealing, but actual unsealing used a single-author unified confirmation (human_review_mode = author_confirmation, reviewer count = 1, not independent, not double-blind, not gold standard). Both deviations are documented in project-internal files. Results can only be used as author-reviewed controlled benchmark evidence, not independent external validation.

3. **Model stochasticity.** LLM temperature is 0.2; independent runs of the same configuration exhibit variance (ablation full 0.550 vs. main experiment 0.610). test_v2 and ablation mitigate this variance through 5 repeats per configuration; External300 and cross-model experiments use single execution per task-method, estimating statistical uncertainty through task-level paired bootstrap.

4. **Unit-alias coverage.** The frozen evaluator's unit-alias table covers only canonical forms (%, celsius/c, ppm, etc.); non-canonical units (°C, klux) cause systematic mismatch (Section 5.7). This depresses all methods' bind scores and means bind-category metrics are highly sensitive to vocabulary coverage.

5. **Base model and inference interface.** v3 main line is validated on DeepSeek-V4-Flash. Cross-model generalization is supplemented by the pre-registered multi-model experiment (Section 5.6): four additional model families show consistent direction. However, all five models are served through the same SiliconFlow inference interface; the service does not expose immutable model weight snapshots; conclusions are limited to *cross-model-family robustness under the same interface*, not cross-provider generalization.

6. **Cost metric.** Cost is based on provider token pricing, which changes over time; the paper reports relative ratios (1.21×) rather than absolute-value conclusions.

## 6. Conclusions

This paper presents KAFarmTwin, a knowledge-constrained agent method for protected-agriculture digital-twin scene construction. The method pipeline is: Intent Intermediate Representation (IntentIR) → deterministic Knowledge Compilation → typed repair (LLM selects repair operators, deterministic executor instantiates and applies admissible parameters within type and side-effect policy boundaries). On the frozen benchmark test_v2 (20 tasks × 5 methods × 5 repeats, unified DeepSeek-V4-Flash base model and budget), KAFarmTwin achieves a paired CVSR difference of +25 pp (95% CI [+9, +44]) and a pass@5 of 0.70 versus 0.50, with zero fatal violations and exact cost ratio 1.24×. Ablation studies demonstrate three independent, non-substitutable component contributions: the Knowledge Compiler determines asset construction success, typed repair contributes fatal-violation elimination rather than scene pass rate, and ontology constraints improve binding correctness.

On the larger author-reviewed controlled benchmark External300 (300 tasks × 2 methods, single execution, DeepSeek-V4-Flash), KAFarmTwin achieves CVSR 0.717 versus 0.480 (paired +23.7 pp, 95% CI [+18.3, +29.0]; McNemar exact *p* < 10<sup>−6</sup>), with zero fatal violations versus 0.250, and exact cost ratio 1.21×. The advantage concentrates in rule repair (1.00 vs. 0.00); asset routing absolute performance remains low (0.083 vs. 0); data binding and memory query both reach ceiling (1.00 vs. 1.00). Cross-model-family generalization experiments (pre-registered) on four additional model families (Kimi-K2.6, MiniMax-M2.5, Qwen3.6-27B, GLM-5.2) replicate this direction: paired KF–SA differences of +18.0 to +25.7 pp with all 95% CI lower bounds positive, achieving pre-registered verdict MODEL_GENERALIZATION_PASS.

This paper simultaneously reports method boundaries: test_v2 is a frozen benchmark consulted during development, not a hidden or independent test; External300 was generated and reviewed by the authors (single-author unified confirmation, not independent double-blind); neither constitutes independent external validation, and results must not be extrapolated to unseen tasks. Data-binding tasks are limited by the frozen evaluator's unit-alias gap. Base model service endpoints do not expose immutable weight snapshots; the multi-model experiment supports only cross-model-family robustness under the same interface, not cross-provider generalization. This paper does not make state-of-the-art claims.

Future work will: (1) construct an independently collected external test set to evaluate genuine out-of-sample generalization; (2) expand unit-alias coverage in the evaluator; (3) repeat multi-model validation across multiple independent inference services; and (4) extend the system to support real device closed-loop control and larger-scale crop production data.

---

## References

Compton, M., Barnaghi, P., Bermudez, L., et al., 2012. The SSN ontology of the W3C semantic sensor network incubator group. J. Web Semant. 17, 25–32.

d'Avila Garcez, A., Lamb, L.C., 2023. Neurosymbolic AI: the 3rd wave. Artif. Intell. Rev. 56 (11), 12387–12406.

Drury, B., Fernandes, R., Moura, M.F., de Andrade Lopes, A., 2019. A survey of semantic web technology for agriculture. Inf. Process. Agric. 6 (4), 487–501.

Gao, Y., Xiong, Y., Gao, X., et al., 2023. Retrieval-augmented generation for large language models: a survey. arXiv preprint arXiv:2312.10997.

Grieves, M., 2014. Digital Twin: Manufacturing Excellence through Virtual Factory Replication. White paper.

Hogan, A., Blomqvist, E., Cochez, M., et al., 2021. Knowledge graphs. ACM Comput. Surv. 54 (4), 1–37.

Janowicz, K., Haller, A., Cox, S.J.D., Le Phuoc, D., Lefrançois, M., 2019. SOSA: a lightweight ontology for sensors, observations, samples, and actuators. J. Web Semant. 56, 1–10.

Jones, D., Snider, C., Nassehi, A., Yon, J., Hicks, B., 2020. Characterising the digital twin: a systematic literature review. CIRP J. Manuf. Sci. Technol. 29, 36–52.

Jonquet, C., Toulet, A., Arnaud, E., et al., 2018. AgroPortal: a vocabulary and ontology repository for agronomy. Comput. Electron. Agric. 144, 126–143.

Kamilaris, A., Prenafeta-Boldú, F.X., 2018. Deep learning in agriculture: a survey. Comput. Electron. Agric. 147, 70–90.

Kojima, T., Gu, S.S., Reid, M., Matsuo, Y., Iwasawa, Y., 2022. Large language models are zero-shot reasoners. In: Advances in Neural Information Processing Systems 35, pp. 22199–22213.

Lewis, P., Perez, E., Piktus, A., et al., 2020. Retrieval-augmented generation for knowledge-intensive NLP tasks. In: Advances in Neural Information Processing Systems 33, pp. 9459–9474.

Li, G., Hammoud, H., Itani, H., Khizbullin, D., Ghanem, B., 2023. CAMEL: communicative agents for "mind" exploration of large language model society. In: Advances in Neural Information Processing Systems 36, pp. 51991–52008.

Liakos, K.G., Busato, P., Moshou, D., Pearson, S., Bochtis, D., 2018. Machine learning in agriculture: a review. Sensors 18 (8), 2674.

Park, J.S., O'Brien, J., Cai, C.J., Morris, M.R., Liang, P., Bernstein, M.S., 2023. Generative agents: interactive simulacra of human behavior. In: Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology, pp. 1–22.

Pylianidis, C., Osinga, S., Athanasiadis, I.N., 2021. Introducing digital twins to agriculture. Comput. Electron. Agric. 184, 105942.

Schick, T., Dwivedi-Yu, J., Dessi, R., et al., 2023. Toolformer: language models can teach themselves to use tools. In: Advances in Neural Information Processing Systems 36, pp. 68539–68551.

Shinn, N., Cassano, F., Gopinath, A., Narasimhan, K., Yao, S., 2023. Reflexion: language agents with verbal reinforcement learning. In: Advances in Neural Information Processing Systems 36, pp. 8634–8652.

Staab, S., Studer, R. (Eds.), 2009. Handbook on Ontologies. Springer, Berlin.

Tao, F., Zhang, H., Liu, A., Nee, A.Y.C., 2019. Digital twin in industry: state-of-the-art. IEEE Trans. Ind. Inform. 15 (4), 2405–2415.

Verdouw, C., Tekinerdogan, B., Beulens, A., Wolfert, S., 2021. Digital twins in smart farming. Agric. Syst. 189, 103046.

Walter, A., Finger, R., Huber, R., Buchmann, N., 2017. Smart farming is key to developing sustainable agriculture. Proc. Natl. Acad. Sci. 114 (24), 6148–6150.

Wang, L., Ma, C., Feng, X., et al., 2023. A survey on large language model based autonomous agents. arXiv preprint arXiv:2308.11432.

Wei, J., Wang, X., Schuurmans, D., et al., 2022. Chain-of-thought prompting elicits reasoning in large language models. In: Advances in Neural Information Processing Systems 35, pp. 24824–24837.

Wolfert, S., Ge, L., Verdouw, C., Bogaardt, M.J., 2017. Big data in smart farming: a review. Agric. Syst. 153, 69–80.

Xi, Z., Chen, W., Guo, X., et al., 2023. The rise and potential of large language model based agents: a survey. arXiv preprint arXiv:2309.07864.

Yao, S., Zhao, J., Yu, D., et al., 2023a. ReAct: synergizing reasoning and acting in language models. In: International Conference on Learning Representations.

Yao, S., Yu, D., Zhao, J., et al., 2023b. Tree of thoughts: deliberate problem solving with large language models. In: Advances in Neural Information Processing Systems 36, pp. 11809–11822.
