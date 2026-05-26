# 智慧农业数字孪生平台 Swagger / API 文档

生成日期：2026-05-26  
适用范围：`digital-twingo/scene-design-v2` 前端、`digital-twingo/scene-server-go` 后端、`TRELLIS.2` 资产生成服务。

已写好一键启动脚本：
`/data/fj/数字孪生/scripts/start_services.sh`
使用方式：
bash

cd /data/fj/数字孪生
./scripts/start_services.sh

它会启动/检查这三个服务：
后端 Go：9010
前端 Vite：5176
TRELLIS.2 FastAPI：9020
系统前端进入地址是：

http://127.0.0.1:5176/scene/

如果你从局域网其他机器访问，可以试：

http://10.121.2.78:5176/scene/

我已经跑过脚本验证了：前端入口返回 200，TRELLIS.2 /health 也是 ready。

## 0. 在线 Swagger / FastAPI 文档入口

项目里可以同时使用两套在线接口文档：Go 后端的 Swagger UI，以及 TRELLIS.2 FastAPI 自动生成的在线文档。

| 文档 | 地址 | 覆盖范围 | 启动前提 |
| --- | --- | --- | --- |
| Go 后端 Swagger UI | `http://127.0.0.1:9010/swagger/index.html` | `/sceneApi/*` 后端接口 | 启动 `scene-server-go`，且 `application.yml` 中 `swagger.enable: true` |
| Go 后端 Swagger JSON | `http://127.0.0.1:9010/swaggerApi` | 后端 OpenAPI/Swagger JSON | 同上 |
| TRELLIS.2 FastAPI Swagger UI | `http://127.0.0.1:9020/docs` | `/health`、`/generate`、`/status/{job_id}`、`/jobs` | 启动 `TRELLIS.2/service/trellis2_service.py` |
| TRELLIS.2 FastAPI ReDoc | `http://127.0.0.1:9020/redoc` | TRELLIS.2 接口的 ReDoc 展示 | 同上 |
| TRELLIS.2 OpenAPI JSON | `http://127.0.0.1:9020/openapi.json` | TRELLIS.2 OpenAPI JSON | 同上 |

后端 Swagger 启动：

```bash
cd /data/fj/数字孪生/digital-twingo/scene-server-go
go run SceneServerApplication.go
```

TRELLIS.2 FastAPI 文档启动：

```bash
cd /data/fj/数字孪生/TRELLIS.2/service
PY_SSIZE_T_CLEAN=1 CUDA_VISIBLE_DEVICES=1 python trellis2_service.py
```

建议演示或联调时打开两个页面：`/swagger/index.html` 看平台后端接口，`/docs` 看 TRELLIS.2 生成服务接口。

## 1. 服务总览

### 1.1 运行入口

| 模块 | 技术栈 | 默认地址 | 说明 |
| --- | --- | --- | --- |
| 前端应用 | Vue 3 + TypeScript + Vite | `http://<host>:<vite-port>/scene/` | Vite `base` 为 `/scene/`，页面路由也挂在该前缀下 |
| 后端 API | Go 1.24 + Gin + MySQL | `http://127.0.0.1:9010/sceneApi` | 统一 REST API 前缀 |
| Swagger UI | swaggo/gin-swagger | `http://127.0.0.1:9010/swagger/index.html` | `application.yml` 中 `swagger.enable: true` 时启用 |
| Swagger JSON | swaggo | `http://127.0.0.1:9010/swaggerApi` | 返回后端生成的 `docs/swagger.json` |
| 静态资产 | Gin Static | `http://127.0.0.1:9010/scene-assets/...` | GLB、缩略图、上传原图等 |
| TRELLIS.2 服务 | FastAPI + CUDA | `http://127.0.0.1:9020` | 后端资产生成任务会转发到该服务 |

### 1.2 前端代理与环境

前端 Vite 配置：

| 路径 | 代理目标 | 用途 |
| --- | --- | --- |
| `/sceneApi` | `http://127.0.0.1:9010` | 后端 REST API 与 WebSocket |
| `/scene-assets` | `http://127.0.0.1:9010` | 模型、缩略图、图片资源 |

前端非 Mock 模式下通过 `VITE_BASEURL` 设置 Axios 基础地址，默认应指向：

```text
http://127.0.0.1:9010/sceneApi
```

### 1.3 统一响应格式

Go 后端大多数接口返回：

```json
{
  "code": 200,
  "data": {}
}
```

