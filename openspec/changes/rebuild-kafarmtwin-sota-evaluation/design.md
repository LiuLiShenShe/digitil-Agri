# Design — Rebuild KAFarmTwin SOTA Evaluation (experiments/v3)

## 架构总览

```
experiments/v3/
├── STATUS.md / WORKLOG.jsonl / DECISIONS.md / FAILURES.md
├── reports/{sota_definition.md, reproducibility_manifest.json}
├── benchmark/               # 版本化冻结基准
│   ├── schema.json, train.jsonl, dev.jsonl,
│   ├── test_public_inputs.jsonl, test_gold.sealed.jsonl,
│   ├── annotation_guideline.md, adjudication_log.jsonl,
│   └── benchmark_manifest.json
├── scripts/
│   ├── benchmark/expand_legacy_tasks.py   # 30条旧任务 → typed gold
│   ├── run_fair_baselines.py              # 每(任务×方法×模型)≥5次
│   ├── run_ablation_v3.py                 # 端到端消融（feature flags）
│   ├── run_robustness.py                  # 多模型鲁棒性
│   ├── statistical_report.py              # bootstrap/CI/配对
│   └── run_sota_gate.py                   # 唯一出口
├── evaluators/             # 独立语义评分器（不调用方法内部状态）
│   ├── node_match.py, edge_match.py, binding_match.py,
│   ├── state_match.py, rule_engine.py, trace_evidence.py,
│   ├── replay.py, metrics.py, statistical_tests.py
├── harness/                # 公平共享基础设施
│   ├── tools.py, validator_api.py, trace_proxy.py,
│   ├── budget.py, canonicalizer.py
├── methods/                # 5 个主方法 + DeterministicFallback
│   ├── single_agent.py, react.py, generic_multia_agent.py,
│   ├── generic_repair.py, kafarmtwin_typed_repair.py,
│   └── deterministic_fallback.py
└── tests/test_anti_cheat.py
```

## 数据契约（benchmark/schema.json）

任务 JSON（对齐总控 §4.1）：

```json
{
  "task_id": "T001", "category": "scene_build|asset_route|data_bind|repair|memory_query",
  "difficulty": "easy|medium|hard", "prompt": "...",
  "initial_state": {}, "goal_state": {},
  "required_nodes": [], "optional_nodes": [], "forbidden_nodes": [],
  "required_edges": [], "required_bindings": [], "constraints": [],
  "equivalence_groups": [], "critical_objects": [], "allowed_variants": []
}
```

- `required_nodes`：typed 节点（type/role/key_attrs/parent_context），对同型多实例显式计数。
- `initial_state`/`goal_state`：**repair 任务必填真实状态**；评分对比最终状态 vs goal_state，并验证 `critical_objects` 被修改。
- 多种合法解经 `equivalence_groups`/`allowed_variants` 表达。

## 评分器设计

- `node_match.py`：约束匹配 + 二分图/匈牙利最优匹配（`scipy.optimize.linear_sum_assignment`），等价组允许语义等价。
- `edge_match.py`：主体/谓词/客体/方向全校验。
- `binding_match.py`：主体/目标/类型/元数据。
- `state_match.py`：repair 任务状态比对 + 关键对象确实被改。
- `rule_engine.py`：R1–R10 可执行化（对齐 Go `SceneBusinessBindingService.ValidateScene`/`SemanticService.validateSemanticPlan` 判定）。
- `trace_evidence.py`：evidence 必须指向真实工具请求/响应/状态/DB 快照；declared 无调用 → 0；自动 evidenceId 无响应 → 不通过。
- `replay.py`：外部 Trace/工具代理重放。
- `metrics.py`：CVSR、pass^1/3/5、Object P/R/F1、Critical Object Recall、Exact Quantity Accuracy、Relation F1、Binding F1、Fatal/Non-fatal violation rate、Repair success、New-conflict rate、Evidence Coverage/Precision、Replay Success、调用/时延/费用。ETF 仅 legacy。
- `statistical_tests.py`：配对 bootstrap 95%CI、sign/McNemar、Wilcoxon、Pareto。

**反作弊测试** `tests/test_anti_cheat.py`：15 条，先写后实现（见 tasks.md）。

## 公平基线协议

- 所有方法共享：同一 ToolRegistry、ValidatorAPI、TraceProxy、BudgetEnforcer、canonicalizer、同一模型（SiliconFlow `deepseek-ai/DeepSeek-V4-Flash`）、同一系统知识、同最大 LLM/工具调用/修复轮数/Token/费用/超时。
- 方法差异仅：Agent 组织、规划方式、冲突表示、冲突路由策略、Patch 选择策略、证据绑定策略。
- 原始输出一律经同一确定性 canonicalizer，**禁止方法专属评分前补关系/补绑定**。

## 类型化修复闭环

```
CONFLICT = {conflict_id, rule_id, severity, conflict_type, object_ids,
            observed, expected, evidence_ids, owner_agent,
            allowed_patch_ops, status: detect|patched|verified|rolled_back|unresolved}
PATCH_OPS = {add_node, remove_node, replace_type, add_edge, remove_edge,
             replace_binding, update_transform, replace_asset, set_placeholder}
流程: detect→classify→route→propose→precheck→transactional apply→local revalidate→global fatal revalidate→commit/rollback
```

## 端到端消融

运行时 feature flags：`use_ontology, use_memory, use_asset_router, use_validator, use_typed_repair, use_multi_agent, use_evidence_binding`。每个消融从原始 prompt/initial_state 重跑模型+工具+独立日志+同一评分器，≥5 次。

## SOTA Gate（唯一出口）

见 `specs/sota-gate/spec.md`。`make sota-gate` 非零退出直到全部通过，通过时输出 `SOTA_GATE=PASS / baseline / delta_cvsr / ci95 / pass5_delta / manifest_sha256`。
