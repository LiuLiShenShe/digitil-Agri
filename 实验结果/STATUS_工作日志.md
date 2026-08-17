# KAFarmTwin v3 — STATUS

当前阶段：test_v2 已冻结（v2-sealed，Annotator 2 批准）；F-015 stepwise 重跑完成 → **F-016 GATE FAIL（delta +0.00，CI [0,0]，未达标）**。
状态：RUNNING_F015（两次完成）→ **GATE_FAIL（F-016，确认）** — 诚实结论：解除输出上限后，KAFarmTwin 仍**未**在冻结 test_v2 上统计显著超越最强公平基线（binding 合约结构性上限，两方法同灭）。

## 当前 SOTA / 基线（dev 集 5× 真实 LLM，8 任务 × 2 方法 × 5 次 = 80 run）
| 方法 | CVSR | pass5 | objF1 | critR | fatal率 | evidP | replay |
|------|------|-------|-------|-------|--------|-------|--------|
| KAFarmTwin-TypedRepair | 0.375 | 0.375 | 0.799 | 0.875 | 0.0 | 1.0 | 1.0 |
| SingleAgent-AllTools | 0.250 | 0.250 | 0.510 | 0.525 | 0.15 | 1.0 | 0.727 |

- **配对 bootstrap（KF vs SA）**：mean diff +0.125，95% CI [+0.025, +0.225]，下界>0，p=0.0044。Pareto=[KF]。
- dev 结果有效（80 run 无 LLM error），但 **非 SOTA Gate 证据**（gate 定义在 frozen test split，见 sota-gate/spec.md L15）。
- replay 修复后 KF 全任务 replay=1.0、evidP=1.0（trace_proxy deepcopy 修复，见 FAILURES F-005）。

## 距离 SOTA Gate — 硬阻塞
- **[BLOCKED] LLM 账户余额耗尽（F-006）**：测试集 5× 运行中 SiliconFlow 报 HTTP 402，28/40 test run 是 API 失败伪影，测试证据不完整。需充值后重跑 28 个缺失 run。
- **[BLOCKED] T031-T035 盲 Gold 未标注（F-004）**：第 3 阶段标注者=用户，5 任务待人工复核。
- [x] gate 脚本已加 `split_is_test` 守卫，dev-only 结果不再误判 PASS。

## 完成里程碑
- [x] 阶段0-5 / 评分器-金标准 8/8 dev 对齐 / 反作弊 21 绿
- [x] 修复循环架构：batched ops 修复、add_edge→parent 一致性、trait(23)/memory(25-26) 数据模型
- [x] trace_proxy deepcopy 修复 → replay 全绿（F-005）
- [x] dev 集 5× 统计实验完成（80 run，无 LLM error）
- [ ] 测试集完整 5× 统计（被 F-006 余额阻断）
- [ ] SOTA Gate 通过（含 gold-hash、cost ≤1.5×、pass5、测试集标注）
- [ ] 测试集 T031-T035 盲测 Gold 标注（BLOCKED_HUMAN_ANNOTATION）

## 阻塞项
- `BLOCKED_LLM_BUDGET`（F-006）：SiliconFlow 余额充值后重跑测试集。
- `BLOCKED_HUMAN_ANNOTATION`（F-004）：T031-T035 盲 Gold 待用户复核。

## 下一步（解锁后）
```
# 充值 + 标注完成后，重跑完整测试集（T27-T30 + 标注后的 T031-T035）
python3 experiments/v3/scripts/run_fair_baselines.py --split test --runs 5 \
  --methods KAFarmTwin-TypedRepair,SingleAgent-AllTools
make statistical-report --split test && make sota-gate
```
- [x] 修复循环架构：batched ops 修复、add_edge→parent 一致性、trait(23)/memory(25-26) 数据模型
- [x] 真实 KAFarmTwin T19/T20/T22/T24 ok、T20 修复循环真实收敛 CVSR=1.0
- [ ] 阶段8 ≥5 次/任务×方法 统计实验 + 配对 bootstrap/sign test/Pareto
- [ ] 阶段8 SOTA Gate 通过（含 gold-hash、cost ≤1.5×、pass5、Names 等全部条件）
- [ ] 测试集 T031-T035 盲测 Gold 标注（BLOCKED_HUMAN_ANNOTATION）

## 阻塞项
- `BLOCKED_HUMAN_ANNOTATION`：测试集盲 Gold 待用户复核。
- 真实 LLM 修复循环方差大：单次运行可能不收敛，需多运行统计平均。

