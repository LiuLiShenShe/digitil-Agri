# TRELLIS.2 生成 GLB 资产入库方案

## Summary
- 方案可行：当前项目已经用 `model.url -> GLTFLoader -> scene.saveModel()` 作为模型引用链路，TRELLIS.2 可直接产出 GLB，能自然接入现有模型库。
- 首版采用“主 Go 服务管资产和任务、独立 Python/GPU 服务只做生成”的架构；普通用户可生成个人待审模型，管理员可生成并直接入库/审核公开。
- 依据：TRELLIS.2 官方要求 Linux + NVIDIA GPU + 至少 24GB 显存，MIT 许可，可导出 PBR GLB；Three.js `GLTFLoader` 支持常见 glTF/PBR/WebP 扩展。参考：https://github.com/microsoft/TRELLIS.2 、https://huggingface.co/microsoft/TRELLIS.2-4B 、https://threejs.org/docs/pages/GLTFLoader.html

## Key Changes
- 新增资产任务流：前端上传单图到 Go 服务，Go 写入任务表和源图文件；GPU 服务轮询任务、调用 TRELLIS.2 生成 GLB、上传结果回 Go 服务；前端轮询任务状态并展示预览。
- 模型库扩展：保留现有 `model` 树结构，给生成资产增加 `status/ownerKey/thumbUrl/sourceImageUrl/source/createdAt/fileSize` 等字段；现有场景保存仍只保存 `url/options`，不改 `scenemodel` 主流程。
- 静态资产存储：生成文件存到主服务本地目录，由 Go 暴露静态路径，例如 `/scene-assets/models/{assetId}.glb`、`/scene-assets/thumbs/{assetId}.jpg`，模型表 `url` 使用该可访问地址。
- 前端入口：在模型选择弹窗增加“AI生成”入口和任务列表；普通用户看到“我的生成/待审/已公开”，管理员模式由新配置开关控制，可审核、重命名、分类、公开或驳回。
- TRELLIS 默认参数：MVP 默认 `resolution=512`、`decimation_target=300000`、`texture_size=2048`；管理员可重试高质量 `1024`，暂不开放 `1536` 给普通用户。

## Public Interfaces
- Go 服务新增接口：`POST /asset/jobs` 上传图片并创建生成任务；`GET /asset/jobs/:id` 查询状态；`GET /asset/jobs` 查询当前用户任务；`POST /asset/jobs/:id/approve` 管理员公开入库；`POST /asset/jobs/:id/reject` 驳回。
- GPU 服务与 Go 服务之间使用共享 token：`GET /asset/jobs/next` 领取任务，`POST /asset/jobs/:id/complete` 回传 GLB、缩略图、统计信息，`POST /asset/jobs/:id/fail` 回传失败原因。
- `/model/list` 保持兼容，默认返回公开模型；前端附带本地 `ownerKey` 时同时返回该用户个人待审/私有模型；旧字段 `id/parentid/name/url/leaf` 不变。

## Test Plan
- 用现有手工 GLB 验证旧模型库、打开场景、保存场景不回归。
- 上传一张带明确主体的 PNG/JPG，确认任务从 `queued -> running -> completed`，GLB 可在预览区加载并能放入场景。
- 验证普通用户生成资产默认仅自己可见，管理员审核后出现在公共模型树。
- 验证失败场景：GPU 服务离线、图片格式错误、生成超时、GLB 超过体积限制、Three.js 加载失败，都能显示可理解状态且不污染公共模型库。
- 用至少 10 个生成模型混入同一场景，检查加载时间、缩放适配、材质显示、保存后重新打开。

## Assumptions
- 首版不新增完整登录系统，用前端本地 `ownerKey` 标识普通用户，用配置开关标识管理员；这是 MVP 权限，不作为强安全边界。
- 资产审核采用“个人待审”：用户可预览和放置自己的生成模型，管理员审核后才进入公共模型库。
- 主服务本地磁盘是首版资产存储；后续模型数量变大时再迁移到 MinIO/对象存储。
- TRELLIS.2 只生成“内容物/单体资产”，不负责自动布置完整数字孪生场景；场景搭建仍由用户在当前编辑器中完成。
