# 07 — Safety / Failure 行为证据

## 证据链

论文主张的机制链：

```
知识约束（知识编译器 + 本体 + 类型化修复）
  → 减少非法/不可执行行为
  → 减少 Fatal Violations
  → 增加可恢复 Replay
  → 提高最终 CVSR
```

### 箭头 1：知识约束 → 减少 Fatal（✅ 强支持）

External300 DeepSeek：KF Fatal = 0.000，SA Fatal = 0.250。
消融 A2：去掉类型化修复后 Fatal 0 → 0.22（paired flips 22:0）。
五模型泛化：KF Fatal 全部 ≤0.003，SA Fatal 全部 0.23–0.29。

### 箭头 2：Fatal↓ → Replay↑（✅ 支持）

External300：KF Replay 0.808 vs SA 0.455。SA 的 0.25 fatal 任务全部不可重放。
消融 A2：去掉修复后 Replay 1.00 → 0.80，与 fatal 上升一致。

### 箭头 3：Replay↑ → CVSR↑（✅ 支持但非唯一因素）

Replay 是 CVSR 的必要条件（不可重放的任务不可能完整有效），但非充分条件——asset_routing 类 KF Replay=1.00 但 CVSR 仅 0.083，说明还有其他失败因素（知识编译器路径限制）。

## Safety Master Table（External300 DeepSeek）

| Metric | KF | SA | 证据强度 |
|---|---:|---:|---|
| Fatal Rate ↓ | 0.000 | 0.250 | 强（五模型一致） |
| Critical Recall ↑ | 1.000 | 0.950 | 中 |
| Evidence Precision ↑ | 1.000 | 0.947 | 中 |
| Replay Success ↑ | 0.8083 | 0.4553 | 强 |
| Binding-F1 ↑ | 0.5939 | 0.2000 | 强 |

## Safety across models（五模型 KF Fatal）

| Model | KF Fatal | SA Fatal |
|---|---:|---:|
| DeepSeek | 0.000 | 0.250 |
| Kimi | 0.000 | 0.290 |
| MiniMax | 0.003 | 0.293 |
| Qwen | 0.000 | 0.250 |
| GLM | 0.000 | 0.227 |

## Failure taxonomy（SA 在 External300 上的规则修复失败）

| Rule | Meaning | SA Failures |
|---|---|---:|
| R4 | constraint violation (fatal) | 60 |
| R6 | incomplete/missing data | 30 |
| R2 | invalid action | 15 |
| R5 | logic inconsistency | 10 |

KF 在所有规则类型上零失败。

**rule_repair 任务难度说明**：所有 60 个 rule_repair 任务均为 D1 难度（单条 R4 违规，prompt 中给出明确修复目标）。SA 的 60 个 R4 失败中，DirectRepair 基线（有修复 prompt 但无 typed repair）同样 0/60 通过，但 SRRR=100%（语义理解正确）vs SESR=10%（结构化输出失败），揭示了 typed repair + deterministic executor 的核心价值。

## Technical failures

- MiniMax 区块：1 个技术失败（EXT-SC-049/SA 读超时），零分保留
- 其余区块：0 技术失败
- 技术失败不是方法缺陷，是网络/超时问题

## 绑定失败分析（DeepSeek External300 已知边界）

- TN21/TN24：方法侧 timestamp 缺失（已修复，Bind-F1 0.333/0.25 → 1.00）
- TN22/TN23：冻结 evaluator 单位别名缺口（°C/celsius、klux/light），benchmark 契约局限

## 资产路由失败分析（ID-invariant audit）

- 78.2% 的 asset_routing 失败为 **asset-routing policy errors**（添加了不需要的设备同时遗漏了需要的设备），而非结构性构建失败
- ID-invariant 审计显示 canonical Rel-F1=0.997, Bind-F1=0.994（结构正确），但 78.2% 的路由资产物理身份错误
- 真正的算法失败（structural mismatch）仅占 ~9.1%
- 结论：瓶颈是资产识别/路由策略，不是场景图构建
