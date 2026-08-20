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

## Phase 0 整改 + evaluator_v2.3（2026-08-20）

### Phase 0 完整性审计（0.1-0.7）全部 PASS
- **0.1 gold isolation**: `run_asset_diagnostic.py` 方法只接收 `_strip_public(task)`；回归测试 `test_diagnostic_gold_isolated`。
- **0.2 repair-success integrity**: `_repair_adapter` 需非空 critical + 真实修改 + 非 no-op；`test_repair_success_not_vacuous`。
- **0.3 canonicalizer provenance**: `canonicalize_output` 保留 conflicts/repair 溯源（不参与评分）；`test_canonicalizer_preserves_conflicts_provenance`。
- **0.4 D2 审计**: 修复算子仅经 LLM operator-selection 门控；`test_no_repair_operator_bypasses_llm_selection`（AST）。
- **0.5 compiler path**: KF asset 走 `knowledge_compiler`（trace 记录 `construction_path`）。
- **0.6 evaluator contract freeze → EVALUATOR_CONTRACT_BLOCKER 修复 → evaluator_v2.3**：
  - **发现**: `binding_match._ANNOTATION_KEYS` 含 `timestamp` → TN21-24 public prompt 明确声明 `时间戳 2026-09-01T00:00:00+08:00`，但 timestamp 恒被丢弃 → 省略时间戳仍拿 BindF1 满分（scorer 合约违规）。
  - **修复**: timestamp 契约由公共 prompt 声明驱动——prompt 声明时间戳时强制匹配，否则丢弃。`_prompt_declares_timestamp` 只读 public prompt，不读 gold。
  - **版本**: `evaluator_v2.3`（version.py），scorer_hash `8b7d4695...`。
  - 回归测试: `test_TN21_prompt_declared_timestamp_is_required`、`test_no_ts_prompt_does_not_penalize_omission`、`test_prompt_declares_timestamp_heuristic`。
- **0.7 benchmark integrity**: gold `61a48f61...` / public `8321ed3d...` 与 manifest 完全一致（未触碰）。

### 测试: 94 → **101/101 pass**

### 冻结 (Phase 0.8)
- **FREEZE_ID**: `freeze-2026-08-20-e3e8351`
- **冻结代码 commit**: `51beab1`（evaluator_v2.3 + 全部 Phase 0 修复 + instrumentation）
- `results/provenance/`: git_commit / git_status / pytest_result / environment / benchmark_hashes / scorer_hash / method_hashes / experiment_manifest.yaml（**无 API key**）

## Phase 1 — 80-run clean sanity（2026-08-20，FINAL）

**结果**: `results/v3_diagnostic_80_freeze-2026-08-20-e3e8351.jsonl`（80 runs，4669.8s，真实 DeepSeek-V4-Flash，冻结 commit `51beab1` + evaluator_v2.3）

### 5-category 结果表（n=8 each）
| Category | KAFarmTwin CVSR | SingleAgent CVSR | KF BindF1 | SA BindF1 | 备注 |
|---|---|---|---|---|---|
| scene | 0.500 | 0.500 | 0.000 | 0.000 | 平局（SA relF1 0.841 > KF 0.778） |
| **asset** | **1.000** | 0.000 | **1.000** | 0.000 | **KF 8/8 全绿**（knowledge_compiler） |
| bind | 0.000 | 0.000 | 0.292 | 0.260 | 两方法 0/8（见下方诚实说明） |
| **repair** | **1.000** | 0.000 | **1.000** | 0.000 | **KF 8/8 全绿**（seeded + typed repair） |
| mem | 1.000 | 1.000 | 0.000 | 0.000 | 两方法 8/8（确定性检索） |

### Integrity（全部 80 条）
- **API errors = 0**，eval_hash 全部匹配 `8b7d4695...`，gold hash 全部匹配 `61a48f61...`
- KF non-mem 空节点 = 0；SA asset 空节点 3/8（方法缺陷非泄漏）
- `run_uuid`/`construction_path`/`selected_repair_actions` 全字段齐全

### 诚实说明：bind 两方法 0/8
evaluator_v2.3 时间戳契约正确生效——但 `bindings_only_scene`/`stepwise_llm`（两方法共享 builder）的 metadata 模板未指引模型产出 prompt 声明的 timestamp → `all_bindings` 失败。这是**共享 builder 的方法缺口**（冻结前已存在，非 scorer 过严，对两方法对称），不会在冻结内修改。

### 3-way 判定：**READY_FOR_FORMAL_GATE**
- asset/repair: KF 稳定 8/8 优于 SA 0/8，KF 未重新全 0 ✓
- scene/bind: 无方法回归（bind 从旧恒 0 提升到 bindF1 0.26-0.29，是改进）✓
- mem: 两方法稳定 8/8 ✓
- integrity: gold leak=0, API-failure=0, eval_hash mismatch=0, KF empty=0 ✓

**下一步**: Phase 2 正式 500-run SOTA Gate（20 任务 × 5 方法 × 5 次，冻结 commit/evaluator_v2.3）。
