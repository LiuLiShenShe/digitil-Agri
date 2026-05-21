# 第 4 周：接 TRELLIS.2 缺失资产闭环

## 1. 本周目标

第 2 周的 LLM 语义解析和第 3 周的 Eino DeepAgents 编排已经完成，本周不再重新做语义解析和 Agent 骨架，而是接在现有链路后面，把“缺模型就提示失败”升级成“缺模型就进入补资产闭环”。

本周的核心目标是：

- `SceneBuilderAgent` 已经能输出 `missingAssets[]` 时，自动创建资产补齐任务。
- TRELLIS.2 只负责“图片到 3D 资产”，不直接参与语义规划。
- 系统先解决 TRELLIS.2 的输入图片来源，再提交生成任务。
- 生成完成后把 GLB 回写个人模型库或待审核库。
- 前端能显示占位资产、生成进度、失败原因和一键替换入口。

最终效果是：用户说“搭一个农业园区，入口放摄像头”，如果摄像头没有可用 GLB，场景仍然能先搭起来，摄像头位置先用占位模型显示，同时后台创建摄像头补资产任务；任务完成后，用户可以把占位模型替换成新生成的 GLB。

## 2. 当前基础

从第 2 周截图可以看到，当前 AI 搭建面板已经具备这些能力：

- 能展示 LLM 解析来源和对象组数量。
- 能展示“可加载模型”和“缺失资产”数量。
- 能把“摄像头”列入缺失资产。
- 能提示“mock 语义表已识别该资产，但当前模型库没有可用 GLB”。

第 3 周完成后，后端已经具备：

- `SceneBuilderAgent` 调度语义规划、资产检索、布局求解和校验。
- 工具白名单和调用日志。
- 前端契约保持 `scenePlan / models / warnings / missingAssets`。

因此第 4 周的改造点不是重新识别缺失资产，而是把 `missingAssets[]` 从“展示信息”变成“可执行任务”。

## 3. 关键结论：TRELLIS.2 的图片怎么获取

TRELLIS.2 补资产需要图片作为输入，所以不能只把 `missingAssets.prompt` 直接交给 TRELLIS.2。平台需要在创建 TRELLIS.2 任务前增加一个“参考图获取”步骤。

图片来源按优先级分为 5 类：

1. 用户上传参考图
   - 最推荐，质量和意图最稳定。
   - 在缺失资产卡片上提供“上传参考图”入口。
   - 适合定制设备、园区专用设施、真实品牌设备。

2. 业务素材库图片
   - 从设备目录、产品库、物联网设备台账、已有 2D 图标或缩略图中取图。
   - 例如“摄像头”可以优先找设备类型表里的 `image_url`、`thumbnail_url` 或后台预置的安防摄像头参考图。
   - 适合摄像头、传感器、水泵、阀门、无人机、配电箱、灌溉设备等常见资产。

3. 管理员预置参考图库
   - 为高频缺失资产维护一套标准参考图。
   - 例如：`camera.ptz`、`camera.bullet`、`greenhouse.glass`、`sensor.soil`、`irrigation.valve`。
   - 适合先把 MVP 跑通，避免每次都要求用户上传。

4. 图像生成服务先生成参考图
   - 如果没有用户上传，也没有业务素材库图片，可以先用文本提示词生成一张 2D 参考图，再把这张图交给 TRELLIS.2。
   - 这是“文本到图，再图到 3D”的两段式补资产。
   - 需要额外接入图片生成模型，且要把生成图也保存为任务输入，方便追溯。

5. 当前场景截图或占位模型截图
   - 只能作为兜底，不建议作为主要来源。
   - 占位模型通常不够准确，容易把错误形态传给 TRELLIS.2。
   - 更适合做生成完成后的对比图，而不是输入图。

本周建议采用“业务素材库 / 管理员预置参考图库 + 用户上传”作为 MVP。图像生成服务可以作为第 4 周增强项，不阻塞主闭环。

## 4. 本周范围

