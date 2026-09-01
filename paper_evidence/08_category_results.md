# 08 — Task/Category-Level Master Table

## External300 DeepSeek 完整分类指标

### KAFarmTwin-TypedRepair

| Type | n | CVSR | Obj-F1 | Rel-F1 | Bind-F1 | Crit-Recall | Fatal | Ev-P | Replay |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rule_repair | 60 | **1.000** | 1.000 | 1.000 | 1.000 | 1.00 | 0.00 | 1.00 | 1.00 |
| data_binding | 60 | **1.000** | 1.000 | 1.000 | 1.000 | 1.00 | 0.00 | 1.00 | 1.00 |
| memory_query | 60 | **1.000** | 0.000 | 0.000 | 0.000 | 1.00 | 0.00 | 1.00 | 0.04 |
| scene_construction | 60 | 0.500 | 0.994 | 0.715 | 0.000 | 1.00 | 0.00 | 1.00 | 1.00 |
| asset_routing | 60 | 0.083 | 0.454 | 0.783 | 0.969 | 1.00 | 0.00 | 1.00 | 1.00 |
| **ALL** | **300** | **0.717** | 0.690 | 0.700 | 0.594 | **1.00** | **0.00** | **1.00** | **0.808** |

### SingleAgent-AllTools

| Type | n | CVSR | Obj-F1 | Rel-F1 | Bind-F1 | Crit-Recall | Fatal | Ev-P | Replay |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rule_repair | 60 | **0.000** | 1.000 | 0.000 | 0.000 | 1.00 | **1.00** | 1.00 | 1.00 |
| data_binding | 60 | 1.000 | 1.000 | 1.000 | 1.000 | 1.00 | 0.00 | 1.00 | 0.00 |
| memory_query | 60 | 1.000 | 0.000 | 0.000 | 0.000 | 1.00 | 0.00 | 1.00 | 0.04 |
| scene_construction | 60 | 0.400 | 0.993 | 0.666 | 0.000 | 1.00 | 0.10 | 1.00 | 0.70 |
| asset_routing | 60 | 0.000 | 0.182 | 0.229 | 0.000 | 0.75 | 0.15 | 0.73 | 0.53 |
| **ALL** | **300** | **0.480** | 0.635 | 0.379 | 0.200 | 0.95 | **0.25** | 0.95 | 0.455 |

### SingleAgent-DirectRepair（rule_repair only, D1 难度, 60 任务）

| Metric | DirectRepair | KF | SA | 说明 |
|---|---:|---:|---:|---|
| CVSR | 0.000 | 1.000 | 0.000 | DirectRepair 与 SA 相同，0/60 通过 |
| Object-F1 | 1.000 | 1.000 | 1.000 | LLM 正确修复所有对象 |
| Relation-F1 | 1.000 | 1.000 | 0.000 | LLM 正确修复所有关系 |
| Binding-F1 | 0.100 | 1.000 | 0.000 | 54/60 省略 bindings，6/60 有 bindings 但缺执行证据 |
| SRRR | 100% | — | — | 语义修复识别率 |
| SESR | 10% | — | — | 结构化执行成功率 |

**关键发现**：rule_repair 任务全部为 D1 难度（单条 R4 违规，prompt 给出明确修复目标）。DirectRepair 的 SRRR=100% vs SESR=10% 表明 LLM 完全理解修复语义但无法产生 schema-compliant 的结构化输出。排除 rule_repair 后，KF-SA 差异从 +23.7pp 缩小至 +4.6pp。

## Delta (KF - SA) 按类型

| Type | CVSR Δ | 正文/附录 |
|---|---:|---|
| rule_repair | **+1.000** | 正文（最大差异；D1 难度，DirectRepair 同样 0/60） |
| data_binding | 0.000 | 正文（天花板对照） |
| memory_query | 0.000 | 附录（天花板） |
| scene_construction | +0.100 | 正文 |
| asset_routing | +0.083 | 正文（诚实报告绝对水平低；78.2% 失败为 asset-routing policy errors） |

## 选择标准

- rule_repair、scene_construction、asset_routing 进入正文（差异有信息量）
- data_binding 作为天花板效应对照进入正文（简述）
- memory_query 适合附录（确定性数据，无差异可宣称）
