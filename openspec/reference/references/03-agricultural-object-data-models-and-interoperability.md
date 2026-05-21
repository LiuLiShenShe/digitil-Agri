# 农业对象数据模型与互操作参考

## 核心结论

农业数字孪生平台要可扩展，不能只保存 GLB 文件和 Three.js 坐标。应建立“农业业务对象 - 3D 场景对象 - 传感器 - 时间序列 - 事件 - 分析结果”的统一绑定模型。FIWARE Smart Data Models、NGSI-LD、Eclipse Ditto 等资料可以作为对象建模和状态同步的参考。

## 关键资料

### FIWARE / Smart Data Models Agrifood

- 来源：smart-data-models/dataModel.Agrifood
- 链接：https://github.com/smart-data-models/dataModel.Agrifood
- 相关点：提供 AgriFood 主题数据模型，包含 AgriParcel、AgriCrop、AgriFarm、AgriGreenhouse、AgriSoil、AgriPest、Animal、WeatherObserved 等方向。
- 对本项目的启发：对象模型可以先采用本地简化版，但命名和边界尽量向这些标准靠拢，方便未来对接外部平台。

### FIWARE 旧 Agrifood 模型索引

- 来源：FIWARE DataModels 文档，已归档但仍有索引价值
- 链接：https://fiware-datamodels.readthedocs.io/en/latest/AgriFood/index.html
- 相关点：列出了 AgriApp、AgriCrop、AgriFarm、AgriGreenhouse、AgriParcel、AgriParcelOperation、AgriParcelRecord、AgriSoil、WeatherObserved 等实体类型。
- 对本项目的启发：可以直接借鉴实体分类，形成本项目 MVP 业务对象：
  - `Farm`：园区/农场。
  - `Greenhouse`：温室。
  - `Parcel`：地块。
  - `CropBatch`：作物批次。
  - `Plant`：关键单株。
  - `Sensor`：传感器。
  - `Device`：执行设备。
  - `Camera`：摄像头点位。
  - `Operation`：灌溉/施肥/巡检事件。
  - `Observation`：环境或表型观测。

### NGSI-LD Smart Farm Tutorials

- 来源：FIWARE NGSI-LD 教程
- 链接：https://ngsi-ld-tutorials.readthedocs.io/en/latest/understanding-%40context.html
- 相关点：介绍如何用 JSON-LD、唯一 ID、上下文和数据模型构建可互操作的 Smart Agricultural Solution。
- 对本项目的启发：即使不直接接入 NGSI-LD，也应采用全局唯一 ID、类型、属性、关系和上下文的建模方式，避免后续数据无法关联。

### FIWARE: open standard-based framework for data integration based on digital twins

- 来源：FIWARE IoT Week 2022 slide
- 链接：https://iotweek.blob.core.windows.net/iotweek2022thursday/4.%20Thursday%2023/3.%20Nally%20Suite/1.%20Current%20Challenges%20and%20actual%20design%20patterns/FIWARE%20an%20open%20standard-based%20framework%20for%20data%20integration%20based%20on%20digital%20twins%20%E2%80%93%20Juanjo%20Hierro.pdf
- 相关点：把数字孪生理解为现实资产的数字表示，由属性和关系组成，属性值可以随时间变化，并强调标准 API 和通用数据模型。
- 对本项目的启发：3D 场景中的对象不能只是可视节点，应能通过 API 查询其业务属性、关系、状态和历史。

### Eclipse Ditto

- 来源：Eclipse Ditto 官网和项目页
- 链接：https://eclipse.dev/ditto/
- 链接：https://projects.eclipse.org/projects/iot.ditto
- 相关点：Ditto 为 IoT 应用提供数字孪生模式，支持设备即服务、状态管理、访问控制、搜索、推送通知，以及 HTTP/WebSocket/AMQP/MQTT/Kafka 集成。
- 对本项目的启发：
  - 区分 `reported`、`desired`、`current` 状态。
  - 所有设备控制应有期望状态、实际回执和当前状态。
  - Agent 不能直接写设备，应通过受控状态机和审计接口。

## 建议的本地对象模型

```json
{
  "businessObjectId": "plant_tomato_001",
  "type": "Plant",
  "name": "番茄单株 001",
  "parentId": "crop_row_01",
  "location": {
    "greenhouseId": "greenhouse_01",
    "row": 1,
    "column": 1
  },
  "sceneBinding": {
    "sceneObjectId": "scene_obj_abc",
    "assetKey": "tomato_stage_flowering",
    "geometryVersion": "f2dmas_20260520",
    "fidelity": "high"
  },
  "dataBindings": [
    "phenotype_daily",
    "greenhouse_microclimate",
    "irrigation_events",
    "growth_analysis"
  ],
  "state": {
    "stage": "flowering",
    "heightCm": 45.2,
    "canopyWidthCm": 31.6,
    "growthScore": 78,
    "stressRisk": "medium",
    "updatedAt": "2026-05-20T18:00:00+08:00"
  }
}
```

## 后续 OpenSpec 候选需求

- 新增农业业务对象表：Farm、Greenhouse、Parcel、CropRow、Plant、Sensor、Device、Camera。
- 新增 3D 对象绑定表：sceneObjectId 与 businessObjectId 关联。
- 新增数据绑定表：对象绑定到设备指标、时序表、事件表、分析结果。
- 新增对象查询接口：从 3D 对象查业务状态，从业务对象定位 3D 场景对象。
- 新增 Agent 可用只读工具：`object.lookup`、`object.relations`、`timeseries.query`、`event.query`。

