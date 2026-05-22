# 智慧农业数字孪生智能体平台分阶段开发文档

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按 OpenSpec active changes 分阶段实现对象驱动的农业数字孪生底座、Agent 运维闭环和多保真资产治理。

**Architecture:** 先建立农业对象和 3D 绑定锚点，再把 IoT、事件、告警和日报纳入对象记忆层；随后扩展 Agent 工具白名单与 trace，最后治理 GLB 资产和保真度路由。每个阶段都必须能独立验证，并为番茄温室 MVP 闭环服务。

**Tech Stack:** Vue 3、TypeScript、Vite、Three.js、Pinia、Element Plus、ECharts、Go 1.24、Gin、sqlx、MySQL、Eino、OpenSpec、TRELLIS.2。

---

## Phase Overview

| 阶段 | 名称 | 主要 OpenSpec Change | 退出标准 |
| --- | --- | --- | --- |
| Phase 0 | 基线收敛与开发护栏 | 全部 changes | OpenSpec、前后端基线可验证，番茄温室 MVP 数据边界确定 |
| Phase 1 | 农业对象底座 | `add-agricultural-object-model` | 核心农业对象和关系可查询 |
| Phase 2 | 3D 场景业务绑定 | `bind-scene-objects-to-business-objects` | 3D 点选到业务详情、业务对象定位到 3D 可用 |
| Phase 3 | 状态与记忆层 | `add-farm-memory-layer` | 对象维度 24h/7d 趋势、事件和日报数据源可用 |
| Phase 4 | Agent 运维闭环 | `add-agent-operation-trace` | 语义搭建、资产路由、对象绑定、校验均有 trace |
| Phase 5 | 资产治理与保真度路由 | `add-asset-metadata-and-fidelity-routing` | 资产元数据、质量审计、缺失资产任务和保真度选择可用 |
| Phase 6 | 综合验收与演示固化 | `harden-tomato-greenhouse-acceptance-demo` + 全部 Phase 1-5 changes | 番茄温室 MVP 端到端验收通过 |

## Shared File Map

本计划是分阶段开发计划，不直接替代各 change 的 `tasks.md`。实施时优先按阶段读取相关 OpenSpec 文档。

**OpenSpec 文档区域**

- `openspec/project.md`：项目级上下文。
- `openspec/roadmap.md`：里程碑和验收指标。
- `openspec/designs/agri-digital-twin-agent-platform-design.md`：总体设计。
- `openspec/changes/*/proposal.md`：变更动机与影响面。
- `openspec/changes/*/design.md`：单变更设计。
- `openspec/changes/*/tasks.md`：单变更任务。
- `openspec/changes/*/specs/**/spec.md`：规范性需求。

**后端候选修改区域**

- `digital-twingo/scene-server-go/controller/`
- `digital-twingo/scene-server-go/service/`
- `digital-twingo/scene-server-go/mapper/`
- `digital-twingo/scene-server-go/vo/`
- `digital-twingo/scene-server-go/scene.sql`
- `digital-twingo/scene-server-go/phase4_migration.sql`
- `digital-twingo/scene-server-go/scene-assets/`

**前端候选修改区域**

- `digital-twingo/scene-design-v2/src/components/`
- `digital-twingo/scene-design-v2/src/services/`
- `digital-twingo/scene-design-v2/src/stores/`
- `digital-twingo/scene-design-v2/src/lib/`
- `digital-twingo/scene-design-v2/src/data/`

**资产生成与治理区域**

- `TRELLIS.2/`
- `convert_obj_to_glb.py`
- `batch_generate.py`
- `digital-twingo/scene-server-go/scene-assets/`
- `asserts/`

## Phase 0: 基线收敛与开发护栏

**Objective:** 确认当前 OpenSpec、前端、后端、数据和资产基线，避免后续阶段把未实现能力误认为已完成。

**Depends On:** 无。

**OpenSpec References:**

- `openspec/README.md`
- `openspec/project.md`
- `openspec/roadmap.md`
- `openspec/development-phases/phase0-baseline-report.md`

**Tasks:**

