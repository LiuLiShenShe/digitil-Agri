# 智慧农业数字孪生智能体平台 OpenSpec 路线图

## Milestones

| 里程碑 | 周期 | 目标 | OpenSpec 变更 |
| --- | --- | --- | --- |
| M1: 孪生对象底座 | 1-2 周 | 建立农业对象图谱和 3D 绑定锚点 | `add-agricultural-object-model`, `bind-scene-objects-to-business-objects` |
| M2: 状态与记忆层 | 2-3 周 | 将 IoT、事件、告警和日级归档按对象组织 | `add-farm-memory-layer` |
| M3: Agent 运维闭环 | 2-3 周 | 扩展 Agent 工具白名单、trace 和可回退运维能力 | `add-agent-operation-trace` |
| M4: 资产治理与保真度路由 | 2-3 周 | 建多保真资产元数据、质量审计和路由策略 | `add-asset-metadata-and-fidelity-routing` |
| M5: 业务子系统拆分 | 3-4 周 | 在统一底座上拆土壤、气象、灌溉、温室、视频、环境子系统 | 待新增 changes |
| M6: 生产化补齐 | 持续 | 补真实设备、安全、权限、测试和部署 | 待新增 changes |

## Recommended Order

1. `add-agricultural-object-model`
2. `bind-scene-objects-to-business-objects`
3. `add-farm-memory-layer`
4. `add-agent-operation-trace`
5. `add-asset-metadata-and-fidelity-routing`

`add-agricultural-object-model`、`bind-scene-objects-to-business-objects`、`add-farm-memory-layer` 和 `add-agent-operation-trace` 已完成。下一步优先推进 `add-asset-metadata-and-fidelity-routing`，把资产元数据、质量审计、缺失资产任务和保真度路由收口。

## Phase 0 Decisions

- 首个 MVP 场景固定为“番茄温室”，对象清单为 1 个温室、20 株番茄、1 个气象站、1 个水泵/灌溉设备、1 个摄像头、1 个传感器组。
- Phase 0 只确认基线和护栏，当时不实现 5 个 active changes 的业务能力，不将未完成任务标为已实现。
- Phase 1 已在 2026-05-21 实现 `add-agricultural-object-model`，当前仍保留在 changes 区等待归档。
- Phase 2 已在 2026-05-21 实现 `bind-scene-objects-to-business-objects`，当前仍保留在 changes 区等待归档。
- Phase 3 已在 2026-05-21 实现 `add-farm-memory-layer`，当前仍保留在 changes 区等待归档；`phase3_farm_memory_layer_migration.sql` 已在当前开发数据库执行。
- Phase 4 已在 2026-05-22 实现 `add-agent-operation-trace`，当前仍保留在 changes 区等待归档。
- 真实设备控制、每日 GLB 重建和完整 RBAC 继续作为后续非 Phase 0 范围。
- 基线状态以 `openspec/development-phases/phase0-baseline-report.md` 和 `python3 openspec/tools/phase0_baseline_guard.py --write-report openspec/development-phases/phase0-baseline-report.md` 为准。

## Current Change Progress

| Change | Progress | 当前判定 |
| --- | ---: | --- |
| `add-agricultural-object-model` | 10/10 | 已实现，待归档 |
| `bind-scene-objects-to-business-objects` | 9/9 | 已实现，待归档 |
| `add-farm-memory-layer` | 10/10 | 已实现，待归档 |
| `add-agent-operation-trace` | 10/10 | 已实现，待归档 |
| `add-asset-metadata-and-fidelity-routing` | 0/10 | 待实现，Phase 5 前置 |

## Success Metrics

- 3D 对象业务绑定率：核心演示场景中可观测对象绑定率不低于 90%。
- 数据绑定完整率：核心业务对象至少绑定一个实时或日级指标。
- Agent trace 完整率：所有 Agent 任务均有可查询 trace。
- 资产元数据完整率：公开资产基础元数据完整率不低于 80%。
- 缺失资产不中断率：语义搭建中缺 GLB 时能用占位模型继续生成场景。
- 日报生成成功率：温室日报可基于对象、指标、事件和告警生成。

## Acceptance Demonstrations

- 典型提示词“搭建番茄温室，包含 20 株番茄、气象站、水泵、摄像头和传感器”能生成可加载场景、资产选择理由、布局结果和 trace。
- 点选温室模型能看到温室对象、传感器、设备、指标、告警和事件。
- 点选异常设备能看到最近指标、告警原因和建议动作。
- 对一个完整场景运行校验，能列出缺绑定、缺数据、缺缩略图和缺元数据的问题。
- 生成一份温室日报，内容包含环境摘要、设备状态、告警、灌溉事件和建议。

## Open Questions

1. 首个 MVP 场景是否固定为“番茄温室”，还是同时保留“综合农业园区”和“智慧示范田”？
2. 真实设备联调优先级是否确定为气象站、土壤传感器、灌溉控制器？
3. 关键植株高保真重建是否已有 F2DMAS 输出样本和采集规范？
4. 是否需要在下一阶段引入正式登录、RBAC 和操作审计，还是先用演示级用户标识？
5. 日报优先做温室日报、园区日报，还是告警处置报告？
6. 资产元数据来源和许可证是否需要满足正式交付审计，还是先满足内部演示和论文验证？
