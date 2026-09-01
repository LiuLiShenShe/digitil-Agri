# 01 — 实验资产清单

## 正式实验总览

| # | Experiment ID | 目的 | 数据集/任务数 | 方法 | repeats | 主要指标 | 原始结果路径 | canonical 统计路径 | 论文状态 |
|---|---|---|---|---|---|---|---|---|---|
| E1 | test_v2 Phase-3 | 冻结基准上多基线比较 | 20 tasks × 5 methods × 5 repeats = 500 runs | KF / SA / ReAct / GenericMulti / GenericRepair | 5 per task-method | CVSR, pass@k, F1, Fatal, Cost | `results/v3_runs.jsonl` | `results/v3_summary.json` | ✅ 正文 |
| E2 | External300 DeepSeek | 更大规模受控基准，KF vs SA | 300 tasks × 2 methods = 600 records (single execution) | KF / SA | 1 per task-method | CVSR, paired Δ, CI, McNemar, F1, Fatal, Replay | `results/external300/ext300_formal_20260825/raw/runs.jsonl` | `results/external300/External300_CANONICAL_METRICS.json` | ✅ 正文 |
| E3 | Ablation (A1/A2/A3/full) | 组件贡献归因 | 20 tasks × 4 variants × 5 repeats = 400 runs | full / A1_no_compiler / A2_no_typed_repair / A3_no_ontology | 5 per task-variant | CVSR, F1, Fatal, Binding-F1 | `results/archive_ablation_v1/v3_runs_ablation_*.jsonl` | `results/analysis/ablation_results.csv` + `v3_ablation_summary.json` | ✅ 正文 |
| E4 | Multimodel Kimi-K2.6 | 跨模型家族泛化 #1 | 300 tasks × 2 methods = 600 records (single execution) | KF / SA | 1 per task-method | CVSR, paired Δ, CI, McNemar | `results/external300/ext300_mm1_kimi_20260825/raw/runs.jsonl` | `results/external300/multimodel/MULTIMODEL_CANONICAL_STATISTICS_v2.json` | ✅ 正文 |
| E5 | Multimodel MiniMax-M2.5 | 跨模型家族泛化 #2 | 300 tasks × 2 methods = 600 records | KF / SA | 1 | CVSR, paired Δ, CI, McNemar | `results/external300/ext300_mm2_minimax_20260825/raw/runs.jsonl` | 同上 | ✅ 正文 |
| E6 | Multimodel Qwen3.6-27B | 跨模型家族泛化 #3 | 300 tasks × 2 methods = 600 records | KF / SA | 1 | CVSR, paired Δ, CI, McNemar | `results/external300/ext300_mm3_qwen_20260825/raw/runs.jsonl` | 同上 | ✅ 正文 |
| E7 | Multimodel GLM-5.2 | 跨模型家族泛化 #4 | 300 tasks × 2 methods = 600 records | KF / SA | 1 | CVSR, paired Δ, CI, McNemar | `results/external300/ext300_mm4_glm_20260825/raw/runs.jsonl` | 同上 | ✅ 正文 |
| E8 | Multimodel DeepSeek baseline | 跨模型泛化对照基线 | 300 tasks × 2 methods = 600 records (同 E2) | KF / SA | 1 | (同 E2) | (同 E2) | (同 E2) | ✅ 正文 |

## 结果性质分类

- **Frozen result**：E1 (test_v2)、E2 (External300 DeepSeek) — raw 数据已冻结，不可重跑
- **Sealed result**：E2、E4–E7 — 各含 `SEAL.json`，raw SHA-256 已校验
- **Canonical result**：E2 由 `External300_CANONICAL_METRICS.json`；E4–E7 由 `MULTIMODEL_CANONICAL_STATISTICS_v2.json`；E1 由 `v3_summary.json`；E3 由 `ablation_results.csv`；E2-DirectRepair 由 `p05r_summary_v2.json`（re-scored after runner bug fix）
- **Archived (stale)**：`archive_formal_20260817*`、`archive_stale_20260817*`、`archive_phase2_frozen*` — 已被后续版本替代，论文不可引用
- **Exploratory**：`cost_breakdown.csv` 中的 GenericMulti/GenericRepair/ReAct 为 test_v2 基线数据（非 canonical）

## 额外基线与审计（非主实验）

| # | 实验 | 任务数 | 方法 | 指标 | 关键发现 |
|---|---|---|---|---|---|
| E9 | DirectRepair 诊断（rule_repair, D1 难度） | 60 tasks × 1 method | SingleAgent-DirectRepair | CVSR=0.000, Obj-F1=1.000, Rel-F1=1.000, Bind-F1=0.100, SRRR=100%, SESR=10% | SRRR vs SESR 揭示 typed repair 的结构化执行价值 |
| E10 | Asset-routing ID-invariant audit | 55 KF 失败任务 | ID-invariant re-evaluation | 78.2% 为 asset-routing policy errors, 9.1% 为 structural mismatch | 结构正确但资产身份错误是主要失败原因 |

## 实验定位说明

- External300 / test_v2 / multimodel 均为 **controlled methodological evaluation**（author-generated, author-reviewed controlled benchmark），不是 field-validated 的温室数字孪生系统实地验证
- rule_repair 任务全部为 **D1 难度**（单条 R4 违规，prompt 中给出明确修复目标），不是多规则/多难度梯度的修复测试
- 排除 rule_repair（60 任务）后，External300 KF-SA 差异从 +23.7pp 缩小至 +4.6pp

## 方法组件清单（基于代码确认）

| 组件 | 代码位置 | 消融变体 |
|---|---|---|
| 知识编译器 (Knowledge Compiler) | `harness/semantic_compiler.py` | A1_no_compiler |
| 类型化修复 (Typed Repair) | `methods/kafarmtwin_typed_repair.py` | A2_no_typed_repair |
| 本体约束执行器 (Ontology Constraint) | `harness/semantic_compiler.py` 内 ontology 校验 | A3_no_ontology |
| ONTOLOGY_NOTE 注入 | `harness/llm.py` ONTOLOGY_NOTE 常量 | (嵌入所有方法) |
| 意图中向表示 (IntentIR) | `harness/semantic_compiler.py` | (无单独消融) |
| 绑定时间戳契约 | `methods/kafarmtwin_typed_repair.py` 内 binding metadata | (已修复 TN21/TN24) |