- [x] 阅读 `openspec/project.md`、`openspec/roadmap.md` 和 5 个 active changes，确认开发顺序。
- [x] 运行 `openspec validate --all --strict`，确保规格仍然通过。
- [x] 在后端目录运行 `go test ./...`，记录当前失败项或通过状态。
- [x] 在前端目录运行 `npm run build`，记录当前失败项或通过状态。
- [x] 固定番茄温室 MVP 的演示对象清单：1 个温室、20 株番茄、1 个气象站、1 个水泵/灌溉设备、1 个摄像头、1 个传感器组。
- [x] 标注当前数据来源状态：模拟、真实、过期、缺失。
- [x] 明确本轮不做真实设备控制、不做每日 GLB 重建、不做完整 RBAC。

**Baseline Guard:**

```bash
python3 openspec/tools/phase0_baseline_guard.py --write-report openspec/development-phases/phase0-baseline-report.md
```

该命令内部会运行前端构建，不要与另一个 `npm run build` 并行执行，以免 Vite 清理 `dist/` 时产生目录竞争。

**Baseline Result:** 2026-05-21 护栏通过，详见 `openspec/development-phases/phase0-baseline-report.md`。Phase 0 当时保持 5 个 active changes 均为 0 个实现任务完成，不将其标为已实现能力。

**Later Progress:** 2026-05-21 Phase 1 已完成 `add-agricultural-object-model`，当前状态为 10/10；Phase 2 已完成 `bind-scene-objects-to-business-objects`，当前状态为 9/9；2026-05-21 Phase 3 已完成 `add-farm-memory-layer`，当前状态为 10/10；2026-05-22 Phase 4 已完成 `add-agent-operation-trace`，当前状态为 10/10；2026-05-22 Phase 5 已完成 `add-asset-metadata-and-fidelity-routing`，当前状态为 10/10；2026-05-22 Phase 6 已完成 `harden-tomato-greenhouse-acceptance-demo`，当前状态为 17/17。以上 changes 待 review 后归档到 canonical specs。

**Verification:**

```bash
python3 -m unittest discover -s openspec/tools -p 'test_*.py'
python3 openspec/tools/phase0_baseline_guard.py --write-report openspec/development-phases/phase0-baseline-report.md
openspec validate --all --strict
cd digital-twingo/scene-server-go && go test ./...
cd digital-twingo/scene-design-v2 && npm run build
```

**Exit Criteria:**

- OpenSpec 校验通过。
- 前后端基线状态已记录。
- 番茄温室 MVP 范围已固定。
- Phase 0 护栏脚本可重复运行并生成报告。

## Phase 1: 农业对象底座

**Objective:** 建立 Farm、Greenhouse、Parcel、CropRow、Plant、CropBatch、Sensor、Device、Camera、Operation、Observation 等农业对象和关系查询能力。

**Primary Change:** `add-agricultural-object-model`

**Depends On:** Phase 0。

**OpenSpec References:**

- `openspec/changes/add-agricultural-object-model/proposal.md`
- `openspec/changes/add-agricultural-object-model/design.md`
- `openspec/changes/add-agricultural-object-model/tasks.md`
- `openspec/changes/add-agricultural-object-model/specs/agricultural-object-model/spec.md`

**Implementation Result:** 2026-05-21 已实现。后端新增农业对象注册表、关系表、番茄温室 MVP 种子数据、对象详情与关系查询 API，并固化 `object.lookup` / `object.relations` 输出结构；前端新增对象调试入口 `/objects`。

**Backend Tasks:**

- [x] 定义农业对象类型枚举，覆盖 Farm、Greenhouse、Parcel、CropRow、Plant、CropBatch、Sensor、Device、Camera、Operation、Observation。
- [x] 设计对象基础表或等价持久结构，包含全局 ID、类型、名称、父级关系、空间位置或所在区域、当前状态、更新时间、数据质量状态、扩展属性。
- [x] 设计对象关系表或等价结构，覆盖层级、设备、传感器、摄像头、作物批次、关键植株和事件关联。
- [x] 新增对象详情查询接口，支持按对象 ID 和类型过滤。
- [x] 新增对象关系查询接口，支持父级、子级、关联设备、关联指标、关联事件和关联资产。
- [x] 为 Agent 工具预留 `object.lookup` 和 `object.relations` 的稳定输入输出结构。

**Frontend Tasks:**

