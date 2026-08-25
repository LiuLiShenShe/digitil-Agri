# External300 source and provenance register

访问日期：2026-08-24。

这些来源用于定义语义、场景族和变量选择。除非下表明确写为“已导入原始记录”，否则只表示概念或场景依据，不表示复制了来源数据。

| ID | 官方来源 | 版本/DOI | 本候选集中的用途 | 实际数据状态 |
|---|---|---|---|---|
| `SAREF4AGRI-v2.1.1` | ETSI SAREF4AGRI: https://saref.etsi.org/saref4agri/v2.1.1/ | v2.1.1，2025-04-24 发布 | Crop、WeatherStation、SoilMoisture、AirTemperature、AmbientHumidity、PlantGrowthStage、部署与 contains 类语义 | 仅引用概念；未复制 ontology 文件；相关文本受 ETSI IPR Policy 约束 |
| `W3C-SOSA-SSN-2017` | W3C Recommendation: https://www.w3.org/TR/vocab-ssn/ | 2017 Recommendation | Sensor、Observation、FeatureOfInterest、observes/monitors、result time 语义 | 仅引用规范概念；未复制 ontology 文件 |
| `FIWARE-SmartDataModels-AgriGreenhouse` | Smart Data Models Agrifood: https://github.com/smart-data-models/dataModel.Agrifood | `AgriGreenhouse` 等公开 data models | 温室条件、农业实体和互操作字段命名依据 | 仅引用模型名称与概念；未复制 schema 内容 |
| `WUR-AGC-2018-cucumber` | Wageningen University & Research: https://research.wur.nl/en/datasets/autonomous-greenhouse-challenge-first-edition-2018/ | DOI `10.4121/uuid:e4987a7b-04dd-4c89-9b18-883aad30ba9a` | 黄瓜温室、气候/灌溉/外部天气场景依据 | 未导入原始记录 |
| `WUR-AGC-2019-cherry-tomato` | Wageningen University & Research: https://research.wur.nl/en/datasets/autonomous-greenhouse-challenge-second-edition-2019/ | DOI `10.4121/uuid:88d22c60-21b3-4ea8-90db-20249a5be2a7` | 樱桃番茄、室内外气候、灌溉、执行器、设定值和资源消耗场景依据 | 未导入原始记录 |
| `WUR-AGC-2022-lettuce` | Wageningen University & Research: https://research.wur.nl/en/datasets/3rd-autonomous-greenhouse-challenge-time-series-data-on-realized-/ | DOI `10.4121/21960932` | 生菜温室、时间序列与视觉监测场景依据 | 未导入原始记录 |
| `WUR-AGC-2024-dwarf-tomato` | Wageningen University & Research: https://research.wur.nl/en/datasets/4th-autonomous-greenhouse-challenge-dwarf-tomato-timeseries-and-i/ | DOI `10.4121/fa102772-32db-4b30-bace-12f2016722ce` | 矮生番茄、5 分钟气候/控制/天气和冠层相机场景依据 | 未导入原始记录 |

## 为什么当前没有把 WUR 数值写成“真实数据”

本次构建能够核实官方元数据与 DOI，但没有取得并校验 4TU 原始压缩包、文件级许可文本和 SHA-256。因此 `EXT-MQ-*` 的时间序列由生成器确定性产生，并在 manifest 中标为 `WUR-AGC-scenario-informed-synthetic`。在原始文件、版本、许可和哈希全部登记前，不得改写为 `real-world records`、`WUR-derived samples` 或类似表述。

## AGROVOC 的处理

FAO AGROVOC（https://www.fao.org/agrovoc/）被评估为可用农业词表，但本版没有固定某个可复现导出版本，也没有记录每个作物的 concept URI，因此没有把 AGROVOC 列为逐条标签来源。后续若使用，必须固定导出日期/版本、许可和 concept URI 映射。
