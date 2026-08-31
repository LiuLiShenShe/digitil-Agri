# 12 — Claim–Evidence Matrix

## 核心 Claims

| Claim ID | Scientific claim | Evidence | Experiment | Statistic | Figure/Table | Strength |
|---|---|---|---|---|---|---|
| C01 | KAFarmTwin 在 External300 上 CVSR 显著高于最强公平基线 | KF 0.717 vs SA 0.480, Δ=+23.7pp | E2 External300 | CI [18.33, 29.00], McNemar p<10⁻⁶ | Table 2, Fig 2 | **Directly supported** |
| C02 | 优势核心来源是约束安全性（Fatal↓, Ev-P↑, Replay↑） | KF Fatal=0 vs SA 0.25, Replay 0.81 vs 0.46 | E2 + E3 A2 | Paired flips 22:0 (ablation) | Table 2, Fig 5 | **Directly supported** |
| C03 | 成本增加可控（≤1.5×） | Token ratio 1.41×, Cost ratio 1.21× | E2 | — | Table 2 | **Directly supported** |
| C04 | 知识编译器对资产构建具有决定性作用 | A1 asset CVSR 0.95→0.00 | E3 Ablation A1 | 100 runs, descriptive | Table 3, Fig 3 | **Directly supported** |
| C05 | 类型化修复贡献安全性而非 CVSR | A2 Fatal 0→0.22; A2 CVSR 0.58 > full 0.55 | E3 Ablation A2 | Paired flips 22:0 | Table 3, Fig 3 | **Directly supported** |
| C06 | 本体约束提升绑定正确性 | A3 Bind-F1 0.529→0.453 | E3 Ablation A3 | 100 runs | Table 3 | **Supported** (moderate effect) |
| C07 | 方法跨模型家族泛化方向一致 | 四新模型 Δ 全部 >0, CI lower >0 | E4–E7 | PASS verdict (4/4) | Table 4, Fig 4 | **Directly supported** |
| C08 | 五模型 rule_repair 完全一致（KF=1.00, SA=0.00） | 五模型数据 | E2 + E4–E7 | Descriptive | Table 5 | **Directly supported** |
| C09 | 资产路由绝对水平仍低 | KF asset CVSR ≤0.18 五模型 | E2 + E4–E7 | Descriptive | Table 5 | **Directly supported** (honest limitation) |
| C10 | 结论限于跨模型家族稳健性，不构成跨 provider 泛化 | 所有模型经同一硅基流动接口 | E4–E7 设计 | — | N/A (methodology) | **N/A** (scope boundary, not empirical claim) |

## Partially supported claims

| Claim ID | Claim | Evidence gap | 当前强度 |
|---|---|---|---|
| C11 | 绑定时间戳修复有效 | TN21/TN24 live run，非正式统计 | Supported (single case) |

## Unsupported claims（当前不存在此类）

论文中不包含 Unsupported 的 claims。所有声明均有对应实验数据。

## 关键观察

- **最强 claim**：C01、C04、C05、C07 — 都有直接的实验对照和统计检验
- **最诚实的 claim**：C09 — 明确报告资产路由的局限
- **需要小心的 claim**：C06（本体约束效果中等，受 evaluator 限制）
