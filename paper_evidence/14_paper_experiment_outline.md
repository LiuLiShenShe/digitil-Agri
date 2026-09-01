# 14 — 论文实验章节建议结构

## 章节规划

### 5.1 Experimental Setup（实验设置）
- **Scientific question**: 实验是如何设计的？为什么这样设计？
- 内容：test_v2 定义（20 tasks, 5 类, 5 repeats）；External300 定义（300 tasks, 5 类各 60, single execution）；方法配置（KF, SA, 其他 baseline）；评估指标定义；底座模型与预算
- **Table 1**: Dataset and Setup

### 5.2 Main Results（主实验结果）
- **Scientific question**: KAFarmTwin 是否优于 SingleAgent？
- 内容：External300 KF vs SA 总体结果；配对统计（Δ, CI, McNemar）；成本比较
- **Table 2**: External300 Main Results
- **Claim M1, M3**
- **注意**：优势集中于 rule_repair（D1 难度，60/71 额外成功）；排除后差异缩小至 +4.6pp

### 5.3 Safety and Failure Analysis（安全性和失败分析）
- **Scientific question**: 优势的核心机制是什么？是性能提升还是安全性提升？
- 内容：Fatal Rate, Evidence Precision, Replay Success 对比；rule_repair 分析（D1 难度）；DirectRepair 诊断（SRRR=100% vs SESR=10%）；失败类型矩阵；证据链（知识约束 → Fatal↓ → Replay↑ → CVSR↑）；asset-routing policy errors（78.2%）
- **Fig 5**: Fatal vs Replay
- **Claim M2, C01d**

### 5.4 Ablation Study（消融实验）
- **Scientific question**: 方法的哪些组件贡献了什么？
- 内容：A1（编译器）→ 资产构建决定性；A2（修复）→ 安全性而非 CVSR；A3（本体）→ 绑定质量
- **Table 3**: Ablation Results
- **Fig 3**: Ablation CVSR + Fatal
- **Claim C04, C05, C06**

### 5.5 External300 Category Analysis（分类分析）
- **Scientific question**: 优势在哪些任务类型上？局限在哪里？
- 内容：五类 CVSR breakdown；rule_repair 完全一致（D1 难度，排除后差异缩小至 +4.6pp）；DirectRepair SRRR=100% vs SESR=10%；asset_routing 绝对水平低（78.2% 失败为 policy errors）；data_binding/memory_query 天花板
- **Table 5**: Category Breakdown
- **Fig 2**: Category CVSR
- **Claim C09, C01q, C01d**

### 5.6 Cross-Model-Family Generalization（跨模型家族泛化）
- **Scientific question**: 方法是否依赖单一模型？
- 内容：四新模型 × 完整 External300；配对统计；安全性模式跨家族复现；rule_repair 完全一致；MiniMax data_binding 退化
- **Table 4**: Multimodel Results
- **Fig 4**: Forest Plot
- **Claim C07, C08**

### 5.7 test_v2 Multi-baseline Comparison（辅助证据）
- **Scientific question**: 在更小规模基准上，KF 相对更多 baseline 的表现如何？
- 内容：五方法对比；pass@k；ReAct 全失败；GenericMulti/GenericRepair 远低于 KF
- **Table 6**: test_v2 Multi-baseline
- **Claim C01 (辅助)**

### 5.8 Validity Threats（有效性威胁）
- 基准接触偏差
- External300 审核身份
- 模型随机性（test_v2/ablation=5 repeats; External300/multimodel=single execution）
- 单位别名覆盖
- 底座模型与推理接口
- 成本口径

## 章节间逻辑

```
5.1 Setup → 5.2 主结果（KF>SA）→ 5.3 为什么（安全性机制）→ 5.4 哪些组件（消融）
                                                          ↓
                                            5.5 哪些类型（category breakdown）
                                                          ↓
                                            5.6 跨模型泛化（方向一致）
                                                          ↓
                                            5.7 辅助证据（test_v2 多基线）
                                                          ↓
                                            5.8 诚实边界
```

核心叙事线：**方法有效（5.2）→ 机制清晰（5.3, DirectRepair 诊断）→ 组件可归因（5.4）→ 分类有信息量（5.5, D1 caveat + policy error）→ 跨模型稳健（5.6）→ 多基线验证（5.7）→ 边界诚实（5.8）**
