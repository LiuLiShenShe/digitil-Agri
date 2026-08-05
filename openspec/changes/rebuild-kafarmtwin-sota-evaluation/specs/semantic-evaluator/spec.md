## ADDED Requirements

### Requirement: Independent semantic evaluator
The system SHALL provide a semantic evaluator under `experiments/v3/evaluators/` that is fully independent of the scored methods and never calls their internal state. All methods SHALL be evaluated identically, without method-specific pre-scoring supplementation.

#### Scenario: Scorer ignores method internals
- **WHEN** a method output is scored
- **THEN** the evaluator SHALL use only the output, the frozen task gold, and the shared external trace/validator, never method-internal state

#### Scenario: No method-specific supplementation
- **WHEN** any method produces output with missing relations or bindings
- **THEN** the evaluator SHALL NOT fabricate relations or bindings on that method's behalf before scoring

### Requirement: Node constrained matching with optimal assignment
Node matching SHALL match on type, role, key attributes, and parent context. Where multiple instances of the same type occur, the evaluator SHALL use bipartite/Hungarian optimal matching. Semantic equivalence groups SHALL permit matching between objects with different IDs but equivalent meaning.

#### Scenario: Optimal multi-instance assignment
- **WHEN** a scene requires 20 tomato plants and a method outputs 20 tomato plants with permuted IDs
- **THEN** the evaluator SHALL find the optimal assignment via Hungarian matching and score them as correctly matched

#### Scenario: Semantic equivalence match
- **WHEN** a method outputs an object with a different ID but semantically equivalent type/role/attributes to a required node in an equivalence group
- **THEN** the evaluator SHALL count it as a correct match

### Requirement: Edge and binding validation
Relations SHALL require subject, predicate, object, and direction to match; a reversed direction or swapped subject/object SHALL be wrong. Bindings SHALL require subject, target, binding type, and necessary metadata.

#### Scenario: Reversed relation direction
- **WHEN** the gold has `contains(greenhouse, cropRow)` but a method outputs `contains(cropRow, greenhouse)`
- **THEN** the evaluator SHALL mark the relation as incorrect

#### Scenario: Wrong binding target
- **WHEN** a binding must attach a sensor to the greenhouse but the method binds it to the pump
- **THEN** the evaluator SHALL mark the binding as incorrect

### Requirement: Optional and forbidden objects
Optional nodes SHALL NOT reduce recall when absent, but a wrong optional object SHALL reduce precision. Forbidden objects SHALL incur a separate penalty.

#### Scenario: Optional object absent
- **WHEN** a task lists an optional node that a method omits
- **THEN** recall SHALL NOT be reduced by that omission

#### Scenario: Forbidden object present
- **WHEN** a method outputs an object listed in `forbidden_nodes`
- **THEN** the evaluator SHALL apply a separate forbidden-object penalty

### Requirement: Rule engine executable
The R1–R10 textual rules SHALL be implemented as an executable rule engine (`rule_engine.py`) consistent with the Go backend's `validateSemanticPlan` and `SceneBusinessBindingService.ValidateScene` judgments.

#### Scenario: Fatal rule conflict detection
- **WHEN** a method's output violates a fatal rule (e.g. R3 out-of-bounds layout)
- **THEN** the rule engine SHALL report the violation and it SHALL affect CVSR as fatal

### Requirement: Evidence and replay faithfulness
Trace evidence SHALL point to real tool requests, responses, state changes, or database snapshots. A declared trace without a real call SHALL score 0 for evidence. Auto-generated evidence IDs without a real response SHALL NOT pass. Rule fallback SHALL be flagged separately and never counted as LLM or multi-agent success.

#### Scenario: Declared trace without real call
- **WHEN** a method emits only declared trace steps with no real tool call evidence
- **THEN** the Evidence Score SHALL be 0

#### Scenario: Auto-generated evidence id without response
- **WHEN** a method supplies a fabricated evidenceId that has no matching real response in the trace proxy
- **THEN** the evaluator SHALL reject it and it SHALL NOT count toward Evidence Precision

#### Scenario: Rule fallback flagged
- **WHEN** a method falls back to the deterministic rule planner
- **THEN** the evaluator SHALL flag it as `DeterministicFallback` and exclude it from LLM/multi-agent success counts

### Requirement: Prohibited scoring shortcuts
The evaluator SHALL NOT use `min(generated_count, required_count)` as a correctness count, SHALL NOT count mere object quantity as semantic F1, and SHALL NOT treat error-free output that omits most required objects as success.

#### Scenario: Empty but numerous objects
- **WHEN** a method outputs the right number of objects but all are empty placeholders with no type or attributes
- **THEN** the evaluator SHALL NOT award a high score (CVSR stays 0 and object precision/recall remain low)