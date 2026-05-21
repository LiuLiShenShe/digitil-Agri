## Why

平台已有 SceneBuilderAgent、语义搭建、布局和 trace 雏形，但 PRD 要求智能体平台必须可追溯、受控和可回退。Agent 不能只输出聊天文本，必须通过白名单工具完成场景规划、资产路由、数据绑定、校验、告警解释和日报生成，并记录每一步的输入输出摘要、耗时、失败原因和回退路径。

## What Changes

- 定义 FarmTwinOrchestrator 总控 Agent 与专用 Agent 分工。
- 建立工具白名单，区分只读工具、受控写工具和禁止工具。
- 扩展 Agent trace 结构，记录 taskId、userGoal、mode、步骤、工具、状态、耗时、输入输出摘要、失败原因和回退路径。
- 支持语义搭建、资产路由、对象绑定和校验至少各有一个可展示 trace。
- 要求 LLM 未配置或调用失败时，核心场景搭建可走确定性回退。

## Capabilities

### New Capabilities

- `agent-operation-trace`: 定义多 Agent 编排角色、工具白名单、trace 结构、受控写入和确定性回退能力。

### Modified Capabilities

暂无。

## Impact

- 影响 AI 助手、SceneBuilderAgent、Agent trace 前端展示、后端 Agent 工具接口、场景搭建、数据绑定和校验流程。
- 需要与对象模型、场景绑定、资产路由和时序查询能力对齐。
- 限制 Agent 直接执行 shell、文件系统写入、任意 HTTP、直接数据库写入和未经状态机的设备控制。

