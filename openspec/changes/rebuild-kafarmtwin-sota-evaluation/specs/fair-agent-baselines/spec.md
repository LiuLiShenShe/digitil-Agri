## ADDED Requirements

### Requirement: Identical capability and budget across methods
All main experiment methods SHALL run under identical capabilities and budgets: the same base model and version, the same system knowledge, the same assets/objects/memory/rules, the same callable tools, the same external Validator API, the same trace proxy, the same maximum LLM calls, the same maximum tool calls, the same maximum repair rounds, the same token/cost budget, and the same timeout/retry/failure rules.

#### Scenario: Shared tool registry
- **WHEN** any method needs to call a tool (scene planning, layout solve, asset routing, object binding, validation)
- **THEN** it SHALL use the shared `ToolRegistry` from `harness/tools.py`, not a per-method duplicate

#### Scenario: Shared external validator
- **WHEN** any method invokes validation
- **THEN** it SHALL call the single external Validator API from `harness/validator_api.py` aligned with the rule engine

#### Scenario: Budget enforcement
- **WHEN** a method exceeds the maximum LLM calls, tool calls, repair rounds, token, or cost budget
- **THEN** the shared `BudgetEnforcer` SHALL stop that run and record the budget exhaustion

### Requirement: Fair baseline methods
The system SHALL implement and compare at least these methods sharing the same capabilities: `SingleAgent-AllTools`, `ReAct-AllTools`, `GenericMultiAgent-AllTools`, `GenericRepair-AllTools`, and `KAFarmTwin-TypedRepair`. A `DeterministicFallback` method MAY be added but SHALL be reported separately and not mixed into the proposed method's main results.

#### Scenario: Single-agent vs multi-agent
- **WHEN** comparing SingleAgent-AllTools to GenericMultiAgent-AllTools
- **THEN** both SHALL have the same tools, knowledge, and budget; only agent organization and planning differ

#### Scenario: Fallback kept separate
- **WHEN** reporting results
- **THEN** `DeterministicFallback` results SHALL be listed separately, and the proposed method's main results SHALL NOT include rule-fallback successes

### Requirement: Method differences are structural only
The permitted differences between methods SHALL be limited to agent organization, planning approach, conflict representation, conflict routing policy, patch selection policy, and evidence binding policy. The raw output of every method SHALL pass through the same deterministic canonicalizer; no method SHALL receive method-specific pre-scoring supplementation of relations or bindings.

#### Scenario: Canonicalization is shared and identical
- **WHEN** any raw method output needs normalization before scoring
- **THEN** the identical `canonicalizer.py` SHALL be applied to all methods

### Requirement: Real execution, not simulation
The main experiment SHALL NOT replace RAG, Validator, or multi-agent with "prompt the LLM to simulate" the component. Every method SHALL exercise the real shared tools and trace proxy.

#### Scenario: No simulated RAG or validator
- **WHEN** a method describes itself as using RAG, a validator, or multiple agents
- **THEN** it SHALL actually invoke those components through the shared harness rather than only describing them in a prompt