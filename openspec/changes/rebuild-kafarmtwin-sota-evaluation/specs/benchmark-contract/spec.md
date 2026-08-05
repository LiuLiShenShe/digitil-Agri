## ADDED Requirements

### Requirement: Versioned frozen benchmark dataset
The system SHALL provide a versioned, frozen benchmark for KAFarmTwin evaluation under `experiments/v3/benchmark/`, with train/dev/test splits, a sealed test gold, and a reproducibility manifest. The dataset SHALL be protected against data leakage: agents executing tasks must not access the gold.
The benchmark revision id, each split's SHA-256, and the sealing command SHALL be recorded in `benchmark_manifest.json`.

#### Scenario: Train output of the expander
- **WHEN** the `expand_legacy_tasks.py` script runs over the legacy 30 tasks
- **THEN** it SHALL produce `train.jsonl`, `dev.jsonl`, `test_public_inputs.jsonl`, and `test_gold.sealed.jsonl` where every task carries typed gold (nodes, edges, bindings, constraints, equivalence groups, critical objects, allowed variants)

#### Scenario: Sealed test gold verification
- **WHEN** `make benchmark-validate` runs
- **THEN** it SHALL recompute the SHA-256 of `test_gold.sealed.jsonl` and compare it to the value recorded in `benchmark_manifest.json`, failing on mismatch

#### Scenario: Gold revision requires full rerun
- **WHEN** the test gold is revised
- **THEN** the benchmark version SHALL be bumped (e.g. `benchmark_v2`) and every method SHALL be rerun on the new frozen split

### Requirement: Typed task schema
Each benchmark task SHALL conform to a JSON schema with these fields: `task_id`, `category` (one of scene_build, asset_route, data_bind, repair, memory_query), `difficulty`, `prompt`, `initial_state`, `goal_state`, `required_nodes`, `optional_nodes`, `forbidden_nodes`, `required_edges`, `required_bindings`, `constraints`, `equivalence_groups`, `critical_objects`, and `allowed_variants`.

#### Scenario: Repair task carries real initial state
- **WHEN** a task has category `repair` (legacy T19–T24)
- **THEN** it SHALL include a real, decidable `initial_state` describing the faulty scene, plus a `goal_state` and `critical_objects` listing the objects that must actually be modified

#### Scenario: Multiple legal scenes
- **WHEN** more than one scene is valid for a task
- **THEN** the alternatives SHALL be expressed through `constraints`, `equivalence_groups`, and `allowed_variants` rather than a single rigid gold graph

### Requirement: Benchmarks must not be gamed
The dataset definitions SHALL NOT be modified to improve the proposed method's ranking, and the agent executing a task SHALL NOT be given access to gold edges, bindings, or goal states.

#### Scenario: No gold in public inputs
- **WHEN** `test_public_inputs.jsonl` is provided to a method
- **THEN** it SHALL contain only the prompt and public task fields, never the sealed gold content