常见约定：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `code` | number | `200` 表示业务成功；`400`、`404`、`500`、`999` 表示业务失败或内部错误 |
| `data` | any | 成功时为业务数据，失败时多为错误字符串 |

注意：部分 IoT 接口会使用 HTTP 状态码表达错误，例如 `503` 表示 IoT 服务未初始化。

## 2. 前端页面与调用关系

### 2.1 页面路由

前端 Vite base 为 `/scene/`，因此实际访问路径如下：

| 页面 | Vue Router path | 实际访问路径 | 主要用途 |
| --- | --- | --- | --- |
| 主场景编辑器 | `/` | `/scene/` | 3D 场景搭建、模型加载、属性面板 |
| 监控中心 | `/monitor` | `/scene/monitor` | 园区监控大屏 |
| 业务中心 | `/business` | `/scene/business` | 农业业务子系统总览 |
| 农业对象 | `/objects` | `/scene/objects` | 农业对象、关系、场景定位调试 |
| AI 助手 | `/assistant` | `/scene/assistant` | 只读工具型助手 |
| 验收控制台 | `/acceptance` | `/scene/acceptance` | 番茄温室 Phase 6 综合验收 |
| 关于页 | `/about` | `/scene/about` | 项目信息 |

### 2.2 前端 Service 到后端 API 映射

| 前端文件 | 主要接口 | 说明 |
| --- | --- | --- |
| `src/services/iotService.ts` | `/iot/*`、`/iot/ws` | 设备 CRUD、数据、告警、IoT WebSocket |
| `src/services/monitorService.ts` | `/monitor/dashboard` | 监控中心大屏 |
| `src/services/businessService.ts` | `/business/overview` | 农业业务中心 |
| `src/services/agriculturalObjectService.ts` | `/objects/*` | 农业业务对象与关系 |
| `src/services/farmMemoryService.ts` | `/memory/*`、`/objects/:id/memory/*` | 对象记忆、指标、时序、事件、日报数据源 |
| `src/services/sceneBusinessBindingService.ts` | `/scene/bindings/*` | 3D 场景对象与农业业务对象绑定 |
| `src/services/semanticService.ts` | `/semantic/*`、`/asset/jobs*` | 语义搭建、资产语义表、AI 资产生成任务 |
| `src/services/assistantService.ts` | `/assistant/*` | AI 助手、工具、上下文、RAG 状态 |
| `src/services/acceptanceService.ts` | `/acceptance/tomato-greenhouse` | 综合验收数据 |
| `src/services/dataService.ts` | `/scene/loadScene`、`/datasvr/*` | 场景与模型绑定数据 |

### 2.3 前端 WebSocket

| 名称 | URL | 消息方向 | 说明 |
| --- | --- | --- | --- |
| IoT WebSocket | `ws://<host>/sceneApi/iot/ws` | 后端推送 | 设备实时指标与告警 |
| 数据可视化 WebSocket | `VITE_DATA_WS_URL` | 双向订阅 | 前端期望消息 `{type:"data", sourceId, metric, point}`；未配置时自动使用 Mock 数据 |

数据可视化订阅消息：

```json
{
  "type": "subscribe",
  "sourceId": "ds-greenhouse-01"
}
```

数据可视化取消订阅消息：

```json
{
  "type": "unsubscribe",
  "sourceId": "ds-greenhouse-01"
}
```

## 3. 后端 API 目录

后端统一前缀：`/sceneApi`

### 3.1 场景接口 `/scene`

| 方法 | 路径 | 参数/Body | 返回 data | 说明 |
| --- | --- | --- | --- | --- |
| `POST` | `/scene/saveScene` | 场景 JSON | 保存结果 | 按 `sceneName` 新增或覆盖场景 |
| `GET` | `/scene/sceneList` | 无 | `string[]` | 场景名列表 |
| `GET` | `/scene/loadScene` | query: `scene` | 场景配置与模型列表 | 加载指定场景 |
| `GET` | `/scene/defaultScene` | 无 | `string` | 获取默认场景名 |

保存场景请求示例：

```json
{
  "sceneName": "番茄温室 MVP",
  "background": {},
  "ambientLight": {},
  "directionalLight": {},
  "spotLight": {},
  "grid": {},
  "groundPane": {},
  "modelList": [
    {
      "url": "/scene-assets/models/Tomato_Crop.glb",
      "options": {
        "scale": 1,
        "angle": 0,
        "dataId": "ds-greenhouse-01",
        "sceneObjectId": "scene-plant-tomato-001",
        "businessObjectId": "plant-tomato-001",
        "assetKey": "tomato",
        "isDefaultBinding": true,
        "offset": { "x": 0, "y": 0, "z": 0 }
      }
    }
  ]
}
```

