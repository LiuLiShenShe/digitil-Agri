# 智慧农业数字孪生智能体平台 OpenSpec 项目说明

## Purpose

本 OpenSpec 项目将 `docs/agri-digital-twin-agent-platform-prd.md` 拆解为可演进的规格层、变更层和参考资料层，服务智慧农业数字孪生平台后续开发、验收、汇报和论文验证。

平台定位为：面向智慧农业数字孪生的多 Agent 场景构建与数据驱动资产更新平台。平台不是单纯的 3D 编辑器，也不是只会聊天的 AI 助手，而是围绕农业实体建立可同步、可查询、可诊断、可运维的虚拟表示。

## Source Inputs

- PRD：`docs/agri-digital-twin-agent-platform-prd.md`
- 参考资料：`openspec/reference/references/`
- 当前系统基线：Vue/Three.js 场景编辑器、Go 后端、农业 GLB 资产库、IoT 模拟链路、告警、监控大屏、业务中心、AI 助手、Eino SceneBuilderAgent、模型语义检索、自动布局和 TRELLIS.2 资产任务入口。

## OpenSpec Layers

- `openspec/project.md`：项目目标、范围、架构原则和分层说明。
- `openspec/roadmap.md`：从 PRD 收敛出的里程碑、近期变更和验收指标。
- `openspec/reference/references/`：外部资料和项目设计备忘，作为规格编写依据。
- `openspec/changes/<change-id>/`：近期候选变更，每个变更包含 `proposal.md`、`design.md`、`tasks.md` 和 `specs/**/spec.md`。

## Product Principles

1. 状态同步优先于几何重建：环境、设备、告警、事件和分析状态实时或日级同步，植株几何按生育期或关键采样点阶段性更新。
2. 不同对象使用不同频率和保真度：传感器实时，日报日级，关键植株阶段级，普通装饰资产静态。
3. 每个可观测对象都必须可查询：3D 对象必须映射到业务对象、状态、指标、关系和历史。
4. Agent 必须可追溯和受控：所有写操作通过白名单工具、显式参数、用户确认、trace、失败原因和回退路径执行。
5. 多保真资产池服务业务目的：F2DMAS 用于关键真实植株，TRELLIS.2 用于普通缺失资产，程序化生成用于规则几何，已有资产优先复用。

## Capability Decomposition

### P0: 数字孪生底座

- `agricultural-object-model`：定义 Farm、Greenhouse、Parcel、CropRow、Plant、CropBatch、Sensor、Device、Camera、Operation、Observation 等农业业务对象及关系。
- `scene-business-binding`：定义 3D 场景对象和业务对象的双向绑定、点选详情、业务对象定位和绑定校验。
- `farm-memory-layer`：定义指标字典、同步频率、时序查询、事件查询、日级归档和 Agent 分析记录。

### P1: 智能体平台

- `agent-operation-trace`：定义 FarmTwinOrchestrator、专用 Agent 分工、工具白名单、trace 结构、受控写入和确定性回退。

### P2: 多保真资产

- `asset-fidelity-routing`：定义资产元数据、入库验收、缺失资产任务、几何版本和多保真资产路由。

## MVP Scenario

首个最小闭环建议固定为“番茄温室”：

```text
自然语言目标
  -> 农业业务对象清单
  -> 3D 场景对象和 GLB 资产选择
  -> 空间布局与场景预览
  -> 业务对象、设备、指标、事件绑定
  -> 状态同步、趋势查询和告警解释
  -> Agent trace、校验报告和温室日报
```

## Non-Goals

- 不承诺完整生产级 6 个业务子系统一次性全部完成。
- 不承诺任意场景的完全自动搭建，先聚焦温室、示范田和综合农业园区。
- 不做每日植株 GLB 重建。
- 不让 Agent 直接控制真实设备。
- 不将 TRELLIS.2 用作关键植株表型测量的可信几何来源。
- 不把模型资产语义检索包装成已完成的文档 RAG 知识库。

## Traceability

PRD 到 OpenSpec 的映射关系：

- PRD 3.1 P0 -> `add-agricultural-object-model`、`bind-scene-objects-to-business-objects`、`add-farm-memory-layer`
- PRD 3.1 P1 -> `add-agent-operation-trace`
- PRD 3.1 P2 -> `add-asset-metadata-and-fidelity-routing`
- PRD 5.1 -> `agricultural-object-model`
- PRD 5.2 -> `scene-business-binding`
- PRD 5.3 -> `farm-memory-layer`
- PRD 5.4 -> `agent-operation-trace`
- PRD 5.5 -> `asset-fidelity-routing`

