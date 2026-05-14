# 数字孪生平台补齐与 LLM 助手接入计划

## Summary

当前项目已经具备 3D 场景编辑、模型库、IoT 模拟链路、告警、监控大屏、业务总览和 AI 资产生成雏形，但还不是完整数字孪生平台。下一步按“两条线”推进：

1. 补齐数字孪生平台底座：模型资产、场景对象、业务对象、IoT、告警、监控、视频、权限、报表。
2. 新增可点击进入的 `AI 助手` 页面：首版接 OpenAI 兼容 LLM，LLM 只读调用当前项目数据，RAG 先预留接口与结构。

默认选择：
- LLM 接入：OpenAI-compatible `/v1/chat/completions` 风格适配器。
- 工具权限：只读，不允许 LLM 直接修改场景、设备、告警或模型。
- RAG：本期预留接口，不接向量库。

## Key Changes

### 1. 平台缺口补齐路线

- 模型资产：
  - 建立模型元数据字段：分类、标签、尺寸、来源、版权、缩略图、面数、贴图大小、适用业务。
  - 增加模型资产健康检查接口：缺缩略图、缺 URL、文件不存在、分类异常、过大模型。
  - 统一前端 `public/models` 与后端 `scene-assets/models` 资产来源，避免两套模型路径并存。

- 场景与业务对象：
  - 增加业务对象层：地块、温室、灌溉区、摄像头点位、环境监测点。
  - 每个业务对象绑定：场景模型 ID、IoT 设备 ID、指标集合、告警规则。
  - 后续 6 个业务子系统都基于业务对象层，而不是直接散查设备数据。

- IoT 与告警：
  - 保留模拟器，但新增真实 MQTT 接入验收路径。
  - 增加指标字典、阈值规则配置、告警批量确认、归档、抑制、关闭。
  - 对 LLM 暴露只读工具：设备列表、设备最新值、历史指标、告警摘要。

- 监控与报表：
  - 监控大屏继续使用 `/monitor/dashboard`。
  - 增加日报/月报数据聚合接口，后续导出 PDF/Excel。
  - 监控页、业务页、AI 助手页共享同一套后端聚合数据。

- 安全与平台化：
  - 增加认证、角色、操作日志。
  - LLM 工具调用也要记录会话、问题、工具名、耗时、错误信息。
  - 生产环境关闭开放 CORS 和无鉴权 Swagger。

### 2. 新增 AI 助手页面

- 前端新增路由：
  - `/assistant`
  - 页面名：`AI 助手`
  - 顶部菜单新增入口，和 `大屏`、`业务` 同级。

- 页面能力：
  - 左侧聊天区：用户输入、助手回复、流式输出状态。
  - 右侧上下文区：当前可调用数据源、最近工具调用、RAG 状态占位。
  - 快捷问题：
    - “当前平台还缺什么？”
    - “模型库有哪些风险？”
    - “当前未确认告警有哪些？”
    - “帮我总结业务子系统完成度”
    - “分析 IoT 设备在线情况”
  - 回复中展示引用的数据源，例如 `model.list`、`iot.alerts`、`monitor.dashboard`。

### 3. 后端 LLM 接口与工具层

- 新增后端配置：
  - `llm.enabled`
  - `llm.base-url`
  - `llm.api-key`
  - `llm.model`
  - `llm.timeout-seconds`
  - `llm.max-tool-rounds`
  - `rag.enabled=false`

- 新增接口：
  - `POST /sceneApi/assistant/chat`
  - `GET /sceneApi/assistant/tools`
  - `GET /sceneApi/assistant/context/summary`
  - `GET /sceneApi/assistant/rag/status`

- `POST /assistant/chat` 请求体：
  - `message: string`
  - `sessionId?: string`
  - `context?: { sceneName?: string; selectedModelId?: number; deviceId?: string }`

- 响应体：
  - `sessionId`
  - `answer`
  - `toolCalls`
  - `citations`
  - `ragUsed: false`

- 首版只读工具：
  - `model.stats`：模型数量、分类、缩略图缺失情况。
  - `model.list`：模型树摘要。
  - `scene.list`：场景列表。
  - `scene.load`：读取指定场景和模型对象。
  - `iot.devices`：设备列表和在线状态。
  - `iot.latest`：设备最新指标。
  - `iot.alerts`：告警列表和未确认统计。
  - `monitor.dashboard`：监控中心聚合数据。
  - `business.overview`：6 个业务子系统完成度。
  - `asset.jobs`：AI 资产生成任务状态。

- 工具调用策略：
  - 后端不让 LLM 直接访问数据库。
  - LLM 只能通过白名单工具拿数据。
  - 每次工具结果做摘要和截断，避免把大量时序数据直接塞给模型。
  - 工具失败时，助手说明“该数据源暂不可用”，不中断整个回答。

### 4. RAG 预留

- 本期只做结构，不接向量库：
  - `GET /assistant/rag/status` 返回 `enabled:false`。
  - 预留文档类型：建设方案、审计报告、接口文档、模型元数据、运维记录。
  - 预留返回结构：`chunks[]`、`source`、`score`、`title`、`excerpt`。

- 后续接入 RAG 时：
  - 文档入库走独立 ingest。
  - embedding 和向量库作为可替换适配器。
  - LLM 回复合并“实时项目数据工具”和“RAG 文档知识”。

## Test Plan

- 后端：
  - LLM 未配置时，`/assistant/chat` 返回明确错误，不影响其他接口。
  - mock OpenAI-compatible 服务时，聊天接口可返回答案。
  - 每个只读工具单独测试：模型、场景、IoT、告警、监控、业务、资产任务。
  - 工具超时、接口失败、空数据都要有可读降级回复。
  - 确认没有任何 LLM 工具会写入数据库。

- 前端：
  - 顶部菜单可进入 `/assistant`。
  - 聊天输入、发送中、失败、空状态、历史消息显示正常。
  - 工具调用记录和引用来源显示正常。
  - 页面刷新后不会影响现有场景编辑、监控、业务页面。
  - `npm run build` 通过。

- 验收场景：
  - 问“现在平台缺什么”，助手能结合审计报告口径和实时接口总结缺口。
  - 问“当前模型库情况”，助手能调用模型统计并指出缩略图、元数据问题。
  - 问“当前告警情况”，助手能调用告警数据并总结未确认告警。
  - 问“6 个业务子系统完成度”，助手能调用业务概览并说明全部 partial。
  - RAG 状态显示为“未启用，已预留”。

## Assumptions

- 首版不实现登录鉴权，但代码结构预留用户/session 字段。
- 首版不做流式 SSE，先用普通 HTTP 返回；后续可升级流式输出。
- 首版不接向量库，不做文档上传，只预留 RAG 状态和返回结构。
- LLM 只读调用当前项目数据，不允许确认告警、保存场景、删除模型、创建设备。
- 新页面采用现有 Vue3 + Element Plus + Pinia + Axios 风格，不引入新的前端 UI 框架。
