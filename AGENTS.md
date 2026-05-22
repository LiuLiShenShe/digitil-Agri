# AGENTS.md instructions for /data/fj/数字孪生

## Project Overview

This repository is a smart-agriculture 3D digital twin workspace. It combines:

- `digital-twingo/scene-design-v2/`: Vue 3 + TypeScript + Vite frontend for 3D scene editing, GLB model loading, data visualization, semantic scene building, and digital twin dashboards.
- `digital-twingo/scene-server-go/`: Go 1.24 + Gin + MySQL backend for scene APIs, asset/model services, IoT/mock data, semantic scene generation, and Agent-related services.
- `TRELLIS.2/`: Python-based image-to-3D / texture-generation research code used for GLB asset generation experiments.
- `openspec/`: OpenSpec planning/specification workspace for PRD-driven changes.
- `docs/`, `openspec/reference/references/`, `审计报告/`, `基于 Eino DeepAgents 的详细实施方案/`: product, design, research, audit, and implementation notes.

For deeper frontend/backend conventions, read `digital-twingo/CLAUDE.md`.

## Context7 / ctx7 Documentation Rule

Use the `ctx7` CLI to fetch current documentation whenever the user asks about a library, framework, SDK, API, CLI tool, or cloud service, even well-known ones like React, Vue, Vite, Three.js, Gin, Eino, Prisma, Express, Tailwind, Django, or Spring Boot. This includes API syntax, configuration, version migration, library-specific debugging, setup instructions, and CLI tool usage. Prefer this over web search for library docs.

Do not use `ctx7` for refactoring, writing scripts from scratch, debugging business logic, code review, or general programming concepts.

Steps:

1. Resolve library:

   ```bash
   npx ctx7@latest library <name> "<user's question>"
   ```

2. Pick the best match by exact name, description relevance, code snippet count, source reputation, and benchmark score.
3. Fetch docs:

   ```bash
   npx ctx7@latest docs <libraryId> "<user's question>"
   ```

4. Answer using the fetched documentation.

Rules:

- Call `library` first unless the user provides a `/org/project` library ID directly.
- Use the user's full question as the query.
- Do not run more than 3 Context7 commands per question.
- Do not include secrets, API keys, passwords, or credentials in queries.
- If a command fails with quota errors, tell the user and suggest `npx ctx7@latest login` or setting `CONTEXT7_API_KEY`.
- If a command fails with DNS, host resolution, or fetch errors, retry according to the active execution environment's network/sandbox rules.

## OpenSpec Workflow

The project uses OpenSpec for PRD-to-implementation planning.

Key files:

- `openspec/README.md`: OpenSpec index.
- `openspec/project.md`: project-level product/spec context.
- `openspec/roadmap.md`: milestone plan and active change order.
- `openspec/changes/<change-id>/`: change proposals with `proposal.md`, `design.md`, `tasks.md`, and `specs/**/spec.md`.
- `openspec/reference/references/`: research and design source material.
- `openspec/development-phases/phase0-baseline-report.md`: Phase 0 baseline report for OpenSpec/frontend/backend/data/assets/MVP boundaries.
- `openspec/tools/phase0_baseline_guard.py`: repeatable Phase 0 guard. It runs OpenSpec validation, backend tests, frontend build, active change status collection, asset counts, and data-source status reporting.

Phase 0 status:

- Phase 0 baseline convergence and development guardrails are complete as of 2026-05-21.
- The baseline guard report is `openspec/development-phases/phase0-baseline-report.md`.
- The first MVP is fixed to the tomato greenhouse: 1 greenhouse, 20 tomato plants, 1 weather station, 1 pump/irrigation device, 1 camera, and 1 sensor group.
- Phase 1 agricultural object foundation is implemented as of 2026-05-21. `add-agricultural-object-model` is complete (10/10) and ready for OpenSpec archive after review.
- Phase 2 scene-business binding is implemented as of 2026-05-21. `bind-scene-objects-to-business-objects` is complete (9/9), with `scenemodel` binding fields, `/scene/bindings/*` APIs, 3D point-select business detail, `/objects` scene location, validation, and the `番茄温室 MVP` bound scene seed.
- Phase 3 farm memory layer is implemented as of 2026-05-21. `add-farm-memory-layer` is complete (10/10), with metric dictionary, object memory APIs, event memory, daily archives/report source, frontend object detail entries, and read-only Agent tools `timeseries.query` / `event.query`. The Phase 3 migration has been executed in the current development database.
- Phase 4 Agent operation trace is implemented as of 2026-05-22. `add-agent-operation-trace` is complete (10/10), with FarmTwinOrchestrator trace mapping, specialized Agent role boundaries, read-only/controlled/prohibited tool policy, expanded `agentTrace.steps`, deterministic fallback recording, trace sanitization, and frontend trace step display.
- Phase 5 asset metadata and fidelity routing is implemented as of 2026-05-22. `add-asset-metadata-and-fidelity-routing` is complete (10/10), with asset metadata registry, quality audit, fidelity routing, plant geometry versions, missing-asset task linkage, Validator issue exposure, semantic Agent routing reasons, and frontend routing/quality display.

Before implementing PRD-level product changes:

1. Check existing OpenSpec changes with:

   ```bash
   openspec list
   openspec status --change <change-id>
   ```

