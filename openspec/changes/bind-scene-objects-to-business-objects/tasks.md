## Development Progress

- Phase 0 baseline guard completed on 2026-05-21; see `openspec/development-phases/phase0-baseline-report.md`.
- Implemented on 2026-05-21: scene-business binding code, schema migration, data/API behavior, UI point-select/detail flow, business-object scene location, and validation are complete.

## 1. 绑定模型

- [x] 1.1 为场景对象增加主业务对象绑定字段或独立绑定表。
- [x] 1.2 支持一个业务对象关联多个场景对象。
- [x] 1.3 定义绑定关系的导入、保存、加载和删除规则。

## 2. 交互链路

- [x] 2.1 实现从 3D 点选场景对象到业务对象详情的链路。
- [x] 2.2 实现从业务对象列表定位到 3D 场景对象的链路。
- [x] 2.3 在对象详情中展示状态、指标摘要、历史趋势入口、告警和关联事件入口。

## 3. 校验

- [x] 3.1 实现场景绑定校验，识别缺业务绑定的核心对象。
- [x] 3.2 扩展校验结果，识别缺数据绑定和缺资产元数据的对象。
- [x] 3.3 验证 Greenhouse、Parcel、Plant、Sensor、Device、Camera 六类对象绑定链路可用。
