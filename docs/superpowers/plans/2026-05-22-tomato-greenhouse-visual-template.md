# Tomato Greenhouse Visual Template Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use executing-plans in this session. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tomato greenhouse visual template that produces a bright, continuous greenhouse scene with traceable local image-to-GLB asset generation tasks.

**Architecture:** Backend semantic planning adds visual-template metadata, real-scale calibration, greenhouse-contained tomato placement, and a staged local asset-generation pipeline. Frontend detects the template and renders procedural greenhouse shell, beds, drip lines, main pipe, valve, and daylight environment while keeping existing GLB loading paths.

**Tech Stack:** Go 1.24 + Gin services, Vue 3 + TypeScript + Three.js, Playwright browser verification.

---

### Task 1: Backend semantic contract

**Files:**
- Modify: `digital-twingo/scene-server-go/vo/SemanticVo.go`
- Modify: `digital-twingo/scene-server-go/service/SemanticService_test.go`
- Modify: `digital-twingo/scene-server-go/service/SemanticService.go`
- Modify: `digital-twingo/scene-server-go/service/SceneBuilderAgent.go`

- [ ] Write failing Go tests for `visualTemplate`, greenhouse-contained tomato offsets, real-scale metadata, and local image/GLB pipeline steps.
- [ ] Run `go test ./service -run 'TestSemanticTomato'` and confirm the new tests fail on missing fields/behavior.
- [ ] Add VO fields and semantic service logic to pass those tests without changing existing Phase 6 counts.
- [ ] Run the targeted tests again and confirm they pass.

### Task 2: Frontend procedural template renderer

**Files:**
- Modify: `digital-twingo/scene-design-v2/src/services/semanticService.ts`
- Modify: `digital-twingo/scene-design-v2/src/lib/model.ts`
- Modify: `digital-twingo/scene-design-v2/src/lib/scene.ts`
- Modify: `digital-twingo/scene-design-v2/src/components/SemanticBuilderPanel.vue`
- Modify: `digital-twingo/scene-design-v2/src/env.d.ts`

- [ ] Extend TypeScript semantic types for `visualTemplate` and scale calibration.
- [ ] Add raw semantic scale support so known agricultural assets do not get over-normalized by `fitScale`.
- [ ] Add scene-level procedural helpers for template layers and daylight background.
- [ ] Apply the template before/around GLB loading and expose a browser test snapshot on `window`.

### Task 3: Browser screenshot acceptance

**Files:**
- Create: `digital-twingo/scene-design-v2/scripts/tomato_greenhouse_visual_acceptance.py`

- [ ] Write Playwright script to open `/scene/`, generate the fixed prompt, capture screenshot, and assert brightness, object counts, greenhouse envelope, and tomato positions.
- [ ] Run the script against local ports 5174/9010 and save screenshot evidence under `/tmp`.

### Task 4: Verification

**Commands:**
- `cd digital-twingo/scene-server-go && go test ./...`
- `cd digital-twingo/scene-design-v2 && npm run build`
- `openspec validate --all --strict`

- [ ] Run all commands fresh.
- [ ] Report exact verification results and any residual risks.