### 3.2 场景业务绑定 `/scene/bindings`

| 方法 | 路径 | 参数/Body | 返回 data | 说明 |
| --- | --- | --- | --- | --- |
| `GET` | `/scene/bindings/by-scene-object` | query: `scene`, `sceneObjectId` | `SceneBindingLookupResponse` | 按 3D 场景对象查业务对象 |
| `GET` | `/scene/bindings/by-business-object` | query: `scene`, `businessObjectId` | `SceneBindingLookupResponse` | 按业务对象反查场景模型 |
| `PUT` | `/scene/bindings` | `SceneBindingUpdateRequest` | `SceneBindingLookupResponse` | 更新绑定 |
| `DELETE` | `/scene/bindings` | query: `scene`, `sceneObjectId` | `SceneBindingLookupResponse` | 清除绑定 |
| `GET` | `/scene/bindings/validate` | query: `scene` | `SceneBindingValidationSummary` | 验证场景绑定完整性 |

更新绑定请求：

```json
{
  "sceneName": "番茄温室 MVP",
  "sceneObjectId": "scene-weather-station-001",
  "businessObjectId": "sensor-greenhouse-001",
  "assetKey": "weather_station",
  "isDefaultBinding": false
}
```

核心字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `sceneName` | string | 场景名 |
| `modelId` | number | 后端 `scenemodel` 记录 ID |
| `sceneObjectId` | string | 前端稳定场景对象 ID |
| `businessObjectId` | string | 农业业务对象 ID |
| `assetKey` | string | 资产语义 key |
| `isDefaultBinding` | boolean | 是否为默认绑定 |
| `url` | string | GLB 资源路径 |

### 3.3 模型与背景资源

#### `/model`

| 方法 | 路径 | 参数 | 返回 data | 说明 |
| --- | --- | --- | --- | --- |
| `GET` | `/model/list` | query: `ownerKey?` | `ModelVo[]` | 模型树；传 `ownerKey` 时包含该用户 AI 生成模型 |

`ModelVo`：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | number | 模型节点 ID |
| `parentid` | number | 父节点 ID |
| `name` | string | 模型名 |
| `url` | string/null | GLB 路径 |
| `leaf` | boolean | 是否叶子节点 |
| `category` | string | 分类 |
| `tags` | string | 标签 |
| `thumbnail` | string | 缩略图 |

#### `/background`

| 方法 | 路径 | 返回 data | 说明 |
| --- | --- | --- | --- |
| `GET` | `/background/list` | 天空盒列表 | 获取天空盒背景 |
| `GET` | `/background/gdTextures` | 地面纹理列表 | 获取地面材质 |

