# Phase 0 基线收敛与开发护栏报告

生成日期：2026-05-21

## 结论

- 护栏状态：PASS
- Phase 0 只确认基线，不实现 5 个 active changes 的业务能力。
- 首个 MVP 固定为番茄温室：1 个温室、20 株番茄、1 个气象站、1 个水泵/灌溉设备、1 个摄像头、1 个传感器组。
- 后续扩展锚点保留 Parcel、CropRow、CropBatch，不在 Phase 0 落库实现。
- 本阶段非目标：不做真实设备控制、不做每日 GLB 重建、不做完整 RBAC。

## 后续进展

- 2026-05-21：Phase 1 `add-agricultural-object-model` 已实现，OpenSpec 任务进度为 10/10，待 review 后归档到 canonical specs。
- 2026-05-21：Phase 2 `bind-scene-objects-to-business-objects` 已实现，OpenSpec 任务进度为 9/9，待 review 后归档到 canonical specs。
- 2026-05-21：Phase 3 `add-farm-memory-layer` 已实现，OpenSpec 任务进度为 10/10，`phase3_farm_memory_layer_migration.sql` 已在当前开发数据库执行，待 review 后归档到 canonical specs。
- 2026-05-22：Phase 4 `add-agent-operation-trace` 已实现，OpenSpec 任务进度为 10/10，待 review 后归档到 canonical specs。
- 本报告中的 Active Changes 表保留 Phase 0 护栏生成时的历史基线，不代表后续开发的当前进度。

## 命令基线

| 命令 | 退出码 | 状态 |
| --- | ---: | --- |
| `openspec validate --all --strict` | 0 | PASS |
| `go test ./...` | 0 | PASS |
| `npm run build` | 0 | PASS |

## 警告

- npm run build: (!) Some chunks are larger than 500 kB after minification. Consider:; - Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.

## OpenSpec Active Changes

| Change | Tasks | Status | Phase 0 判定 |
| --- | ---: | --- | --- |
| add-asset-metadata-and-fidelity-routing | 0/10 | in-progress | 未实现 |
| add-agent-operation-trace | 0/10 | in-progress | 未实现 |
| add-farm-memory-layer | 0/10 | in-progress | 未实现 |
| bind-scene-objects-to-business-objects | 0/9 | in-progress | 未实现 |
| add-agricultural-object-model | 0/10 | in-progress | 未实现 |

## 资产盘点

| 口径 | 数量 |
| --- | ---: |
| backend scene-assets GLB | 593 |
| backend scene-assets/thumbs files | 7 |
| frontend public GLB | 27 |
| frontend public images | 34 |

## 数据来源状态

| 数据源 | 状态 | 证据 |
| --- | --- | --- |
| IoT 设备与指标 | 模拟 | `iot.simulator-enabled: true`，当前以模拟器和 mock 数据链路为主 |
| 真实设备接入 | 缺失 | 未发现 Phase 0 真实设备联调记录，本阶段不做真实设备控制 |
| LLM Agent | 缺失 | `llm.enabled: false`，语义搭建保留确定性回退路径 |
| RAG 知识库 | 缺失 | `rag.enabled: false`，不可误标为已完成文档 RAG |
| 资产元数据 | 缺失 | GLB 数量多于缩略图和元数据治理结果，待 Phase 5 收敛 |
| 前端业务展示 | 模拟 | 业务中心、监控大屏、图表主要面向演示和模拟数据聚合 |
| 过期数据 | 过期 | Phase 0 仅定义状态标签，后续对象/记忆层实现具体判定规则 |

## 命令输出摘要

### `openspec validate --all --strict`

```text
✓ change/add-agent-operation-trace
✓ change/add-agricultural-object-model
✓ change/add-asset-metadata-and-fidelity-routing
✓ change/add-farm-memory-layer
✓ change/bind-scene-objects-to-business-objects
Totals: 5 passed, 0 failed (5 items)

- Validating...
```

### `go test ./...`

```text
?   	scene-server-go	[no test files]
?   	scene-server-go/config	[no test files]
?   	scene-server-go/controller	[no test files]
?   	scene-server-go/docs	[no test files]
?   	scene-server-go/iot	[no test files]
?   	scene-server-go/mapper	[no test files]
ok  	scene-server-go/service	(cached)
?   	scene-server-go/vo	[no test files]
```

### `npm run build`

```text
> scene-design-v2@0.1.0 build
> vue-tsc --noEmit && vite build

vite v6.4.2 building for production...
transforming...
✓ 2597 modules transformed.
rendering chunks...
computing gzip size...
dist/scene/index.html                                  0.54 kB │ gzip:     0.38 kB
dist/scene/assets/BusinessCenterView-CY7GPd4w.css      5.14 kB │ gzip:     1.36 kB
dist/scene/assets/AssistantView-ByTLvgUz.css           5.59 kB │ gzip:     1.50 kB
dist/scene/assets/MonitorCenterView-nianEaff.css       9.77 kB │ gzip:     2.23 kB
dist/scene/assets/index-BbhOen7Q.css                 402.03 kB │ gzip:    58.30 kB
dist/scene/assets/AboutView-D8y_cFyL.js                0.24 kB │ gzip:     0.21 kB
dist/scene/assets/BusinessCenterView-BmWAcbWx.js       4.85 kB │ gzip:     2.23 kB
dist/scene/assets/AssistantView-D3HfgLDG.js            7.79 kB │ gzip:     3.30 kB
dist/scene/assets/MonitorCenterView-vlILEoyp.js       15.00 kB │ gzip:     5.97 kB
dist/scene/assets/index-BGfwnM0u.js                3,576.47 kB │ gzip: 1,103.76 kB
✓ built in 16.56s


(!) Some chunks are larger than 500 kB after minification. Consider:
- Using dynamic import() to code-split the application
- Use build.rollupOptions.output.manualChunks to improve chunking: https://rollupjs.org/configuration-options/#output-manualchunks
- Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.
```