- 扩展 `missingAssets[]` 字段，补充参考图状态。
- 新增参考图获取器 `ReferenceImageResolver`。
- 新增资产生成任务表和任务状态机。
- 新增 TRELLIS.2 worker，对接外部推理服务。
- 新增任务查询、上传参考图、重试、替换占位模型接口。
- 前端在 AI 搭建面板展示缺失资产补齐状态。
- 生成完成后回写个人模型库或待审核库。

不做：

- 不把 TRELLIS.2 放进主 Agent 的自由工具调用里。
- 不允许 Agent 任意访问外网找图。
- 不保证所有资产自动生成成功。
- 不让未审核资产直接进入公共模型库。

## 5. 数据结构设计

### 5.1 扩展 `missingAssets[]`

建议把第 2 周已有的 `missingAssets[]` 从展示字段扩展为可创建任务的结构：

```json
{
  "assetKey": "camera.ptz",
  "assetName": "摄像头",
  "category": "security",
  "reason": "mock 语义表已识别该资产，但当前模型库没有可用 GLB",
  "prompt": "农业园区入口处使用的白色云台摄像头，工业设备风格，适合数字孪生场景",
  "fallbackModelKey": "placeholder.device",
  "placementRefs": ["sceneObject_001"],
  "referenceImage": {
    "status": "missing",
    "source": null,
    "url": null,
    "candidates": []
  },
  "generation": {
    "enabled": true,
    "taskId": null,
    "status": "not_created"
  }
}
```

关键字段说明：

- `assetKey`：缺失资产的稳定标识，后续用它做查重和入库。
- `prompt`：给参考图生成或 TRELLIS.2 任务记录使用，不直接替代图片输入。
- `placementRefs`：哪些场景对象正在等待这个资产。
- `referenceImage.status`：`missing / resolved / uploaded / generated / rejected`。
- `generation.status`：`not_created / waiting_image / queued / running / completed / failed / cancelled`。

### 5.2 新增资产生成任务表

建议新增 `asset_generation_tasks`：

| 字段 | 说明 |
| --- | --- |
| `id` | 任务 ID |
| `user_id` | 所属用户 |
| `scene_id` | 来源场景 |
| `asset_key` | 缺失资产标识 |
| `asset_name` | 展示名称 |
| `category` | 资产分类 |
| `prompt` | 生成提示词 |
| `reference_image_url` | TRELLIS.2 输入图 |
| `reference_image_source` | `upload / catalog / preset / generated / scene_capture` |
| `status` | `waiting_image / queued / running / completed / failed / cancelled` |
| `progress` | 0-100 |
| `result_glb_url` | 生成结果 |
| `result_thumbnail_url` | 缩略图 |
| `result_asset_id` | 入库后的模型 ID |
| `error_code` | 失败码 |
| `error_message` | 失败原因 |
| `review_status` | `personal_draft / pending_review / approved / rejected` |
| `created_at` | 创建时间 |
| `updated_at` | 更新时间 |

### 5.3 参考图候选表

如果业务素材库和预置图库会返回多个候选，建议新增 `asset_reference_images`：

| 字段 | 说明 |
| --- | --- |
| `id` | 候选图 ID |
| `asset_key` | 对应资产 |
| `source` | `catalog / preset / generated / upload` |
| `url` | 图片 URL |
| `score` | 匹配分 |
| `license_status` | 授权状态 |
| `created_by` | 上传人或系统 |
| `approved` | 是否可用于生成 |

这样可以避免从公网随便拿图导致版权和来源不可追溯。

## 6. 后端实施任务

### 6.1 新增 `ReferenceImageResolver`

职责：给每个 `missingAsset` 找到可用于 TRELLIS.2 的参考图。

处理顺序：

1. 查用户是否已经为该缺失资产上传参考图。
2. 查设备目录或业务素材库是否有匹配图片。
3. 查管理员预置参考图库。
4. 如果开启图片生成能力，则创建参考图生成任务。
5. 如果仍然没有图片，把资产任务置为 `waiting_image`。

输出结构：

