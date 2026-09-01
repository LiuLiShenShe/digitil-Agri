# 11 — Figure Plan

## Main-text figures

### Fig 1: KAFarmTwin 系统架构图
- **Purpose**: 展示方法整体流程
- **X**: 处理阶段（输入 → IntentIR → 知识编译 → 类型化修复 → 输出）
- **Y**: 各阶段组件
- **Data source**: 方法描述（Section 3）
- **Location**: 正文 Section 3
- **Status**: 需绘制

### Fig 2: External300 分类型 CVSR 对比
- **Purpose**: 展示 KF vs SA 在五类任务上的优势分布
- **X**: 任务类别（rule_repair, data_binding, memory_query, scene_construction, asset_routing）
- **Y**: CVSR (0–1.0)
- **Data source**: `External300_CANONICAL_METRICS.json` by_type
- **Location**: 正文 Section 5.5
- **Status**: 需用现有数据绘制
- **Note**: rule_repair 为 D1 难度；asset_routing 失败中 78.2% 为 policy errors

### Fig 3: 消融实验 CVSR + Fatal Rate 对照
- **Purpose**: 展示三个组件各自的贡献维度
- **X**: 变体（full, A1, A2, A3）
- **Y**: CVSR (bar) + Fatal Rate (line/dot)
- **Data source**: `ablation_results.csv`
- **Location**: 正文 Section 5.6
- **Status**: 需用现有数据绘制

### Fig 4: 跨模型家族 Δ + 95% CI Forest Plot
- **Purpose**: 展示五模型方向一致性与置信区间
- **X**: Δ (KF - SA CVSR)
- **Y**: 模型家族（DeepSeek, Kimi, MiniMax, Qwen, GLM）
- **Data source**: `MULTIMODEL_CANONICAL_STATISTICS_v2.json`
- **Location**: 正文 Section 5.4.6
- **Status**: 需用现有数据绘制（forest plot 格式）

### Fig 5: Fatal Rate vs Replay Success 散点
- **Purpose**: 展示安全性机制链
- **X**: Fatal Rate ↓
- **Y**: Replay Success ↑
- **Data source**: External300 by_type + multimodal
- **Location**: 正文 Section 5.4.5
- **Status**: 需用现有数据绘制

## Appendix figures

### Fig A1: 配对 bootstrap 分布直方图
- **Purpose**: 展示 External300 b=77 vs c=6 的不对称性
- **Data source**: 10,000 bootstrap samples
- **Location**: Appendix

### Fig A2: 延迟 p50/p95 对比（双口径）
- **Purpose**: 展示 LLM-invoking vs all-tasks 延迟差异
- **Data source**: `External300_CANONICAL_METRICS.json` latency
- **Location**: Appendix

共 **5 张正文图 + 2 张附录图**。所有图均可用现有数据绘制，无需新增实验。
