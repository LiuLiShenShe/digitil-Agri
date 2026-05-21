## Why

当前平台已有 3D 场景、模型资产、IoT 模拟、告警和 Agent 搭建能力，但缺少统一农业业务对象锚点。没有 Farm、Greenhouse、Parcel、Plant、Sensor、Device 等对象模型，场景、指标、事件、资产和 Agent 分析无法形成真正可查询的数字孪生底座。

## What Changes

- 新增农业业务对象模型，覆盖园区、温室、地块、作物行、植株、作物批次、传感器、设备、摄像头、农业事件和观测。
- 为每个业务对象定义全局 ID、类型、名称、父级关系、空间位置或所在区域、当前状态、更新时间、数据质量状态和扩展属性。
- 新增对象关系查询能力，支持从温室查地块、作物行、设备、传感器、摄像头、作物批次和关键植株。
- 为后续 3D 绑定、时序记忆、告警诊断、日报和资产保真度路由提供统一对象锚点。

## Capabilities

### New Capabilities

- `agricultural-object-model`: 定义农业数字孪生业务对象、对象层级、对象状态、数据质量和对象关系查询。

### Modified Capabilities

暂无。

## Impact

- 影响后端对象模型、数据库表、对象查询 API、关系查询 API 和基础演示数据。
- 影响前端对象列表、对象详情、3D 绑定入口和后续 Agent 工具入参。
- 作为 `scene-business-binding`、`farm-memory-layer`、`agent-operation-trace` 和 `asset-fidelity-routing` 的前置基础。

