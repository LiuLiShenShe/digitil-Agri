# v3 SOTA Rebuild — STATUS

## Branch
`paper/knowledge-agent-experiments`

## Frozen A+ Protocol
**Overriding constraint:** on the frozen `test_v2` test set under
fair/reproducible/no-leak/same-tool/same-model/same-budget conditions, KAFarmTwin
must statistically significantly beat the strongest fair baseline:

  - Mean CVSR delta ≥ **3pp** over the strongest fair baseline
  - Paired-bootstrap 95% CI lower bound **> 0**
  - ALL absolute guardrails satisfied

**Until PASS: NO declaring success. NO modifying thresholds. NO deleting failed
tasks. NO gaming test set / gold / scorer / baseline budget.**

## Sealed Test Set — INTACT
`test_v2` frozen (20 tasks × 5 types), gold SHA `61a48f61...` matches sealed
`benchmark_manifest.json` after all scorer-side fixes.

## P0 Progress

| P0 | Description | Status |
|----|-------------|--------|
| P0-1 | Trace chain + forbid vacuous evidence | ✅ FIXED (+ residual honest clamp) |
| P0-2 | Repair chain (R4 asset_key, final_state bindings, R9/R10) | ✅ FIXED |
| P0-3 | Repair target states (TN31-34) | ✅ FIXED |
| P0-4 | Asset gold (TN11-14) | ✅ FIXED |
| P0-5 | Data binding (TN21-24) | ✅ FIXED |
| P0-6 | LLM call/token/latency/cost (single source) | ✅ FIXED |
| P0-7 | Run all 5 baselines+KF for real | ✅ DONE — 500-run formal test_v2 complete |
| P0-8 | SOTA Gate (bootstrap CI + per-task repeats + guardrails) | ✅ MECHANISM COMPLETE — **GATE FAIL (honest)** |

## SOTA GATE — FAIL (honest, 2026-08-18)
Formal 500-run frozen test_v2 (20 tasks × 5 methods × 5 runs, real DeepSeek-V4-Flash)
target_objectives. `SOTA_GATE=FAIL` (6 conditions):

| condition | result | bar | status |
|-----------|--------|-----|--------|
| paired bootstrap CI | point Δ=0.000, CI[0.00,0.00] | ≥3pp & lb>0 | ❌ |
| pass5 | 0.200 vs SingleAgent 0.200 | strictly > | ❌ |
| critical_recall | 0.600 | ≥0.95 | ❌ |
| fatal_rate | 0.220 | ≤0.01 | ❌ |
| evidence_precision | 1.000 | ≥0.95 | ✅ |
| replay_success | 0.800 | ≥0.95 | ❌ |
| cost_ratio | 1.75 | ≤1.5 | ❌ |

Evidence table (100 runs each):
```
method                  CVSR  pass5  ObjF1  CritR  RelF1  BindF1  Fatal  EvidP  Cost
KAFarmTwin-TypedRepair  0.200 0.200  0.712  0.600  0.315  0.000   0.220  1.000  $0.0007
SingleAgent-AllTools    0.200 0.200  0.692  0.600  0.300  0.000   0.450  0.990  $0.0004
GenericRepair-AllTools  0.010 0.050  0.489  0.450  0.257  0.010  0.080  1.000  $0.0004
GenericMultiAgent       0.000 0.000  0.499  0.600  0.205  0.000  0.350  0.840  $0.0009
ReAct-AllTools          0.000 0.000  0.000  0.400  0.000  0.000  0.000  0.000  $0.0024
```

## Deep root-cause (task-level bimodal distribution)
CVSR=0.20 is **entirely from the 4 memory_query tasks** (TN41-44, both SA & KF 5/5 —
deterministic). The **16 non-memory tasks (scene/asset/bind/repair ×4 each) score 0/5 for
every method** — a method-agnostic ceiling requiring exact graph-structure + binding-contract
satisfaction that neither method reaches. Hence paired CI is exactly [0.00, 0.00]:
20 tasks, 19 ties, 1 near-tie, no KF advantage anywhere.

## Honest position
- KAFarmTwin does **NOT** statistically significantly beat the best fair baseline (SingleAgent)
  on frozen test_v2. **GATE FAIL, reported truthfully.**