#### `/scene-assets`

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/scene-assets/models/<file>.glb` | GLB 模型文件 |
| `GET` | `/scene-assets/thumbs/<file>.jpg` | 模型缩略图 |
| `GET` | `/scene-assets/sources/<file>` | AI 资产生成原始图片 |

### 3.4 数据服务 `/datasvr`

| 方法 | 路径 | 参数 | 返回 data | 说明 |
| --- | --- | --- | --- | --- |
| `GET` | `/datasvr/getData` | query: `dataId` | 数据对象 | 按数据 ID 获取模型绑定数据 |
| `GET` | `/datasvr/dataIndex` | query: `dataId` | 数据对象 | 兼容前端数据面板 |
| `GET` | `/datasvr/list` | 无 | 数据对象列表 | 可绑定数据源列表 |

### 3.5 农业对象 `/objects`

| 方法 | 路径 | 参数 | 返回 data | 说明 |
| --- | --- | --- | --- | --- |
| `GET` | `/objects` | query: `id?`, `type?` | `AgriculturalObjectVo[]` 或单对象 | 列表或条件查找 |
| `GET` | `/objects/:id` | path: `id` | `AgriculturalObjectVo` | 获取单个农业对象 |
| `GET` | `/objects/:id/relations` | query: `relationType[]?` | `ObjectRelationsResponse` | 获取对象关系 |

对象类型：

```text
Farm, Greenhouse, Parcel, CropRow, Plant, CropBatch,
Sensor, Device, Camera, Operation, Observation
```

`AgriculturalObjectVo`：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string | 对象 ID |
| `type` | string | 对象类型 |
| `name` | string | 名称 |
| `parentId` | string | 父对象 |
| `containingArea` | string | 所属区域 |
| `spatial` | object | 空间信息 |
| `status` | string | 业务状态 |
| `updatedAt` | string | 更新时间 |
| `dataQuality` | string | `real`、`simulated`、`stale`、`missing` |
| `metadata` | object | 扩展元数据 |

### 3.6 农场记忆 `/memory` 与 `/objects/:id/memory`

| 方法 | 路径 | 参数 | 返回 data | 说明 |
| --- | --- | --- | --- | --- |
| `GET` | `/memory/metrics` | 无 | `Record<string,FarmMetricDefinitionVo>` | 指标字典 |
| `GET` | `/memory/sync-policies` | 无 | `FarmSyncPolicyVo[]` | 同步策略列表 |
| `GET` | `/objects/:id/memory/sync-policy` | path: `id` | `FarmSyncPolicyVo` | 单对象同步策略 |
| `GET` | `/objects/:id/memory/latest` | query: `metric?` | `FarmLatestResponseVo` | 最新指标值 |
| `GET` | `/objects/:id/memory/timeseries` | query: `range=24h`, `metric?`, `limit?` | `TimeSeriesResponseVo` | 时序数据 |
| `GET` | `/objects/:id/memory/events` | query: `range=24h`, `eventType?`, `limit?` | `EventQueryResponseVo` | 事件记忆 |
| `GET` | `/objects/:id/memory/daily-archives` | query: `days=7` | `FarmDailyArchivesResponseVo` | 日归档 |
| `GET` | `/objects/:id/memory/report-source` | query: `date?` | `GreenhouseReportSourceVo` | 日报/报告数据源 |

指标 key：

```text
temperature, humidity, soilMoisture, co2, lightIntensity,
ph, ec, waterPressure, flow, switchState
```

别名兼容：

| 别名 | 归一化 key |
| --- | --- |
| `waterFlow` | `flow` |
| `status` | `switchState` |

时序查询示例：

```http
GET /sceneApi/objects/gh-tomato-001/memory/timeseries?range=24h&metric=temperature&metric=humidity&limit=200
```

报告数据源日期格式：

```text
YYYY-MM-DD
```

### 3.7 IoT 设备与告警 `/iot`

| 方法 | 路径 | 参数/Body | 返回 data | 说明 |
| --- | --- | --- | --- | --- |
| `GET` | `/iot/devices` | 无 | `IotDevice[]` | 设备列表 |
| `GET` | `/iot/devices/:deviceId` | path: `deviceId` | `IotDevice` | 设备详情 |
| `POST` | `/iot/devices` | `IotDevice` | `IotDevice` | 创建设备 |
| `PUT` | `/iot/devices/:deviceId` | `IotDevice` | `IotDevice` | 更新设备 |
| `DELETE` | `/iot/devices/:deviceId` | path: `deviceId` | `"deleted"` | 删除设备 |
| `GET` | `/iot/devices/:deviceId/data` | query: `limit=100` | `IotDataPoint[]` | 设备数据 |
| `GET` | `/iot/devices/:deviceId/metrics/:metricKey` | query: `limit=100` | `IotDataPoint[]` | 单指标数据 |
| `POST` | `/iot/devices/:deviceId/bind/:modelId` | path 参数 | `"bound"` | 绑定设备与模型 |
| `GET` | `/iot/alerts` | query: `limit=50` | `AlertLog[]` | 最近告警 |
| `GET` | `/iot/alerts/unacked-count` | 无 | `{count:number}` | 未确认告警数 |
| `PUT` | `/iot/alerts/:alertId/acknowledge` | path: `alertId` | `"acknowledged"` | 确认告警 |
| `GET` | `/iot/simulator/devices` | 无 | 模拟器设备列表 | 获取模拟设备 |
| `GET` | `/iot/ws` | WebSocket | 推送消息 | IoT 实时数据 |

`IotDevice`：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `deviceId` | string | 设备 ID |
| `deviceName` | string | 设备名 |
| `deviceType` | string | 设备类型 |
| `modelId` | number/null | 绑定模型 ID |
| `position` | string | JSON 字符串形式的位置 |
| `mqttTopic` | string | MQTT Topic |
| `status` | string | `online`、`offline`、`warning`、`critical` 等 |
| `lastDataTime` | string/null | 最后数据时间 |
| `config` | string | JSON 字符串配置 |
| `createdAt` | string | 创建时间 |

IoT WebSocket 推送示例：

```json
{
  "type": "iotData",
  "deviceId": "sensor-greenhouse-001",
  "timestamp": 1710000000000,
  "metrics": {
    "temperature": 26.5,
    "humidity": 64.2
  }
}
```

告警推送示例：

```json
{
  "type": "alert",
  "id": 12,
  "deviceId": "sensor-greenhouse-001",
  "severity": "warning",
  "alertType": "threshold",
  "message": "温度超过阈值",
  "acknowledged": false,
  "createdAt": "2026-05-26T10:00:00+08:00"
}
```

### 3.8 监控中心 `/monitor`

| 方法 | 路径 | 返回 data | 说明 |
| --- | --- | --- | --- |
| `GET` | `/monitor/dashboard` | `MonitorDashboardVo` | 园区概览、关键指标、设备状态、能耗、产量、环境、告警、实时指标 |

核心返回结构：

```json
{
  "updatedAt": "2026-05-26T10:00:00+08:00",
  "overview": {},
  "keyMetrics": [],
  "deviceStatus": [],
  "energy": {},
  "yieldAnalysis": {},
  "environment": {},
  "recentAlerts": [],
  "realtimeMetrics": []
}
```

### 3.9 业务中心 `/business`

| 方法 | 路径 | 返回 data | 说明 |
| --- | --- | --- | --- |
| `GET` | `/business/overview` | `BusinessOverviewVo` | 聚合土壤墒情、气象、水肥灌溉、大棚控制、视频监控、环境监测等子系统 |

子系统状态字段：

| 字段 | 取值 |
| --- | --- |
| `status` | `normal`、`warning`、`critical` |
| `implementationLevel` | `ready`、`partial`、`missing` |
| `metric.status` | `normal`、`warning`、`critical`、`missing` |

### 3.10 AI 助手 `/assistant`

| 方法 | 路径 | 参数/Body | 返回 data | 说明 |
| --- | --- | --- | --- | --- |
| `POST` | `/assistant/chat` | `AssistantChatRequest` | `AssistantChatResponse` | 基于只读工具回答问题 |
| `GET` | `/assistant/tools` | 无 | `AssistantToolVo[]` | 助手可用工具 |
| `GET` | `/assistant/context/summary` | 无 | `AssistantContextSummaryVo` | 模型、场景、IoT、告警、业务摘要 |
| `GET` | `/assistant/rag/status` | 无 | `AssistantRAGStatusVo` | RAG 预留状态 |

聊天请求：

```json
{
  "message": "查看番茄温室最近 24 小时温湿度和告警",
  "sessionId": "session-001",
  "context": {
    "sceneName": "番茄温室 MVP"
  }
}
```

聊天返回：

```json
{
  "sessionId": "session-001",
  "answer": "当前温室环境整体正常...",
  "toolCalls": [
    {
      "name": "timeseries.query",
      "label": "时序查询",
      "status": "success",
      "durationMs": 12,
      "summary": "读取 gh-tomato-001 24h temperature/humidity"
    }
  ],
  "citations": [],
  "ragUsed": false
}
```

### 3.11 语义搭建 `/semantic`

| 方法 | 路径 | 参数/Body | 返回 data | 说明 |
| --- | --- | --- | --- | --- |
| `POST` | `/semantic/build/plan` | `SemanticBuildRequest` | `SemanticBuildResponse` | 根据自然语言生成场景计划与模型放置清单 |
| `GET` | `/semantic/assets` | 无 | `AssetSemantic[]` | 语义资产表 |
| `GET` | `/semantic/samples` | 无 | `BuildSampleVo[]` | 演示输入样例 |

语义搭建请求：

```json
{
  "message": "搭建番茄温室，包含 20 株番茄、气象站、水泵、摄像头和传感器",
  "sceneName": "番茄温室 MVP",
  "mode": "preview",
  "ownerKey": "anonymous",
  "context": {
    "sceneName": "番茄温室 MVP",
    "appendMode": false,
    "sceneSummary": {
      "objectCount": 0,
      "modelCount": 0
    },
    "existingObjects": []
  }
}
```

核心返回字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `scenePlan` | object | 场景意图、地面、对象、关系 |
| `models` | array | 可直接加载到前端 Three.js 场景的模型列表 |
| `missingAssets` | array | 缺失资产、占位模型、生成任务建议 |
| `samples` | array | 示例 prompt |
| `planSource` | object | `rule` 或 `llm` 来源说明 |
| `visualTemplate` | object | 番茄温室等视觉模板约束 |
| `agentTrace` | object | FarmTwinOrchestrator 与各专业 Agent 步骤 |

`BuildModel` 示例：

```json
{
  "url": "/scene-assets/models/Tomato_Crop.glb",
  "options": {
    "offset": { "x": 1.2, "y": 0, "z": 3.4 },
    "scale": 1,
    "angle": 0
  },
  "meta": {
    "id": "tomato-001",
    "label": "番茄种植区",
    "assetKey": "tomato",
    "category": "crop",
    "area": "greenhouse",
    "layout": "grid"
  }
}
```

`agentTrace.steps` 工具类别：

| 类别 | 说明 |
| --- | --- |
| `read-only` | 只读查询，例如对象、时序、事件 |
| `controlled-write` | 受控写入合约，例如预览模式的绑定或生成任务 |
| `prohibited` | 禁止工具，例如 shell、文件写入、任意 HTTP、直接数据库写、真实设备控制 |

### 3.12 AI 资产生成与资产治理 `/asset`

| 方法 | 路径 | 参数/Body | 返回 data | 说明 |
| --- | --- | --- | --- | --- |
| `POST` | `/asset/jobs` | `AssetJobRequest` | `AssetJobResponse` | 创建 TRELLIS.2 资产生成任务 |
| `GET` | `/asset/jobs/:id` | path: `id` | `AssetJobResponse` | 查询生成任务，并同步 TRELLIS.2 状态 |
| `GET` | `/asset/jobs` | query: `ownerKey=anonymous` | `AssetJobResponse[]` | 用户任务列表 |
| `POST` | `/asset/jobs/:id/approve` | `AssetApproveRequest?` | `"approved"` | 审核通过并加入模型库 |
| `POST` | `/asset/jobs/:id/reject` | path: `id` | `"rejected"` | 驳回任务 |
| `GET` | `/asset/metadata` | 无 | `AssetMetadataVo[]` | 资产元数据注册表 |
| `GET` | `/asset/metadata/:assetKey` | path: `assetKey` | `AssetMetadataVo` | 单资产元数据 |
| `GET` | `/asset/audit` | query: `assetKey?` | `AssetQualityAuditReportVo` 或数组 | 资产质量审计 |
| `POST` | `/asset/routing/decide` | `AssetFidelityRoutingRequest` | `AssetFidelityRoutingDecisionVo` | 资产保真度路由决策 |
| `GET` | `/asset/plant-geometry/:objectId` | path: `objectId` | `PlantGeometryVersionVo[]` | 植株几何版本 |

创建任务请求：

```json
{
  "imageBase64": "<base64 without data:image prefix>",
  "imageFileName": "camera-reference.png",
  "ownerKey": "anonymous",
  "assetKey": "camera",
  "assetName": "摄像头",
  "prompt": "生成适合番茄温室的监控摄像头 GLB 模型",
  "referenceImageSource": "upload",
  "resolution": 512,
  "decimationTarget": 300000,
  "textureSize": 2048
}
```

任务状态：

```text
queued, running, completed, failed, approved, rejected
```

后端与 TRELLIS.2 的联动：

1. 前端调用 `POST /sceneApi/asset/jobs`，上传 base64 图片。
2. Go 后端解码图片，使用 multipart/form-data 转发到 `http://127.0.0.1:9020/generate`。
3. TRELLIS.2 返回 `job_id`，Go 后端将任务写入 `asset_jobs`。
4. 前端轮询 `GET /sceneApi/asset/jobs/:id`。
5. Go 后端轮询 `GET http://127.0.0.1:9020/status/:job_id`。
6. 完成后模型路径为 `/scene-assets/models/<job_id>.glb`，缩略图为 `/scene-assets/thumbs/<job_id>.jpg`。