2. Read the target change's `proposal.md`, `design.md`, `tasks.md`, and delta specs.
3. Keep implementation scoped to the relevant change.
4. Validate OpenSpec changes after editing specs:

   ```bash
   openspec validate --all --strict
   ```

Current OpenSpec changes:

- `add-agricultural-object-model`: 10/10 implementation tasks complete; implemented, pending archive to canonical specs.
- `bind-scene-objects-to-business-objects`: 9/9 implementation tasks complete; implemented, pending archive to canonical specs.
- `add-farm-memory-layer`: 10/10 implementation tasks complete; implemented, pending archive to canonical specs.
- `add-agent-operation-trace`: 10/10 implementation tasks complete; implemented, pending archive to canonical specs.
- `add-asset-metadata-and-fidelity-routing`: 10/10 implementation tasks complete; implemented, pending archive to canonical specs.

Phase 0 guard command:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 openspec/tools/phase0_baseline_guard.py --write-report openspec/development-phases/phase0-baseline-report.md
```

Do not run the Phase 0 guard in parallel with another frontend `npm run build`; both commands clean/write `digital-twingo/scene-design-v2/dist/`.

## Frontend Notes

Frontend path: `digital-twingo/scene-design-v2/`

Common commands:

```bash
npm install
npm run serve
npm run dev
npm run build
npm run build-view
```

Important conventions:

- Start Vite with project scripts or `./node_modules/.bin/vite`; do not use `npx vite`.
- Base path is `/scene/`.
- Main stack: Vue 3, TypeScript, Vite, Three.js, Pinia, Element Plus, ECharts, ECharts GL.
- Preserve the dark glassmorphism UI style and existing panel patterns.
- Panel visibility is usually managed through Pinia dialog state.
- Scene operations go through the existing `Scene` singleton and event bus patterns.
- Keep existing typos that are API-compatible, such as `laodScene` and `winowResize`, unless a change explicitly migrates them.

## Backend Notes

Backend path: `digital-twingo/scene-server-go/`

Common commands:

```bash
go build -o scene-server
go run SceneServerApplication.go
```

Backend conventions:

- Go 1.24, Gin, sqlx, MySQL.
- Server runs on port `9010` with context path `/sceneApi`.
- Follow the existing controller/service/mapper/vo structure.
- Prefer additive API changes that keep existing frontend flows working.
- Do not bypass services with direct database writes from Agent tools.
- Phase 4 Agent trace implementation lives in `service/SceneBuilderAgent.go`, `service/AgentOperationPolicy.go`, `service/AgentOperationTrace_test.go`, and `vo/SemanticVo.go`. Keep `SceneBuilderAgent` as the compatible semantic-build entry while exposing `FarmTwinOrchestrator` and specialized Agent steps through `agentTrace.steps`.
- Agent tools must stay governed by read-only, controlled-write, and prohibited categories. Prohibited shell/filesystem/HTTP/direct database/device-control operations must be blocked and recorded as policy violations in trace summaries.
- Phase 5 asset fidelity implementation lives in `service/AssetRegistryService.go`, `service/AssetQualityAuditService.go`, `service/AssetFidelityRoutingService.go`, `controller/AssetController.go`, and `vo/AssetMetadataVo.go`. Keep asset selection additive and traceable through metadata, audit issues, routing reasons, placeholders, and generation-task contracts rather than blocking semantic scene construction.

Database:

```bash
docker exec gofast-mysql mysql -u root -proot scene < scene.sql
docker exec gofast-mysql mysql -u root -proot scene < phase2_scene_business_binding_migration.sql
docker exec gofast-mysql mysql -u root -proot scene < phase3_farm_memory_layer_migration.sql
```

Phase 2 binding schema adds `scenemodel.sceneObjectId`, `businessObjectId`, `assetKey`, and `isDefaultBinding`. Existing databases must run the Phase 2 migration before using `/sceneApi/scene/bindings/*`.
Phase 3 memory schema adds `farm_event_memory` and `farm_daily_archive`. Existing databases must run the Phase 3 migration before using `/sceneApi/objects/:id/memory/*` and report-source APIs; the current development database has already run it.

## TRELLIS.2 / Asset Generation Notes

`TRELLIS.2/` is a heavy Python research dependency for 3D generation. Treat it as an asset-generation subsystem, not as the main app runtime.

- Avoid running GPU-heavy training or inference unless explicitly requested.
- For platform integration, prefer task records, metadata, and generated GLB handoff rather than blocking UI/backend flows.
- Generated assets should be validated before becoming managed scene assets.

## Verification

Use focused verification based on touched areas:

- OpenSpec docs: `openspec validate --all --strict`
- Frontend: `npm run build` from `digital-twingo/scene-design-v2/`
- Backend: `go test ./...` or `go build -o scene-server` from `digital-twingo/scene-server-go/`

If verification is not run, state that clearly in the final response.

## Collaboration And Safety

- The worktree may already contain user changes. Do not revert or overwrite changes you did not make.
- Keep edits scoped to the user's request.
- Prefer existing project patterns over new abstractions.
- Do not commit unless the user explicitly asks.
- Do not add secrets to docs, code, prompts, logs, or Context7 queries.