```json
{
  "status": "resolved",
  "source": "preset",
  "url": "https://assets.example.com/reference/camera-ptz.png",
  "candidates": [
    {
      "id": "ref_001",
      "source": "preset",
      "url": "https://assets.example.com/reference/camera-ptz.png",
      "score": 0.92
    }
  ]
}
```

### 6.2 创建资产生成任务

在 `SceneBuilderAgent` 返回结果后，不让 Agent 直接调用 TRELLIS.2，而是由业务服务读取 `missingAssets[]` 并创建任务：

1. 对 `missingAssets[]` 按 `assetKey` 去重。
2. 调用 `ReferenceImageResolver`。
3. 有参考图则创建 `queued` 任务。
4. 无参考图则创建 `waiting_image` 任务。
5. 把任务 ID 回写给前端结果。

这样 Agent 仍然只负责规划和判断，生成服务负责异步执行。

### 6.3 TRELLIS.2 worker

worker 独立部署，避免阻塞主业务接口。

流程：

1. 领取 `queued` 任务。
2. 校验 `reference_image_url` 是否存在、可访问、格式合法。
3. 调用 TRELLIS.2 推理服务。
4. 获取 GLB 或中间结果。
5. 生成缩略图和基础元数据。
6. 上传 GLB、缩略图和输入参考图快照。
7. 创建个人模型库资产记录。
8. 回写任务为 `completed`。
9. 通知前端刷新，或等待前端轮询。

失败时：

- 输入图不可访问：`failed_input_image_unavailable`
- 推理服务超时：`failed_trellis_timeout`
- 生成结果为空：`failed_empty_result`
- GLB 校验失败：`failed_invalid_glb`
- 上传失败：`failed_upload`

### 6.4 入库和审核

生成结果不要直接进入公共模型库。

推荐状态：

1. `personal_draft`：生成成功后先进入用户个人草稿库。
2. `pending_review`：用户确认质量后提交审核。
3. `approved`：管理员审核后进入公共模型库。
4. `rejected`：管理员拒绝，保留个人可见或删除。

MVP 可以先做 `personal_draft`，公共审核放到后续迭代。

## 7. 接口设计

### 7.1 查询缺失资产任务

`GET /api/asset-generation/tasks?sceneId=xxx`

返回当前场景所有补资产任务。

### 7.2 上传参考图

`POST /api/asset-generation/tasks/{taskId}/reference-image`

用途：

- 用户给 `waiting_image` 任务补图。
- 用户替换系统自动匹配的参考图。

上传成功后：

- `reference_image_source = upload`
- `status = queued`
- 进入 worker 队列

### 7.3 重试任务

`POST /api/asset-generation/tasks/{taskId}/retry`

规则：

- 只有 `failed` 和 `cancelled` 可重试。
- 如果失败原因是缺少输入图，重试后仍然进入 `waiting_image`。
- 如果已有有效参考图，重试后进入 `queued`。

### 7.4 替换占位模型

`POST /api/scenes/{sceneId}/objects/{objectId}/replace-asset`

请求体：

```json
{
  "assetId": "asset_generated_001",
  "taskId": "task_001",
  "keepTransform": true
}
```

替换时保留：

- `position`
- `rotation`
- `scale`，必要时按新模型包围盒自动归一化
- 原对象业务属性，例如设备绑定、告警配置、IoT 点位

## 8. 前端改造

### 8.1 AI 搭建面板

在现有“缺失资产”卡片里增加：

- 参考图状态：未找到 / 已匹配 / 用户上传 / 生成中。
- 任务状态：待补图 / 排队中 / 生成中 / 已完成 / 失败。
- 操作按钮：上传参考图、查看候选图、重新生成、替换占位模型。

对于当前截图里的“摄像头”卡片，理想展示为：

- 缺失资产：摄像头
- 参考图：已使用预置图库 `camera.ptz`
- 生成状态：排队中
- 场景占位：入口南侧摄像头位置

如果没有参考图，则展示：

- 状态：待补参考图
- 操作：上传图片
- 提示：TRELLIS.2 需要一张清晰的单物体参考图才能生成 3D 模型

### 8.2 场景画布

占位模型需要带上补资产状态：

