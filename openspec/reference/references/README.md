# 农业数字孪生智能体平台参考资料索引

本目录整理外部资料，服务后续 OpenSpec 设计、论文写作和平台架构迭代。整理时重点围绕当前项目已有思路：多 Agent 场景构建、多保真 GLB 资产池、阶段性几何更新、高频状态同步、农业对象图谱、时序记忆层和可追溯工具链。

## 资料分组

| 文件 | 关注问题 | 后续设计用途 |
| --- | --- | --- |
| [01-digital-twin-definition-and-architecture.md](./01-digital-twin-definition-and-architecture.md) | 什么才算数字孪生，架构如何分层 | 定义平台边界，支撑“状态同步优先于每天重建几何”的原则 |
| [02-smart-agriculture-digital-twin-literature.md](./02-smart-agriculture-digital-twin-literature.md) | 农业数字孪生有哪些场景和研究缺口 | 写论文相关工作、确定温室/作物监测/灌溉/运维场景 |
| [03-agricultural-object-data-models-and-interoperability.md](./03-agricultural-object-data-models-and-interoperability.md) | 农业对象、传感器、时间序列如何标准化 | 设计 Farm/Greenhouse/Parcel/Plant/Sensor 等业务对象模型 |
| [04-agent-platform-and-orchestration.md](./04-agent-platform-and-orchestration.md) | 多 Agent 如何编排、追踪和受控执行 | 设计 FarmTwin Orchestrator、工具白名单、Agent trace |
| [05-3d-glb-asset-pipeline-and-plant-reconstruction.md](./05-3d-glb-asset-pipeline-and-plant-reconstruction.md) | GLB 资产、TRELLIS.2、植物三维重建如何结合 | 设计多保真资产调度、F2DMAS/TRELLIS.2 分工、资产入库治理 |
| [06-design-notes-for-this-project.md](./06-design-notes-for-this-project.md) | 如何映射到当前项目 | 形成可直接转 OpenSpec 的设计备忘和候选任务 |

## 资料使用建议

- 写平台定义时，优先引用数字孪生联盟、ISO/NIST、FIWARE/Eclipse Ditto 这类标准或工程来源。
- 写农业场景和研究意义时，优先引用农业数字孪生综述、温室数字孪生综述、作物监测数字孪生综述。
- 写工程实现时，把本项目已有能力与外部资料对齐：当前已有 Eino SceneBuilderAgent、模型语义检索、自动布局、IoT 模拟链路和 TRELLIS.2 任务入口，后续重点是对象模型、数据绑定、资产治理和 Agent 运维闭环。
- 资料仅做设计参考。论文正式引用前，建议再次核对 DOI、作者、年份、页码和 BibTeX。

