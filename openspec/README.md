# 智慧农业数字孪生智能体平台 OpenSpec 索引

本目录将 `docs/agri-digital-twin-agent-platform-prd.md` 拆解为 OpenSpec 分层文档。

## 目录分层

- `project.md`：项目定位、输入来源、产品原则、能力拆解和 PRD 映射关系。
- `roadmap.md`：里程碑、近期变更顺序、成功指标、验收演示和待确认问题。
- `designs/agri-digital-twin-agent-platform-design.md`：总体设计文档，串联对象底座、场景绑定、记忆层、Agent trace 和资产治理。
- `development-phases/agri-digital-twin-agent-platform-phased-plan.md`：分阶段开发文档，定义 Phase 0-6 的目标、任务、验收和退出标准。
- `development-phases/phase0-baseline-report.md`：Phase 0 基线收敛与开发护栏报告，记录 OpenSpec、前端、后端、数据、资产和 MVP 边界。
- `work-plans/`：本轮文档生成使用的 superpowers 持久化计划和资料笔记。
- `reference/references/`：外部资料、设计备忘和项目参考依据。
- `changes/`：按 OpenSpec `proposal -> specs -> design -> tasks` 工作流组织的近期候选变更。

## Active Changes

| Change | Capability | 目的 |
| --- | --- | --- |
| `add-agricultural-object-model` | `agricultural-object-model` | 已实现 Farm、Greenhouse、Parcel、CropRow、Plant、Sensor、Device、Camera 等农业业务对象和关系查询，待归档 |
| `bind-scene-objects-to-business-objects` | `scene-business-binding` | 建立 3D 场景对象与业务对象绑定、点选详情、业务定位和绑定校验 |
| `add-farm-memory-layer` | `farm-memory-layer` | 已实现指标字典、同步频率、对象级时序查询、事件记忆和日报数据源，待归档 |
| `add-agent-operation-trace` | `agent-operation-trace` | 已实现多 Agent 职责、工具白名单、trace 结构、确定性回退和前端 trace 展示，待归档 |
| `add-asset-metadata-and-fidelity-routing` | `asset-fidelity-routing` | 已实现资产元数据、质量验收、保真度路由、缺失资产任务和植株几何版本，待归档 |

## Development Progress

- Phase 0 基线收敛与开发护栏已于 2026-05-21 完成，报告见 `development-phases/phase0-baseline-report.md`。
- 当前 active changes 进度：
  - `add-agricultural-object-model`: 10/10，已实现，待归档到 canonical specs
  - `bind-scene-objects-to-business-objects`: 9/9，已实现，待归档到 canonical specs
  - `add-farm-memory-layer`: 10/10，已实现，待归档到 canonical specs
  - `add-agent-operation-trace`: 10/10，已实现，待归档到 canonical specs
  - `add-asset-metadata-and-fidelity-routing`: 10/10，已实现，待归档到 canonical specs

## Why Changes Instead Of Canonical Specs

这些能力来自下一阶段 PRD，当前仍通过 `openspec/changes/` 保留 review 和 archive 流程，避免把未归档变更直接混入 canonical specs。`add-agricultural-object-model`、`bind-scene-objects-to-business-objects`、`add-farm-memory-layer`、`add-agent-operation-trace` 和 `add-asset-metadata-and-fidelity-routing` 已经实现，完成 review 后可使用 OpenSpec archive 流程归档到 `openspec/specs/`。

## Validation

Phase 0 护栏命令：

```bash
python3 openspec/tools/phase0_baseline_guard.py --write-report openspec/development-phases/phase0-baseline-report.md
```

该命令内部会运行前端构建，不要与另一个 `npm run build` 并行执行，以免 Vite 清理 `dist/` 时产生目录竞争。

已使用严格模式校验：

```bash
openspec validate --all --strict --json
```

结果：5 个 change 全部通过。