- [x] 增加农业对象列表或对象调试入口。
- [x] 增加对象详情基础展示，至少展示 ID、类型、名称、状态、更新时间、数据质量状态。
- [x] 为后续 3D 点选详情复用对象详情展示组件或服务方法。

**Data Tasks:**

- [x] 准备番茄温室 MVP 种子对象数据。
- [x] 确保从 Greenhouse 能查询到 Parcel、CropBatch、Sensor、Device、Camera 和关键 Plant。
- [x] 用数据质量状态区分模拟、真实、过期和缺失。

**Verification:**

```bash
openspec validate --all --strict
cd digital-twingo/scene-server-go && go test ./...
```

**Exit Criteria:**

- Greenhouse、Parcel、Plant、Sensor、Device、Camera 六类对象可查询。
- 从温室对象能查到关联地块、作物批次、传感器、设备、摄像头和关键植株。
- 对象数据质量状态可区分模拟、真实、过期和缺失。

## Phase 2: 3D 场景业务绑定

**Objective:** 建立 3D 场景对象与农业业务对象的双向绑定，支持点选详情、业务定位和绑定校验。

**Primary Change:** `bind-scene-objects-to-business-objects`

**Depends On:** Phase 1。

**OpenSpec References:**

- `openspec/changes/bind-scene-objects-to-business-objects/proposal.md`
- `openspec/changes/bind-scene-objects-to-business-objects/design.md`
- `openspec/changes/bind-scene-objects-to-business-objects/tasks.md`
- `openspec/changes/bind-scene-objects-to-business-objects/specs/scene-business-binding/spec.md`

**Backend Tasks:**

- [x] 为场景对象增加主业务对象绑定字段或独立绑定表。
- [x] 支持一个业务对象关联多个场景对象。
- [x] 定义绑定关系导入、保存、加载和删除规则。
- [x] 暴露 `sceneObjectId -> businessObjectId` 查询。
- [x] 暴露 `businessObjectId -> sceneObjectIds` 查询。
- [x] 增加场景绑定校验接口，识别缺业务绑定、缺数据绑定、缺资产元数据。

**Frontend Tasks:**

- [x] 在 3D 点选流程中读取 sceneObjectId，并查询业务对象绑定。
- [x] 在对象详情面板中展示业务对象、状态、指标摘要、历史趋势入口、告警和关联事件入口。
- [x] 在业务对象列表中增加“定位到场景对象”动作。
- [x] 对多个场景对象绑定同一业务对象的情况，提供默认聚焦或候选选择。
- [x] 对未绑定对象显示“未绑定业务对象”，不阻断场景操作。

**Validation Tasks:**

- [x] 校验 Greenhouse、Parcel、Plant、Sensor、Device、Camera 六类对象绑定链路。
- [x] 输出核心演示场景 3D 对象业务绑定率。
- [x] 将未绑定、缺数据绑定、缺资产元数据的问题纳入校验结果。

**Implementation Result:** 2026-05-21 已实现。`scenemodel` 扩展 `sceneObjectId`、`businessObjectId`、`assetKey`、`isDefaultBinding`；后端新增 `/scene/bindings/*` 查询、更新、删除、校验接口；前端点选属性面板展示业务对象详情，`/objects` 支持定位到 3D 场景对象；新增 `番茄温室 MVP` 种子场景和 Phase 2 迁移脚本。

**Verification:**

```bash
openspec validate --all --strict
cd digital-twingo/scene-server-go && go test ./...
cd digital-twingo/scene-design-v2 && npm run build
```

**Exit Criteria:**

- 从 3D 点选到业务详情的链路可用。
- 从业务对象定位到 3D 场景对象的链路可用。
- 核心演示场景可观测对象绑定率达到或接近 90%，未达到时必须有校验报告说明缺口。

## Phase 3: 状态与记忆层

**Objective:** 将 IoT、事件、告警、日级归档和 Agent 分析记录按农业对象组织，支持趋势查询、事件查询和日报数据源。

**Primary Change:** `add-farm-memory-layer`

**Depends On:** Phase 1、Phase 2。

**Implementation Status:** Completed on 2026-05-21. `add-farm-memory-layer` is 10/10 complete and remains in `openspec/changes/` for review/archive. `digital-twingo/phase3_farm_memory_layer_migration.sql` has been executed in the current development database, creating `farm_event_memory` and `farm_daily_archive`.

