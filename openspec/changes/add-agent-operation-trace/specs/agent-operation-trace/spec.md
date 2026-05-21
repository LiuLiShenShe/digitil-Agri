## ADDED Requirements

### Requirement: Agent role boundaries
The system SHALL define FarmTwinOrchestrator as the coordinating Agent and SHALL define specialized responsibilities for ScenePlannerAgent, AssetFidelityAgent, LayoutAgent, DataBindingAgent, TimeSeriesAgent, GrowthAnalysisAgent, AlertDiagnosisAgent, ReportAgent, and ValidatorAgent.

#### Scenario: Orchestrate tomato greenhouse build
- **WHEN** a user asks the platform to build a tomato greenhouse scene
- **THEN** FarmTwinOrchestrator SHALL coordinate planning, asset selection, layout, binding, validation, and result summarization through specialized Agent responsibilities

#### Scenario: Route validation task
- **WHEN** a user asks to validate a complete greenhouse scene
- **THEN** FarmTwinOrchestrator SHALL route the task to ValidatorAgent or an equivalent validator responsibility

### Requirement: Agent tool whitelist
Agents SHALL use only approved tools, separating read-only tools, controlled write tools, and prohibited operations.

#### Scenario: Read-only tool use
- **WHEN** an Agent needs current scene, model metadata, object details, time-series data, or events
- **THEN** it SHALL use approved read-only tools such as `scene.current`, `model.search`, `model.metadata`, `object.lookup`, `object.relations`, `timeseries.query`, or `event.query`

#### Scenario: Controlled write tool use
- **WHEN** an Agent needs to plan, solve layout, apply a scene plan, create an asset job, bind an object, or acknowledge an alert
- **THEN** it SHALL use approved controlled write tools such as `scene.plan`, `layout.solve`, `scene.applyPlan`, `asset.job.create`, `object.bind`, or `alert.acknowledge`

#### Scenario: Prohibited operation
- **WHEN** an Agent attempts arbitrary shell execution, arbitrary filesystem writes, arbitrary HTTP, direct database writes, or direct device control without a state machine
- **THEN** the system SHALL block the operation and record the policy violation in trace

### Requirement: Agent trace schema
Every Agent task SHALL record taskId, userGoal, mode, ordered steps, Agent name, tool name, status, duration, input summary, output summary, failure reason when applicable, and fallback path when applicable.

#### Scenario: Successful semantic scene build trace
- **WHEN** semantic scene construction completes successfully
- **THEN** the trace SHALL show the planning, asset selection, layout, binding, and validation steps with status and summaries

#### Scenario: Failed tool call trace
- **WHEN** an Agent tool call fails
- **THEN** the trace SHALL record the failed step, failure reason, duration, and fallback path when one exists

### Requirement: Trace display coverage
The system SHALL provide displayable traces for semantic construction, asset routing, object binding, and validation.

#### Scenario: View asset routing trace
- **WHEN** a user inspects an asset routing task
- **THEN** the trace SHALL show the selected route, decision summary, tool status, and any missing asset job creation

#### Scenario: View binding validation trace
- **WHEN** a user inspects a validation task
- **THEN** the trace SHALL show which objects were checked and which missing bindings, data bindings, or metadata issues were found

### Requirement: Deterministic fallback
Core scene construction SHALL support deterministic fallback when the LLM is not configured or a model call fails.

#### Scenario: LLM unavailable during greenhouse generation
- **WHEN** a user requests a supported greenhouse scene and the LLM is unavailable
- **THEN** the system SHALL use a deterministic template, rule-based parser, or predefined scene plan to continue the core scene construction flow

#### Scenario: Fallback trace
- **WHEN** deterministic fallback is used
- **THEN** the Agent trace SHALL record that fallback was used and summarize the fallback path