## 下一步（下一条可执行命令）
```
# 6 个 repair 任务 × 5 次 × 2 方法（KF vs SA）对比统计
python3 experiments/v3/scripts/run_fair_baselines.py --split dev --runs 5 \
  --methods KAFarmTwin-TypedRepair,SingleAgent-AllTools
# 达标后
make statistical-report && make sota-gate
```
## 2026-08-05 更新：dev vs test 诚实对比（SiliconFlow V4-Flash，same-model）
- **dev**（T19-T26，8 任务）：KF CVSR=0.375 vs SA 0.250，配对 bootstrap +0.125，95%CI [+0.025,+0.225] 下界>0，p=0.0044，Pareto=[KF]。80 run 全部有效。
- **test**（T27-T30，4 记忆查询任务）：**两方法全部 CVSR=0（0/40）**，无 API error。根因是 F-007：test gold 对 memory_query 检索任务要求构建植物场景（T27/T30 各 20 Plant），prompt 与 gold 自相矛盾。
- **Gate 状态**：FAIL（split 为 test 才算数；且 test gold 需先解决 F-007 标注矛盾 + T031-T035 仍未标注）。诚实结论：**当前无法通过 SOTA Gate，dev 优势不能作为 test gate 证据。**

## 2026-08-05 A+ 重建评测协议：F-007 → F-014 完成
- **F-007**: test_v1 归档 + INVALIDATION_REPORT（T27-T30 Prompt-Gold 矛盾，CVSR 恒 0 根因）
- **F-008**: 多任务 Gold Schema v2（task_type + per-type gold，schema.json 重写）+ task_types.py 分发
- **F-009**: memory_query fixture + Oracle（确定性 expected_answer/evidence，不要求建场景）
- **F-010**: Query-CVSR（10 条件二元指标 + 连续诊断）+ 12 单测
- **F-011**: T27-T30 重标注迁至 regression/（oracle 自洽通过）
- **F-012**: T031-T035 标注审查包（5 包，PENDING_HUMAN_REVIEW，T034 用 Query-Gold）
- **F-013**: Gold 静态审计器（能捕获 test_v1 缺陷类）+ 6 单测
- **F-014**: test_v2 候选集（20 任务 × 5 类 × 4，0 审计错误，oracle 自洽，SHA-256 记录）

**Gate 状态**: BLOCKED（两个待人工解锁项）：
1. method/evaluator freeze commit（experiments/v3 未提交）
2. test_v2 20 任务 gold 人工批准（annotator 2 = 用户）+ T031-T035 复核

## 2026-08-05 Annotator 2 第一轮复核 → 全部修订完成
- Annotator 2 复核:test_v2 20/20 和 T031-T035 5/5 均需修订,0 条可直接批准。
- 已按 6 类系统性问题全部修订:scene(WS+Cam+equivalence)、asset(补光占位+fatal)、bind(prompt 明确+时间戳+equivalence)、repair(资产类别设备派生+修正后编码+双变体)、memory(trend+行关系+TN43 修复+Oracle 统一)、T031-T035 同步。
- **验证**:gold audit 0 错误;39 测试全绿;4 memory_query Oracle 自洽 + expected_outcome 统一;MANIFEST.sha256 重冻结。
- **Gate 状态**:BLOCKED_ANNOTATION_REVIEW — 已重新提交第二轮复核;所有任务仍 PENDING_HUMAN_REVIEW。

## 2026-08-07 Annotator 2 第二轮复核 → P0/P1 全部修复（v2.0-rev2）
- **P0-1 防泄漏**: test_v2_public_inputs 改白名单（task_id/task_type/difficulty/prompt/policy_ref/initial_state），无 required_nodes/edges/bindings/critical/equivalence/fatal/forbidden/variants 泄漏。`test_public_inputs_have_no_gold_fields` 锁定。
- **P0-2 Schema**: schema.json 重写，96 → 0 错误；task_id slug pattern、review_status 统一 {pending,needs_revision,approved,rejected}、allowed_variants/equivalence_groups 对象化。gold_audit 现并入 schema 校验。
- **P0-3 资产绑定**: focus→focus_asset、bg→bg_asset、light_dev→placeholder asset_job；referential-integrity 测试。
- **P0-4 repair 双分支**: 专用适配器接受 replace_asset OR set_placeholder；保留错误绑定/no-op 均失败；TN31-TN34 两分支均可评分。
- **P1-1 equivalence_groups** 对象结构；node_match 兼容新老格式。
- **P1-2 data_binding** initial_state 预置对象 + relations。
- **P1-3 memory gold** ≥3 记录/天、干扰记录、trend(net_change_direction+shape)、TN43 阈值 35°C；query_cvsr 评分 daily_means+trend。
- **P1-4 T031-T035** 包修订：T031 control_bind、T032 event_bind、T033 双分支、T034 增强、T035 referential-clean。
- **P1-5 哈希同步**: MANIFEST/DATASHEET/benchmark_manifest 全部重冻结并校验通过。
- **验证**: 53 测试全绿（含 test_benchmark_integrity.py 14 条）；gold audit 0 错误 + schema 0 错误；4 memory Oracle 自洽 + T034 自洽；repair 双分支 4/4 可评分；MANIFEST sha256sum -c 6/6 成功。
- **Gate 状态**: **BLOCKED_ANNOTATION_REVIEW** — v2.0-rev2 已重新提交第二轮复核；所有任务仍 `pending`（未设 approved）；F-015/F-016 仍被阻塞。

