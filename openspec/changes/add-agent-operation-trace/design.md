## Context

参考 `openspec/reference/references/04-agent-platform-and-orchestration.md`，农业数字孪生智能体平台不应把所有能力塞进一个聊天助手。更稳妥的路线是总控 Agent 接收用户目标，拆解为专用 Agent 和受控工具链，并通过 trace 记录每一步。

## Goals / Non-Goals

**Goals:**

- 定义 FarmTwinOrchestrator 与 ScenePlannerAgent、AssetFidelityAgent、LayoutAgent、DataBindingAgent、TimeSeriesAgent、GrowthAnalysisAgent、AlertDiagnosisAgent、ReportAgent、ValidatorAgent 的职责边界。
- 建立工具白名单和禁止工具清单。
- 规范 Agent trace 字段和可展示步骤。
- 支持核心流程在 LLM 不可用时确定性回退。

**Non-Goals:**

- 不实现完全自主的任意多 Agent 系统。
- 不允许 Agent 直接控制真实设备。
- 不允许 Agent 执行任意 shell、任意文件系统写入、任意 HTTP 或直接数据库写入。
- 不把文档 RAG 或模型语义检索包装成已完成的完整知识库。

## Decisions

- FarmTwinOrchestrator 负责接收用户目标、拆解任务、组织 handoff 和汇总结果。
- 专用 Agent 只通过白名单工具访问系统能力，工具返回结构化结果。
- 写操作必须区分 preview 和 apply 模式，关键写操作需要用户确认或状态机约束。
- trace 以 task 为根，step 为序列，记录 agent、tool、status、duration、inputSummary、outputSummary、failureReason 和 fallback。
- LLM 失败时，语义搭建至少可退回到模板、规则解析或预置场景生成。
- 本期实现采用契约化编排：保留现有 SceneBuilderAgent 入口，把执行步骤映射为 FarmTwinOrchestrator 和专用 Agent trace；trace 随响应返回并在前端展示，不新增持久化 trace 表或历史查询 API。
- `alert.acknowledge`、`scene.applyPlan`、`object.bind`、`asset.job.create` 在本期作为受控工具契约和 trace 能力表达；preview 模式不直接控制真实设备，也不绕过已有服务做数据库写入。

## Risks / Trade-offs

- Trace 过细会增加噪声，过粗无法审计；本设计要求摘要和关键字段，不保存敏感原始 payload。
- 多 Agent 名称过多可能超过 MVP 范围，因此实现可先合并为少数服务，但规格保留职责边界。
- 白名单会限制灵活性，但这是避免误操作和支撑验收的必要边界。
