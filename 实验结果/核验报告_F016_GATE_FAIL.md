# KAFarmTwin 真实 LLM 公平复现实验 — 结果与依据（核验版）

> 日期：2026-08-17（数据采集 2026-08-08）
> 分支：`paper/knowledge-agent-experiments`；冻结测试集：`test_v2`（v2-sealed，Annotator 2 已批准）
> 唯一主指标：**CVSR**（Complete-and-Valid Scene Rate）
> 结论先行：**F-016 GATE FAIL（诚实）** — 在冻结 test_v2、公平条件（same-tool/same-model/same-budget）下，KAFarmTwin **未统计显著**超越最强公平基线 SingleAgent。

---

## 0. 核验入口（数据文件）

`实验结果/数据/`：
| 文件 | 内容 | SHA-256 |
|------|------|---------|
| `F015_stepwise_200run_v3_runs.jsonl` | **stepwise 重跑 200 run**（每任务×方法 5 次，20 任务×2 方法=200） | `de4f4437…c0fb1e` |
| `F015_stepwise_summary.json/.csv` | 200 run 按方法聚合 | `3128a159…38863` |
| `F015_oneshot_200run_归档.jsonl` | **旧 one-shot 200 run**（修复前，归档） | `c532f16e…05703` |
| `test_v2_gold.jsonl` | 冻结金标准（20 任务） | 见 MANIFEST |
| `test_v2_public_inputs.jsonl` | 冻结公开输入（方法只见此） | 见 MANIFEST |
| `test_v2_MANIFEST.sha256` | 冻结集哈希清单 | `sha256sum -c` 6/6 成功 |

工作区日志：`experiments/v3/STATUS.md`、`FAILURES.md`、`WORKLOG.jsonl`、`results/`。

---

## 1. 方法与一次性改动（本轮，用户选 Option A）

本轮唯一架构改动 = **解除模型单次输出上限**（根因 F-018），机制对两方法**完全相同**，公平：

- 新增共享 `harness/stepwise_builder.py`：`stepwise_build_scene()` 把场景拆成 3 次独立 LLM 调用（objects → relations → bindings），每次都在 ~1200 token 输出上限内。解析同时兼容 dict 包裹与**裸数组**形态（模型对 objects 步常返回 `[{...}]` 而非 `{"objects":[...]}`）。
- **两方法（SingleAgent 与 KAFarmTwin）调用同一个 builder**，场景创作能力对称。
- 修复 SingleAgent 修复分派诚实性：原判 `category=="rule_repair"`（runner 映射后恒 false）→ 修复任务被静默当场景重建；改为 `category=="repair" or task_type=="rule_repair"`，honest no-repair 分支真正触发。
- 测试：58 全绿（含新反作弊测试 18）。**未改**阈值/gold/评分器/基线预算/测试集。

---

## 2. F-015 结果（真实 LLM，SiliconFlow DeepSeek-V4-Flash，200 run，0 error）

运行清单核验：200 run；`(task_id, method)` 每格恰 5 次；0 LLM error。

### 2.1 按方法聚合
| 方法 | mean CVSR | pass5 | object_f1 | critical_recall | relation_f1 | binding_f1 | fatal率 |
|------|-----------|-------|-----------|-----------------|-------------|------------|---------|
| **KAFarmTwin-TypedRepair** | **0.200** | 0.20 | 0.724 | 0.600 | 0.326 | **0.000** | 0.28 |
| **SingleAgent-AllTools** | **0.200** | 0.20 | 0.705 | 0.600 | 0.316 | **0.000** | 0.42 |

### 2.2 按任务类型×方法（每格 20 run）
| task_type | KAFarmTwin | SingleAgent |
|-----------|-----------|-------------|
| scene_construction | 0/20 | 0/20 |
| asset_routing | 0/20 | 0/20 |
| data_binding | 0/20 | 0/20 |
| rule_repair | 0/20 | 0/20 |
| **memory_query** | **20/20** | **20/20** |

### 2.3 关键观察
- **CVSR 的 0.20 全部来自 4 个确定性 memory 任务**（两方法各 20/20，因为 `build_memory_answer` 确定性且共享）。
- **非 memory 的 16 个任务，两方法 CVSR 全 0。** 且 objF1/relation_f1 两方法都 >0（objF1≈0.71～0.72、relF1≈0.32），证明"空场景/输出截断"问题已解除；**失效的唯一维度是绑定（binding_f1 恒 0）**。

---

## 3. F-016 统计门控（诚实裁决：FAIL）

对 200 run 按 `(task_id, run_id)` 配对（100 对），配对 bootstrap 95% CI + sign test：

- mean Δ（KF − SA）= **+0.0000**
- 配对 bootstrap 95% CI = **[+0.00, +0.00]** → **下界 = 0，未 > 0**
- sign test：wins=0 / losses=0 / ties=**100**（100 对全部打平）

**裁决：GATE FAIL。** Δ=0 远未达 ≥3pp，bootstrap 下界未 >0。**KAFarmTwin 未在冻结 test_v2 上统计显著超越最强公平基线。** 不调整阈值、不删失败任务、不改 gold/评分器/基线预算。

---

## 4. 根因（如实）—— 已识别的 Benchmark 与执行链联合缺陷

