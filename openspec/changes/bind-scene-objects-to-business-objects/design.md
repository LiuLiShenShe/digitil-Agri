## Context

PRD 将“每个可观测对象都必须可查询”列为核心原则。现有场景对象需要从 mesh/model 升级为业务对象的可视表达。绑定层是对象底座、时序记忆、Agent 运维和资产治理之间的连接点。

## Goals / Non-Goals

**Goals:**

- 支持场景对象与业务对象双向绑定。
- 支持 3D 点选到业务详情。
- 支持业务对象定位到场景对象。
- 支持 ValidatorAgent 或校验流程发现缺绑定、缺数据绑定和缺资产元数据。

**Non-Goals:**

- 不在本变更中定义农业对象模型本身。
- 不在本变更中实现完整时序存储。
- 不在本变更中实现 Agent 编排，只保留可被 Agent 使用的校验结果。

## Decisions

- 场景对象最多绑定一个主业务对象，避免点选详情产生歧义。
- 业务对象可绑定多个场景对象，用于多 LOD、内部/外部模型、局部组件和多视角表达。
- 绑定关系保存在场景对象或独立绑定表中，但对外暴露稳定的 `sceneObjectId -> businessObjectId` 和 `businessObjectId -> sceneObjectIds` 查询。
- 点选详情面板以业务对象为中心聚合状态、指标、事件、告警和资产信息。
- 未绑定对象不阻断场景加载，但必须进入校验结果。

## Implementation Notes

- Phase 2 implementation stores binding fields directly on `scenemodel`: `sceneObjectId`, `businessObjectId`, `assetKey`, and `isDefaultBinding`.
- The backend exposes scene binding lookup, update, delete, and validation endpoints under `/sceneApi/scene/bindings`.
- Legacy rows without `sceneObjectId` are given a deterministic fallback ID from `sceneName + modelId` during load/query, and the next scene save persists a stable ID.
- The seeded `番茄温室 MVP` scene binds Greenhouse, Parcel, Plant, Sensor, Device, and Camera objects for end-to-end validation.

## Risks / Trade-offs

- 过早要求所有对象绑定会影响场景搭建效率，因此允许 0 绑定，但核心可观测对象必须纳入验收。
- 同一个业务对象多场景表达会带来定位歧义，需要在定位结果中标注主视图或默认场景对象。
- 场景对象历史数据可能缺少业务对象 ID，需要迁移或兼容显示为未绑定。
