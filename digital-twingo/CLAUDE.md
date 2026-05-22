# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **3D Digital Twin platform** (智慧农业数字孪生平台) by Beijing Yupont Electric Power Tech Co., Ltd. It consists of two sub-projects:

- **scene-design-v2** — Vue 3 + TypeScript + Vite frontend for building and viewing 3D scenes (GLTF/GLB models, data visualization)
- **scene-server-go** — Go + Gin backend providing scene storage, model list, data APIs, and AI 3D asset generation

Current implementation phase: **Phase 5 asset metadata and fidelity routing is implemented** as of 2026-05-22. The next planned phase is **Phase 6 integrated acceptance and demo hardening**.

- Previous app baseline still includes Phase 3 data visualization capabilities: real-time line chart, gauge, radar, 3D bar chart, heatmap, pie chart, WebSocket mock data stream, and 3D data overlays.
- OpenSpec implementation progress: `add-agricultural-object-model` is complete (10/10), `bind-scene-objects-to-business-objects` is complete (9/9), `add-farm-memory-layer` is complete (10/10), `add-agent-operation-trace` is complete (10/10), and `add-asset-metadata-and-fidelity-routing` is complete (10/10). These changes remain in `openspec/changes/` pending review/archive to canonical specs.
- Phase 1 object foundation includes backend object lookup/relation APIs, tomato greenhouse MVP seed data, stable `object.lookup` / `object.relations` output shapes, and the frontend `/objects` debug entry. Archive `add-agricultural-object-model` after review.
- Phase 2 scene-business binding includes stable `sceneObjectId`, `businessObjectId`, `assetKey`, and `isDefaultBinding` fields on `scenemodel`; `/scene/bindings/*` lookup/update/delete/validation APIs; 3D point-select business detail in `ProperityPane`; `/objects` scene location; and the `番茄温室 MVP` bound scene seed.
- Phase 3 farm memory layer includes metric dictionary and aliases, default sync policies, object-level latest/timeseries/events/daily-archive/report-source APIs, `farm_event_memory` and `farm_daily_archive` schema, frontend object memory panels, 3D point-select memory summaries, and read-only Assistant tools `timeseries.query` / `event.query`.
- Phase 4 Agent operation trace includes `FarmTwinOrchestrator` trace mapping over the compatible `SceneBuilderAgent` entry, specialized Agent role boundaries, read-only/controlled/prohibited tool policy, expanded `agentTrace.steps`, deterministic fallback recording, sensitive trace-summary sanitization, and frontend Agent trace step display.
- Phase 5 asset metadata/fidelity routing includes backend asset registry, quality audit, routing decisions, plant geometry versions, missing-asset task linkage, Validator asset-quality issues, semantic Agent routing reasons, and frontend routing/quality/task display.
- Phase 3 migration `digital-twingo/phase3_farm_memory_layer_migration.sql` has been executed in the current development database.
- Phase 0 artifacts live under `openspec/development-phases/phase0-baseline-report.md` and `openspec/tools/phase0_baseline_guard.py`.

## Common Commands

### Frontend (scene-design-v2/)
```
npm install              # Install dependencies
npm run serve            # Dev server (standard mode — mock data, editor enabled)
npm run dev              # Dev server (debug mode — real API, test UI elements visible)
npm run serve-view       # Dev server (mock viewer mode — mock data, editor hidden)
npm run build            # Production build → dist/scene/ (editor mode, type-checks first)
npm run build-view       # Viewer-only production build → dist/scene/
npm run preview          # Preview production build locally
```

**CRITICAL**: Always use `./node_modules/.bin/vite` to start Vite, NOT `npx vite`. `npx` may pull a cached bogus version (8.0.11) from `~/.npm/_npx/` while the real project uses Vite 6.4.2.

There are no test or lint scripts.

### Backend (scene-server-go/)
```
go build -o scene-server     # Build binary
./scene-server               # Run (reads application.yml, starts on port 9010)
go run SceneServerApplication.go   # Run directly
```

Swagger UI available at `http://localhost:9010/swagger/index.html` when swagger is enabled in config.

