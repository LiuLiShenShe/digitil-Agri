## Context

平台当前更接近“3D 场景 + 资产 + 模拟 IoT”的演示原型。PRD 判断下一阶段应先补孪生底座，使每个可观测农业实体都能作为业务对象被查询、绑定、同步和分析。

参考资料来自 `openspec/reference/references/03-agricultural-object-data-models-and-interoperability.md`、`06-design-notes-for-this-project.md` 和 PRD 第 5.1 节。

## Goals / Non-Goals

**Goals:**

- 建立最小但可扩展的农业业务对象图谱。
- 覆盖温室 MVP 必需对象：Farm、Greenhouse、Parcel、CropRow、Plant、CropBatch、Sensor、Device、Camera、Operation、Observation。
- 支持对象详情查询和关系查询。
- 为场景绑定、时序查询、告警解释、日报和 Agent 工具提供统一对象 ID。

**Non-Goals:**

- 不一次性实现完整农业行业标准数据模型。
- 不在本变更中实现 3D 对象绑定 UI。
- 不在本变更中实现时序存储、日报生成或资产路由。
- 不让对象模型直接控制真实设备。

## Decisions

- 对象类型采用显式枚举，先覆盖 PRD P0 必需类型，保留 `metadata` 或扩展属性承载项目差异。
- 每个对象必须有全局唯一 ID、对象类型、名称、父级关系、空间锚点、状态、更新时间和数据质量状态。
- 层级关系以父子关系为主，辅助关系用于设备、指标、作物批次、摄像头和事件关联。
- 对象状态分为业务状态和数据质量状态，避免把“设备离线”和“数据过期”混成同一字段。
- 对象查询能力优先面向后续工具：`object.lookup` 查询详情，`object.relations` 查询关系。

## Risks / Trade-offs

- 模型过细会拖慢 MVP，过粗会导致后续绑定混乱；本设计选择“核心对象枚举 + 扩展属性”的折中。
- 初期演示数据可能来自模拟链路，必须标明数据质量状态，避免演示能力被误解为生产能力。
- 若没有稳定对象 ID，后续 3D 绑定和时序归档会反复迁移，因此 ID 设计应先稳定。

