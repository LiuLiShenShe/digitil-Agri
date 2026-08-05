## ADDED Requirements

### Requirement: Evidence must be real and auditable
Every evidence claim SHALL point to a real tool request, response, state change, or database snapshot recorded through the shared external trace proxy. A declared trace with no real call SHALL score zero for evidence. The system SHALL NOT auto-fabricate evidence IDs; a fabricated evidenceId with no matching real response SHALL NOT pass.

#### Scenario: Declared trace without real call
- **WHEN** a method records a trace step as declared with no backing tool call in the trace proxy
- **THEN** the evidence score for that step SHALL be 0

#### Scenario: Fabricated evidence id rejected
- **WHEN** a method emits an evidenceId that does not correspond to any recorded real response
- **THEN** the evaluator SHALL reject it and exclude it from Evidence Precision

### Requirement: Shared external trace proxy
All methods SHALL emit their traces through the same `harness/trace_proxy.py`, which records real agent IDs, messages, and tool calls rather than labeling steps post-hoc by tool name. Replay (`evaluators/replay.py`) SHALL use the same trace proxy to recompute Replay Success.

#### Scenario: Replay from shared trace
- **WHEN** `evaluators/replay.py` runs
- **THEN** it SHALL replay the recorded tool calls through the shared trace proxy and report Replay Success

### Requirement: Rule fallback is separately flagged
A method that falls back to the deterministic rule planner SHALL be flagged as `DeterministicFallback` in the trace and SHALL NOT be counted as LLM or multi-agent success.

#### Scenario: Fallback excluded from success
- **WHEN** a run used the rule fallback
- **THEN** its result SHALL be excluded from the proposed method's main LLM/multi-agent success counts and reported separately as a fallback rate

### Requirement: Evidence metrics
The evaluator SHALL report Evidence Coverage, Evidence Precision, and Replay Success for every method, targeted at or above 0.95.

#### Scenario: Report evidence metrics
- **WHEN** generating the statistical report
- **THEN** it SHALL include Evidence Coverage, Evidence Precision, and Replay Success per method