# 03 — 消融实验完整整理

**Canonical source**：`experiments/v3/results/analysis/ablation_results.csv` + `experiments/v3/results/v3_ablation_summary.json`

实验设计：v3 冻结协议，20 tasks × 5 repeats = 100 runs per variant，DeepSeek-V4-Flash，temperature 0.2。full 与主实验 KF 是**独立随机运行**（非同一批 runs），二者不可作配对比较。

## A. 组件消融 Master Table

| Ablation | Removed Component | CVSR | Obj-F1 | Rel-F1 | Bind-F1 | Crit-Recall | Fatal ↓ | Ev-P | Replay | Cost/run | Repeats |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **full** | (none) | 0.550 | 0.7963 | 0.5053 | 0.5292 | 1.000 | **0.000** | 1.000 | 1.000 | $0.00033 | 100 |
| **A1** no_compiler | knowledge compiler | 0.370 | 0.7211 | 0.3589 | 0.3292 | 0.950 | 0.010 | 0.950 | 0.950 | $0.00044 | 100 |
| **A2** no_typed_repair | typed repair loop | 0.580 | 0.7976 | 0.5369 | 0.3292 | 1.000 | **0.220** | 1.000 | 0.800 | $0.00018 | 100 |
| **A3** no_ontology | ontology constraint | 0.530 | 0.7956 | 0.5217 | 0.4525 | 1.000 | 0.000 | 1.000 | 1.000 | $0.00052 | 100 |

## B. Δ 分析（full vs each ablation）

| Variant | CVSR Δ | Bind-F1 Δ | Fatal Δ | 关键发现 |
|---|---|---|---|---|
| full → A1 | −0.180 | −0.200 | +0.010 | 编译器移除导致 CVSR 大幅下降；资产类完全失效；Critical Recall 降至 0.95 |
| full → A2 | +0.030 | −0.200 | **+0.220** | **CVSR 不降反升**——不得宣称修复带来 CVSR 增益；真实价值在安全性（fatal 0→0.22） |
| full → A3 | −0.020 | −0.077 | 0.000 | 本体移除对 CVSR 影响有限但 bind 明显下降；fatal 不变 |

## C. 按任务类型消融细节

**知识编译器（A1）的决定性作用——资产类**：

| 指标 | full (asset) | A1 (asset) | Δ |
|---|---|---|---|
| CVSR | 0.95 (19/20) | **0.00 (0/20)** | −0.95 |
| Object-F1 | 0.996 | 0.655 | −0.341 |
| Critical Recall | 1.00 | 0.95 | −0.05 |

**类型化修复（A2）的安全性作用——规则修复类**：

| 指标 | full (rule_repair) | A2 (rule_repair) | Δ |
|---|---|---|---|
| CVSR | 1.00 | 1.00 | 0 |
| Fatal Rate | **0.00** | **1.00 (全部致命)** | +1.00 |
| Paired flips | — | A2-fatal/full-clean = 22, reverse = 0 | — |

**本体约束（A3）的绑定作用**：

| 指标 | full (binding) | A3 (binding) | Δ |
|---|---|---|---|
| Bind-F1 | 0.5292 | 0.4525 | −0.077 |
| Fatal | 0.000 | 0.000 | 0 |

## D. 回答关键问题

### A. 哪些消融真正证明了某个组件有效？

- **A1（知识编译器）**：最强证据。资产类 CVSR 从 0.95 降至 0.00——绝对归因清晰，无可争议。
- **A2（类型化修复）**：安全性归因明确——fatal rate 0→0.22，paired flips 22:0。但 CVSR 不降反升（0.580 vs 0.550），必须如实报告。
- **A3（本体约束）**：Bind-F1 有下降（0.529→0.453），但幅度中等，且受冻结 evaluator 单位别名缺口限制。

### B. 哪些组件是主要性能来源？

知识编译器（A1 → CVSR −0.18）是最大的 CVSR 贡献者。

### C. 哪些组件主要改善 safety 而非平均性能？

类型化修复（A2）——CVSR 不升反降，但 fatal 从 0.22 降至 0。这是安全性组件，不是性能组件。

### D. 是否存在组件对不同任务类型作用不同？

是。知识编译器对 asset_routing 有决定性作用（CVSR 0.95→0.00），对 rule_repair 无影响（始终 1.00）。本体约束主要影响 binding 类。

### E. 哪些消融应进入论文正文？

A1 和 A2 必须进入正文——它们分别支撑"编译器决定构建成败"和"修复贡献安全性"两个核心 claim。A3 可进入正文或附录。

### F. 哪些消融只适合 appendix/supplement？

A3 适合放在正文简述 + 附录详表。无负结果需要隐藏——所有消融都如实报告。
