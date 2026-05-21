## Why

平台已有农业 GLB 资产、前端 public models、后端 scene-assets 和 TRELLIS.2 任务入口，但资产治理不足。PRD 要求统一资产来源、补充缩略图、来源、许可、面数、贴图、体积、LOD、保真度和适用对象，并按业务价值选择已有资产、F2DMAS、TRELLIS.2、程序化生成或占位模型。

## What Changes

- 新增资产元数据规范，覆盖 assetKey、分类、来源、许可、保真度、缩略图、GLB 地址、适用对象、质量信息和版本信息。
- 新增资产入库验收要求：Three.js 可加载、坐标轴/单位/中心点正常、面数/贴图/体积在阈值内、有缩略图、有来源和许可。
- 新增多保真资产路由策略。
- 支持关键植株阶段性几何版本和表型数据绑定。
- 支持缺失资产不中断：占位模型 + 生成任务。

## Capabilities

### New Capabilities

- `asset-fidelity-routing`: 定义资产元数据、质量验收、多保真路由、缺失资产任务和关键植株几何版本能力。

### Modified Capabilities

暂无。

## Impact

- 影响资产库、模型检索、缩略图生成、资产任务、TRELLIS.2 入口、关键植株重建、场景搭建和 ValidatorAgent。
- 需要逐步统一前端 `public/models` 和后端 `scene-assets` 的资产来源。
- 为论文创新点“多保真农业 GLB 资产调度机制”提供工程规格。