### Database
MySQL 8.0 runs in Docker container `gofast-mysql` on port 3306 (root:root). Database: `scene`.
```
docker exec gofast-mysql mysql -u root -proot scene < scene.sql    # Initialize schema
docker exec gofast-mysql mysql -u root -proot scene < phase2_scene_business_binding_migration.sql    # Upgrade existing DB for scene-business binding
docker exec gofast-mysql mysql -u root -proot scene < phase3_farm_memory_layer_migration.sql    # Upgrade existing DB for farm memory layer
```

### Model Asset Conversion
```
pip install trimesh
cd /data/fj/数字孪生
python3 convert_obj_to_glb.py    # Convert OBJ+MTL → GLB, outputs to scene-server-go/scene-assets/import/
```

### Phase 0 Baseline Guard
```
cd /data/fj/数字孪生
PYTHONDONTWRITEBYTECODE=1 python3 openspec/tools/phase0_baseline_guard.py --write-report openspec/development-phases/phase0-baseline-report.md
```

The guard runs OpenSpec validation, backend `go test ./...`, frontend `npm run build`, active change status collection, asset counts, and data-source status reporting. Do not run it in parallel with another `npm run build`, because both commands clean/write `scene-design-v2/dist/`.

## Architecture

### Frontend Architecture (scene-design-v2/)

**Build Tool**: Vite 6.4.2. Base path is `/scene/`.

**UI Theme**: Dark glassmorphism design — deep navy background (`#070b18`), accent cyan (`#00d4ff`), glass panels with `backdrop-filter: blur()`, rounded corners. All Element Plus components overridden to dark theme via App.vue global CSS.

**Logo**: Inline SVG in HeadMenu.vue — 3D cube wireframe with gradient (`#00d4ff` → `#4090ff`) + "数字孪生 / DIGITAL TWIN" text.

**Communication Pattern**: Components communicate via mitt event bus (`$bus`). Key events:
- `winowResize` — Window resize (note the typo, kept for compatibility)
- `toggleBoxSelect` — Toggle box selection mode
- `terrainGenerate` / `terrainClear` — Terrain operations
- `terrainBrushToggle` — Brush on/off
- `snapToggle` — Snap config change
- `templateApply` — Apply scene template
- `layerAdd` / `layerRemove` / `layerToggleVisible` / `layerToggleLocked` / `layerRename` / `layerSelectAll` / `batchMoveToLayer` — Layer operations

#### Core 3D Engine (`src/lib/`)

| File | Version | Purpose |
|------|---------|---------|
| `scene.ts` | v2.1 | Singleton `Scene` class manages the entire Three.js env: WebGL renderer, PerspectiveCamera, OrbitControls, lighting, skybox, ground, grid, model registry, animation loop, terrain, layers, batch ops, snap, templates, brush. Also supports secondary instances for mini-viewports. |
| `model.ts` | v2.0 | `Model` class: GLTF/GLB loading, auto-fit scale/bounds via Box3, selection highlighting, animation support, and stable `sceneObjectId` / primary business binding metadata. |
| `dragcontrol.ts` | v2.1 | Custom drag handler with Y-lock, grid snap (`_snapConfig`), model-to-model alignment snap, multi-model drag (`_models[]`), visual snap indicator. |
| `terrain.ts` | NEW Phase 2 | `TerrainImporter`: heightmap image → PlaneGeometry displacement, GeoJSON elevation parsing, vertex color gradient. |
| `layerManager.ts` | NEW Phase 2 | `LayerManager`: model group/layer CRUD, visibility/lock toggle, model-layer mapping, JSON serialization. |
| `boxSelector.ts` | NEW Phase 2 | `BoxSelector`: rubber-band rectangle selection in canvas, world-to-screen projection, multi-model selection. |
| `terrainBrush.ts` | NEW Phase 2 | `TerrainBrush`: multi-layer canvas-based texture painting on ground plane, radial gradient brush strokes, erase mode, composite texture generation. |
| `dataOverlay.ts` | NEW Phase 3 | `DataOverlayManager`: 3D data labels/sprites above models, status rings (cyan/orange/red), animated pulse rings, proportional 3D data bars (cylinder + emissive sphere). Singleton via `getDataOverlayManager(scene)`. |
| `utils.ts` | v2.0 | `uuid()`, `fmtNumber()`, date helpers. |

