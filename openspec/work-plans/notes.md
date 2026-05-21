# Notes: OpenSpec Design And Phased Development Documents

## Sources

### Source 1: `openspec/project.md`

- 平台定位：面向智慧农业数字孪生的多 Agent 场景构建与数据驱动资产更新平台。
- 分层：项目说明、路线图、参考资料、changes。
- 能力拆解：
  - P0：农业对象模型、3D 场景绑定、农场记忆层。
  - P1：Agent 操作 trace。
  - P2：资产保真度路由。
- MVP 建议：番茄温室。

### Source 2: `openspec/roadmap.md`

- 推荐顺序：
  1. `add-agricultural-object-model`
  2. `bind-scene-objects-to-business-objects`
  3. `add-farm-memory-layer`
  4. `add-agent-operation-trace`
  5. `add-asset-metadata-and-fidelity-routing`
- 成功指标：绑定率、数据绑定完整率、trace 完整率、资产元数据完整率、缺失资产不中断率、日报生成成功率。

### Source 3: `openspec/changes/*`

- 每个 change 已包含 proposal/design/tasks/specs。
- 5 个 change 已通过 `openspec validate --all --strict`。
- 设计文档应引用这些 change，而不是复制所有细节。

### Source 4: PRD

- 当前平台已有 Vue/Three.js 场景编辑器、Go 后端、GLB 资产库、IoT 模拟链路、告警、监控大屏、业务中心、AI 助手、Eino SceneBuilderAgent、模型语义检索、自动布局和 TRELLIS.2 资产任务入口。
- 核心判断：下一阶段主线应从“展示型 3D 平台”转向“对象驱动的农业数字孪生底座”。

## Synthesized Findings

### Design Shape

- 总体设计应该以“对象驱动”为中心，而不是以页面或模型数量为中心。
- 架构层次应为：入口体验、Agent 编排、孪生对象底座、场景绑定层、状态记忆层、资产治理层、现有前后端基础设施。
- Agent 只通过白名单工具访问系统能力，写操作必须受控。

### Phase Shape

- Phase 0：基线收敛与 OpenSpec 对齐。
- Phase 1：农业对象底座。
- Phase 2：3D 场景对象绑定。
- Phase 3：状态记忆层。
- Phase 4：Agent 运维闭环。
- Phase 5：资产元数据与保真度路由。
- Phase 6：综合验收与演示场景固化。

### Constraints

- 不做每日植株 GLB 重建。
- 不让 Agent 直接控制真实设备。
- 不将 TRELLIS.2 作为关键植株可信表型几何来源。
- 不把未实现能力写成已完成基线。

