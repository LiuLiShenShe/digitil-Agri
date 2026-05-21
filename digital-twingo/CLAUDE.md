# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **3D Digital Twin platform** (智慧农业数字孪生平台) by Beijing Yupont Electric Power Tech Co., Ltd. It consists of two sub-projects:

- **scene-design-v2** — Vue 3 + TypeScript + Vite frontend for building and viewing 3D scenes (GLTF/GLB models, data visualization)
- **scene-server-go** — Go + Gin backend providing scene storage, model list, data APIs, and AI 3D asset generation

Current implementation phase: **Phase 1 agricultural object foundation is implemented** as of 2026-05-21.

- Previous app baseline still includes Phase 3 data visualization capabilities: real-time line chart, gauge, radar, 3D bar chart, heatmap, pie chart, WebSocket mock data stream, and 3D data overlays.
- OpenSpec implementation progress: `add-agricultural-object-model` is complete (10/10). Remaining changes are `bind-scene-objects-to-business-objects` (0/9), `add-farm-memory-layer` (0/10), `add-agent-operation-trace` (0/10), and `add-asset-metadata-and-fidelity-routing` (0/10).
- Phase 1 object foundation includes backend object lookup/relation APIs, tomato greenhouse MVP seed data, stable `object.lookup` / `object.relations` output shapes, and the frontend `/objects` debug entry. Archive `add-agricultural-object-model` after review.
- Phase 0 artifacts live under `openspec/development-phases/phase0-baseline-report.md` and `openspec/tools/phase0_baseline_guard.py`.
- Do not treat scene-business binding, object-scoped memory layer, expanded Agent trace, or asset metadata/fidelity routing as completed until the matching OpenSpec change tasks are implemented and verified.

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
| `model.ts` | v2.0 | `Model` class: GLTF/GLB loading, auto-fit scale/bounds via Box3, selection highlighting, animation support. |
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
| `ProperityPane.vue` | v2.1 | Left panel: model position/scale/rotation sliders, data binding, carbon chart. |
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

### Data Flow
1. Frontend loads scenes via `Scene.laodScene(name)` → `GET /sceneApi/scene/loadScene?scene=name`
2. Backend returns scene config + model list
3. Frontend reconstructs environment, loads models, assigns to layers
4. Scene save dumps config + models + **layers** + **terrain brush data** as JSON → `POST /sceneApi/scene/saveScene`

### Key Conventions
- **Vite binary**: Always `./node_modules/.bin/vite`, never `npx vite`
- API base URL via `VITE_BASEURL` env; frontend path is `/scene/`
- Scene singleton initialized in `SceneContainer.mounted()` — must exist before any 3D ops
- Model selection: raycasting → traverse parent chain → find `userData.type === 'targetObj'`
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