> **结论修订（2026-08-17，Annotator 2 深度审计后）**：本节不再是"非方法缺陷、对两方法公平"的单因结论。F-016 的 0.2 vs 0.2 是 **Benchmark 标注设计约束（F-019）+ 执行链缺陷（Trace/Repair/规则引擎/计数/基线/门控等 P0 项）** 联合造成的，尚不能解释为"KAFarmTwin 与 SingleAgent 真实能力打平"。当前结果仅作为 **失败实验与调试证据** 保留，不作为论文最终实验，也不作为判断方法有效/无效的依据。

stepwise 已解除输出上限（F-018 RESOLVED），但 **绑定合约对非 memory 任务两方法同为结构性不可能**（记 **F-019**）：

1. **asset_routing（TN11–TN14）**：gold 绑定 `target` 为 `{subject}_asset`（如 `N11_mango_focus_asset`），**该 id 不在 `required_nodes` 中** → 无节点对应可经 `id_map` 对齐；方法只能输出语义资产目标，结构性不匹配。验证见 §5。

2. **data_binding（TN21–TN24）**：gold 元数据**全等严格**（`unit:"%"` vs 生成 `unit:"percent"`、精确 `metrics:["humidity"]` 键、`trait` 键），`binding_match` 的 `meta_ok` 全等比较使任何措辞差异即判错。

3. **rule_repair（TN31–TN34）**：gold 绑定 metadata 含**标注键** `"fixed": true`，`binding_match` 要求 `gen_md["fixed"]=="true"`；KAFarmTwin 的 `replace_asset`/`set_placeholder` 与 LLM 均不产出该键 → 即使 `_repair_adapter` 判 `repair_success=True`，图形绑定仍判错。旧 one-shot 归档中 KF 4 修复任务 20/20 `repair_success=False`。

**执行链缺陷（Annotator 2 已逐条核实，8 项 P0，修复后再重跑）**：
- P0-1 **Trace 链断裂**：`canonicalize_output` 把 `traceSteps` 折叠进 `trace.steps` 后丢弃顶层键，runner 却读 `out["traceSteps"]` → 恒空；空 trace 使 `evidence_precision` 退化为空洞的 1.0（`trace_evidence.py` L63）。
- P0-2 **Repair 执行/评分脱节**：R4 只查 `bindings` 不查 `node.asset_key`；runner 的 `final_state` 只传 objects 不传 bindings；R9 是空 `pass`；R10 需 initial+goal 同时传入（runner 从不这样）。
- P0-3 **计数/代价失真**：`stepwise_builder` 与 `llm_call_fn` 双重计 token/调用；latency 恒 0。
- P0-4 **memory 任务非真实 LLM**：`build_memory_answer` 是确定性共享助手，两方法同分来源。
- P0-5 **基线不全**：5 个基线只有 2 个（SA/KF）实际运行，最强公平基线可能未被测量。
- P0-6 **Gate 缺硬约束**：无 bootstrap CI 检查、无 per-task 5× 判定、critical_recall/fatal 用相对基线而非绝对 0.95/0.01 护栏。
- P0-7 **Benchmark 标注缺口**：TN11–TN14 资产目标 id 不在 required_nodes；TN31–TN34 依赖 `fixed:true` 标注键；TN21–TN24 全等元数据过严（与 F-019 重叠）。
- P0-8 **密钥曾明文入会话**（已从仓库文件移除；历史清理与轮换为人工操作，HUMAN_BLOCKED）。

**结论：当前 0.2 vs 0.2 不可解释为方法真实能力对比。** 不修改冻结 gold/评分器/阈值；按上述 8 项 P0 修复执行链后，在冻结 test_v2 上重跑正式 F-015/F-016 再做裁决。

---

## 5. 绑定引用完整性证据（gold 层面）

对全部 gold 绑定检查 subject/target 是否落在 `required_nodes`：

- **asset_routing**：12/12 绑定 target **N 不在** required_nodes（如 `N11_mango_focus_asset`）。
- data_binding / rule_repair：subject 与 target 均在 required_nodes，但 metadata 契约严格（data_binding 全等 keys；rule_repair 含 `fixed:true` 标注键）。

具体见 `数据/test_v2_gold.jsonl`。

---

## 6. 冻结完整性（A+ 协议校验）

```
$ cd experiments/v3/benchmark/test_v2 && sha256sum -c MANIFEST.sha256
test_v2_gold.jsonl: 成功
test_v2_public_inputs.jsonl: 成功
DATASHEET.md: 成功
CHANGELOG.md: 成功
ANNOTATION_REPORT.md: 成功
ANNOTATOR2_REVIEW.md: 成功
```
6/6 全部通过 → 冻结测试集未被本实验改动，无泄漏。

---

## 7. 诚实边界
- **未声明任何成功**；当前为 GATE FAIL，如实上报。
- 未修改成功阈值 / 删除失败任务 / 改测试集 / 改 gold / 改评分器 / 改基线预算。
- 旧 one-shot 200 run 与 stepwise 200 run **两者均如实归档**，可复算对比。
- 判定依据的可复现条目：`实验结果/数据/F015_stepwise_200run_v3_runs.jsonl`（SHA `de4f4437…c0fb1e`）。