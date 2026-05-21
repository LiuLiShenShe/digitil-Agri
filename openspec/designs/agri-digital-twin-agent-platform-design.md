# 智慧农业数字孪生智能体平台总体设计

## Context

本设计文档基于 `docs/agri-digital-twin-agent-platform-prd.md`、`openspec/project.md`、`openspec/roadmap.md`、`openspec/reference/references/` 和 `openspec/changes/` 下 5 个 active changes 编写。

当前平台已具备 Vue/Three.js 场景编辑器、Go 后端、农业 GLB 资产库、IoT 模拟链路、告警、监控大屏、业务中心、AI 助手、Eino SceneBuilderAgent、模型语义检索、自动布局和 TRELLIS.2 资产任务入口。下一阶段设计目标不是继续堆叠页面和模型数量，而是建立对象驱动、数据绑定、状态同步、资产治理和 Agent 可追溯运维闭环。

## Goals / Non-Goals

**Goals:**

- 让“农业数字孪生”成立：每个核心农业实体可被查询、绑定、同步、诊断和追溯。
- 让“智能体平台”成立：Agent 通过受控工具链完成规划、搭建、绑定、校验、告警解释和报告生成。
- 让“多保真资产池”成立：资产具备元数据、质量状态、保真度路由和缺失资产不中断机制。
- 固化番茄温室 MVP 闭环：自然语言目标到场景、对象、数据、事件、trace、校验和日报。

**Non-Goals:**

- 不一次性完成生产级 6 个业务子系统。
- 不承诺任意场景完全自动搭建，先聚焦番茄温室、示范田和综合农业园区。
- 不做每日植株 GLB 重建。
- 不让 Agent 直接控制真实设备。
- 不将 TRELLIS.2 用作关键植株表型测量的可信几何来源。
- 不把模型资产语义检索包装成已完成的文档 RAG 知识库。

## Design Principles

1. **对象优先**：农业业务对象是场景、指标、事件、资产、告警和 Agent 分析的统一锚点。
2. **状态优先于几何**：温湿度、设备、告警和事件高频同步；植株几何按关键生育期或采样点阶段性更新。
3. **绑定可校验**：3D 场景对象允许未绑定，但核心可观测对象必须能被 ValidatorAgent 或校验流程识别。
4. **Agent 受控执行**：Agent 只通过白名单工具访问系统能力，写操作区分 preview/apply，并记录 trace。
5. **资产按业务价值调度**：关键植株、普通设备、背景作物行、规则几何和缺失资产使用不同保真度策略。

## Architecture

```text
用户目标 / 业务操作 / 监控告警
  -> 入口体验层
      -> 3D 场景编辑器
      -> 业务对象列表与详情
      -> 数据趋势、告警、日报、校验面板
  -> Agent 编排层
      -> FarmTwinOrchestrator
      -> ScenePlannerAgent / AssetFidelityAgent / LayoutAgent
      -> DataBindingAgent / TimeSeriesAgent / GrowthAnalysisAgent
      -> AlertDiagnosisAgent / ReportAgent / ValidatorAgent
  -> 孪生底座层
      -> 农业对象模型
      -> 3D 场景对象绑定
      -> 指标、时序、事件、日级归档
      -> Agent Trace
  -> 资产治理层
      -> GLB 资产元数据
      -> 质量验收
      -> F2DMAS / TRELLIS.2 / 程序化生成 / 占位模型
  -> 基础设施层
      -> Vue 3 + Three.js 前端
      -> Go + Gin + MySQL 后端
      -> IoT/模拟数据/告警/WebSocket
```

## Capability Map

| 能力 | OpenSpec Change | 核心职责 |
| --- | --- | --- |
| 农业对象模型 | `add-agricultural-object-model` | 定义 Farm、Greenhouse、Parcel、CropRow、Plant、CropBatch、Sensor、Device、Camera、Operation、Observation 和对象关系 |
| 3D 业务绑定 | `bind-scene-objects-to-business-objects` | 建立 sceneObject 与 businessObject 双向绑定、点选详情、业务定位和绑定校验 |
| 农场记忆层 | `add-farm-memory-layer` | 建立指标字典、同步频率、时序查询、事件记忆、日级归档和日报数据源 |
| Agent Trace | `add-agent-operation-trace` | 建立多 Agent 分工、工具白名单、受控写入、trace 结构和确定性回退 |
| 资产保真度路由 | `add-asset-metadata-and-fidelity-routing` | 建立资产元数据、质量验收、保真度路由、缺失资产任务和植株几何版本 |

## Core Data Flow

### Semantic Scene Construction

```text
用户自然语言目标
  -> FarmTwinOrchestrator
  -> ScenePlannerAgent 生成对象清单和 ScenePlan
  -> AssetFidelityAgent 选择已有资产 / F2DMAS / TRELLIS.2 / 程序化 / 占位
  -> LayoutAgent 求解坐标、朝向、行列和网格
  -> scene.plan 生成预览
  -> scene.applyPlan 在确认后应用
  -> DataBindingAgent 绑定业务对象、设备、指标和场景对象
  -> ValidatorAgent 输出缺模型、缺绑定、缺数据、缺元数据问题
  -> Agent Trace 记录每一步
```