## 2026-08-07 Annotator 2 批准 → test_v2 冻结（v2-sealed）
- Annotator 2（用户）第二轮复核 **批准** v2.0-rev2。执行 `approve_freeze.py`：
  - 20 个 test_v2 任务 `review_status`: pending → **approved**（一个单向门，Idempotency 守卫拒绝重复批准）。
  - T031-T035 5 个标注包同步置 `approved`。
  - gold 静态审计 → **20 clean / 0 errors / 0 warnings**（pending 警告随批准消失）。
  - MANIFEST.sha256 重密封：gold `61a48f60…b4c61`、public `8321ed3d…e6c9c`、文档 4 项不变；`sha256sum -c` 6/6 成功。
  - benchmark_manifest.json: `v2-candidate` → **`v2-sealed`**，note 记录批准与冻结单向门。
  - 53 测试全绿。
- **Gate 状态**: **UNLOCKED** — 冻结批准完成；test_v2 可自由用于 F-015/F-016（gold 仅用于评分，不注入 prompt）。评审准入条件全部满足。

## 2026-08-08 F-015w 布线完成 → F-015 真实 LLM 回放进行中
- **F-015w 功能补全**(使 test_v2 5 类任务可公平评分):
  - `harness/memory_retrieval.py`: 确定性窗口派生(≥3记录/天的连续日)+Oracle 同语义聚合;4 个 memory 任务 Query-CVSR 全过。
  - `tools.ts/event_query`: 由空壳改为实读 `ctx.memory_state`，按 metric/object/range 过滤+聚合。
  - 单/多方法 memory_query 分支产出结构化 `answer`;runner 注入 memory_state + threading answer。
  - `metrics`: task_type 路由 memory→Query-CVSR、repair→disjunctive `_repair_adapter`。
  - `_apply_patch` 修 `replace_asset`(读 changes.target,写 asset_key)/`set_placeholder`(asset_job placeholder binding),与 evaluator 对齐。
  - runner/gate 接入 test_v2(public+gold),gate 校验 test_v2_gold hash。
  - 53 测试全绿;dev 结果备份 archive/dev_20260808。
- **Gate 状态**: RUNNING_F015 — 启动 test_v2 20任务×2方法×5次=200 run 真实 LLM(SiliconFlow DeepSeek V4 Flash)。

## 2026-08-08 F-015 完成 → **F-016 GATE FAIL（诚实结论）**
- **修复两个 evaluator/harness 恒错缺陷**（方法无关，公平）：
  - **F-016(evaluator)**：`edge_match`/`binding_match` 未复用 `node_match` 的生成⇄required 节点对应 → 边/绑定按字面 gold id 匹配，因 gold id 从不注入方法，relation/binding F1 结构性恒 0。新 `node_match.id_correspondence` 由已匹配节点派生 `gen_id→req_id`（含 count 展开基名），edge/binding 经 remap 匹配；方法一致、不补充。
  - **F-017(token cap)**：`max_tokens=1200` 截断大型场景 JSON → `content_json=None` → 空场景。共享 `ONTOLOGY_NOTE` 加【实体压缩规则】(同类重复对象用 `count=N`)，`id_correspondence` 映射基名。TN01 复算 nodes 18/18、edges 4/5；55 测试全绿。
- **F-015 结果（200 run，含 0 LLM error → 有效）**：
  | 方法 | mean CVSR | pass5 | object_f1 | binding_f1 |
  |------|-----------|-------|-----------|-----------|
  | KAFarmTwin-TypedRepair | 0.22 | 0.25 | 0.573 | 0.0 |
  | SingleAgent-AllTools | 0.20 | 0.20 | 0.481 | 0.0 |
