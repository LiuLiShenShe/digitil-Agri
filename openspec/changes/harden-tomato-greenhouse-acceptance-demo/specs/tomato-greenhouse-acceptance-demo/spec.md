## ADDED Requirements

### Requirement: Tomato greenhouse MVP semantic acceptance
The system SHALL provide a deterministic acceptance flow for the fixed tomato greenhouse MVP prompt.

#### Scenario: Build tomato greenhouse MVP counts
- **WHEN** Phase 6 runs the prompt "搭建番茄温室，包含 20 株番茄、气象站、水泵、摄像头和传感器"
- **THEN** the semantic build result SHALL include 20 tomato models, one greenhouse model, one weather station model, one irrigation or pump model, one camera placeholder with a generation task, and one sensor placeholder with a generation task

#### Scenario: Preserve non-blocking missing assets
- **WHEN** the camera or sensor GLB is unavailable
- **THEN** the system SHALL keep the scene build loadable by using placeholder models and SHALL expose the related asset generation task state

### Requirement: Integrated acceptance evidence
The system SHALL aggregate Phase 1-5 acceptance evidence into one tomato greenhouse acceptance response.

#### Scenario: Acceptance response includes cross-phase evidence
- **WHEN** a user opens the Phase 6 acceptance endpoint
- **THEN** the response SHALL include semantic build status, Agent trace steps, asset routing reasons, scene binding validation, greenhouse object context, abnormal device context, greenhouse report source data, success metrics, and archive readiness

#### Scenario: Acceptance failures are explainable
- **WHEN** one acceptance check does not meet its target
- **THEN** the response SHALL keep running other checks and SHALL include the failed check, target, actual value, and issue message

### Requirement: Acceptance demonstration console
The frontend SHALL provide a complete Phase 6 demonstration console.

#### Scenario: View acceptance dashboard
- **WHEN** a user navigates to `/acceptance`
- **THEN** the console SHALL display overall status, MVP model counts, demo steps, success metrics, Agent trace, missing asset routing, object drill-down context, validation issues, greenhouse report summary, and archive readiness

#### Scenario: Refresh acceptance evidence
- **WHEN** a user clicks the console refresh action
- **THEN** the console SHALL reload acceptance evidence from the backend and display any failures without blocking the page