**OpenSpec References:**

- `openspec/changes/add-farm-memory-layer/proposal.md`
- `openspec/changes/add-farm-memory-layer/design.md`
- `openspec/changes/add-farm-memory-layer/tasks.md`
- `openspec/changes/add-farm-memory-layer/specs/farm-memory-layer/spec.md`

**Backend Tasks:**

- [x] 定义同步频率枚举：realtime、hourly、daily、milestone、static。
- [x] 建立指标字典，覆盖温度、湿度、土壤水分、CO2、光照、pH、EC、水压、流量和设备开关状态。
- [x] 为 Greenhouse、Parcel、Plant、Sensor、Device、Camera 定义默认同步频率和指标绑定策略。
- [x] 实现按对象查询最新值、历史曲线和聚合统计。
- [x] 支持 24 小时和 7 天两个时间范围。
- [x] 实现事件查询，覆盖灌溉、施肥、告警、巡检、维护和 Agent 分析记录。
- [x] 建立日级归档数据结构或归档任务。
- [x] 提供温室日报数据源，聚合环境、设备、告警、灌溉事件和建议上下文。

**Frontend Tasks:**

- [x] 在对象详情中展示最新值和数据质量状态。
- [x] 增加 24 小时和 7 天趋势入口。
- [x] 展示对象关联事件列表。
- [x] 为温室日报预留入口或调试面板。

**Agent Readiness Tasks:**

- [x] 定义 `timeseries.query` 输入输出结构。
- [x] 定义 `event.query` 输入输出结构。
- [x] 确保 Agent 查询只能按对象和时间范围读取，不暴露任意 SQL。

**Verification:**

```bash
openspec validate --all --strict
cd digital-twingo/scene-server-go && go test ./...
cd digital-twingo/scene-design-v2 && npm run build
```

**Exit Criteria:**

- 温室环境、地块墒情、灌溉设备和摄像头在线状态可按对象查询。
- 24 小时和 7 天趋势查询可用。
- 温室日报数据源能返回环境摘要、设备状态、告警和灌溉事件。

## Phase 4: Agent 运维闭环

**Objective:** 扩展现有 SceneBuilderAgent 能力，使语义搭建、资产路由、对象绑定、校验、告警诊断和日报生成具备受控工具和可展示 trace。

**Primary Change:** `add-agent-operation-trace`

**Depends On:** Phase 1、Phase 2、Phase 3。

**OpenSpec References:**

- `openspec/changes/add-agent-operation-trace/proposal.md`
- `openspec/changes/add-agent-operation-trace/design.md`
- `openspec/changes/add-agent-operation-trace/tasks.md`
- `openspec/changes/add-agent-operation-trace/specs/agent-operation-trace/spec.md`

**Implementation Result:** 2026-05-22 已实现。现有 `SceneBuilderAgent` 保留兼容入口，并映射到 `FarmTwinOrchestrator` 总控 trace；后端新增 Agent role registry、工具策略 registry、禁止工具策略违规 trace、扩展 `agentTrace.steps`、确定性回退记录和敏感摘要脱敏；前端 `SemanticBuilderPanel` 展示步骤、Agent、工具类别、状态、耗时、输出摘要、失败原因、回退路径和 preview/apply 模式。

**Backend Tasks:**

- [x] 定义 FarmTwinOrchestrator 的任务入口、handoff 和汇总职责。
- [x] 定义 ScenePlannerAgent、AssetFidelityAgent、LayoutAgent、DataBindingAgent、TimeSeriesAgent、GrowthAnalysisAgent、AlertDiagnosisAgent、ReportAgent、ValidatorAgent 的职责边界。
- [x] 将现有 SceneBuilderAgent 映射到新的 Agent 职责边界，保留兼容路径。
- [x] 定义只读工具：`scene.current`、`model.search`、`model.metadata`、`object.lookup`、`object.relations`、`timeseries.query`、`event.query`。
- [x] 定义受控写工具：`scene.plan`、`layout.solve`、`scene.applyPlan`、`asset.job.create`、`object.bind`、`alert.acknowledge`。
- [x] 阻断任意 shell、任意文件系统写入、任意 HTTP、直接数据库写入、未经状态机的设备控制。
- [x] 扩展 Agent trace 字段：taskId、userGoal、mode、steps、tool、status、duration、inputSummary、outputSummary、failureReason、fallback。
- [x] 实现 LLM 未配置或调用失败时的确定性回退路径。

