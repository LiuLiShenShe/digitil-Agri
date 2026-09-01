# KAFarmTwin: A Knowledge-Constrained Agent Approach for Traceable Digital Twin Scene Construction in Protected Agriculture

**Author A**<sup>a</sup>, **Author B**<sup>a,b</sup>, **Author C**<sup>a</sup>

<sup>a</sup> Affiliation 1, City, Country
<sup>b</sup> Affiliation 2, City, Country

**Corresponding author:** Author B (email@university.edu)

---

## Abstract

Digital twins in protected agriculture require greenhouse structures, crops, devices, sensors, 3D assets, and operational data to be organized into a common object graph that is queryable, traceable, and verifiable. Existing scene-construction workflows remain largely manual, whereas unconstrained large language model (LLM) agents can produce incomplete hierarchies, invalid data-binding contracts, mismatched assets, and execution traces that describe rather than prove tool use. This paper presents KAFarmTwin, a knowledge-constrained agent method that separates semantic interpretation from deterministic constraint enforcement. First, an LLM converts a natural-language request into a compact Intent Intermediate Representation (IntentIR). Second, a deterministic Knowledge Compiler expands the IntentIR using an agricultural ontology, binding vocabulary, unit registry, and asset-routing policies. Third, rule violations are converted into typed RepairTickets; the LLM selects an admissible repair operator, while a deterministic executor instantiates parameters and commits a repair only when re-validation does not increase the number of fatal violations. We evaluate the method on a frozen development-contact benchmark, test_v2 (20 tasks, five categories, five repeats per task-method pair), and an author-generated, author-reviewed controlled benchmark, External300 (300 tasks, five categories, one execution per task-method pair). On External300, KAFarmTwin obtains a Complete-and-Valid Scene Rate (CVSR) of 0.717 versus 0.480 for the strongest fair baseline, SingleAgent, corresponding to a paired improvement of +23.7 percentage points (95% CI [+18.3, +29.0]; exact McNemar test, p = 8.45 × 10^-17), while the fatal-violation rate decreases from 0.250 to 0.000. The net improvement is concentrated in rule-repair tasks (60 of 71 additional successes), all of which are single-rule R4 violations with explicit fix targets; excluding rule repair, the paired difference narrows to +4.6 pp. Scene construction shows modest improvement (+6 tasks), asset routing remains weak in absolute terms (CVSR 0.083) but post-hoc analysis reveals 78% of failures are naming mismatches rather than structural failures, and data-binding and memory-query categories reach ceiling performance for both methods. In the test_v2 ablation family, removing the Knowledge Compiler eliminates successful completion on the asset subset, removing typed repair increases the fatal-violation rate from 0 to 0.22, and removing ontology constraints reduces Binding-F1 from 0.529 to 0.453. Four additional model families reproduce a positive paired KF–SA difference under the same inference interface. These results support the value of separating LLM semantic decisions from executable domain constraints, but they do not establish performance on independently collected or field-deployed protected-agriculture tasks.

**Keywords:** protected agriculture; digital twin; knowledge-augmented AI; LLM agent; knowledge constraint; typed repair; scene construction



**Fig. 1.** KAFarmTwin system architecture. The pipeline contains three main stages: (a) LLM-based IntentIR parsing, (b) deterministic Knowledge Compilation using ontology, mapping, binding, unit, constraint, and asset-policy modules, and (c) validation-triggered typed repair. The LLM is used for semantic parsing and repair-operator selection; graph expansion, parameter instantiation, patch application, and re-validation are deterministic.

**Fig. 2.** External300 CVSR comparison by task category. Grouped bar chart showing KAFarmTwin (KF) versus SingleAgent (SA) for rule_repair (1.00 vs. 0.00), scene_construction (0.50 vs. 0.40), asset_routing (0.083 vs. 0.00), data_binding (1.00 vs. 1.00), and memory_query (1.00 vs. 1.00). The figure highlights the concentration of the aggregate improvement in rule-repair tasks and the ceiling effects in data binding and memory query.

**Fig. 3.** Ablation study results. Two-panel figure: (a) CVSR for full (0.550), A1 no_compiler (0.370), A2 no_typed_repair (0.580), A3 no_ontology (0.530); (b) Fatal rate for the same variants (0.000, 0.010, 0.220, 0.000), illustrating that typed repair contributes safety rather than CVSR.

**Fig. 4.** Cross-model-family robustness forest plot. Point estimates and 95% task-level paired-bootstrap confidence intervals for the KF–SA CVSR difference across five model families: DeepSeek-V4-Flash (+23.67 pp), Kimi-K2.6 (+18.00 pp), MiniMax-M2.5 (+25.67 pp), Qwen3.6-27B (+21.67 pp), and GLM-5.2 (+24.33 pp). All intervals have positive lower bounds under the common inference interface.

**Fig. 5.** Execution-trace example. A representative trace links the IntentIR, tool-call identifiers, evidence identifiers, validation findings, selected repair operator, deterministic patch application, and post-repair validation result. The figure distinguishes executable evidence from LLM-generated narration.


---

## 1. Introduction

Digital twins create dynamic mappings among virtual models, physical objects, and operational data and are increasingly used for state awareness, process analysis, and decision support (Grieves, 2014; Tao et al., 2019; Jones et al., 2020). In protected agriculture, this concept is particularly relevant because production management spans several coupled levels: greenhouse compartments, plots, crop rows, individual plants, environmental sensors, cameras, irrigation and fertigation devices, phenotypic observations, and time-stamped production events (Pylianidis et al., 2021; Verdouw et al., 2021; Walter et al., 2017). Conventional monitoring platforms can display temperature, humidity, light, CO2, or device status, but the data are often not represented in a common object model that explicitly states which physical entity is being observed, controlled, visualized, or queried. A 3D digital-twin scene can provide such a spatial-semantic layer when scene objects are linked to business objects, sensor streams, assets, and historical events rather than treated only as visual geometry.

Constructing this layer remains labor-intensive. A greenhouse scene typically requires creation of a valid object hierarchy, spatial placement, assignment of 3D assets, association of sensors and actuators with targets, unit and timestamp normalization, and generation of traceable records that allow downstream systems to verify how the scene was produced. The same physical sensor may simultaneously appear as a 3D model, a device record, and a time-series source. If these representations are connected inconsistently, an apparently complete scene can still be unusable for object-level queries or validation.

LLM agents offer a natural-language interface to this construction problem. A request such as "construct a 30 m × 8 m tomato greenhouse with four crop rows, environmental sensors, a camera, and drip-irrigation equipment" contains semantic information that an LLM can extract effectively. However, direct generation of the complete scene by a general-purpose agent creates three recurrent failure surfaces. First, the generated object graph may omit mandatory intermediate nodes or use invalid relationships. Second, assets and data bindings may violate type, unit, timestamp, or target constraints. Third, a textual trace may claim that tools or validators were executed without carrying machine-verifiable evidence of those calls. These are not primarily language-understanding errors; they are failures to enforce executable domain contracts.

KAFarmTwin addresses this distinction by assigning different responsibilities to the LLM and to deterministic components. The LLM produces a compact Intent Intermediate Representation (IntentIR) that captures semantic candidates rather than complete instances. A Knowledge Compiler then expands the intent using protected-agriculture ontology, mapping, binding, unit, constraint, and asset-policy modules. Validation results are converted into typed RepairTickets. For a repairable violation, the LLM chooses among admissible operators, whereas a deterministic executor instantiates parameters, applies the candidate patch to a copy of the current state, re-validates the state, and commits only a non-degrading repair. The resulting design is therefore not a prompt-only knowledge-augmentation scheme; agricultural knowledge is implemented as executable transformations, type restrictions, and validation predicates.