资产路由请求：

```json
{
  "assetKey": "camera",
  "objectType": "Camera",
  "businessValue": "safety_monitoring",
  "requiredFidelity": "high",
  "isKeyPlant": false,
  "isAbnormalPlant": false,
  "isResearchSample": false,
  "maxWaitMinutes": 30
}
```

资产路由返回关键字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `strategy` | string | `existing_asset`、`TRELLIS.2`、`procedural`、`placeholder` 等 |
| `selectedAssetKey` | string | 命中的资产 key |
| `selectedUrl` | string | 可直接加载的模型 URL |
| `requiresGenerationTask` | boolean | 是否需要生成任务 |
| `placeholderAssetKey` | string | 缺失资产的占位模型 |
| `routingReason` | string | 路由原因 |

### 3.13 综合验收 `/acceptance`

| 方法 | 路径 | 返回 data | 说明 |
| --- | --- | --- | --- |
| `GET` | `/acceptance/tomato-greenhouse` | `TomatoGreenhouseAcceptanceVo` | 番茄温室 Phase 6 综合验收聚合 |

固定验收 prompt：

```text
搭建番茄温室，包含 20 株番茄、气象站、水泵、摄像头和传感器
```

返回包含：

| 字段 | 说明 |
| --- | --- |
| `overallPassed` | 总体验收是否通过 |
| `modelCounts` | greenhouse、tomato、weather_station、irrigation、camera、sensor 等数量核验 |
| `steps` | 分阶段验收步骤 |
| `successMetrics` | 成功指标 |
| `issues` | 问题清单 |
| `semanticBuild` | 语义搭建结果、缺失资产、Agent trace |
| `bindingValidation` | 场景业务绑定验证 |
| `greenhouseContext` | 温室对象关系 |
| `abnormalContext` | 异常设备记忆上下文 |
| `reportSource` | 日报数据源 |
| `archiveReadiness` | OpenSpec 归档准备度 |

