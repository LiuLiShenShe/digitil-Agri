# 10 — Table Plan

## Main-text tables

### Table 1: Dataset and Experimental Setup
- **Title**: 实验数据集与设置
- **Purpose**: 定义两个评测面（test_v2 + External300）及方法配置
- **Rows**: test_v2, External300, Multimodel
- **Cols**: 任务数, 类别数, 方法数, repeats, 底座模型, 预算
- **Data source**: 论文 Section 5.1
- **Claim**: 实验设置透明可复现
- **Location**: 正文

### Table 2: Main Results — External300 (KF vs SA)
- **Title**: External300 受控评测主结果
- **Purpose**: 核心主实验对比
- **Rows**: KAFarmTwin, SingleAgent
- **Cols**: CVSR, Obj-F1, Rel-F1, Bind-F1, Crit-Recall, Fatal, Ev-P, Replay, Cost
- **Data source**: `External300_CANONICAL_METRICS.json`
- **Claim M1**: KF CVSR 0.717 显著高于 SA 0.480
- **Location**: 正文

### Table 3: Ablation Study
- **Title**: 组件消融结果
- **Purpose**: 组件贡献归因
- **Rows**: full, A1_no_compiler, A2_no_typed_repair, A3_no_ontology
- **Cols**: CVSR, Obj-F1, Rel-F1, Bind-F1, Fatal, Cost
- **Data source**: `ablation_results.csv`
- **Claim**: 编译器决定资产构建，修复贡献安全性
- **Location**: 正文

### Table 4: Cross-Model-Family Generalization
- **Title**: 跨模型家族泛化结果
- **Purpose**: 方法不依赖单一模型
- **Rows**: DeepSeek, Kimi, MiniMax, Qwen, GLM
- **Cols**: KF CVSR, SA CVSR, Δ, 95% CI, McNemar
- **Data source**: `MULTIMODEL_CANONICAL_STATISTICS_v2.json`
- **Claim**: 四模型方向一致，PASS
- **Location**: 正文

### Table 5: Task-Category Breakdown (External300)
- **Title**: External300 分类型 CVSR
- **Purpose**: 展示优势分布
- **Rows**: rule_repair, data_binding, memory_query, scene_construction, asset_routing
- **Cols**: KF CVSR, SA CVSR, Δ
- **Data source**: `External300_CANONICAL_METRICS.json` by_type
- **Claim**: 优势集中于规则修复类
- **Location**: 正文

### Table 6: test_v2 Multi-baseline Comparison
- **Title**: test_v2 多基线对比
- **Purpose**: 展示 KF 相对多种 baseline 的优势
- **Rows**: KF, SA, ReAct, GenericMulti, GenericRepair
- **Cols**: CVSR, pass@1, pass@5, Obj-F1, Bind-F1, Fatal, Cost
- **Data source**: `v3_summary.json`
- **Claim**: 所有无约束基线均远低于 KF
- **Location**: 正文简述 + 附录详表

## Appendix tables

### Table A1: test_v2 逐任务详细结果
### Table A2: External300 模型延迟与成本全表
### Table A3: Multimodel 每模型完整指标（F1 族 + 分类型）
### Table A4: 早期原型历史对照（30 任务一代）

共 **6 张正文表 + 4 张附录表**。