**Key Scene methods (Phase 2 additions)**:
- `generateTerrain(params)` — Terrain from heightmap/GeoJSON/DEM
- `createLayer(name, color)` / `deleteLayer(id)` / `toggleLayerVisible(id)` / `toggleLayerLocked(id)`
- `batchMove` / `batchRotate` / `batchScale` / `batchCopy` / `batchDelete`
- `toggleSnap(enabled?)` — Toggle grid/alignment snapping (MUST also call `dragControl.setSnapConfig()`)
- `applyTemplate(id)` — Load preset scene template
- `initTerrainBrush()` — Get or create TerrainBrush instance
- `getGroundIntersection(event)` — Raycast ground for brush UV coordinates
- `toggleBoxSelect()` — Toggle rubber-band selection mode
- `getSceneName()` — Return current scene name for binding queries
- `findModelBySceneObjectId(sceneObjectId)` / `focusSceneObject(sceneObjectId)` — Locate and focus a model by stable scene object ID

**IMPORTANT**: Snap config changes must be propagated to DragControl explicitly. `setSnapConfig()` and `toggleSnap()` both call `this.dragControl.setSnapConfig(this.snapConfig)`.

#### State Management (Pinia, Composition API)

| Store | Version | Purpose |
|-------|---------|---------|
| `stores/scene.ts` | v2.1 | Scene config: lights, skybox, ground, grid, **terrain state, snap config, brush/box-select active flags**. |
| `stores/model.ts` | v2.1 | Active model + **multi-selection** (`selectedModels[]`, `hasMultiSelection`, `selectedCount`). |
| `stores/dialog.ts` | v2.1 | Dialog visibility: propPane, sceneSettingPane, saveDialog, modelTreeDialog, **layerPanel, terrainToolbar, dataVizPanel**. |
| `stores/layer.ts` | NEW Phase 2 | Layer list, selected layer ID, panel visibility. |
| `stores/dataviz.ts` | NEW Phase 3 | Data viz state: `activeChart` (line/gauge/radar/bar3d/heatmap/pie), `activeDataSourceId`, `activeMetric`, `timeRange`, `wsConnected`/`wsReconnecting`, `realtimeData` cache (keyed by sourceId), `dataSources[]` (5 pre-configured agri-IoT sources), `pushRealtimeData()`, `bindModelToDataSource()`. |

#### UI Components (`src/components/`)

| Component | Version | Purpose |
|-----------|---------|---------|
| `SceneContainer.vue` | v2.1 | WebGL canvas host + **Phase 2 event bus hub**: terrain, layer, box-select, brush, snap, template events all handled here. |
| `HeadMenu.vue` | v2.1 | Top nav with logo + scene menu (new/save/open) + settings button. |
| `ProperityPane.vue` | v2.1 | Left panel: model position/scale/rotation sliders, data binding, carbon chart, and bound agricultural object detail/status/metrics/event entries, including Phase 3 latest metric and event count summaries. |
| `SceneSetting.vue` | v2.1 | Right panel: view switch, lights, background, **snap config, batch operations, box-select button, layer/terrain tool buttons**. |
| `LayerPanel.vue` | NEW Phase 2 | Right panel (below settings): layer list with visibility/lock toggles, batch op buttons (select all in layer, move to layer, box select). Uses `dialogStore.layerPanel` for visibility. |
| `TerrainToolbar.vue` | NEW Phase 2 | **Center-screen** floating panel: terrain import (heightmap/GeoJSON/DEM), texture brush config, scene template selector. Uses `dialogStore.terrainToolbar` for visibility. |
| `DataVizPanel.vue` | NEW Phase 3 | Right panel (left of SceneSetting, 420px): data source/metric selectors, 6 chart-type icon tabs, dynamic chart switching, live footer with color-coded current value, WS status badge. Uses `dialogStore.dataVizPanel` for visibility. |
| `charts/RealtimeLineChart.vue` | NEW Phase 3 | ECharts line chart: real-time streaming curve, cyan-blue gradient area fill, auto-scrolling time axis, tooltip with formatted time+value. |
| `charts/GaugeChart.vue` | NEW Phase 3 | ECharts gauge: semi-circular 210° arc, tri-color axis (blue→cyan→red), custom pointer, large centered value display. |
| `charts/RadarChart.vue` | NEW Phase 3 | ECharts radar: multi-dimensional metric polygon, radial gradient fill, reads all metrics from active data source. |
| `charts/BarChart3D.vue` | NEW Phase 3 | ECharts GL bar3D: 3D comparison bars across all data sources, visualMap coloring, elastic-out animation. Requires `echarts-gl`. |
| `charts/HeatmapChart.vue` | NEW Phase 3 | ECharts heatmap: 7-day × 24-hour grid, realistic day-peak pattern generation, vertical visualMap. |
| `charts/PieChart.vue` | NEW Phase 3 | ECharts donut: ring chart (55%-78% radius), center total display, gradient per-slice colors, emphasis scale animation. |
| `SaveDialog.vue` | v2.0 | Scene save dialog. |
| `ModelTreeDialg.vue` | v2.0 | Model library (tree + 3D preview) + AI generation tab. |

