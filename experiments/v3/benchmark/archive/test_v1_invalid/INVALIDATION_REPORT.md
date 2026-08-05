# INVALIDATION_REPORT — test_v1

**基准版本**: `test_v1`（已作废）
**状态**: `INVALID` — 任务 Prompt 与 Gold 评价目标根本冲突，不能用作 SOTA Gate 证据
**归档日期**: 2026-08-05
**发现日期**: 2026-08-05（test 5× 重跑，SiliconFlow V4-Flash，40 run 无 API error）

---

## 1. 受影响任务

| 任务 | category | Prompt 真实任务类型 | Gold 要求 | 冲突 |
|------|----------|--------------------|-----------|------|
| T27 | memory_query | 检索聚合（"查询最近 7 天环境状态，汇总温度、湿度、CO2…"） | required_nodes 20 Plant + Greenhouse root + contains 边 | 检索任务被要求构建场景 |
| T28 | memory_query | 检索（"查询植株 P15 生育阶段、F2DMAS 版本…"） | required_nodes=[]（空） | 无评判维度，CVSR 结构上失败 |
| T29 | memory_query | 检索（"查询摄像头 C02 观测覆盖…"） | required_nodes 3 Plant + Camera + CropRow + 边 | 检索任务被要求构建场景 |
| T30 | memory_query | 检索聚合（"生产日报：环境摘要、设备状态、灌溉记录…"） | required_nodes 20 Plant + Greenhouse root + 边 | 检索任务被要求构建场景 |

## 2. Prompt 的真实任务类型

T27-T30 全部为 **memory_query（状态检索/时序聚合问答）**。Prompt 要求 Agent 从既有环境状态中**查询并汇总**（温度、湿度、CO2、充光、告警、生育阶段、观测覆盖、日报），而非**构建/变更**对象图。这是 τ-bench 式"从执行后状态检索正确答案"的评测意图，评价目标应与任务意图和环境状态一致。

## 3. 原 Gold 所要求的错误目标

原 `test_gold.sealed.jsonl` 对 T27-T30 用 `required_nodes` / `required_edges` 表达**场景构建**目标：

- T27：`required_nodes = [{"type":"Greenhouse","count":1},{"type":"Plant","count":20}]` + `required_edges=[{"subject":"greenhouse_root","predicate":"contains","object":"tomato_01"}]`
- T30：同上（20 Plant）
- T29：3 Plant + 1 Camera + 1 CropRow
- T28：空 required_nodes

这些目标把"检索并返回正确答案"错误地映射成"构建一个含 N 株植物的对象图"。

## 4. 为什么现有 CVSR 恒为失败

现评分器（metrics.py）对所有任务统一用对象图匹配：`match_nodes`（required_nodes 匈牙利匹配）+ `match_edges` + `match_bindings` + 规则引擎 + evidence。CVSR 只有 `all_nodes AND all_critical AND all_edges AND all_bindings AND no_fatal AND evidence_ok` 全部为真才通过。

对 memory_query：
- Agent 正确执行检索（不构建场景，nodes=[]），但 required_nodes 要求 20 Plant → `match_nodes` 必然未全部覆盖 → CVSR=False。
- 即便 Agent 真的构建了 20 Plant 场景，也与 Prompt 的检索意图无关，`required_edges` 若缺一条仍 False。
- T28 required_nodes=[]，`match_nodes` 空满足，但无 fatality/evidence 之外的维度，CVSR 结构上取 False（因 repair_success=None 且其他维度空）。

结论：**CVSR 在 T27-T30 恒为 0 是该错误评测目标的必然结果**，不是任何方法（包括 KAFarmTwin）的真实能力反映。

## 5. 受影响的历史实验结果

- **test 5×（2026-08-05，V4-Flash）**：T27-T30 两方法（KAFarmTwin-TypedRepair、SingleAgent-AllTools）全 5 次 × 5=40 run，**CVSR 全部 False（0/40）**。无 API error，evidence_precision=1.0。结果保留在 `experiments/v3/results/v3_runs.jsonl` 原始日志，不删不改。
- 此 0/40 **不得**被解释为"KAFarmTwin 在检索任务上失败"，因为 0 分来自 Prompt-Gold 矛盾，而非方法真实表现。
- dev 集（T19-T26）80 run 有效且无此矛盾，标为 `PRELIMINARY_DEV_RESULT`，不作 SOTA Gate 最终证据。

## 6. 文件 SHA-256

| 文件 | SHA-256 |
|------|---------|
| `test_public_inputs.jsonl` | `27902c0c32f141e9da8e4bd296c0bcb54a49570d1c3463ed7191f2d7c4cb1cc1` |
| `test_gold.sealed.jsonl` | `b41069c6d07990f49cdc50e10322b80d8cf3f717467905f732fba508397c4f4e` |
| `benchmark_manifest.json` | `0e3b372c9c3cdc567452621d7b56b587e07de6c7b1de4a15aab8fd7d811a3bdb` |

## 7. 修复方案（A+ 重建评测协议）

1. 重建多任务 Gold Schema：任务显式含 `task_type`（scene_construction / asset_routing / data_binding / rule_repair / memory_query），不同任务类型用各自适应的 CVSR，**不再用单一对象图 required_nodes 评价所有任务**。
2. memory_query 改为**状态式检索**：提供确定性 `initial_state`（含 timeseries/events/daily_reports），Agent 从既有状态检索返回答案；Query-CVSR 判目标/时间窗/指标/聚合/数值/单位/证据/无副作用，而非构建场景。
3. T27-T30 重标注后迁入 `benchmark/regression/` 或 `dev_v2`，仅作评分器验证 / memory 工具回归 / 案例分析，**不再作最终隐藏测试集**。
4. 新冻结 `test_v2`（≥20 任务、每类≥4、memory_query≥4、rule_repair≥4，与 train/dev 不同对象名/数量/时间窗/数据值），冻结前通过静态 Gold 审计。

## 8. 新版本编号

- **test_v1**（本报废版本）→ 归档于 `benchmark/archive/test_v1_invalid/`
- **test_v2**（新冻结版本）→ `benchmark/test_v2/`（见 F-014）

---

## 状态结论

当前 SOTA Gate 状态: **`BLOCKED_INVALID_BENCHMARK`**
（不是 `FAIL_METHOD`）
