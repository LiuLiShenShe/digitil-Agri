## ADDED Requirements

### Requirement: SOTA Gate as the sole exit condition
The system SHALL provide a `make sota-gate` command that exits non-zero until all success conditions are met, then exits zero and prints the evidence summary. No completed status SHALL be announced before the gate passes.

#### Scenario: Gate fails when baselines run
- **WHEN** `make sota-gate` runs before all fairness baselines are executed
- **THEN** it SHALL exit non-zero and report which conditions are missing

#### Scenario: Gate passes with evidence
- **WHEN** all conditions are satisfied
- **THEN** `make sota-gate` SHALL exit zero and print `SOTA_GATE=PASS`, `baseline=<name>`, `delta_cvsr=<value>`, `ci95=<low,high>`, `pass5_delta=<value>`, and `manifest_sha256=<value>`

### Requirement: Metric and coverage gates
The primary metric SHALL be CVSR. The proposed method's test-set Mean CVSR SHALL exceed the strongest fair baseline by at least 3 percentage points. Paired per-task bootstrap on the difference MUST yield a 95% CI whose lower bound is greater than 0. pass^5 MUST be higher than the strongest baseline. Critical Object Recall SHALL NOT be lower than the strongest baseline (target 0.95). Fatal Violation Rate SHALL NOT be higher than the strongest baseline (target at most 0.01).

#### Scenario: CVSR difference too small
- **WHEN** KAFarmTwin's Mean CVSR exceeds the strongest baseline by only 1.5 percentage points
- **THEN** the gate SHALL fail even if other metrics look strong

#### Scenario: pass^5 not higher
- **WHEN** KAFarmTwin's pass^5 is not strictly greater than the strongest baseline
- **THEN** the gate SHALL fail

### Requirement: Cost and latency guard
Cost and p95 latency SHALL NOT grow without bound. If the proposed method costs more than 1.5 times the strongest baseline, it MUST still dominate on a budget-normalized metric or Pareto front to pass.

#### Scenario: Cost exceeds 1.5x without Pareto advantage
- **WHEN** KAFarmTwin's cost is 1.6x the strongest baseline and it does not Pareto-dominate on the cost-normalized CVSR vs latency tradeoff
- **THEN** the gate SHALL fail

### Requirement: Multi-model consistency or model-specific claim
The result MUST be direction-consistent across at least 3 base models, or the paper MUST explicitly limit its conclusion to the specific model family shown to work.

#### Scenario: Single-model claim accepted when limited
- **WHEN** the method is only validated on `deepseek-ai/DeepSeek-V4-Flash` and the paper explicitly scopes its claim to that model
- **THEN** the gate SHALL pass subject to all other conditions but the claim SHALL be model-limited

### Requirement: Reproducibility
The result MUST be reproducible from a clean environment with one command (`make sota-gate`), with raw logs and statistical scripts present. All paper numbers SHALL be auto-generated from the new results, never hand-copied from prior tables.

#### Scenario: Hand-copied table detected
- **WHEN** any number in the paper output is manually copied from `experiments/legacy/` tables
- **THEN** `make reproduce-paper` SHALL fail and `make sota-gate` SHALL fail

### Requirement: No threshold gaming
Success thresholds SHALL NOT be changed to fit results, failing tasks SHALL NOT be deleted, and the test set, gold, scorer, or baseline budget SHALL NOT be altered to raise the proposed method's rank.

#### Scenario: Altering baseline budget to harm baselines
- **WHEN** a baseline's budget is reduced to lower its CVSR for gate passage
- **THEN** the gate SHALL reject the result as inconsistent with the fairness contract