### 3D Object Drill-Down

```text
用户点选 3D 对象
  -> sceneObjectId
  -> scene-business-binding 查 primary businessObjectId
  -> object.lookup / object.relations
  -> timeseries.query / event.query
  -> 对象详情面板展示状态、指标、趋势、告警、事件和资产信息
```

### Report And Diagnosis

```text
温室 / 设备 / 告警对象
  -> object.lookup 获取对象上下文
  -> timeseries.query 获取 24h / 7d 趋势
  -> event.query 获取灌溉、施肥、巡检、维护、告警、Agent 分析记录
  -> AlertDiagnosisAgent 或 ReportAgent 生成解释和日报
  -> trace 记录工具、摘要、失败原因和回退路径
```

## Data Model Boundaries

### Agricultural Object

农业对象是平台最小业务锚点。每个对象必须包含：

- 全局唯一 ID。
- 对象类型。
- 名称。
- 父级关系。
- 空间位置或所在区域。
- 当前状态。
- 更新时间。
- 数据质量状态。
- 扩展属性。

对象类型至少覆盖 Farm、Greenhouse、Parcel、CropRow、Plant、CropBatch、Sensor、Device、Camera、Operation、Observation。

### Scene Binding

- 一个 3D 场景对象绑定 0 到 1 个主业务对象。
- 一个业务对象绑定 0 到多个 3D 场景对象。
- 未绑定对象可加载，但必须进入校验结果。
- 核心演示场景中可观测对象绑定率目标不低于 90%。

### Memory Layer

- 同步频率：realtime、hourly、daily、milestone、static。
- 指标字典：温度、湿度、土壤水分、CO2、光照、pH、EC、水压、流量、设备开关状态。
- 事件类型：灌溉、施肥、告警、巡检、维护、Agent 分析记录。
- 查询窗口：至少支持 24 小时和 7 天。

### Asset Metadata

每个受管 GLB 资产必须包含：

- `assetKey`
- 分类
- 来源
- 许可
- 保真度
- 缩略图
- GLB 地址
- 适用对象
- 质量信息
- 版本信息

## Agent Tool Boundary

只读工具：

- `scene.current`
- `model.search`
- `model.metadata`
- `object.lookup`
- `object.relations`
- `timeseries.query`
- `event.query`

受控写工具：

- `scene.plan`
- `layout.solve`
- `scene.applyPlan`
- `asset.job.create`
- `object.bind`
- `alert.acknowledge`

禁止能力：

- 任意 shell。
- 任意文件系统写入。
- 任意 HTTP。
- 直接数据库写入。
- 未经状态机的设备控制。

## MVP Definition

首个 MVP 固定为番茄温室。最小验收闭环：

1. 输入“搭建番茄温室，包含 20 株番茄、气象站、水泵、摄像头和传感器”。
2. 系统生成可加载场景、资产选择理由、布局结果和 trace。
3. 点选温室模型能看到温室对象、传感器、设备、指标、告警和事件。
4. 点选异常设备能看到最近指标、告警原因和建议动作。
5. 场景校验能列出缺绑定、缺数据、缺缩略图和缺元数据的问题。
6. 系统能生成一份温室日报，包含环境摘要、设备状态、告警、灌溉事件和建议。

## Risks / Trade-offs

| 风险 | 表现 | 设计缓解 |
| --- | --- | --- |
| 演示能力被误认为生产能力 | 页面丰富但真实设备、权限、控制闭环不足 | 数据质量状态标注模拟、真实、过期和缺失 |
| 资产数量掩盖质量问题 | GLB 多但缺缩略图、版权、面数和适用标签 | 资产元数据完整率和入库验收 |
| Agent 自动化不可控 | LLM 输出不可解释或误操作 | 工具白名单、preview/apply、trace、确定性回退 |
| 每日 GLB 重建成本高 | 植株几何变化频繁但重建慢 | 阶段性几何更新 + 高频状态同步 |
| 业务子系统过早拆分 | 对象、指标、告警重复建设 | 先统一对象、指标、时序和事件底座 |

## Verification Strategy

- OpenSpec 文档：`openspec validate --all --strict`
- 后端：`go test ./...` 或 `go build -o scene-server`
- 前端：`npm run build`
- MVP 演示：按番茄温室验收闭环逐项验证。

## Traceability

- 本文总体架构来自 `openspec/project.md` 的能力拆解。
- 阶段顺序来自 `openspec/roadmap.md`。
- 具体需求以 `openspec/changes/*/specs/**/spec.md` 为准。
- 具体开发任务以 `openspec/changes/*/tasks.md` 和 `openspec/development-phases/agri-digital-twin-agent-platform-phased-plan.md` 为准。