The contributions of this study are threefold:

1. **A representation boundary between semantic intent and executable scene structure.** We define IntentIR as a compact semantic interface and formulate protected-agriculture scene construction as generation of a typed attributed graph with object, binding, asset, and trace constraints.
2. **A deterministic Knowledge Compiler for domain-constrained scene construction.** The compiler transforms semantic candidates into graph structure, normalized bindings, and asset routes by applying agricultural ontology, mapping rules, unit canonicalization, and asset policies. This makes a substantial part of scene construction reproducible and independent of LLM sampling.
3. **A transaction-safe typed-repair mechanism and an empirical evaluation of its effects.** Repair operators have explicit applicability and side-effect boundaries; candidate repairs are committed only when re-validation does not increase fatal violations. On External300, the typed repair loop achieves 60/60 on template-matched single-rule R4 violations (D1 difficulty), demonstrating reliable mechanism execution for controlled repair scenarios; task homogeneity limits the generality of this result. We evaluate the complete system against shared-tool agent baselines, conduct component ablations and cross-model-family tests, and report both positive and negative category-level results, including weak absolute asset-routing performance, naming-convention divergence in asset routing, and the absence of independent field validation.

The remainder of this paper is organized as follows. Section 2 reviews agricultural digital twins, LLM agents, knowledge-constrained execution, and traceability. Section 3 presents the formal problem and KAFarmTwin method. Section 4 describes the prototype implementation. Section 5 reports the experimental results and validity limits. Section 6 summarizes the conclusions and the remaining validation requirements.

## 2. Related work

### 2.1. Agricultural digital twins and semantic scene construction

Digital-twin research has expanded from manufacturing to agricultural production-process modelling and smart-farm management (Tao et al., 2019; Verdouw et al., 2021; Pylianidis et al., 2021). Agricultural applications commonly emphasize sensor-data integration, crop-state monitoring, machinery or greenhouse-equipment management, and visualization (Liakos et al., 2018; Drury et al., 2019; Kamilaris and Prenafeta-Boldú, 2018). These studies establish the value of integrating physical and digital production states, but they do not by themselves solve semantic scene construction. For object-level operations, a scene must encode not only geometry but also typed entities, containment relations, device targets, data provenance, asset identity, and temporal events. KAFarmTwin therefore treats scene construction as a graph-and-contract generation problem rather than a graphics-generation problem.

Agricultural semantic-web and ontology research provides a complementary foundation. AgroPortal aggregates domain vocabularies and ontologies for agronomy (Jonquet et al., 2018), while SSN/SOSA standardizes concepts for sensors, observations, samples, and actuators (Compton et al., 2012; Janowicz et al., 2019). These resources motivate explicit representation of sensor and observation semantics, but an ontology is not automatically an execution mechanism. The problem addressed here is how ontology and related domain contracts can be compiled into a scene-building procedure that is triggered from natural-language intent.

### 2.2. LLM agents and tool-mediated execution

LLM agents extend text generation with task decomposition, tool use, intermediate state, and result aggregation (Wang et al., 2023; Xi et al., 2023). ReAct interleaves reasoning and actions (Yao et al., 2023a), Toolformer demonstrates model-mediated API use (Schick et al., 2023), and chain-of-thought and tree-search approaches improve decomposition and candidate exploration (Wei et al., 2022; Kojima et al., 2022; Yao et al., 2023b). Multi-agent approaches further divide planning or execution among roles (Li et al., 2023). These methods improve the ability of language models to interact with external systems, but tool availability does not guarantee that the produced state satisfies domain-specific structural contracts. In scene construction, an agent may invoke the correct class of tool while still producing an illegal parent-child relation, inconsistent asset type, malformed binding, or incomplete trace.

This distinction motivates a different control boundary. KAFarmTwin does not ask the LLM to generate and validate the entire scene state. It uses the model where semantic ambiguity is highest—intent interpretation and selection among typed repair alternatives—and uses deterministic modules where structural repeatability and policy enforcement are required.

### 2.3. Knowledge augmentation and neurosymbolic constraint enforcement

