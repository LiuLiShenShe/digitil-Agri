# 智慧农业数字孪生智能体平台 OpenSpec 索引

本目录将 `docs/agri-digital-twin-agent-platform-prd.md` 拆解为 OpenSpec 分层文档。

## 目录分层

- `project.md`：项目定位、输入来源、产品原则、能力拆解和 PRD 映射关系。
- `roadmap.md`：里程碑、近期变更顺序、成功指标、验收演示和待确认问题。
- `designs/agri-digital-twin-agent-platform-design.md`：总体设计文档，串联对象底座、场景绑定、记忆层、Agent trace 和资产治理。
- `development-phases/agri-digital-twin-agent-platform-phased-plan.md`：分阶段开发文档，定义 Phase 0-6 的目标、任务、验收和退出标准。
- `work-plans/`：本轮文档生成使用的 superpowers 持久化计划和资料笔记。
- `reference/references/`：外部资料、设计备忘和项目参考依据。
- `changes/`：按 OpenSpec `proposal -> specs -> design -> tasks` 工作流组织的近期候选变更。

## Active Changes

| Change | Capability | 目的 |
| --- | --- | --- |
| `add-agricultural-object-model` | `agricultural-object-model` | 建立 Farm、Greenhouse、Parcel、CropRow、Plant、Sensor、Device、Camera 等农业业务对象和关系查询 |
| `bind-scene-objects-to-business-objects` | `scene-business-binding` | 建立 3D 场景对象与业务对象绑定、点选详情、业务定位和绑定校验 |
| `add-farm-memory-layer` | `farm-memory-layer` | 建立指标字典、同步频率、时序查询、事件记忆和日报数据源 |
| `add-agent-operation-trace` | `agent-operation-trace` | 建立多 Agent 职责、工具白名单、trace 结构和确定性回退 |
| `add-asset-metadata-and-fidelity-routing` | `asset-fidelity-routing` | 建立资产元数据、质量验收、保真度路由、缺失资产任务和植株几何版本 |

## Why Changes Instead Of Canonical Specs

这些能力来自下一阶段 PRD，当前系统尚未全部实现。为避免把未实现能力误标为当前基线，本次将它们放入 `openspec/changes/` 作为待实施变更；每个变更都包含 delta spec、设计和任务。实施完成后可使用 OpenSpec archive 流程归档到 `openspec/specs/`。

## Validation

已使用严格模式校验：

```bash
openspec validate --all --strict --json
```

结果：5 个 change 全部通过。