**Frontend Tasks:**

- [x] 扩展 Agent trace 展示，支持步骤、工具、状态、耗时、输入摘要、输出摘要、失败原因和回退路径。
- [x] 为语义搭建、资产路由、对象绑定、校验各准备一个可展示 trace。
- [x] 将 preview/apply 模式在 UI 上明确区分。

**Safety Tasks:**

- [x] 确认 trace 不记录敏感原始 payload。
- [x] 确认所有受控写操作有明确参数和状态。
- [x] 确认告警确认不等同于真实设备控制。

**Verification:**

```bash
openspec validate --all --strict
cd digital-twingo/scene-server-go && go test ./...
cd digital-twingo/scene-design-v2 && npm run build
```

**Exit Criteria:**

- 语义搭建、资产路由、对象绑定和校验至少各有一个可展示 trace。
- LLM 未配置或调用失败时，核心场景搭建仍能走确定性回退。
- 禁止工具被调用时会被阻断并记录策略违规。

## Phase 5: 资产治理与保真度路由

**Objective:** 统一 GLB 资产元数据、质量验收、缺失资产任务和多保真资产选择策略。

**Primary Change:** `add-asset-metadata-and-fidelity-routing`

**Depends On:** Phase 1、Phase 2、Phase 4。

**OpenSpec References:**

- `openspec/changes/add-asset-metadata-and-fidelity-routing/proposal.md`
- `openspec/changes/add-asset-metadata-and-fidelity-routing/design.md`
- `openspec/changes/add-asset-metadata-and-fidelity-routing/tasks.md`
- `openspec/changes/add-asset-metadata-and-fidelity-routing/specs/asset-fidelity-routing/spec.md`

**Implementation Result:** 2026-05-22 已实现。后端新增资产元数据注册表、质量审计、保真度路由、植株阶段几何版本和 `/sceneApi/asset/metadata`、`/asset/audit`、`/asset/routing/decide`、`/asset/plant-geometry/:objectId` 接口；语义搭建结果为缺失摄像头/传感器生成 TRELLIS.2 任务契约并关联占位模型；Validator 校验输出缺缩略图、缺来源、缺许可和质量异常；前端 AI 搭建面板展示路由策略、保真度、参考图、任务状态和资产质量摘要。

**Backend Tasks:**

- [x] 定义资产元数据字段：assetKey、分类、来源、许可、保真度、缩略图、GLB 地址、适用对象、质量信息、版本信息。
- [x] 统一前端 `public/models` 和后端 `scene-assets` 的资产索引方式。
- [x] 定义 Three.js 可加载、坐标轴、单位、中心点、面数、贴图、体积、缩略图、来源和许可检查规则。
- [x] 实现或接入资产质量审计流程。
- [x] 将缺缩略图、缺来源、缺许可和质量异常暴露给校验流程。
- [x] 支持缺失资产创建生成任务并关联到场景占位对象。

**Frontend Tasks:**

- [x] 在模型/资产列表中展示资产元数据完整性。
- [x] 在语义搭建结果中展示资产选择理由。
- [x] 在场景中保留占位模型，并展示关联生成任务状态。
- [x] 在 ValidatorAgent 结果中展示缺缩略图、缺来源、缺许可和质量异常。

**Asset Pipeline Tasks:**

- [x] 为公开 GLB 批量补充基础元数据和缩略图。
- [x] 为关键植株定义阶段性几何版本：苗期、营养生长期、开花期、结果期、成熟期。
- [x] 实现资产策略：已有资产、F2DMAS、TRELLIS.2、程序化生成、占位模型。
- [x] 验证 AssetFidelityAgent 能为典型温室场景输出资产选择理由。

**Verification:**

```bash
openspec validate --all --strict
cd digital-twingo/scene-server-go && go test ./...
cd digital-twingo/scene-design-v2 && npm run build
```

**Exit Criteria:**

- 资产列表中至少 80% 的公开 GLB 有缩略图和基础元数据。
- 缺失资产能生成任务并关联到场景占位对象。
- AssetFidelityAgent 能为典型温室场景输出资产选择理由。

