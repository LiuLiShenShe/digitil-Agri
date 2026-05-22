## Why

Phase 1-5 have implemented the agricultural object model, 3D business binding, farm memory layer, Agent operation trace, and asset fidelity routing. Phase 6 needs a repeatable acceptance surface that proves those capabilities work together as one tomato greenhouse MVP instead of as separate feature slices.

Without an integrated acceptance demo, regressions can hide across subsystem boundaries: the semantic builder may parse the prompt, but generate the wrong object counts; missing assets may continue with placeholders, but not expose generation tasks; or report data may exist, but not be connected to the demo story.

## What Changes

- Add a Phase 6 acceptance capability for the fixed tomato greenhouse MVP prompt.
- Add a backend acceptance endpoint that aggregates semantic construction, model counts, Agent trace, asset routing, binding validation, object drill-down context, abnormal device context, report source data, success metrics, and archive readiness.
- Harden the deterministic semantic fallback so the prompt "搭建番茄温室，包含 20 株番茄、气象站、水泵、摄像头和传感器" produces the MVP object counts exactly.
- Add a frontend acceptance console at `/acceptance` for demonstration and regression review.
- Update Phase 6 OpenSpec and roadmap documentation with the active change and acceptance evidence path.

## Implementation Status

Implemented on 2026-05-22. The change is `17/17` complete in `tasks.md`, OpenSpec reports `state: all_done`, and the demo is available through `GET /sceneApi/acceptance/tomato-greenhouse` plus the frontend route `/scene/acceptance`. This change records archive readiness only; Phase 1-5 changes still require the normal OpenSpec review/archive step before moving into canonical specs.

## Capabilities

### New Capabilities

- `tomato-greenhouse-acceptance-demo`: Provides an end-to-end tomato greenhouse MVP acceptance and demonstration flow.

### Modified Capabilities

- `asset-fidelity-routing`: Semantic construction keeps missing camera and sensor assets non-blocking through placeholders and generation tasks.
- `agent-operation-trace`: Acceptance output surfaces existing trace steps and confirms the controlled tool policy remains visible.

## Impact

- Backend service/controller/VO additions under `digital-twingo/scene-server-go/`.
- Frontend service/view/router/navigation additions under `digital-twingo/scene-design-v2/src/`.
- OpenSpec documentation updates under `openspec/changes/`, `openspec/development-phases/`, `openspec/README.md`, and `openspec/roadmap.md`.
- No direct archive of Phase 1-5 changes; Phase 6 only records archive readiness.