**Panel visibility pattern (Phase 2 & 3)**: New panels (LayerPanel, TerrainToolbar) toggle via `dialogStore` flags, NOT local state. The buttons in SceneSetting call `dialogStore.showLayerPanel(!dialogStore.layerPanel)` — the component template binds `v-show="dialogStore.layerPanel"`.

#### Services (`src/services/`)

| File | Version | Purpose |
|------|---------|---------|
| `sceneBusinessBindingService.ts` | NEW Phase 2 | HTTP service for `/scene/bindings/*`: scene-object lookup, business-object reverse lookup, binding update, and validation summary. |
| `farmMemoryService.ts` | NEW Phase 3 | HTTP service for `/memory/*` and `/objects/:id/memory/*`: metric dictionary, sync policy, latest values, timeseries, events, daily archives, and report-source data. |
| `dataService.ts` | NEW Phase 3 | HTTP data fetching + mock historical data generator: `generateHistoricalData(sourceId, duration, interval)` returns 24h of sensor points with realistic random-walk values, `applyDayNightCycle()` adds circadian rhythm, `fetchSceneData()`, `fetchModelData()`. |
| `websocket.ts` | NEW Phase 3 | `RealtimeDataService` (singleton via `getRealtimeService()`): WebSocket client with exponential-backoff auto-reconnect, subscription API (`subscribe`/`unsubscribe`), **built-in Mock engine** — when WS is unavailable, generates data every 2s via random-walk algorithm around realistic baselines per source type. Mock auto-disables when real WS connects. |

#### Data (`src/data/`)
- `templates.ts` — 3 scene templates: 标准温室大棚, 智慧示范田, 综合农业园区. Each defines lights, ground, grid, terrain, and model placements.

#### Build Modes (`.env.*` files)
| Command | VITE_MOCK | VITE_EDITMODE | VITE_SHOWTEST |
|---------|-----------|---------------|---------------|
| `serve` | true | true | false |
| `dev` (debug) | false | true | true |
| `serve-view` | true | true | false |
| `build` | false | true | false |
| `build-view` | false | false | false |

Key env vars: `VITE_MOCK`, `VITE_EDITMODE`, `VITE_SHOWTEST`, `VITE_BASEURL` (default `http://127.0.0.1:9010/sceneApi`).

**Global Injection** (`src/composables/useGlobals.ts`):
- `$http` — Axios instance
- `$envCfg` — `{ editMode, showTest }`
- `$bus` — mitt event bus

**Router**: 2 routes — `/` → MainView, `/about` → AboutView (lazy).

### Phase 3 Data Visualization Architecture

**Data Flow**:
1. User opens DataVizPanel via HeadMenu "数据" button → `dialogStore.showDataVizPanel(true)`
2. Panel auto-selects first data source, subscribes to WebSocket/Mock stream
3. `RealtimeDataService` pushes `SensorPoint { timestamp, value }` to dataviz store every 2s
4. Chart components watch `store.lastUpdate` and re-render via ECharts `setOption()` (not full re-init)
5. `DataOverlayManager` can render floating labels + 3D bars above models in the Three.js scene

**Pre-configured Data Sources** (in `stores/dataviz.ts`):
| Source ID | Name | Type | Key Metrics |
|-----------|------|------|-------------|
| `ds-greenhouse-01` | 1号温室传感器组 | greenhouse | temperature, humidity, soilMoisture, co2, lightIntensity, ph |
| `ds-solar-01` | 光伏阵列监测 | solar | powerOutput, temperature, lightIntensity |
| `ds-wind-01` | 风力发电机组 | wind | powerOutput, windSpeed, temperature |
| `ds-field-01` | 智慧示范田传感器 | field | soilMoisture, temperature, ph, humidity, lightIntensity |
| `ds-irrigation-01` | 智能灌溉系统 | irrigation | soilMoisture, temperature, humidity |

