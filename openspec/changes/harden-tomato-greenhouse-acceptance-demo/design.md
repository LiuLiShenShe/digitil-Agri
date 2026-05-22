## Context

The previous changes are complete and remain active for review/archive. Phase 6 should not duplicate their internals. It should provide a stable acceptance aggregator and a demo console that read from the existing services and expose the tomato greenhouse MVP story in one place.

## Goals / Non-Goals

**Goals:**

- Verify the fixed tomato greenhouse MVP prompt end to end.
- Make expected MVP counts explicit and regression-tested.
- Surface acceptance status for semantic build, trace, asset routing, object drill-down, validation, and greenhouse report source.
- Provide a frontend console suitable for internal demonstration and review.

**Non-Goals:**

- Do not archive the existing five completed changes automatically.
- Do not introduce real device control, RBAC, production audit, or daily GLB reconstruction.
- Do not require missing camera or sensor GLBs to be available before a scene can be accepted.

## Backend Design

Add `AcceptanceService` as a thin orchestration service. It will call existing services instead of bypassing their contracts:

- `SemanticService.BuildPlan` for the MVP prompt and Agent trace.
- `AgriculturalObjectService` for greenhouse/device object details and relationships.
- `SceneBusinessBindingService.ValidateScene` with an in-memory Phase 6 demo model set for deterministic acceptance evidence.
- `FarmMemoryService.GreenhouseReportSource` for greenhouse report data.
- Asset routing and missing asset task state from the semantic build result.

The service returns one `TomatoGreenhouseAcceptanceVo` with:

- Fixed prompt, scene name, run timestamp, overall status.
- Expected and actual MVP model counts by asset key.
- Ordered demo steps with pass/fail status and evidence text.
- Success metric rows matching `openspec/roadmap.md`.
- Semantic build result, Agent trace summary, validation summary, greenhouse/device drill-down context, report source, issues, and archive readiness.

### Implemented Backend Shape

- `service/AcceptanceService.go` owns the Phase 6 aggregation and deterministic demo stores used for acceptance evidence.
- `controller/AcceptanceController.go` exposes `GET /sceneApi/acceptance/tomato-greenhouse`.
- `vo/AcceptanceVo.go` defines the response contract for counts, steps, metrics, issues, semantic build evidence, missing assets, object memory context, report source, and archive readiness.
- `service/SemanticService.go` now preserves the fixed MVP prompt counts for 20 tomato plants, 1 greenhouse, 1 weather station, 1 irrigation or pump device, 1 camera placeholder task, and 1 sensor placeholder task.

## Frontend Design

Add an independent route `/acceptance`. The view loads `GET /acceptance/tomato-greenhouse` through `acceptanceService.ts`, displays a refresh/run button, and renders a dense dashboard:

- Overall pass/fail and updated time.
- MVP count cards.
- Demo step timeline.
- Success metric matrix.
- Trace step list.
- Missing asset routing and generation task list.
- Object drill-down and abnormal device context.
- Validation issue list.
- Greenhouse report summary and recommendations.

The page follows the existing dark glassmorphism dashboard style and avoids a marketing landing page.

### Implemented Frontend Shape

- `src/services/acceptanceService.ts` contains the typed API client for the acceptance contract.
- `src/views/AcceptanceDemoView.vue` renders the full Phase 6 dashboard.
- `src/router/index.ts` maps `/acceptance`, which is served to users as `/scene/acceptance` because the Vite base path is `/scene/`.
- `src/components/HeadMenu.vue` adds the "验收" navigation entry.

## Error Handling

- The acceptance endpoint returns HTTP 200 with `ResultVo.Code = 200` when the aggregator can run, even if individual acceptance checks fail.
- Individual failed checks appear in `steps`, `metrics`, and `issues`.
- Service-level unexpected errors return `ResultVo.Code = 500` with a concise message.

## Testing

- Backend TDD tests first lock the expected MVP counts and acceptance aggregation contract.
- Existing Phase 1-5 tests remain the regression net.
- Frontend verification is `npm run build`, since the project has no test script.

Verification completed on 2026-05-22:

- `openspec validate --all --strict`
- `cd digital-twingo/scene-server-go && go test ./service -run 'Acceptance|SemanticTomato' -v`
- `cd digital-twingo/scene-server-go && go test ./...`
- `cd digital-twingo/scene-design-v2 && npm run build`