### 3.14 管理接口 `/admin`

| 方法 | 路径 | 返回 data | 说明 |
| --- | --- | --- | --- |
| `POST` | `/admin/import-models` | `{imported:number}` | 扫描 `scene-assets/import/` 下 GLB 并入库 |
| `GET` | `/admin/stats` | 统计对象 | 模型总数、叶子节点、目录、分类统计 |

## 4. TRELLIS.2 FastAPI 服务

服务文件：`TRELLIS.2/service/trellis2_service.py`  
启动示例：

```bash
cd /data/fj/数字孪生/TRELLIS.2/service
PY_SSIZE_T_CLEAN=1 CUDA_VISIBLE_DEVICES=1 python trellis2_service.py
```

默认配置：

| 配置 | 值 |
| --- | --- |
| Host | `0.0.0.0` |
| Port | `9020` |
| 权重路径 | `TRELLIS.2/TRELLIS.2-4B` |
| 输出模型目录 | `/data/fj/数字孪生/digital-twingo/scene-server-go/scene-assets/models` |
| 输出缩略图目录 | `/data/fj/数字孪生/digital-twingo/scene-server-go/scene-assets/thumbs` |
| 任务模式 | 单 worker 队列，逐个处理 |

### 4.1 健康检查

```http
GET /health
```