**Chart types** (`ChartType`): `'line' | 'gauge' | 'radar' | 'bar3d' | 'heatmap' | 'pie'`

**Model-to-Data Binding**: Models have a `dataId` field (set via ProperityPane). Call `store.bindModelToDataSource(modelId, sourceId)` to link. The `DataOverlayManager.createOverlay(modelId, model, config)` then renders the bound data directly in the 3D scene.

**Mock Engine Behavior**: `RealtimeDataService` tries real WebSocket first (`ws://127.0.0.1:9010/sceneApi/ws/data`). On failure, falls back to mock mode automatically. Mock generates data via random-walk: `value = base + (prev-base)*0.85 + random(-amp, +amp)`. Different base values per source type (e.g., greenhouse temp base=26°C, solar panel temp base=35°C).

**Phase 3 Key Conventions**:
- DataVizPanel uses `dialogStore.dataVizPanel` for visibility, NOT `store.panelVisible` — follows Phase 2 panel pattern
- Chart components use ECharts `setOption()` on every update (NOT full `dispose`+`init`) — except when data source changes
- `RealtimeDataService` is a class singleton via `getRealtimeService()`, NOT a Pinia store
- Mock data only runs when `store.wsConnected === false`
- Data overlay textures are Canvas-rendered (256×96) with glass-border style, using `THREE.CanvasTexture`
- `echarts-gl` must be installed (`npm install echarts-gl`) for BarChart3D — it side-effects the ECharts namespace

### Backend Architecture (scene-server-go/)

Gin framework, MySQL via sqlx, Spring Boot-idiom package structure. Port 9010, context path `/sceneApi`.

### Phase 3 Farm Memory Layer

- Backend files: `vo/FarmMemoryVo.go`, `service/FarmMemoryService.go`, `service/FarmMemoryDictionary.go`, `service/FarmMemoryStore.go`, `mapper/FarmMemoryMapper.go`, and `controller/FarmMemoryController.go`.
- Read-only APIs: `/memory/metrics`, `/memory/sync-policies`, `/objects/:id/memory/sync-policy`, `/objects/:id/memory/latest`, `/objects/:id/memory/timeseries`, `/objects/:id/memory/events`, `/objects/:id/memory/daily-archives`, and `/objects/:id/memory/report-source`.
- Metric dictionary covers `temperature`, `humidity`, `soilMoisture`, `co2`, `lightIntensity`, `ph`, `ec`, `waterPressure`, `flow`, and `switchState`; compatibility aliases map `waterFlow -> flow` and `status -> switchState`.
- `farm_event_memory` and `farm_daily_archive` are created by `phase3_farm_memory_layer_migration.sql`. The current development database has already run this migration.
- Assistant exposes only read-only `timeseries.query` and `event.query` tool shapes. These must stay constrained to object ID, dictionary metric key, range, event type, and limit; do not add arbitrary SQL, shell, filesystem, HTTP, or device-control capabilities.

### Phase 4 Agent Operation Trace

- Backend files: `service/SceneBuilderAgent.go`, `service/AgentOperationPolicy.go`, `service/AgentOperationTrace_test.go`, and `vo/SemanticVo.go`.
- Frontend files: `src/services/semanticService.ts` and `src/components/SemanticBuilderPanel.vue`.
- `SceneBuilderAgent` remains the compatible semantic-build entry. It now exposes a `FarmTwinOrchestrator` root trace plus specialized Agent steps for semantic construction, asset routing, object binding, and validation.
- `agentTrace.tools` remains for compatibility; new UI should prefer `agentTrace.steps`, with `taskId`, `userGoal`, `agent`, `tool`, `toolCategory`, `status`, `durationMs`, summaries, `failureReason`, and `fallback`.
- Tool policy categories are read-only, controlled-write, and prohibited. Prohibited shell, filesystem write, arbitrary HTTP, direct database write, and direct device-control operations must be blocked and recorded as policy violations.
- Preview-mode controlled writes such as `object.bind`, `scene.applyPlan`, `asset.job.create`, and `alert.acknowledge` are trace/contracts only unless an implementation explicitly routes through existing services and state constraints.