## Phase 6: 综合验收与演示固化

**Objective:** 将对象模型、场景绑定、记忆层、Agent trace 和资产路由串成番茄温室端到端演示闭环。

**Primary Changes:** `harden-tomato-greenhouse-acceptance-demo`，并聚合全部 Phase 1-5 active changes。

**Depends On:** Phase 1、Phase 2、Phase 3、Phase 4、Phase 5。

**Implementation Status:** 2026-05-22 已实现。新增后端 `/sceneApi/acceptance/tomato-greenhouse` 综合验收接口和前端 `/scene/acceptance` 演示控制台；固定提示词能稳定生成 20 株番茄、1 个温室、1 个气象站、1 个水泵/灌溉设备、1 个摄像头占位任务和 1 个传感器占位任务。

**Progress Evidence:** `openspec status --change harden-tomato-greenhouse-acceptance-demo --json` 返回 `isComplete: true`；`openspec instructions apply --change harden-tomato-greenhouse-acceptance-demo --json` 返回 `17/17` complete、`state: all_done`。

**OpenSpec References:**

- `openspec/changes/harden-tomato-greenhouse-acceptance-demo/proposal.md`
- `openspec/changes/harden-tomato-greenhouse-acceptance-demo/design.md`
- `openspec/changes/harden-tomato-greenhouse-acceptance-demo/tasks.md`
- `openspec/changes/harden-tomato-greenhouse-acceptance-demo/specs/tomato-greenhouse-acceptance-demo/spec.md`

**End-to-End Tasks:**

- [x] 输入“搭建番茄温室，包含 20 株番茄、气象站、水泵、摄像头和传感器”，生成可加载场景。
- [x] 确认生成结果包含资产选择理由、布局结果和 trace。
- [x] 点选温室模型，确认能看到温室对象、传感器、设备、指标、告警和事件。
- [x] 点选异常设备，确认能看到最近指标、告警原因和建议动作。
- [x] 对完整场景运行校验，确认能列出缺绑定、缺数据、缺缩略图和缺元数据的问题。
- [x] 生成温室日报，确认包含环境摘要、设备状态、告警、灌溉事件和建议。
- [x] 对照 `openspec/roadmap.md` 成功指标记录验收结果。
- [x] 将通过验收的 changes 按 OpenSpec archive 流程准备归档到 `openspec/specs/`。

**Verification:**

```bash
openspec validate --all --strict
cd digital-twingo/scene-server-go && go test ./...
cd digital-twingo/scene-design-v2 && npm run build
```

**Exit Criteria:**

- 番茄温室 MVP 端到端演示通过。
- 5 个 active changes 的任务状态已更新；`add-agricultural-object-model`、`bind-scene-objects-to-business-objects`、`add-farm-memory-layer`、`add-agent-operation-trace` 和 `add-asset-metadata-and-fidelity-routing` 已完成，等待 review/archive。
- 具备归档到 canonical specs 的条件；Phase 6 接口返回 archive readiness，不自动归档。

## Cross-Phase Acceptance Matrix

| 指标 | 目标 | 对应阶段 |
| --- | --- | --- |
| 3D 对象业务绑定率 | 核心演示场景可观测对象不低于 90% | Phase 2 |
| 数据绑定完整率 | 核心业务对象至少绑定一个实时或日级指标 | Phase 3 |
| Agent trace 完整率 | 所有 Agent 任务均有可查询 trace | Phase 4 |
| 资产元数据完整率 | 公开资产基础元数据不低于 80% | Phase 5 |
| 缺失资产不中断率 | 缺 GLB 时占位模型继续生成场景 | Phase 5 |
| 日报生成成功率 | 温室日报可基于对象、指标、事件和告警生成 | Phase 3 / Phase 6 |

## Development Rules

- 每个阶段开始前先读对应 `openspec/changes/<change-id>/specs/**/spec.md`。
- 每个阶段结束时运行 `openspec validate --all --strict`。
- 涉及代码时遵循现有前端/后端结构，不做无关重构。
- 不让 Agent 直接控制真实设备。
- 不将模拟数据伪装为真实数据。
- 不把未实现能力移动到 canonical `openspec/specs/`。
- 每个阶段完成后更新对应 change 的 `tasks.md` 复选框，或在实施记录中说明未勾选原因。