Knowledge-augmented AI incorporates external knowledge through retrieval-augmented generation, knowledge graphs, ontologies, rule systems, and memory (Lewis et al., 2020; Gao et al., 2023; Hogan et al., 2021). Retrieval can improve factual context, but retrieved text remains advisory unless downstream execution converts it into enforceable predicates or transformations. Neurosymbolic research explicitly separates neural functions such as language interpretation from symbolic functions such as logical constraint checking and structured state manipulation (d'Avila Garcez and Lamb, 2023; Staab and Studer, 2009).

KAFarmTwin follows this separation at the execution level. Agricultural knowledge is not appended only to an LLM prompt. It is represented in deterministic modules that expand required hierarchy, normalize metric and unit names, resolve parent-child mappings, constrain asset classes, and validate the resulting state. The central methodological difference is therefore **knowledge compilation**: semantic intent is transformed by executable domain knowledge before the scene is accepted.

### 2.4. Memory, provenance, and traceable reasoning

Long-term-memory and reflective-agent research has highlighted the importance of persistent state and inspectable intermediate processes (Park et al., 2023; Shinn et al., 2023). Protected-agriculture digital twins additionally require temporal provenance because environmental observations, crop traits, irrigation events, maintenance actions, and alarms are meaningful only when associated with an object and time range. KAFarmTwin supports object-level memory and bounded historical queries, but memory is treated as a supporting digital-twin service rather than the principal methodological contribution of this paper.

A separate issue is execution provenance. A language model can narrate that a validator or tool was used even when no corresponding call occurred. We therefore distinguish declarative reasoning text from executable trace evidence. Tool calls, evidence identifiers, validation outcomes, repair decisions, and commit/rollback events are recorded as scoring objects. This makes trace completeness part of scene validity rather than a cosmetic log.

Across these four lines of work, the unresolved gap is not simply whether an LLM can describe a greenhouse scene or call scene-building tools. The relevant question is whether natural-language intent can be converted into a typed, data-bound, asset-aware, and traceable digital-twin state while keeping stochastic model decisions inside explicitly bounded interfaces. This is the gap targeted by KAFarmTwin.

## 3. Materials and methods

**Overview.** KAFarmTwin separates semantic interpretation from structural state transformation. Given a natural-language scene request, the pipeline performs three stages: (i) an LLM parses the request into IntentIR; (ii) a deterministic Knowledge Compiler expands and canonicalizes the intent using six knowledge modules; and (iii) a validator emits typed violations that may trigger bounded repair. The LLM is not allowed to directly commit arbitrary scene mutations in the normal repair path. Instead, it selects an operator from a rule-specific admissible set, and a deterministic executor instantiates and applies the operator under a transactional commit criterion.

### 3.1. Problem formulation

Let the construction input be

$$Q=(q,D_s,A,M_t,R,K),$$

where $q$ is the natural-language request; $D_s$ contains available sensor, phenotypic, and event data; $A$ is the 3D-asset registry; $M_t$ is optional object-level temporal memory; $R$ is the validation-rule set; and $K$ denotes the deterministic domain-knowledge modules used by the compiler.

The output state is

$$Y=(G,B,V,T),$$

where $G=(N,E)$ is a typed attributed scene graph, $B$ is the set of data and asset bindings, $V$ is the validation result, and $T$ is the executable trace.

For each node $n\in N$, $\tau(n)\in C$ denotes its ontology type and $\alpha(n)$ its attributes. For each edge $e=(n_i,n_j)\in E$, $\rho(e)\in R_o$ denotes its relationship type. A scene is evaluated by a set of rule predicates $\{\phi_r\}_{r\in R}$, with $\phi_r(Y)=1$ when rule $r$ is satisfied. Let $R_f\subseteq R$ denote fatal rules. The fatal-violation count is

$$F(Y)=\sum_{r\in R_f}\mathbb{1}[\phi_r(Y)=0].$$

The set of fully valid outputs for a task is

$$\mathcal{F}(Q)=\{Y\mid \phi_r(Y)=1,\ \forall r\in R_{\mathrm{required}}\},$$

where $R_{\mathrm{required}}$ includes the task-specific critical-object, binding, trace, and rule requirements enforced by the evaluator. The construction problem is to generate $Y\in\mathcal{F}(Q)$ while respecting the common LLM/tool budget.

A run is counted as complete and valid only when all critical objects are present, no fatal rule violations remain, required binding contracts are valid, and the execution trace passes its evidence checks. Accordingly,

$$\mathrm{CVSR}=\frac{1}{|\mathcal{T}|}\sum_{i=1}^{|\mathcal{T}|}\mathbb{1}[Y_i\in\mathcal{F}(Q_i)].$$

This formulation is intentionally stricter than object-generation accuracy: a visually plausible scene can fail CVSR because of invalid bindings, missing evidence, or a fatal rule violation.

### 3.2. Agricultural ontology and executable knowledge

The agricultural ontology is represented as

$$K_o=(C,R_o,P,I_o),$$

where $C$ contains object categories (e.g., Greenhouse, Plot, CropRow, Plant, Sensor, Camera, Device, Trait, Event, and Asset), $R_o$ contains typed relationships (e.g., *contains*, *belongs_to*, *monitors*, *observes*, *controls*, *has_asset*, *has_trait*, and *has_event*), $P$ contains attribute schemas, and $I_o$ contains instantiated ontology entities used by the system.

Ontology membership alone is insufficient for construction; KAFarmTwin therefore represents domain knowledge as six deterministic modules:

1. **Ontology:** admissible object and relationship types and required hierarchy;
2. **Constraint:** device defaults, asset classes, aggregatable types, and rule-linked restrictions;
3. **Mapping:** parent resolution, identity-type handling, and child lookup;
4. **Binding vocabulary:** canonical metrics and construction of sensor/asset binding records;
5. **Asset policy:** object-type and crop-specific routing preferences;
6. **Unit registry:** canonical units and supported metric-unit mappings.

For example, the hierarchy constraint requires a plant instance to be reachable through a Greenhouse → Plot → CropRow → Plant containment path. Device relationships are separately typed: plants cannot originate *monitors* or *controls* edges, and every node referenced by a binding must exist in the scene graph. These constraints are implemented as executable checks or transformations rather than as prose supplied only to the LLM.

### 3.3. Intent Intermediate Representation

The LLM first maps the user request $q$ to a compact semantic representation

$$I=f_{\theta}(q)=\left(O_{\mathrm{cand}},E_{\mathrm{cand}},B_{\mathrm{cand}},P_{\mathrm{cand}}\right),$$

where $O_{\mathrm{cand}}$ contains candidate object types, counts, and key attributes; $E_{\mathrm{cand}}$ contains candidate hierarchy or monitoring relations; $B_{\mathrm{cand}}$ contains requested metrics or data associations; and $P_{\mathrm{cand}}$ contains layout and asset preferences.

IntentIR deliberately does not assign all final object identifiers, guarantee ontology legality, or directly commit scene state. Its role is to preserve semantic information from the request while reducing the amount of instance-level structure generated stochastically. Required hierarchy nodes, canonical binding fields, and asset-route decisions are supplied downstream by deterministic modules where possible.

### 3.4. Deterministic Knowledge Compiler

Let

$$K=(K_o,K_c,K_m,K_b,K_a,K_u)$$

collect the six knowledge modules described above. The Knowledge Compiler is a deterministic mapping

$$\mathcal{C}_K:I\rightarrow (G_0,B_0,A_0),$$

where $G_0$ is the compiled graph, $B_0$ the normalized binding plan, and $A_0$ the asset-routing plan. Operationally,

$$\mathcal{C}_K = \mathcal{C}_{\mathrm{asset}}\circ\mathcal{C}_{\mathrm{bind}}\circ\mathcal{C}_{\mathrm{graph}},$$

with each stage using only deterministic code and registered knowledge. For an identical IntentIR and identical knowledge snapshot, the compiler therefore produces the same output.

The compiler is not assumed to solve every validation rule. Let $R_C\subseteq R$ denote rules directly enforced during compilation. The intended property is

$$\phi_r(\mathcal{C}_K(I))=1,\qquad r\in R_C,$$

provided the required registry entries and mapping rules exist. Rules outside $R_C$, missing registry coverage, or ambiguous user intent are handled by downstream validation and repair. This distinction is important: the compiler reduces the stochastic search space and enforces encoded contracts, but it does not guarantee that every open-world task has a valid asset or binding solution.

**Algorithm 1. Knowledge Compiler** (`knowledge_compiler.build_scene_from_intent`)

**Input:** IntentIR $I$

**Output:** compiled scene state $(G_0,B_0,A_0)$

1. **Graph expansion.** Resolve ontology types and required parents; insert missing hierarchy nodes; normalize object multiplicities according to identity semantics; assign deterministic node identifiers.
2. **Binding compilation.** Map requested metrics to canonical vocabulary; normalize supported units; create sensor/data binding records and required metadata.
3. **Asset-route compilation.** Resolve object type and crop policy; select an available route among registered GLB/high-fidelity, procedural, generation-task, or placeholder options; attach asset keys or fallback tasks according to policy.
4. Return the compiled state for validation.

The use of a deterministic compiler is the principal architectural difference from a full-scene LLM generator: the model does not need to rediscover the same hierarchy, binding schema, and asset policy for every request.

### 3.5. Typed repair with transactional commit

Validation produces a set of structured violations

$$\mathcal{V}(Y)=\{v_j=(r_j,s_j,z_j,m_j)\},$$

where $r_j$ is the violated rule, $s_j$ is its severity, $z_j$ identifies the affected scene scope, and $m_j$ contains machine-readable violation metadata. A fatal violation is converted into a RepairTicket rather than an unrestricted natural-language repair prompt.

Each repair operator $a\in\mathcal{A}$ is described by

$$a=(\mathrm{name}_a,\mathrm{pre}_a,\mathrm{schema}_a,\mathrm{scope}_a,\mathrm{effect}_a),$$

where $\mathrm{pre}_a$ defines applicability, $\mathrm{schema}_a$ constrains parameters, $\mathrm{scope}_a$ limits writable state, and $\mathrm{effect}_a$ defines the permitted mutation class. For violation $v$, the deterministic controller exposes only

$$\mathcal{A}(v)=\{a\in\mathcal{A}\mid \mathrm{pre}_a(v)=1\}.$$

Examples include replacing an invalid asset, attaching a rootless object to an admissible parent, assigning a placeholder route, filling a missing observation target, or escalating an ambiguous case to the user. The specific admissible set depends on the violated rule and state.

The LLM selects

$$a^*=\pi_\theta(v,\mathcal{A}(v)),$$

but parameter instantiation and state mutation are performed by a deterministic executor $E_{\mathrm{det}}$. Given current state $Y_t$, the executor creates a candidate state

$$\tilde{Y}_{t+1}=E_{\mathrm{det}}(Y_t,a^*,v).$$

The candidate is re-validated before commit. For the normal typed-repair path, KAFarmTwin commits only if the candidate respects the operator's type/scope policy and does not increase fatal violations:

$$Y_{t+1}=\begin{cases}
\tilde{Y}_{t+1}, & F(\tilde{Y}_{t+1})\leq F(Y_t)\ \land\ \mathrm{policy}(\tilde{Y}_{t+1},a^*)=1,\\
Y_t, & \text{otherwise (rollback).}
\end{cases}$$

Consequently, for committed typed repairs,

$$F(Y_{t+1})\leq F(Y_t).$$

This is a **non-degradation property**, not a convergence proof: the system can still terminate with unresolved violations when no admissible repair exists or when external resources are missing. The implementation also supports an `ask_user` escalation for ambiguity; any higher-risk free-form patch path is separately logged and is not covered by the typed-operator property above.

**Algorithm 2. Typed repair loop**

1. Validate the compiled state and sort violations by severity.
2. For the next fatal violation, compute $\mathcal{A}(v)$.
3. Ask the LLM to select one admissible operator.
4. Instantiate parameters and apply the operator to a deep copy of the current state.
5. Re-validate; commit only under the criterion above, otherwise rollback.
6. Stop when no fatal violation remains, no admissible action exists, the repair-round budget is exhausted, or consecutive states produce the same unresolved signature.

### 3.6. Data binding and object-level memory support

A binding record links a target object to a data or asset source under an explicit relationship and temporal contract. We represent it as

$$b=(o_i,d_j,r_{ij},u_j,t_j,m_j),$$

where $o_i$ is the target object, $d_j$ is the data/asset source, $r_{ij}$ is the binding relationship, $u_j$ is the canonical unit when applicable, $t_j$ is temporal metadata, and $m_j$ contains additional binding fields. The binding compiler normalizes supported metric and unit aliases and rejects references to objects absent from $G$.

Object-level memory is a supporting service for temporal digital-twin queries:

$$M(o_i)=\{P_i,S_i^t,E_i^t,A_i,T_i\},$$

where $P_i$ contains static attributes, $S_i^t$ dynamic state, $E_i^t$ events, $A_i$ associated assets, and $T_i$ operation records. Historical-query tasks are constrained by object, metric, time range, and event type and are evaluated as read-only operations. Because memory-query tasks reach ceiling performance for both compared methods in External300, we do not treat memory retrieval as an experimentally demonstrated source of KAFarmTwin's performance advantage.

### 3.7. Rule validation and executable trace evidence

The validator implements ten checkpoint groups (Table 1) covering hierarchy, binding, spatial layout, asset consistency, camera logic, device coverage, trace completeness, historical queries, missing assets, and correctability. Each rule produces structured findings with severity and affected scope. Fatal findings contribute to $F(Y)$ and prevent a scene from satisfying CVSR.

**Table 1.** Rule checkpoints R1–R10.

| Rule | Description |
|:----:|:------------|
| R1 | Object hierarchy legality: greenhouse contains plots, plots contain crop rows, crop rows contain plants. |
| R2 | Data binding legality: sensors, phenotypic data, and events must have bound objects, units, and timestamps. |
| R3 | Spatial layout legality: objects do not float or exceed boundaries; crop rows lie within plot boundaries. |
| R4 | Asset type consistency: object type matches GLB model, high-fidelity asset, 3D generation task, procedural, or placeholder policy. |
| R5 | Camera legality: cameras must have pose, observation target, and field-of-view coverage. |
| R6 | Device coverage legality: irrigation, fertigation, supplemental-lighting, and ventilation devices must bind control zones or service targets. |
| R7 | Execution-trace completeness: required construction and validation steps must have machine-recorded evidence. |
| R8 | Memory-query legality: historical queries must constrain object, metric, time range, event type, and result count. |
| R9 | Missing-asset non-interruption: when registered 3D assets are unavailable, an allowed fallback route or generation task must be emitted. |
| R10 | Error correctability: rule conflicts must expose conflict type, triggering rule, and an admissible correction path or escalation. |

The trace records actual tool calls and state transitions. Tools are classified as read-only, controlled-write, or prohibited. Trace records include call identifiers, evidence identifiers, inputs/outputs required for replay, validation findings, repair selections, and commit/rollback status. A textual claim such as "validation passed" is not sufficient evidence unless a corresponding validator call and result are recorded. Trace quality is therefore evaluated through evidence precision and replay success rather than through narrative plausibility.

### 3.8. Statistical evaluation protocol

For each paired task $i$, let $s_i^{\mathrm{KF}}$ and $s_i^{\mathrm{SA}}$ denote binary CVSR outcomes. The paired mean difference is

$$\Delta=\frac{1}{|\mathcal{T}|}\sum_{i=1}^{|\mathcal{T}|}\left(s_i^{\mathrm{KF}}-s_i^{\mathrm{SA}}\right).$$

A 95% confidence interval for $\Delta$ is estimated with 10,000 paired bootstrap resamples over tasks (Efron and Tibshirani, 1993). For External300 and the cross-model experiments, each task-method pair is executed once; therefore these intervals quantify uncertainty with respect to the sampled task set and do **not** quantify inference-run variance at temperature 0.2.

For McNemar's exact test (McNemar, 1947), let $b$ be the number of discordant tasks on which only KAFarmTwin succeeds and $c$ the number on which only SingleAgent succeeds. With $X=b+c$ and the null probability 0.5, the two-sided exact p-value is

$$p=\min\left(1,\ 2\sum_{k=0}^{\min(b,c)}\binom{X}{k}\left(\frac{1}{2}\right)^X\right).$$

For the repeated test_v2 protocol, pass@$k$ is

$$\mathrm{pass@}k=\frac{1}{|\mathcal{T}|}\sum_{i=1}^{|\mathcal{T}|}\mathbb{1}\left[\sum_{j=1}^{k}s_i^{(j)}\geq 1\right].$$

The project also used pre-specified engineering acceptance criteria (paired difference, guardrail metrics, replay, and cost ratio) to decide whether an implementation revision was accepted. These gates are reported for reproducibility but are not inferential hypotheses and are not used as evidence of state-of-the-art performance.

## 4. System implementation

KAFarmTwin is implemented as a prototype system for validating that the knowledge-constrained pipeline can be realized as an invocable scene-construction service. The system frontend is built on Vue 3, TypeScript, Vite, Three.js, Pinia, and Element Plus, responsible for 3D scene display, object tree, property panel, natural-language input, acceptance console, Agent Trace, and asset routing result display. The system backend is built on Go, Gin, sqlx, and MySQL, providing agricultural object management, scene object binding, object-level memory, asset metadata, asset quality auditing, asset routing, semantic construction, and acceptance aggregation interfaces.

The backend service adopts layered implementation for object management, scene binding, memory management, asset governance, and agent orchestration. The agent orchestration service extends the SceneBuilderAgent compatible entry to FarmTwinOrchestrator, exposing planning, layout, asset routing, data binding, and validation step evidence in trace.steps; the tool strategy classifies tools into read-only, controlled-write, and prohibited categories, with prohibited operations blocked and logged as policy violations. The experimental evaluation (experiments/v3) implements a shared harness in Python: a unified tool registry, budget controller (LLM calls / tool calls / repair-round limits), trace proxy, canonicalized output layer, and versioned evaluator, ensuring all methods compare under the same budget and scoring protocol.

The prototype system validates object-graph construction, typed repair, data binding, and trace mechanisms; it is not equivalent to a complete production-grade agricultural control platform. Real device closed-loop control, long-term operational stability, and larger-scale crop data will be extended in future work.

## 5. Results and discussion

### 5.1. Experimental setup

Experiments address five research questions: **RQ1**, how does KAFarmTwin compare with shared-tool agent baselines in complete-and-valid scene construction? **RQ2**, what distinct effects are attributable to the Knowledge Compiler, typed repair, and ontology constraints? **RQ3**, does the typed-repair design reduce fatal violations and improve replayable execution? **RQ4**, what latency and token-cost overhead is introduced by the constrained pipeline? **RQ5**, is the direction of the KF–SA difference consistent across several model families under the same inference interface?

**Benchmarks.** Two controlled benchmarks are used. test_v2 provides repeated multi-baseline measurements but was consulted during development. External300 is larger and was generated after the main implementation, but it was also generated and reviewed by the authors and therefore is not an independent external test set.

*Benchmark A: test_v2.* test_v2 contains 20 tasks across five categories (four per category), each executed five times per method at temperature 0.2 with the experiment configuration's fixed seed. The base model is DeepSeek-V4-Flash through the SiliconFlow access layer. All methods use the same model interface, maximum budgets (30 LLM calls, 100 tool calls, three repair rounds), public task fields, output schema, and rule text. The gold answers are held by the frozen evaluator (evaluator_v2.3), whose source fingerprint is logged with each run. Because this benchmark was consulted during development, its results should be interpreted as repeated performance on a frozen known distribution rather than independent generalization evidence.

*Benchmark B: External300.* External300 contains 300 tasks: 60 each for scene construction, asset routing, data binding, rule repair, and memory query. Each task-method pair is executed once with DeepSeek-V4-Flash at temperature 0.2. The original review plan specified independent dual review and third-party adjudication, whereas the realized protocol used single-author unified confirmation before unsealing. We therefore refer to External300 as an **author-generated, author-reviewed controlled benchmark** throughout this paper. The deviation is retained in the provenance records and summarized in Section 5.9.

**Table 2.** External300 task composition.

| Task Category | Count | Key Capability Tested |
|:-------------|------:|:-----------------------|
| scene_construction | 60 | Object hierarchy, spatial layout, relation-graph completeness |
| asset_routing | 60 | Asset-policy routing, fallbacks, and object-asset consistency |
| data_binding | 60 | Sensor/device/phenotype binding contracts: metrics, units, timestamps |
| rule_repair | 60 | Violation handling, typed operator selection, and post-repair validation |
| memory_query | 60 | Pre-placed retrieval, answer boundaries, and no-side-effect behavior |

**Baseline methods.** All methods receive identical public task fields, object and relation vocabularies, rule text, common tools, and budget limits. The primary control is SingleAgent-AllTools, which has access to the shared tool set but does not use the proposed compiler/typed-repair closed loop.

**Table 3.** Baseline method definitions.

| Method | Setting | Purpose |
|:-------|:--------|:--------|
| SingleAgent-AllTools (SA) | Single agent with all shared tools, no typed repair loop | Primary shared-tool baseline |
| GenericMultiAgent-AllTools | Multi-role division with shared tools, no proposed closed-loop constraint enforcement | Tests role decomposition without the proposed control boundary |
| GenericRepair-AllTools | Single agent with untyped generic repair | Tests repair availability without typed operators and deterministic instantiation |
| ReAct-AllTools | Reasoning-acting alternation without the proposed structured construction path | Free-form tool-use baseline |
| **KAFarmTwin-TypedRepair (Ours)** | IntentIR → Knowledge Compiler → validation → typed repair | Proposed method |

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

KAFarmTwin achieves a paired CVSR difference of **+25 percentage points** over SingleAgent (95% CI [+9, +44] pp; 20-task paired bootstrap, 10,000 resamples); pass@5 is 0.700 versus 0.500. All guardrail metrics pass: Critical Recall 1.000, Fatal 0.000 (SingleAgent 0.320), Evidence Precision 1.000, Replay 1.000. Cost: exact cost ratio 1.24×, below the 1.5× threshold. ReAct achieves CVSR 0.000 on this benchmark. This result shows that the tested free-form ReAct configuration is poorly matched to the frozen structured-output protocol; it should not be generalized to all ReAct-style agents or all scene-construction settings.

### 5.3. Main results: External300

Table 5 reports the comparison on External300.

**Table 5.** External300 main results (300 task executions per method).

| Method | CVSR ↑ | Obj-F1 ↑ | Rel-F1 ↑ | Bind-F1 ↑ | Crit-Recall ↑ | Fatal ↓ | Ev-P ↑ | Replay ↑ | Total Cost | Total Tokens |
|:-------|-------:|---------:|---------:|----------:|--------------:|--------:|-------:|---------:|-----------:|-------------:|
| KAFarmTwin (Ours) | **0.717** | 0.690 | 0.700 | 0.594 | **1.000** | **0.000** | **1.000** | **0.808** | $0.1035 | 668,769 |
| SingleAgent | 0.480 | 0.635 | 0.379 | 0.200 | 0.950 | 0.250 | 0.947 | 0.455 | $0.0854 | 472,722 |

KAFarmTwin succeeds on 215/300 tasks and SingleAgent on 144/300. The paired CVSR difference is **+23.67 pp** (95% task-level paired-bootstrap CI [+18.33, +29.00] pp). The discordant counts are $b=77$ and $c=6$, giving a two-sided exact McNemar p-value of $8.45\times10^{-17}$. The exact cost ratio is 1.21× and the token ratio is 1.41×. Because each task-method pair is executed once, the confidence interval and McNemar test characterize paired differences over the sampled tasks; they do not include repeated-inference variance.

**Table 6.** External300 CVSR by task category.

| Category | KF | SA | Difference | Interpretation |
|:---------|---:|---:|-----------:|:---------------|
| rule_repair | **1.00** | 0.00 | +1.00 | Dominant source of net improvement |
| scene_construction | 0.50 | 0.40 | +0.10 | Modest improvement |
| asset_routing | 0.083 | 0.00 | +0.083 | Small relative gain; weak absolute performance |
| data_binding | 1.00 | 1.00 | 0.00 | Ceiling; no comparative evidence |
| memory_query | 1.00 | 1.00 | 0.00 | Ceiling; no comparative evidence |

The category breakdown materially qualifies the aggregate result. Of the 71 additional successful tasks obtained by KAFarmTwin, 60 (84.5%) come from rule repair, six from scene construction, and five from asset routing. Excluding rule repair, the paired CVSR difference narrows to +4.6 pp (KF 0.646 vs SA 0.600 on 240 tasks). The rule-repair category therefore dominates the aggregate result. Post-hoc analysis (Appendix A3) reveals that all 60 rule-repair tasks are D1 difficulty: single-rule R4 violations with explicit fix targets in the prompt, requiring one deterministic repair step. The 60/60 vs 0/60 comparison primarily measures the presence of an explicit repair loop versus an execution path that performs no repair by design (SingleAgent routes rule-repair tasks to `bare_seed_no_repair`; source code: `single_agent.py:40-53`). It should not be interpreted as evidence of general repair reasoning ability across diverse rules or difficulty levels.

Asset routing requires separate interpretation. Although KAFarmTwin achieves a higher CVSR than SingleAgent (0.083 vs 0.000), the absolute performance remains low. Post-hoc failure analysis (Appendix A4) shows that 78% of the 55 failed asset-routing tasks are naming or labeling mismatches (the compiler produces structurally valid, bound, replayable scenes with perfect Critical Recall and zero fatal violations, but object naming conventions diverge from the gold standard). The true algorithmic failure rate—edge/binding detail issues and unclassified cases—is approximately 22%, not 91.7%. This suggests the primary limitation is asset-registry naming-convention alignment rather than scene-construction logic.

Data-binding and memory-query categories reach ceiling performance for both methods and provide no comparative evidence.

**Latency.** Table 7 reports nearest-rank quantiles at two granularities.

**Table 7.** Latency (nearest-rank quantiles).

| Granularity | KF p50 (s) | KF p95 (s) | SA p50 (s) | SA p95 (s) |
|:-----|-----------:|-----------:|-----------:|-----------:|
| All tasks ($n$ = 300) | 2.52 | 9.59 | 2.06 | 12.52 |
| LLM-invoking tasks | 2.82 | 10.01 | 6.72 | 15.45 |

Across all tasks, SingleAgent has the lower median because 120/300 SA tasks are deterministic zero-LLM executions counted as near-zero latency. Restricting the comparison to tasks that invoke the LLM, KAFarmTwin has lower p50 and p95 latency. This result is consistent with moving repeated structural work from language-model generation to deterministic compilation, but it should not be interpreted as a hardware-independent latency guarantee.

### 5.4. Safety and failure analysis

The intended mechanism is not that every knowledge-constrained scene will pass, but that deterministic constraints and typed state transitions reduce specific classes of invalid execution. Three observations support this interpretation.

**Fatal violations.** On External300, the fatal-violation rate is 0.000 for KAFarmTwin and 0.250 for SingleAgent. In the ablation family, removing typed repair raises the fatal rate from 0.000 to 0.220. Across the five tested model families, KAFarmTwin remains at or near zero fatal violations, whereas SingleAgent remains in the 0.23–0.29 range. These empirical results are consistent with the transactional non-degradation property in Section 3.5, although they do not prove that every task will converge to a valid state.

**Replayability.** External300 replay success is 0.808 for KAFarmTwin versus 0.455 for SingleAgent. Fatal violations and non-replayable traces overlap strongly in the baseline: all tasks carrying the reported SA fatal condition are non-replayable. Replayability is therefore an important necessary component of CVSR, but it is not sufficient. The asset-routing category illustrates this distinction: KAFarmTwin can produce replayable executions that still fail the asset-matching requirements.

**Failure concentration.** Table 8 reports rule findings for the 60 SingleAgent executions in the External300 rule-repair category.

**Table 8.** SingleAgent rule findings in External300 rule_repair ($n$ = 60).

| Rule | Meaning | SA findings |
|:----:|:--------|------------:|
| R4 | Asset-type constraint violation (fatal) | 60 |
| R6 | Incomplete device coverage | 30 |
| R2 | Invalid data binding | 15 |
| R5 | Camera logic inconsistency | 10 |

The complete concentration of R4 fatal findings in this category explains much of the aggregate performance difference. It also exposes an evaluation limitation: the rule-repair subset directly targets failure modes addressed by KAFarmTwin's compiler/repair design. Post-hoc analysis (Appendix A3) confirms that all 60 tasks are D1 difficulty (single-rule R4 violations with explicit fix targets), and SingleAgent routes these tasks to a no-repair execution path by design (`single_agent.py:40-53`). The 60/60 vs 0/60 result is therefore a controlled mechanism test demonstrating that an explicit typed repair loop can reliably execute single-step R4 corrections when the repair target is unambiguous; it should not be interpreted as evidence of general repair capability across diverse rules, multi-rule cascades, or ambiguous repair scenarios.

### 5.5. Ablation study

Ablation uses the frozen v3 protocol: 20 tasks × five repeats = 100 runs per variant, DeepSeek-V4-Flash, temperature 0.2. The `full` ablation variant and the main-experiment KAFarmTwin result are independent stochastic samples; their CVSR values (0.550 and 0.610) are therefore not paired and are not used to estimate a treatment effect. Component interpretation is made only within the ablation family.

**Table 9.** Component ablation results (100 runs per variant).

| Variant | Removed Component | CVSR | Obj-F1 | Bind-F1 | Crit-Recall | Fatal ↓ | Cost/run |
|:--------|:------------------|-----:|-------:|--------:|------------:|--------:|---------:|
| full | (none) | 0.550 | 0.796 | 0.529 | 1.000 | **0.000** | $0.00033 |
| A1 (no_compiler) | Knowledge Compiler | 0.370 | 0.721 | 0.329 | 0.950 | 0.010 | $0.00044 |
| A2 (no_typed_repair) | Typed repair loop | 0.580 | 0.798 | 0.329 | 1.000 | **0.220** | $0.00018 |
| A3 (no_ontology) | Ontology constraint | 0.530 | 0.796 | 0.453 | 1.000 | 0.000 | $0.00052 |

**Knowledge Compiler.** Removing the compiler decreases overall CVSR by 18 pp within the ablation family and reduces Binding-F1 from 0.529 to 0.329. On the four-task asset subset of test_v2, CVSR falls from 0.95 to 0.00 across the repeated runs. This is strong evidence that the implemented compiler is required for success on this particular asset-construction subset; it is not evidence that the current compiler solves general asset routing, as demonstrated by the 0.083 asset-routing CVSR on External300.

**Typed repair.** Removing typed repair does not reduce CVSR in this ablation sample: A2 obtains 0.580 compared with 0.550 for full. Its measurable contribution is instead the fatal-violation rate, which rises from 0.000 to 0.220 when repair is removed. The paired fatal flips are 22 in the no-repair-to-full direction and 0 in the reverse direction. This pattern is consistent with typed repair acting as a safety-control mechanism rather than a general pass-rate enhancer.

**Ontology constraints.** Removing the ontology constraint reduces Binding-F1 from 0.529 to 0.453 while leaving Critical Recall and Fatal unchanged. The result suggests that ontology-derived type and relationship restrictions improve binding consistency on the frozen task distribution. Because the current ablation reports point estimates from a small set of 20 task templates, effect-size uncertainty for the individual ablations should be quantified in a larger or independently sampled follow-up experiment.

### 5.6. Cross-model-family robustness

To test whether the direction of the KF–SA difference is specific to DeepSeek-V4-Flash, a pre-specified multi-model experiment was run on four additional model families—Kimi-K2.6, MiniMax-M2.5, Qwen3.6-27B, and GLM-5.2—using the same SiliconFlow inference interface. Each family executes the full External300 once per task-method pair.

**Table 10.** Cross-model-family robustness on External300.

| Model Family | KF CVSR | SA CVSR | Δ (pp) | 95% CI | McNemar ($b$, $c$) | $p$ |
|:-------------|--------:|--------:|-------:|:-------|:-------------------|:----|
| DeepSeek-V4-Flash | 0.717 | 0.480 | +23.67 | [+18.33, +29.00] | (77, 6) | < 10^-6 |
| Kimi-K2.6 | 0.673 | 0.493 | +18.00 | [+13.00, +23.33] | (63, 9) | < 10^-6 |
| MiniMax-M2.5 | 0.607 | 0.350 | +25.67 | [+19.67, +31.67] | (91, 14) | < 10^-6 |
| Qwen3.6-27B | 0.697 | 0.480 | +21.67 | [+16.67, +26.67] | (69, 4) | < 10^-6 |
| GLM-5.2 | 0.737 | 0.493 | +24.33 | [+18.33, +30.33] | (88, 15) | < 10^-6 |

All four additional model families satisfy the pre-specified directional criterion: the paired KF–SA difference is positive and its task-level bootstrap lower bound is above zero. This supports **cross-model-family robustness under the common inference interface**, not provider-independent or weight-snapshot-independent generalization.

The safety pattern is also consistent across model families: KAFarmTwin fatal-violation rates remain at or near zero, whereas SingleAgent remains between 0.23 and 0.29. In the rule-repair category, KAFarmTwin obtains CVSR 1.00 and SingleAgent 0.00 for all five families. Because this category is mechanism-aligned, the consistency indicates that the control architecture is not dependent on one LLM family; it does not eliminate the benchmark-construction concern described in Section 5.9.

One category-specific anomaly occurs for MiniMax-M2.5, where KAFarmTwin data-binding CVSR is 0.27 compared with 0.87–1.00 for the other model families. We retain this result rather than excluding it. Its unresolved cause is evidence that semantic parsing differences can still affect downstream deterministic compilation even when the structural execution path is shared.

### 5.7. Binding and asset-routing failure analysis

Data binding and asset routing expose two different limitations: evaluator vocabulary coverage and system knowledge-resource coverage.

**Method-side binding defect corrected during development.** The shared scene-binding constructor initially omitted a timestamp field that was explicitly required by the public binding contract and the frozen evaluator. After the deterministic constructor was corrected to copy the task-declared ISO-8601 timestamp into binding metadata, the affected TN21/TN24 Binding-F1 values increased from 0.333/0.250 to 1.000. Because test_v2 was consulted during this correction, these tasks contribute to the benchmark-contact limitation and are not independent validation cases.

**Frozen evaluator alias gap.** For TN22/TN23, the reference and generated forms use unit/metric aliases such as `°C` versus `celsius`, and `klux/light` versus `lux/light_intensity`, for which the frozen evaluator's alias table contains no equivalence. The evaluator was not modified during the frozen evaluation period. These cases show that binding metrics depend partly on the benchmark's canonicalization coverage; they should not be interpreted as pure semantic binding failures.

**Asset-routing limitation.** Asset routing is the weakest External300 category for KAFarmTwin (5/60 successful tasks; CVSR 0.083). Post-hoc failure analysis (Appendix A4) classifies the 55 failed tasks into failure patterns: 78% are naming or labeling mismatches (the compiler generates structurally valid scenes with correct topology, perfect Critical Recall, zero fatal violations, and Binding-F1 of 0.973, but object naming conventions diverge from the gold standard), 13% are edge/binding detail issues, and 9% are unclassified. The absence of structural failures (Pattern B) indicates that the compiler's scene-construction logic is fundamentally sound for asset routing; the primary limitation is asset-registry naming-convention alignment. This also explains why the test_v2 asset ablation and External300 asset result can coexist: the compiler is necessary for the encoded asset subset, and the current knowledge base produces structurally correct scenes, but naming conventions in the registry do not always match the evaluator's gold-standard expectations. Expanding the registry naming vocabulary is therefore a targeted engineering improvement.

### 5.8. Illustrative worked example: tomato greenhouse construction

This subsection is a worked benchmark example intended to make the execution path concrete; it is **not** a field validation study. The request is: "Construct a 30 m × 8 m greenhouse for tomato cultivation, containing 4 crop rows of 10 plants each, with temperature sensors, humidity sensors, a camera, and drip-irrigation devices."

**Intent parsing and compilation.** The LLM emits an IntentIR containing the greenhouse request, tomato crop, four CropRow candidates, 40 Plant instances, the requested sensors, one camera, and drip-irrigation equipment. The Knowledge Compiler inserts the required Greenhouse → Plot → CropRow → Plant containment structure, creates deterministic node identifiers, assigns available asset routes according to the registered crop/device policy, and generates binding contracts using canonical metric and unit names.

**Validation and repair.** In the representative trace, validation reports an R5 camera violation because an observation target is missing. The repair controller exposes the rule-compatible candidate actions. The LLM selects `fill_observes`; the deterministic executor resolves an admissible crop-row target and the required parameters, applies the change to a copied scene, re-validates, and commits the patch only because the fatal-violation count does not increase and the operator's scope constraints are satisfied.

**Trace outcome.** The accepted scene records the IntentIR, compiler calls, validator result, RepairTicket, operator selection, deterministic patch, and post-repair validation using evidence/call identifiers. The task is loadable by the prototype Three.js viewer. In the recorded benchmark execution, the KAFarmTwin run completes in under 3 s, whereas the corresponding SingleAgent execution is approximately 6.7 s and retains two fatal findings. These timing values illustrate one recorded task and should not be generalized beyond the aggregate latency results in Table 7.

The example demonstrates the intended responsibility boundary: the LLM specifies semantic intent and chooses among bounded alternatives, while deterministic modules own hierarchy expansion, canonicalization, state mutation, and post-mutation validation.

### 5.9. Threats to validity

1. **No independent field validation.** The present experiments evaluate controlled scene-construction tasks rather than deployment in an operating greenhouse. No independently collected set of real operator requests, physical device inventory, live sensor bindings, or expert acceptance study is included. This is the most important limitation for claims of practical protected-agriculture utility.

2. **Benchmark contact and construction bias.** test_v2 was consulted during development and directly motivated implementation corrections; it is a frozen known benchmark rather than a hidden test set. External300 is larger but was generated and reviewed by the authors. Its realized review process used single-author confirmation rather than the originally planned independent dual review and adjudication. Moreover, 84.5% of the net KF–SA success difference arises from the rule-repair category, which directly targets failure modes addressed by the proposed mechanism. Post-hoc analysis (Appendix A3) confirms that all 60 rule-repair tasks are D1 difficulty (single-rule R4, explicit fix target, one deterministic step), and the baseline comparison is asymmetric by design (SingleAgent has no repair loop). Neither benchmark should therefore be treated as independent evidence of open-world generalization.

3. **Inference stochasticity is incompletely measured.** test_v2 and the ablation family use repeated runs, and independent full-system samples differ (0.550 versus 0.610 CVSR). External300 and the cross-model-family experiments use one execution per task-method pair. Their paired-bootstrap intervals quantify variation over tasks, not repeated model sampling. Repeated inference on an independently selected External300 subset is needed to estimate run-to-run variance and method-by-task stability.

4. **Evaluator and vocabulary dependence.** Binding scores depend on canonicalization rules in the frozen evaluator. Unsupported aliases such as `°C`/`celsius` or `klux`/`lux` can create mismatches despite semantically compatible outputs. Conversely, deterministic benchmark categories such as memory query can produce ceiling effects and provide little discrimination among methods.

5. **Incomplete asset knowledge and naming-convention divergence.** The current asset registry and routing policy do not cover the diversity required by External300; asset-routing CVSR is only 0.083. Post-hoc analysis (Appendix A4) reveals that 78% of the 55 failed asset-routing tasks are naming or labeling mismatches rather than structural failures—the compiler produces structurally valid scenes with perfect Critical Recall, zero fatal violations, and Binding-F1 of 0.973, but object naming conventions diverge from the gold standard. The paper therefore demonstrates the architecture of policy-constrained routing more strongly than it demonstrates practically adequate open-world asset assignment, and the naming-convention gap is a specific, addressable engineering limitation rather than a fundamental architectural deficiency.

6. **Model and provider scope.** Five model families show a consistent direction under the same SiliconFlow interface, but the service does not expose immutable weight snapshots and all experiments use one provider interface. The results establish neither cross-provider robustness nor reproducibility to an exact future model snapshot.

7. **Cost scope.** Reported costs use provider token pricing and exclude engineering, maintenance, knowledge-base curation, asset-library construction, and infrastructure costs. The per-task cost ratio should not be interpreted as a total-cost-of-ownership estimate.

## 6. Conclusions

KAFarmTwin addresses protected-agriculture digital-twin scene construction by separating stochastic semantic interpretation from deterministic structural enforcement. Natural-language requests are first reduced to IntentIR. A Knowledge Compiler then expands hierarchy, bindings, units, and asset routes using executable agricultural knowledge. Validation findings are handled through typed repair: the LLM selects among admissible operators, while deterministic code instantiates and applies a candidate patch and commits it only when type/scope constraints are respected and fatal violations do not increase. This yields a transaction-level non-degradation property for committed typed repairs; it does not imply guaranteed convergence to a valid scene.

On test_v2, KAFarmTwin obtains CVSR 0.610 versus 0.360 for SingleAgent, with pass@5 0.700 versus 0.500 and zero fatal violations in the reported runs. Within the independent ablation family, removing the Knowledge Compiler substantially degrades the encoded asset subset, removing typed repair increases fatal violations from 0.000 to 0.220, and removing ontology constraints reduces Binding-F1. These findings support distinct roles for compilation, safety control, and semantic/type constraints.

On the larger External300 controlled benchmark, KAFarmTwin obtains CVSR 0.717 versus 0.480, a paired difference of +23.67 pp. The aggregate result must be interpreted by category: 60 of the 71 additional successful tasks arise from rule repair, all of which are D1 difficulty (single-rule R4 violations with explicit fix targets); scene-construction improvement is modest (+6 tasks); asset-routing CVSR is 0.083 but post-hoc analysis shows 78% of failures are naming mismatches rather than structural failures; and data-binding and memory-query tasks are at ceiling for both methods. Excluding rule repair, the paired difference narrows to +4.6 pp. Four additional model families reproduce a positive KF–SA direction under the same inference interface, indicating that the observed mechanism is not specific to one tested model family.

The present evidence therefore supports a narrower claim than general autonomous greenhouse construction: **encoding agricultural knowledge as deterministic compilation and bounded state transitions can improve validity and execution safety relative to shared-tool LLM agents on the tested controlled task distributions.** The study does not yet establish open-world asset routing, independent out-of-distribution generalization, or operational benefit in a real protected-agriculture facility.

The next validation stage should prioritize evidence rather than additional framework complexity: independently collected greenhouse requests and device/asset inventories, repeated inference to quantify stochastic stability, blinded or independent benchmark annotation, and a small field or expert-in-the-loop study measuring scene validity, correction effort, and construction time. These experiments are necessary before making stronger claims about deployability in production greenhouse digital twins.

---

## Data and code availability

The evaluation protocol, frozen evaluator (evaluator_v2.3, with source fingerprint logged for each run), configurations, task-generation scripts, and result records are intended to accompany the manuscript in the project repository **[repository URL to be inserted before submission]**. Raw run records include tool-call traces, binding contracts, and evidence identifiers. The External300 run is associated with SEAL SHA-256 `b52f00c4bee3b43723689c3556300e0754a8ab9564b96341d05e88b591d40d91`, allowing released artifacts to be checked against the sealed record. External300 tasks were generated and reviewed by the authors; this provenance is part of the released metadata and the benchmark is not described as independent external validation. Model weight snapshots are hosted by a third-party inference provider that does not expose immutable weight identifiers; the manuscript therefore records catalog model identifiers and experiment dates rather than claiming exact future model reproducibility.

## Appendix A: Supplementary analysis

### A3. Rule-repair task difficulty analysis

Table A3 summarizes the post-hoc difficulty analysis of the 60 External300 rule-repair tasks.

**Table A3.** Rule-repair task difficulty classification.

| Property | Value |
|:---------|:------|
| Total tasks | 60 |
| Violation rule | R4 (asset-type mismatch) — all 60 tasks |
| Difficulty tier | D1 — all 60 tasks |
| Explicit fix target in prompt | 60/60 (100%) |
| Repair steps required | 1 (all tasks) |
| Semantic reasoning required | No (all tasks) |
| Multiple valid repairs | No (all tasks) |
| Template families | 4 × 15 (Pump→irrigation, Irrigation→irrigation, Camera→camera, Sensor→sensor) |

The D1-D4 difficulty taxonomy is defined as follows:
- **D1**: Single rule, explicit fix target → deterministic single step.
- **D2**: Single rule, fix target requires semantic inference → single LLM call.
- **D3**: Multi-rule, cascading violations → sequential repair.
- **D4**: Ambiguous or multiple valid repairs → requires disambiguation.

All 60 tasks fall in D1. The 60/60 vs 0/60 result demonstrates that (i) the typed repair loop mechanism works for template-matched single-rule violations, and (ii) SingleAgent routes rule-repair tasks to a no-repair execution path by design. It does not demonstrate general repair capability across D2-D4 difficulty levels.

### A4. Asset-routing failure taxonomy

Table A4 classifies the 55 failed KF asset-routing tasks by failure pattern.

**Table A4.** Asset-routing failure taxonomy (KF, 55 failed tasks).

| Pattern | Count | % | Object-F1 | Relation-F1 | Binding-F1 | Description |
|:--------|------:|--:|----------:|------------:|-----------:|:------------|
| A: Naming mismatch | 32 | 58.2% | < 0.3 | ≥ 0.6 | ≥ 0.5 | Object IDs diverge from gold; relation structure largely correct |
| C: Partial naming | 11 | 20.0% | 0.3–0.7 | ≥ 0.6 | ≥ 0.5 | Partial overlap with gold naming convention |
| D: Edge/binding detail | 7 | 12.7% | ≥ 0.7 | variable | variable | Object identification mostly correct; edge/binding specifics differ |
| E: Unclassified | 5 | 9.1% | variable | variable | variable | Does not fit other patterns |

Sub-metric profiles for the 55 failed tasks:
- Critical Recall: 1.000 (all 55) — no missing critical objects
- Replay Success: 1.000 (all 55) — fully replayable
- Fatal violations: 0 (all 55) — no fatal errors
- Binding-F1: mean 0.973 — nearly perfect bindings
- Object-F1: mean 0.406 — primary failure point
- Relation-F1: mean 0.766 — moderate

The absence of structural failures (zero tasks with Critical Recall < 1.0 or fatal violations > 0) indicates that the compiler produces structurally valid, bound, replayable scenes. The failures are evaluative (naming convention mismatch) rather than generative (scene construction failure). The naming-mismatch fraction (Patterns A+C, 78.2%) represents an addressable engineering limitation in asset-registry naming conventions, not a fundamental architectural deficiency.

## References

Compton, M., Barnaghi, P., Bermudez, L., et al., 2012. The SSN ontology of the W3C semantic sensor network incubator group. J. Web Semant. 17, 25–32.

Efron, B., Tibshirani, R.J., 1993. An Introduction to the Bootstrap. Chapman & Hall/CRC, New York.

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

McNemar, Q., 1947. Note on the sampling error of the difference between correlated proportions or percentages. Psychometrika 12, 153–157.

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