### Phase 5 Asset Metadata And Fidelity Routing

- Backend files: `service/AssetRegistryService.go`, `service/AssetQualityAuditService.go`, `service/AssetFidelityRoutingService.go`, `controller/AssetController.go`, and `vo/AssetMetadataVo.go`.
- Frontend files: `src/services/semanticService.ts`, `src/components/SemanticBuilderPanel.vue`, and `src/mock/modules/semantic.ts`.
- Asset APIs under `/sceneApi/asset`: `GET /metadata`, `GET /metadata/:assetKey`, `GET /audit`, `POST /routing/decide`, and `GET /plant-geometry/:objectId`.
- Fidelity strategies include existing managed assets, F2DMAS/high-fidelity reconstruction for key plants, TRELLIS.2 generation for ordinary missing equipment, procedural geometry for rule-based objects, and placeholders with generation-task contracts when assets are unavailable.
- Semantic scene construction should preserve continuity when an asset is missing: keep the placeholder scene object, expose the routing reason and generation task status, and let Validator output missing thumbnail/source/license/quality issues.

### Data Flow
1. Frontend loads scenes via `Scene.laodScene(name)` → `GET /sceneApi/scene/loadScene?scene=name`
2. Backend returns scene config + model list
3. Frontend reconstructs environment, loads models, assigns to layers
4. Scene save dumps config + models + **layers** + **terrain brush data** + scene-business binding metadata as JSON → `POST /sceneApi/scene/saveScene`
5. 3D point-select reads `sceneObjectId` → `GET /sceneApi/scene/bindings/by-scene-object` → `ProperityPane` renders the bound agricultural object detail.
6. Object detail and 3D point-select memory panels read `businessObjectId` → `/sceneApi/objects/:id/memory/*` for latest values, trends, events, archives, and report-source context.
7. `/objects` reverse location reads `businessObjectId` → `GET /sceneApi/scene/bindings/by-business-object` → routes back to `/` with `sceneObjectId` and focuses the model.

### Key Conventions
- **Vite binary**: Always `./node_modules/.bin/vite`, never `npx vite`
- API base URL via `VITE_BASEURL` env; frontend path is `/scene/`
- Scene singleton initialized in `SceneContainer.mounted()` — must exist before any 3D ops
- Model selection: raycasting → traverse parent chain → find `userData.type === 'targetObj'`
- Scene-business binding identity uses `sceneObjectId`, not runtime `modelId`; runtime `modelId` is regenerated by the frontend and must not be used for durable business links.
- All 3D coordinates use right-hand Y-up system (Three.js standard)
- Mock mode: `VITE_MOCK=true` → no `axios.defaults.baseURL`; Production: `VITE_MOCK=false` → baseURL from env
- `laodScene` method name has a typo (kept for backward compatibility)
- SpotLight config may use `angle` or `angular` key depending on data source
- Model preview scenes use RoomEnvironment, lighting moderate (ambient 0.5, directional 1.2)
- `el-menu-item` does NOT have `#title` slot in Element Plus — only `el-sub-menu` does
- **Snap sync**: Always call `dragControl.setSnapConfig()` after changing `snapConfig`
- **Box select**: Only ONE handler (`SceneContainer` via `$bus`) calls `scene.toggleBoxSelect()`; other components emit the event only
- **Panel visibility**: LayerPanel and TerrainToolbar bind to `dialogStore.*`, not local refs
- **Batch ops**: Work on single selected model OR multi-selection (via `getTargetModelIds()`)
- **DataViz panel positioning**: `right: 372px` — sits left of SceneSetting (340px at right:16px), 24px gap. Adjust if SceneSetting width changes
- **ECharts instances**: Dispose on unmount (`chart.dispose()`), re-init only on data-source change, use `setOption()` for real-time updates
- **WS/Mock duality**: Always use `getRealtimeService()` — it transparently handles real WS vs mock, no special casing needed in components
- **DataOverlayManager lifecycle**: Init with `getDataOverlayManager(scene)` once scene exists, dispose with `disposeDataOverlayManager()`. Overlays follow model positions (stored as child of model group)
