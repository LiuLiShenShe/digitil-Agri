# 04 — Baseline 对比整理

**Canonical source**：`experiments/v3/results/v3_summary.json`（test_v2）+ `External300_CANONICAL_METRICS.json`

## Baseline 清单

| Baseline | 核心差异 | 同模型 | 同任务 | 同Evaluator | Fair Paired |
|---|---|---|---|---|---|
| SingleAgent-AllTools | 无知识编译、无类型化修复、无本体约束；直接 LLM 构造 | ✅ | ✅ | ✅ | ✅ (同 task 配对) |
| ReAct-AllTools | 推理-行动循环，无结构化知识约束 | ✅ | ✅ | ✅ | ✅ |
| GenericMultiAgent-AllTools | 多智能体协作，无编译器 | ✅ | ✅ | ✅ | ✅ |
| GenericRepair-AllTools | 通用修复，无类型化动作空间 | ✅ | ✅ | ✅ | ✅ |

## test_v2 多基线对比

| Method | CVSR | Obj-F1 | Rel-F1 | Bind-F1 | Crit-Recall | Fatal | Ev-P | Replay | Cost/run |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **KAFarmTwin (Ours)** | **0.610** | **0.7997** | **0.5342** | **0.5292** | **1.000** | **0.000** | **1.000** | **1.000** | $0.0003 |
| SingleAgent | 0.360 | 0.6854 | 0.3911 | 0.1267 | 0.900 | 0.320 | 0.900 | 0.6068 | $0.0003 |
| GenericRepair | 0.060 | 0.4566 | 0.2453 | 0.0425 | 0.800 | 0.070 | 1.000 | 1.0000 | $0.0004 |
| GenericMultiAgent | 0.010 | 0.4613 | 0.1999 | 0.0433 | 0.800 | 0.310 | 0.790 | 0.0000 | $0.0011 |
| ReAct | 0.000 | 0.0000 | 0.0000 | 0.0000 | 0.400 | 0.000 | 0.000 | 0.0000 | $0.0026 |

## External300 精简对比（仅 KF vs SA）

| Method | CVSR | Obj-F1 | Rel-F1 | Bind-F1 | Fatal | Replay | Cost $ |
|---|---:|---:|---:|---:|---:|---:|---:|
| **KF (Ours)** | **0.7167** | 0.6896 | 0.6995 | 0.5939 | **0.000** | **0.8083** | 0.1035 |
| SA | 0.4800 | 0.6351 | 0.3790 | 0.2000 | 0.250 | 0.4553 | 0.0854 |

## 论文选择

- **正文保留**：SingleAgent-AllTools 作为同工具集无约束对照（External300 主实验 + test_v2）
- **test_v2 正文简述**：ReAct/GenericMulti/GenericRepair 的对比用于说明"无约束 LLM 智能体的局限"
- **不新增 baseline**：所有 baseline 均已完成