返回：

```json
{
  "status": "ok",
  "pipeline_loaded": true
}
```

### 4.2 创建 3D 生成任务

```http
POST /generate
Content-Type: multipart/form-data
```

表单字段：

| 字段 | 类型 | 必填 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| `image` | file | 是 | 无 | 输入参考图 |
| `resolution` | int | 否 | `512` | 仅支持 `512`、`1024`、`1536` |
| `decimation_target` | int | 否 | `300000` | 导出 GLB 网格简化目标 |
| `texture_size` | int | 否 | `2048` | 纹理尺寸 |

请求示例：

```bash
curl -X POST http://127.0.0.1:9020/generate \
  -F "image=@camera-reference.png" \
  -F "resolution=512" \
  -F "decimation_target=300000" \
  -F "texture_size=2048"
```

返回：

```json
{
  "job_id": "a1b2c3d4e5f6",
  "status": "queued",
  "queue_position": 1
}
```

### 4.3 查询任务状态

```http
GET /status/{job_id}
```

排队或运行中：

```json
{
  "job_id": "a1b2c3d4e5f6",
  "status": "running",
  "progress": 80,
  "queue_position": 0
}
```

完成：

```json
{
  "job_id": "a1b2c3d4e5f6",
  "status": "completed",
  "progress": 100,
  "result": {
    "glb_url": "/scene-assets/models/a1b2c3d4e5f6.glb",
    "thumb_url": "/scene-assets/thumbs/a1b2c3d4e5f6.jpg",
    "file_size": 12345678
  }
}
```

失败：

```json
{
  "job_id": "a1b2c3d4e5f6",
  "status": "failed",
  "progress": 0,
  "error": "error message"
}
```

### 4.4 任务列表

```http
GET /jobs
```

返回：

```json
{
  "jobs": [
    {
      "job_id": "a1b2c3d4e5f6",
      "status": "completed",
      "progress": 100,
      "created_at": 1710000000.0,
      "resolution": 512
    }
  ]
}
```

### 4.5 TRELLIS.2 与平台约束

