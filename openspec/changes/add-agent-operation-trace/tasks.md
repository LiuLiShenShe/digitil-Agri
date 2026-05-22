## Development Progress

- Phase 0 baseline guard completed on 2026-05-21; see `openspec/development-phases/phase0-baseline-report.md`.
- Phase 4 implementation completed on 2026-05-22: 10/10 implementation tasks complete.
- Implemented scope: Agent role boundaries, tool whitelist and prohibited policy, expanded trace schema, displayable trace steps, deterministic fallback, and trace sanitization.

## 1. Agent 分工

- [x] 1.1 定义 FarmTwinOrchestrator 的任务入口、handoff 和汇总职责。
- [x] 1.2 定义 ScenePlannerAgent、AssetFidelityAgent、LayoutAgent、DataBindingAgent、TimeSeriesAgent、GrowthAnalysisAgent、AlertDiagnosisAgent、ReportAgent、ValidatorAgent 的职责。
- [x] 1.3 将现有 SceneBuilderAgent 映射到新的 Agent 职责边界，保留兼容路径。

## 2. 工具白名单

- [x] 2.1 定义只读工具：`scene.current`、`model.search`、`model.metadata`、`object.lookup`、`object.relations`、`timeseries.query`、`event.query`。
- [x] 2.2 定义受控写工具：`scene.plan`、`layout.solve`、`scene.applyPlan`、`asset.job.create`、`object.bind`、`alert.acknowledge`。
- [x] 2.3 明确禁止工具：任意 shell、任意文件系统写入、任意 HTTP、直接数据库写入、未经状态机的设备控制。

## 3. Trace 与回退

- [x] 3.1 扩展 Agent trace 字段：taskId、userGoal、mode、steps、tool、status、duration、inputSummary、outputSummary、failureReason、fallback。
- [x] 3.2 为语义搭建、资产路由、对象绑定和校验各准备一个可展示 trace。
- [x] 3.3 实现 LLM 未配置或调用失败时的确定性回退路径。
- [x] 3.4 验证 trace 不包含敏感原始 payload。
