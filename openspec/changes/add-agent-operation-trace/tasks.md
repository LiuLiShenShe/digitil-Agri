## Development Progress

- Phase 0 baseline guard completed on 2026-05-21; see `openspec/development-phases/phase0-baseline-report.md`.
- This change remains unimplemented: 0/10 implementation tasks complete.
- Do not mark tasks below complete until Agent role boundaries, tool whitelist, trace schema, fallback behavior, and verification are implemented.

## 1. Agent 分工

- [ ] 1.1 定义 FarmTwinOrchestrator 的任务入口、handoff 和汇总职责。
- [ ] 1.2 定义 ScenePlannerAgent、AssetFidelityAgent、LayoutAgent、DataBindingAgent、TimeSeriesAgent、GrowthAnalysisAgent、AlertDiagnosisAgent、ReportAgent、ValidatorAgent 的职责。
- [ ] 1.3 将现有 SceneBuilderAgent 映射到新的 Agent 职责边界，保留兼容路径。

## 2. 工具白名单

- [ ] 2.1 定义只读工具：`scene.current`、`model.search`、`model.metadata`、`object.lookup`、`object.relations`、`timeseries.query`、`event.query`。
- [ ] 2.2 定义受控写工具：`scene.plan`、`layout.solve`、`scene.applyPlan`、`asset.job.create`、`object.bind`、`alert.acknowledge`。
- [ ] 2.3 明确禁止工具：任意 shell、任意文件系统写入、任意 HTTP、直接数据库写入、未经状态机的设备控制。

## 3. Trace 与回退

- [ ] 3.1 扩展 Agent trace 字段：taskId、userGoal、mode、steps、tool、status、duration、inputSummary、outputSummary、failureReason、fallback。
- [ ] 3.2 为语义搭建、资产路由、对象绑定和校验各准备一个可展示 trace。
- [ ] 3.3 实现 LLM 未配置或调用失败时的确定性回退路径。
- [ ] 3.4 验证 trace 不包含敏感原始 payload。