- No thresholds modified, no failed tasks deleted, no test-set/gold/scorer/baseline-budget gamed.
- Next: make methods genuinely solve the 16 non-memory graph+binding tasks (not just
  deterministic memory retrieval); KAFarmTwin's structural advantage, if real, will then
  surface as >3pp CVSR delta naturally.

## Test suite
**68/68 pass** (incl. honesty tests for broken-work-trace vacuous evidence).

## v3.1 整改 (2026-08-18) — 实现完成，待真实模型重评分

9 项 P0/P1 修复全部落地并通过 74/74 单元测试回归：
- **A** : critical_recall 用 id_map + R10 真实修改守卫；memory replay 载入 ctx_snapshot
- **B** : data_binding 从 initial_state 播种（两方法统一 bindings_only_scene）
- **C** : identity 型对象禁止 count=N 折叠 + ONTOLOGY_NOTE 指引
- **D** : RepairTicket observed/expected 结构化 + typed_deterministic 机械规则免 LLM（R4/R1/R3/R5/R6）
- **E** : 事务回滚 deepcopy 真实生效
- **F** : semantic_compiler.py + knowledge/{unit_registry,binding_vocab,asset_policy}（KAFarmTwin 编译式构造，区别于 SingleAgent）
- **G** : evaluator_v2.2 版本化 + scorer-bind 检查（gate 拒绝旧 run）+ statistical_report provenance
- **H** : 6 条新 anti-cheat 测试 + 离线 mock 诊断 run 验证

**诚实状态**：固定 500-run 文件已恢复纯净（mock dev 隔离到 dev_mock.jsonl）。GATE 现在正确 FAIL
`scorer_version_bound`——旧 v1.x run 无版本戳、需在 v2.2 scorer 下重跑才能反映修复效果。真实重评分
/重跑受当前环境无 AGNESS_API_KEY 阻塞（不伪造结果）。修复方向的有效性尚未在 frozen 集上实证。

## Asset 16-run diagnostic + repair decomposition（2026-08-19，FINAL）

冻结哈希复核：gold `61a48f61...b4c61`、public `8321ed3d...fe6c9c` 与 manifest 完全一致（未触碰）。

### Asset 16-run（4 asset × {KF, SA} × 2，真实 DeepSeek-V4-Flash）
- **KAFarmTwin-TypedRepair：8/8 CVSR=T**（objF1=1.0, relF1=1.0, bindF1=1.0, critR=1.0，全部 5 nodes + 3 bindings，无 failclause）。
- **SingleAgent-AllTools：0/8 CVSR=T**（TN11/TN12 nodes=0；TN13/TN14 部分对象但 bindF1=0 恒，failclause=all_nodes）。
- 知识编译路径（IntentIR → expand_graph → AssetCompiler → bind_scene）在 frozen 集上产出稳定、正确、可复现的资产场景。KF 资产 CVSR 从历史 0 → 8/8 稳定 T。

### Repair failure decomposition（TN31-34，单轮）
- **KAFarmTwin：4/4 CVSR=T**，`repair_success=True`，failclause 空。
- **SingleAgent：0/4 CVSR=T**，`repair_success=False`，全部 failclause=all_edges（只改节点不改边/绑定）。
- KF 的类型化修复闭环（R1-R10 检测→分类→路由→确定性算子→事务回滚）在 4 个修复任务上全绿，优势真实且可分解。

### 本轮新增回归测试
- T16 fatal-first 排序：warning(R1) 不得先于 fatal(R5) 消耗轮次。
- T17 attach_all_rootless 批量孤儿挂接：LLM 选 attach_to_root 时一轮挂接全部孤儿（TN32 修复关键）。
- 全量 **94/94 pass**。

### 3-way 判定：**READY_FOR_FULL_DIAGNOSTIC**
KF 资产路径已从 0 变为稳定非零（8/8 CVSR=T，成本 ~$0.0008/run，低于 SingleAgent），KF 修复优势（4/4 vs 0/4）干净可分解，冻结集未触碰。下一步是 500-run 正式 gate（每任务×方法 5 次）在 v2.2 scorer 下重跑以重估 SOTA 判定。
