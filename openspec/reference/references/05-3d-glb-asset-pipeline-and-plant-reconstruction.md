# 3D/GLB 资产管线与植物重建参考

## 核心结论

当前项目的资产路线应采用“多保真资产池 + 智能调度”。高价值植株资产使用 F2DMAS 或其他高保真重建方法；普通设备、装饰、缺失资产可使用 TRELLIS.2 快速生成；地块、道路、围栏、作物行等可程序化生成；所有资产入库前都应补元数据、缩略图、质量检测、版权来源和业务适用标签。

## 关键资料

### Khronos glTF / GLB

- 来源：Khronos glTF
- 链接：https://www.khronos.org/gltf/
- 链接：https://github.com/khronosgroup/gltf
- 相关点：glTF 是面向运行时传输和加载的 3D 资产格式，GLB 是单文件二进制形式。Khronos 将其定位为高效传输和加载 3D 场景/模型的开放规范。
- 对本项目的启发：GLB 适合作为 Web 端 Three.js 场景的资产主格式，但要治理压缩、LOD、贴图、PBR、尺寸和坐标轴。

### glTF PBR

- 来源：Khronos glTF PBR
- 链接：https://www.khronos.org/gltf/pbr/
- 相关点：glTF PBR 定义了一组物理渲染材质参数，用于模拟现实光照、材质和表面属性。
- 对本项目的启发：资产入库质量不只看能否加载，还应记录材质类型、贴图、透明度、是否适合农业环境光照。

### Library of Congress glTF 2.0

- 来源：Library of Congress, Sustainability of Digital Formats
- 链接：https://www.loc.gov/preservation/digital/formats/fdd/fdd000500.shtml
- 相关点：从长期保存和格式可持续性角度描述 glTF 2.0。
- 对本项目的启发：如果平台要长期维护资产库，GLB 元数据、来源、许可和版本管理比临时演示更重要。

### TRELLIS.2

- 来源：Microsoft TRELLIS.2 GitHub
- 链接：https://github.com/microsoft/TRELLIS.2
- 来源：Hugging Face microsoft/TRELLIS.2-4B
- 链接：https://huggingface.co/microsoft/TRELLIS.2-4B
- 来源：TRELLIS.2 project page
- 链接：https://microsoft.github.io/TRELLIS.2/
- 相关点：TRELLIS.2 面向 3D 生成，适合从图像快速生成普通 3D 资产。
- 对本项目的启发：TRELLIS.2 适合做“缺失资产补齐”和“普通农业设备/装饰快速生成”，不应承担关键植株表型测量或高精度几何验证。

### 植物三维重建与表型

- 来源：A Review of Optical-Based Three-Dimensional Reconstruction and Multi-Source Fusion for Plant Phenotyping
- 链接：https://pmc.ncbi.nlm.nih.gov/articles/PMC12158188/
- 相关点：综述光学三维重建和多源融合在植物表型中的应用。
- 对本项目的启发：高保真植株重建的价值在于可测量、可追溯、与真实表型关联，而不是单纯视觉好看。

- 来源：High-fidelity 3D Reconstruction of Plants using Neural Radiance Field
- 链接：https://arxiv.org/abs/2311.04154
- 相关点：NeRF 类方法用于高保真植物重建。
- 对本项目的启发：可作为 F2DMAS 之外的相关工作材料，说明高保真植物几何重建是农业数字孪生的重要支撑方向。

- 来源：A 3D reconstruction platform for complex plants using OB-NeRF
- 链接：https://pmc.ncbi.nlm.nih.gov/articles/PMC11931026/
- 相关点：复杂植物三维重建平台，关注植物几何结构表达。
- 对本项目的启发：关键植株可在里程碑日期执行重建，形成阶段性几何版本。

- 来源：CropCraft: Inverse Procedural Modeling for 3D Reconstruction of Crop Plants
- 链接：https://arxiv.org/html/2411.09693v1
- 相关点：逆向程序化建模用于作物植物三维重建。
- 对本项目的启发：大面积作物行不一定都靠神经生成，可用程序化模型结合少量真实样本驱动实例化。

## 多保真资产调度规则建议

| 对象类型 | 推荐策略 | 原因 |
| --- | --- | --- |
| 关键植株、异常植株、论文展示样本 | F2DMAS/高保真重建 | 需要真实来源、表型可测、几何可信 |
| 普通背景植株、大面积作物行 | 已有低模实例 + 数据缩放 | 关注整体态势，不需要单株高精度 |
| 水泵、摄像头、水塔、设备外壳 | 资产库优先，缺失时 TRELLIS.2 | 快速补齐演示资产 |
| 地块、道路、围栏、沟渠、灌溉管线 | 程序化生成 | 规则几何更稳定，易编辑 |
| 临时缺失资产 | 占位模型 + 生成任务 | 保证场景搭建不中断 |

## 资产元数据建议

```json
{
  "assetKey": "tomato_stage_flowering_high",
  "category": "plant",
  "source": "F2DMAS",
  "fidelity": "high",
  "geometryUpdateMode": "milestone",
  "stateUpdateMode": "daily",
  "glbUrl": "/scene-assets/models/tomato_stage_flowering_high.glb",
  "thumbnailUrl": "/scene-assets/thumbs/tomato_stage_flowering_high.jpg",
  "license": "internal-captured",
  "quality": {
    "triangleCount": 280000,
    "textureCount": 4,
    "fileSizeMb": 18.2,
    "lod": ["high", "medium", "low"]
  },
  "phenotype": {
    "heightCm": 45.2,
    "canopyWidthCm": 31.6,
    "captureDate": "2026-05-20"
  }
}
```

## 入库验收清单

- GLB 能被 Three.js 加载。
- 坐标轴、单位、中心点、缩放正常。
- 面数、贴图尺寸、文件体积在阈值内。
- 有缩略图。
- 有来源、许可、生成参数或采集记录。
- 有业务标签：作物、设备、温室、地块、装饰等。
- 有保真度等级和适用场景。
- 可生成至少一个 LOD 或轻量版本。

