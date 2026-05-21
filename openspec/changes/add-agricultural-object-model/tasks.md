## Development Progress

- Phase 0 baseline guard completed on 2026-05-21; see `openspec/development-phases/phase0-baseline-report.md`.
- This change is implemented as of 2026-05-21: 10/10 implementation tasks complete.
- Verified scope: agricultural object model code, tomato greenhouse MVP seed data, object lookup/relation APIs, frontend debug entry, and acceptance checks have been implemented.
- Next status action: review and archive this change into canonical OpenSpec specs when ready.

## 1. 数据模型

- [x] 1.1 定义农业对象类型枚举：Farm、Greenhouse、Parcel、CropRow、Plant、CropBatch、Sensor、Device、Camera、Operation、Observation。
- [x] 1.2 设计对象基础字段：全局 ID、类型、名称、父级关系、空间位置或所在区域、当前状态、更新时间、数据质量状态、扩展属性。
- [x] 1.3 设计对象关系字段或关系表，覆盖层级、设备、传感器、摄像头、作物批次、关键植株和事件关联。
- [x] 1.4 准备番茄温室 MVP 的种子对象数据。

## 2. 查询接口

- [x] 2.1 实现对象详情查询能力，支持按对象 ID 和类型过滤。
- [x] 2.2 实现对象关系查询能力，支持查询父级、子级、关联设备、关联指标、关联事件和关联资产。
- [x] 2.3 为后续 Agent 工具预留 `object.lookup` 和 `object.relations` 的稳定输入输出结构。

## 3. 验收

- [x] 3.1 验证温室、地块、作物行、植株、传感器、设备和摄像头对象可查询。
- [x] 3.2 验证从温室对象能查到关联地块、作物批次、传感器、设备、摄像头和关键植株。
- [x] 3.3 验证对象数据质量状态能区分模拟、真实、过期和缺失数据。