- `waiting_image`：灰色占位设备，标记“待补图”。
- `queued / running`：保留占位，显示生成中状态。
- `completed`：提示可替换。
- `failed`：保留占位，提供重试入口。

不要在生成完成后自动替换所有场景对象，除非用户开启自动替换。第一版建议由用户确认替换，避免生成质量不稳定影响场景。

### 8.3 模型库

新增个人生成资产分组：

- 生成中
- 生成成功
- 待审核
- 失败

生成成功的资产可以被当前用户复用，管理员审核后再进入公共库。

## 9. 推荐实现顺序

1. 扩展 `missingAssets[]` 返回结构，前端先能展示任务状态。
2. 建 `asset_generation_tasks` 表和基础 CRUD。
3. 实现 `ReferenceImageResolver`，先接预置参考图库。
4. 给“摄像头”准备一张管理员预置参考图，跑通第一个真实任务。
5. 实现 TRELLIS.2 worker 的任务领取和状态回写。
6. 实现上传参考图接口，解决没有预置图的资产。
7. 实现 GLB 入个人模型库。
8. 实现场景对象替换占位模型。
9. 增加失败重试和错误展示。
10. 增加审核流和公共模型库发布。

## 10. 验收场景

### 10.1 摄像头缺失资产闭环

输入：

> 搭一个农业示范园区，在入口放一个摄像头。

期望：

- `SceneBuilderAgent` 输出摄像头对象和 `missingAssets[]`。
- 系统从预置参考图库找到摄像头图片。
- 自动创建 TRELLIS.2 任务。
- 前端显示摄像头占位模型和“生成中”状态。
- worker 生成 GLB 后写入个人模型库。
- 用户点击“替换”，摄像头占位模型被新 GLB 替换。
- 场景可以保存。

### 10.2 无参考图的定制资产

输入：

> 在园区中心放一个自定义农业机器人。

期望：

- 系统识别缺失资产。
- 找不到业务素材和预置参考图。
- 创建 `waiting_image` 任务。
- 前端提示用户上传参考图。
- 用户上传图片后任务进入 `queued`。

### 10.3 生成失败重试

期望：

- worker 失败后记录 `error_code` 和 `error_message`。
- 前端展示失败原因。
- 用户可以重新上传参考图或点击重试。
- 重试不会重复创建无关资产记录。

## 11. 产出物

- 扩展后的 `missingAssets[]` 协议。
- `ReferenceImageResolver`。
- `asset_generation_tasks` 表。
- 可选的 `asset_reference_images` 表。
- TRELLIS.2 worker。
- 上传参考图、查询任务、重试任务、替换占位模型接口。
- AI 搭建面板里的缺失资产任务状态。
- 个人模型库入库流程。

## 12. 风险与处理

- 风险：TRELLIS.2 只能吃图片，LLM 只有文本提示词。  
  处理：增加 `ReferenceImageResolver`，先拿到参考图，再创建 TRELLIS.2 任务。

- 风险：自动找图有版权和来源问题。  
  处理：只使用用户上传、业务素材库、管理员预置图库和可追溯的生成图，不默认抓公网图片。

- 风险：生成时间长。  
  处理：任务异步化，前端轮询或订阅任务状态。

- 风险：生成质量波动。  
  处理：先进入个人模型库，用户确认后替换；公共库必须审核。

- 风险：GPU 环境不稳定。  
  处理：保留失败重试、错误码、占位模型和人工上传 GLB 兜底。

## 13. 本周完成判定

本周不要求 TRELLIS.2 生成的所有模型都能达到生产质量，但必须完成端到端闭环：

- 第 2 周已有的“摄像头缺失资产”能自动变成补资产任务。
- 有参考图时能进入 TRELLIS.2 生成队列。
- 没有参考图时能进入 `waiting_image`，并允许用户上传。
- 任务状态能在前端看到。
- 生成成功后能入个人模型库。
- 场景里的占位模型能被生成资产替换。

我可以完成任务表、接口、状态流转、前端闭环和 worker 对接代码。TRELLIS.2 的真实生成还需要你提供 GPU 环境、模型权重和可用的推理服务地址。
