# 农业数字孪生研究与应用参考

## 核心结论

农业数字孪生的主流场景包括受控环境农业、温室管理、作物监测、土壤和灌溉管理、农机与供应链等。当前项目最适合聚焦“温室/园区 3D 场景 + IoT 状态同步 + 作物长势分析 + Agent 运维”，不要把目标扩散成完整农业全链路系统。

## 关键资料

### Agricultural digital twin for smart farming: A review

- 来源：Green Technologies and Sustainability, 2026, Review article
- 链接：https://www.sciencedirect.com/science/article/pii/S2949736125001332
- DOI：https://doi.org/10.1016/j.grets.2025.100299
- 相关点：综述了农业数字孪生在受控环境农业、土壤和灌溉管理、作物监测、栽培支持等场景中的应用。
- 对本项目的启发：平台功能可以按农业数字孪生应用域组织，而不是按前端页面组织。例如：场景构建、环境监测、灌溉诊断、作物监测、资产维护、日报。

### Digital Twins in Agriculture: Orchestration and Applications

- 来源：Journal of Agricultural and Food Chemistry, 2024
- 链接：https://pubs.acs.org/doi/10.1021/acs.jafc.4c01934
- 相关点：强调农业数字孪生不仅是模型，还涉及对象/植物功能的实时数字化复制、编排和应用。
- 对本项目的启发：可以将论文或设计贡献表述为“农业数字孪生编排平台”，即通过 Agent 编排场景、资产、数据、分析和告警。

### Digital twin-based applications in crop monitoring

- 来源：PMC/NIH 开放全文
- 链接：https://pmc.ncbi.nlm.nih.gov/articles/PMC11795032/
- 相关点：梳理作物监测数字孪生中的建模方法，包括物理模型、Agent-based、数据驱动、混合模型等。
- 对本项目的启发：当前项目不必一步到位做生理机理模型，可以采用工程可落地的混合路线：IoT 数据 + 表型数据 + 规则/机器学习分析 + Agent 解释。

### Digital Twins in greenhouse horticulture: A review

- 来源：Computers and Electronics in Agriculture, 2022
- 链接：https://www.sciencedirect.com/science/article/pii/S0168169922005002
- 相关点：系统性综述温室园艺中的数字孪生应用。
- 对本项目的启发：温室是最适合做 MVP 和论文实验的农业数字孪生场景，因为温湿度、CO2、光照、灌溉、摄像头、作物行和控制设备都能形成闭环。

### Digital twin deployment for smart agriculture in Cloud-Fog-Edge infrastructure

- 来源：Taylor & Francis, 2023
- 链接：https://www.tandfonline.com/doi/full/10.1080/17445760.2023.2235653
- 相关点：提出基于 Cloud/Fog/Edge 和 Multi-Agent Systems 的智慧农业数字孪生架构。
- 对本项目的启发：可以把本项目多 Agent 设计与边云协同关联：前端/边缘做数据采集和实时展示，后端做孪生状态管理，Agent 层做规划、诊断和报告。

### A Digital Twin Framework for Sensor Selection and Microclimate Monitoring in Greenhouses

- 来源：MDPI AgriEngineering, 2025
- 链接：https://www.mdpi.com/2624-7402/7/10/315
- 相关点：关注温室微气候监测和传感器选择。
- 对本项目的启发：后续可以加入 `SensorPlacementAgent` 或 `DataQualityAgent`，检查温室传感器覆盖、数据缺失和微气候异常。

## 可用于论文/设计的研究缺口

1. 很多农业数字孪生研究强调传感器和模型，但对 3D 资产生成、资产保真度调度和模型入库治理讨论不足。
2. 很多平台展示数字孪生状态，但缺少从自然语言到场景规划、资产选择、数据绑定、告警分析的一体化 Agent 工具链。
3. 植株数字孪生存在“高频状态变化”和“高成本几何重建”的矛盾，适合提出阶段性几何更新与高频状态同步机制。
4. 农业业务对象、3D 对象、传感器、时间序列和 Agent 记忆常常分散存储，适合提出统一绑定模型。

## 和当前审计报告的连接

当前系统已有：

- 3D 场景编辑器和农业资产库。
- IoT 模拟数据、设备台账、告警和 WebSocket。
- 监控大屏、业务中心、AI 助手。
- Eino SceneBuilderAgent、模型语义检索、自然语言规划、自动布局和缺失资产补齐入口。

后续应补齐：

- 真实设备接入和数据质量记录。
- 农业对象模型和 3D 对象绑定。
- 作物状态每日归档和长势分析。
- Agent 生成日报、解释告警、检查资产和数据绑定缺口。

