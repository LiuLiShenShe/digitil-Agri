# 面向当前项目的设计备忘

## 平台定位建议

建议将平台定位为：

> 面向智慧农业数字孪生的多 Agent 场景构建与数据驱动资产更新平台。

核心不是“能生成 3D 模型”，而是：

- 自然语言驱动农业场景搭建。
- 多保真资产调度和缺失资产补齐。
- 3D 对象与农业业务对象、传感器和时序数据绑定。
- 实时/日级状态同步。
- Agent 可追溯地规划、搭建、绑定、分析、预警和生成报告。

## 推荐架构

```text
用户目标
  -> FarmTwinOrchestrator
      -> 场景规划 ScenePlannerAgent
      -> 资产调度 AssetFidelityAgent
      -> 布局求解 LayoutAgent
      -> 数据绑定 DataBindingAgent
      -> 状态同步 TimeSeriesAgent
      -> 长势分析 GrowthAnalysisAgent
      -> 告警诊断 AlertDiagnosisAgent
      -> 报告生成 ReportAgent
      -> 校验 ValidatorAgent

孪生底座
  -> 农业对象图谱
  -> 3D 场景对象
  -> GLB 多保真资产池
  -> IoT/时序数据
  -> 农业事件
  -> Agent Trace
```

## 和已有系统的对齐

已有能力：

- Vue/Three.js 场景编辑器。
- Go 后端场景保存、模型列表、静态资产。
- IoT 设备、模拟数据、告警、WebSocket。
- 监控大屏、业务中心、AI 助手。
- Eino SceneBuilderAgent。
- 模型语义检索、自然语言解析、布局求解、缺失资产占位。
- TRELLIS.2 资产生成任务接口。

建议下一阶段不要先大改前端，而是补底座：

1. 农业业务对象模型。
2. 3D 对象与业务对象绑定。
3. 资产元数据治理。
4. 时序归档和事件层。
5. Agent 运维工具链。

## 优先级建议

### P0：让“数字孪生”成立

- 新增业务对象：园区、温室、地块、作物行、植株、传感器、摄像头、执行设备。
- 每个 3D 对象支持绑定业务对象。
- 每个业务对象支持绑定指标、设备、事件和状态。
- 增加对象详情接口，支持从 3D 点选跳到业务数据。
- 明确状态同步频率：实时、日级、阶段性、静态。

### P1：让“智能体平台”成立

- 扩展 Agent 工具：`object.lookup`、`timeseries.query`、`event.query`、`asset.metadata.audit`、`data.quality.check`。
- Agent trace 增加输入、输出摘要、耗时、失败原因和回退路径。
- 增加 `ValidatorAgent`：检查场景对象是否缺模型、缺业务绑定、缺数据绑定、缺缩略图。
- 增加 `ReportAgent`：基于监控数据生成温室日报。

### P2：让“多保真资产”成立

- 统一前端 public models 和后端 scene-assets 的资产源。
- 给资产补元数据：来源、许可、面数、贴图、体积、缩略图、保真度、适用对象。
- 新增 `AssetFidelityAgent`，根据对象类型、精度、等待时间和用途选择：已有资产、F2DMAS、TRELLIS.2、程序化生成或占位。
- 关键植株支持几何版本：苗期、营养生长期、开花期、结果期、成熟期。

## 三个可写成论文创新点的方向

### 1. 多保真农业 GLB 资产调度机制

解决 F2DMAS 慢但真实、TRELLIS.2 快但粗的问题。根据对象类别、业务价值、表型需求、等待时间和已有资产自动选择生成/检索策略。

可验证指标：

- 总生成耗时。
- 缺失资产补齐率。
- 关键植株几何/表型可用性。
- 用户等待时间。

### 2. 阶段性几何更新 + 高频状态同步

解决植物每天变化但每日 GLB 重建成本过高的问题。状态实时或日级更新，几何按关键生育期或关键样本更新。

可验证指标：

- 状态表达完整性。
- 场景更新成本。
- 异常识别率。
- 用户对长势变化的理解度。

### 3. 可追溯多 Agent 农业孪生工具链

解决自然语言场景搭建、资产生成、数据绑定和运维分析不可解释的问题。所有 Agent 调用白名单工具，输出 trace，支持失败回退。

可验证指标：

- 语义搭建成功率。
- 数据绑定准确率。
- Trace 完整率。
- 告警解释准确率。

## 近期 OpenSpec 选题建议

1. `add-agricultural-object-model`
   - 建立 Farm/Greenhouse/Parcel/CropRow/Plant/Sensor/Device/Camera 对象模型。
   - 增加对象查询和关系查询接口。

2. `bind-scene-objects-to-business-objects`
   - 给 3D 场景对象增加业务对象绑定。
   - 支持点选模型查看业务详情。

3. `add-asset-metadata-and-fidelity-routing`
   - 给资产增加保真度、来源、质量、缩略图和适用场景。
   - 增加资产质量审计接口。

4. `add-agent-operation-trace`
   - 扩展现有 `agentTrace`。
   - 记录工具输入输出摘要、耗时、回退和校验结果。

5. `add-farm-memory-layer`
   - 建立日级归档、事件表和 Agent 分析记录。
   - 支持按对象查询最近 N 天趋势和事件。

## 写设计文档时可直接使用的表述

> 本项目采用“多保真资产 + 多频率同步”的农业数字孪生构建方式。对于关键植株对象，系统保留阶段性高保真 GLB 几何版本，并绑定表型数据；对于普通场景对象，系统优先复用已有资产或通过 TRELLIS.2 快速补齐；对于实时农业状态，系统通过 IoT、日级归档和 Agent 分析结果持续更新，使 3D 场景从静态可视化模型转化为可查询、可诊断、可运维的农业数字孪生实体集合。

