# 多 Agent 平台与编排参考

## 核心结论

农业数字孪生智能体平台不应把所有能力塞进一个聊天助手。更稳妥的路线是：总控 Agent 接收用户目标，拆解为受控工具链；专用 Agent 分别负责场景规划、资产保真度选择、布局、数据绑定、长势分析、告警诊断、日报和校验；所有写操作都通过白名单工具、显式参数、可追溯 trace 和失败回退执行。

## 关键资料

### Digital Twin deployment for smart agriculture in Cloud-Fog-Edge infrastructure

- 来源：Taylor & Francis, 2023
- 链接：https://www.tandfonline.com/doi/full/10.1080/17445760.2023.2235653
- 相关点：提出 Cloud/Fog/Edge 与 Multi-Agent Systems 结合的智慧农业数字孪生架构。
- 对本项目的启发：本项目可以把多 Agent 定位为数字孪生编排层，而不是普通问答层。Agent 不仅回答问题，还能调度场景、资产、数据和告警。

### The Role of Multi-Agents in Digital Twin Implementation

- 来源：ACM Computing Surveys
- 链接：https://dl.acm.org/doi/10.1145/3697350
- 相关点：多 Agent 与数字孪生结合是一个独立研究方向，关注多个智能主体如何支撑复杂孪生系统。
- 对本项目的启发：可以把“多 Agent 工具链可追溯”作为创新点，而不是只展示 LLM 聊天能力。

### OpenAI Cookbook: Orchestrating Agents, Routines and Handoffs

- 来源：OpenAI Developers Cookbook
- 链接：https://developers.openai.com/cookbook/examples/orchestrating_agents
- 相关点：介绍 routines 和 handoffs 思路，用于在多流程、多角色场景下组织 Agent。
- 对本项目的启发：场景搭建和运维可以采用 handoff：
  - 用户目标进入 `FarmTwinOrchestrator`。
  - 需要搭建时交给 `ScenePlannerAgent`。
  - 需要资产判断时交给 `AssetFidelityAgent`。
  - 需要运维分析时交给 `GrowthAnalysisAgent` 或 `AlertDiagnosisAgent`。

### OpenAI Swarm

- 来源：OpenAI Swarm GitHub
- 链接：https://github.com/openai/swarm
- 相关点：Swarm 是探索轻量多 Agent 编排的教育框架，强调 Agent 和 handoff 两个基本抽象。
- 对本项目的启发：即使项目使用 Eino DeepAgents，也可以借鉴轻量、显式、可追踪的设计理念，避免黑箱式自动化。

### Digital Twin Consortium Members Develop and Deploy Multi-Agent Gen AI Systems

- 来源：Digital Twin Consortium press release
- 链接：https://www.digitaltwinconsortium.org/press-room/07-23-24/
- 相关点：数字孪生联盟成员关注多 Agent GenAI 系统的开发和部署。
- 对本项目的启发：将 Agent 与数字孪生结合有产业方向支撑，但平台需要可审计、可治理，不能只做演示聊天。

## 建议的 Agent 划分

```text
FarmTwinOrchestrator 总控 Agent
  -> ScenePlannerAgent 场景规划
  -> AssetFidelityAgent 资产保真度决策
  -> F2DMASAgent 高保真植株重建任务
  -> TrellisAssetAgent 快速普通资产生成任务
  -> LayoutAgent 布局求解
  -> DataBindingAgent 业务对象与数据绑定
  -> TimeSeriesAgent 时序查询与聚合
  -> GrowthAnalysisAgent 长势分析
  -> AlertDiagnosisAgent 告警诊断
  -> ReportAgent 日报/周报
  -> ValidatorAgent 完整性和安全校验
```

## 工具白名单建议

只读工具：

- `scene.current`：读取当前场景。
- `model.search`：检索资产。
- `model.metadata`：读取资产元数据。
- `object.lookup`：查询业务对象。
- `timeseries.query`：查询时序数据。
- `event.query`：查询灌溉、施肥、告警、巡检事件。

受控写工具：

- `scene.plan`：生成场景计划，不直接落库。
- `layout.solve`：生成坐标。
- `scene.applyPlan`：经用户确认后应用计划。
- `asset.job.create`：创建资产生成任务。
- `object.bind`：绑定业务对象与 3D 对象。
- `alert.acknowledge`：确认告警，必须记录操作者。

禁止工具：

- 任意 shell。
- 任意文件系统写入。
- 任意 HTTP。
- 直接数据库写入。
- 未经状态机的设备控制。

## Agent Trace 结构建议

```json
{
  "taskId": "task_20260520_001",
  "userGoal": "搭建番茄温室并分析今日长势",
  "mode": "preview",
  "steps": [
    {
      "agent": "ScenePlannerAgent",
      "tool": "scene.plan",
      "status": "success",
      "summary": "识别温室 1 个、番茄 20 株、气象站 1 个、水泵 1 个"
    },
    {
      "agent": "AssetFidelityAgent",
      "tool": "asset.route",
      "status": "success",
      "summary": "关键番茄使用 F2DMAS，高频背景植株使用低模实例，设备使用已有模型或 TRELLIS.2"
    },
    {
      "agent": "DataBindingAgent",
      "tool": "object.bind",
      "status": "success",
      "summary": "温室绑定 3 个传感器，番茄行绑定微气候和表型数据"
    }
  ]
}
```

## 和当前项目的连接

当前项目已具备良好起点：

- `SceneBuilderAgent` 已接入 Eino DeepAgents。
- 受控白名单工具已有雏形：`model.search`、`model.metadata`、`scene.current`、`scene.plan`、`layout.solve`、`layout.validate`。
- 前端已展示 `agentTrace`。
- LLM 未配置时有确定性流水线回退。

下一步应把 Agent 从“场景生成”扩展到“场景运维”：

- 查哪些对象没有绑定业务数据。
- 查哪些设备超过 24 小时未更新。
- 查哪些 GLB 资产缺少来源、缩略图、面数或版权。
- 自动生成温室日报。
- 对告警给出基于时序数据和事件的解释。