| 约束 | 说明 |
| --- | --- |
| GPU | 服务启动时加载 TRELLIS.2 pipeline，依赖 CUDA |
| 队列 | 当前实现为单 worker，适合 MVP 和单卡环境 |
| 输出 | GLB 与缩略图直接写入后端 `scene-assets`，由 Go 静态服务暴露 |
| 错误 | FastAPI 使用 HTTP 状态码；Go 后端会转换为 `ResultVo{code:999,data:"..."}` |
| 生产化建议 | 增加鉴权、任务持久化、队列长度限制、文件大小限制、GPU 资源监控 |

## 5. 端到端调用流程

### 5.1 打开并加载场景

1. 前端访问 `/scene/`。
2. 调用 `GET /sceneApi/scene/defaultScene` 获取默认场景。
3. 调用 `GET /sceneApi/scene/loadScene?scene=<sceneName>` 加载场景配置。
4. 对返回的 `modelList` 逐个加载 `url` 指向的 GLB。
5. 如需对象详情，按模型 `sceneObjectId` 调用 `/scene/bindings/by-scene-object`。

### 5.2 语义生成番茄温室

1. 前端提交 prompt 到 `POST /sceneApi/semantic/build/plan`。
2. 后端生成 `scenePlan`、`models`、`missingAssets`、`agentTrace`。
3. 前端根据 `models` 加载 GLB。
4. 缺失摄像头、传感器等资产时，前端展示 `missingAssets[].generation` 和占位模型。
5. 用户可上传参考图，调用 `POST /sceneApi/asset/jobs` 创建 TRELLIS.2 生成任务。
6. 任务完成后，通过 `/scene-assets/models/<job_id>.glb` 加载新资产。

### 5.3 对象记忆与日报

1. 点选 3D 模型得到 `sceneObjectId`。
2. 调用 `/scene/bindings/by-scene-object` 得到 `businessObjectId`。
3. 调用 `/objects/:id` 与 `/objects/:id/relations` 获取业务上下文。
4. 调用 `/objects/:id/memory/latest`、`/timeseries`、`/events` 展示最新值、曲线与事件。
5. 调用 `/objects/:id/memory/report-source` 生成日报数据源。

### 5.4 IoT 实时数据

1. 前端启动时连接 `ws://<host>/sceneApi/iot/ws`。
2. 后端 IoT simulator 或 MQTT adapter 写入设备数据。
3. WebSocket 推送 `iotData` 更新设备实时指标。
4. 阈值触发时推送 `alert`，前端同步告警列表。
5. 用户通过 `PUT /sceneApi/iot/alerts/:alertId/acknowledge` 确认告警。

## 6. Swagger 维护说明

后端已集成 swaggo：

```bash
cd /data/fj/数字孪生/digital-twingo/scene-server-go
go install github.com/swaggo/swag/cmd/swag@latest
swag init -g SceneServerApplication.go
```

启动后端时，如果系统存在 `swag` CLI，会自动生成：

```text
digital-twingo/scene-server-go/docs/docs.go
digital-twingo/scene-server-go/docs/swagger.json
digital-twingo/scene-server-go/docs/swagger.yaml
```

建议后续补充：

| 优先级 | 项目 | 说明 |
| --- | --- | --- |
| 高 | 为新增 Phase 1-6 接口补齐 swag 注解 | 当前部分新接口没有完整 `@Summary`、`@Param`、`@Success` |
| 高 | 为 VO 增加稳定示例 | 方便 Swagger UI 展示请求/响应 |
| 中 | 为 WebSocket 写独立协议文档 | Swagger 2.0 对 WebSocket 支持有限 |
| 中 | 为 TRELLIS.2 导出 OpenAPI JSON | FastAPI 原生支持 `/openapi.json` 与 `/docs` |
| 低 | 统一错误码枚举 | 将 `400`、`404`、`500`、`999` 含义固化 |

## 7. 快速联调命令

后端：

```bash
cd /data/fj/数字孪生/digital-twingo/scene-server-go
go run SceneServerApplication.go
```

前端：

```bash
cd /data/fj/数字孪生/digital-twingo/scene-design-v2
npm run serve
```

TRELLIS.2：

```bash
cd /data/fj/数字孪生/TRELLIS.2/service
PY_SSIZE_T_CLEAN=1 CUDA_VISIBLE_DEVICES=1 python trellis2_service.py
```

API smoke check：

```bash
curl http://127.0.0.1:9010/sceneApi/acceptance/tomato-greenhouse
curl http://127.0.0.1:9010/sceneApi/semantic/samples
curl http://127.0.0.1:9020/health
```
