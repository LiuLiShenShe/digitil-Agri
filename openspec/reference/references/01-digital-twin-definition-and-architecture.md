# 数字孪生定义与架构参考

## 核心结论

数字孪生不是“有一个 3D 模型”的系统，而是现实实体或过程的虚拟表示，并且与现实对象以指定频率、指定保真度同步。这个定义非常适合当前项目采用“阶段性几何更新 + 高频状态同步”的路线：植株 GLB 不需要每天重建，但环境、设备、告警、表型和分析状态应持续同步。

## 关键资料

### Digital Twin Consortium：同步频率与保真度

- 来源：Digital Twin Consortium, “Digital Twin Consortium Defines Digital Twin”
- 链接：https://www.digitaltwinconsortium.org/2020/12/digital-twin-consortium-defines-digital-twin/
- 相关点：DTC 对数字孪生的定义强调虚拟表示、现实实体/过程、指定频率和保真度的同步。
- 对本项目的启发：可以把植株拆成 `Geometry Twin` 和 `State Twin`。几何层按生育期或关键样本更新，状态层按实时/日级数据持续更新。

### ISO 23247：数字孪生分层框架

- 来源：ISO 23247-1/2，Automation systems and integration - Digital twin framework for manufacturing
- 链接：https://www.iso.org/obp/ui/en/#!iso:std:75066:en
- 链接：https://www.iso.org/obp/ui/en/#!iso:std:78743:en
- 相关点：ISO 23247 面向制造数字孪生，但它的分层思想可迁移到农业平台：可观测实体、设备通信、数字孪生实体、用户/应用实体。
- 对本项目的启发：农业平台也可以分成四层：
  - 物理层：温室、地块、植株、传感器、摄像头、水泵、阀门。
  - 通信层：MQTT、HTTP、WebSocket、设备适配器、数据清洗。
  - 孪生层：业务对象、3D 对象、状态、时序数据、告警、资产版本。
  - 应用层：3D 编辑器、监控大屏、AI 助手、多 Agent 运维、日报。

### NIST：标准化、可信和互操作

- 来源：NIST/ACM, “Manufacturing Digital Twin Standards”
- 链接：https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=957622
- 相关点：数字孪生跨学科且复杂，工程落地需要标准、可信性、互操作和用例边界。
- 对本项目的启发：后续设计不宜只追求 Agent 自动化，还要明确工具白名单、状态来源、审计日志、失败回退和数据质量检查。

### AP238 对 ISO 23247 的解释

- 来源：AP238.org, “ISO 23247 Digital Twin Framework for Manufacturing”
- 链接：https://www.ap238.org/iso23247/
- 相关点：该页面用较工程化语言解释了 ISO 23247 的分层：设备通信实体汇总状态变化，数字孪生实体读取数据并更新模型，用户实体消费孪生能力。
- 对本项目的启发：可将当前 Go 后端的 IoT/MQTT/WebSocket 作为“设备通信实体”，将场景对象/业务对象/资产状态/时序记忆作为“数字孪生实体”。

## 可落地到本项目的设计原则

1. `State first`：状态同步是数字孪生的核心，3D 几何只是表达层之一。
2. `Different frequency, different fidelity`：不同对象可以有不同同步频率和保真度。环境传感器实时，日报日级，植株几何阶段级，普通装饰资产静态。
3. `Observable object`：每个可观测农业对象都应有业务 ID、类型、空间位置、状态字段和数据绑定。
4. `Traceable update`：每次 Agent 修改场景、绑定数据、替换 GLB 或生成告警，都应记录工具调用链和输入输出摘要。

## 推荐引用方式

可以在平台定义中写：

> 本平台将农业数字孪生理解为农业实体和生产过程的可同步虚拟表示。系统不追求所有对象几何形态的高频重建，而是依据对象类型和业务价值设置不同同步频率与保真度：环境与设备状态实时同步，农业事件和表型数据日级归档，关键植株几何按生育期或关键采样点更新。