- **配对统计（KF vs SA，同任务 5 次）**：mean Δ = **+0.02**；配对 bootstrap 95% CI = **[0.00, 0.05]（0 含于下界）**，P(Δ>0)≈0.87。**20 任务 19 个完全打平**，仅 TN02 不同（KF 2/5 vs SA 0/5）。
- **0.2 基线来源**：两方法 mean CVSR 的 0.2 全部来自 4 个 memory 任务（40/40 都过，确定性 `build_memory_answer` 两方法一致）。非 memory 16 任务：KF 仅 TN02 2/5、SA 0/5；asset/bind/repair 全部 0/5。
- **根因（模型能力上限，非方法缺陷）**：非 memory 任务的 scene+asset 绑定+修复 JSON 超出单次 ~1200 token 输出上限 → `finish=length` 截断非法 JSON → 方法空场景（asset/bind/repair 全灭）。gold 本身可满足（3-6 节点/1-3 绑定），是模型单 shot 输出上限，对两方法一致。
- **Gate 裁决：FAIL** — Δ=+0.02 远未达 ≥3pp，bootstrap 95% CI 下界=0 未 >0。KAFarmTwin **未在冻结 test_v2 上统计显著超越 Best 公平基线**。不调整阈值/不删失败任务/不改基线预算。
- 数据：`results/v3_runs.jsonl`（200 run）；旧失效结果 `results/archive_v3_runs.jsonl`；F-006 余额、F-016 修复、F-017 见 FAILURES.md。

## 2026-08-08 用户选择 Option A（stepwise 构建）→ F-015 重跑 → **F-016 GATE FAIL（诚实结论，确认）**
- **用户决策**：Option A — 实现分步/增量场景构建，解除模型单次输出上限对两方法的一致性压制（F-018 根因），机制对两方法完全相同，然后重跑 F-016。
- **实现（F-018 解除）**：
  - 新增共享 `harness/stepwise_builder.py`：`stepwise_build_scene()` 将场景拆成 3 次独立 LLM 调用（objects → relations → bindings），每次都在 ~1200 token 输出上限内；上一步的真实 id 作为下一步上下文；解析同时支持 dict 包裹和**裸数组**两种形态（模型对 objects 步常返回 `[{...}]` 而非 `{"objects":[...]}`）。
  - 两方法（SingleAgent 与 KAFarmTwin）**同一** builder，场景创作能力对称（公平）。
  - **修复方法分派诚实性**：SingleAgent 修复分支判 `category=="rule_repair"`（runner 将 task_type 映射为 `category="repair"` 后恒 false）→ 修复任务被静默当场景重建。改为 `category=="repair" or task_type=="rule_repair"`，诚实 no-repair 分支真正触发（与 KAFarmTwin 修复循环对称）。新增反作弊测试 18。
  - 58 测试全绿。
- **F-015 重跑（200 run，0 LLM error，有效）**：
  | 方法 | mean CVSR | pass5 | object_f1 | critical_recall | relation_f1 | binding_f1 | fatal率 |
  |------|-----------|-------|-----------|-----------------|-------------|------------|---------|
  | KAFarmTwin-TypedRepair | **0.20** | 0.20 | 0.724 | 0.60 | 0.326 | **0.0** | 0.28 |
  | SingleAgent-AllTools | **0.20** | 0.20 | 0.705 | 0.60 | 0.316 | **0.0** | 0.42 |
- **配对统计（KF vs SA，100 对）**：mean Δ = **+0.0000**；配对 bootstrap 95% CI = **[+0.00, +0.00]（下界=0，未 >0）**；sign test wins=0/losses=0/ties=100。**100 对全部打平**，无任何一对 KF 胜出。
- **诚实结论：F-016 GATE FAIL（确认）**。stepwise builder 已解除输出上限（F-018 RESOLVED：asset/bind/repair 现产出 nodes/edges，objF1/relF1 均>0），但 **binding_f1 恒 0**（非 memory 任务全灭）→ CVSR 只由 4 个确定性 memory 任务提供，两方法完全同分。KAFarmTwin **未在冻结 test_v2 上统计显著超越最强公平基线**。不调整阈值/不删失败任务/不改 gold/评分器/基线预算。
- 数据：`results/v3_runs.jsonl`（stepwise 200 run）；旧 one-shot 200 run 归档 `results/archive/F015_one_shot/`；F-018 根因与修复、F-019 绑定合约结构性上限见 FAILURES.md。
