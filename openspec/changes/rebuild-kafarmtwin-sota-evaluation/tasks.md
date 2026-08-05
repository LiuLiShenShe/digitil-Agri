# Rebuild KAFarmTwin SOTA Evaluation — 自动生成任务清单

状态：`TODO` / `IN_PROGRESS` / `BLOCKED` / `FAILED` / `PASSED`
优先级：P0（阻塞所有下游）/ P1（必须完成才能运行 Gate）/ P2（可并行加固）/ P3（增强）

---

## S0. 安全审计与基线（P0）— 完成

- [x] **S0.1** [P0] 扫描硬编码密钥/凭据。涉及：仓库全量。验收：`grep -rnE 'sk-[A-Za-z0-9]{8,}'` 其真实密钥零命中。命令：见 WORKLOG。状态：PASSED。证据：experiments/v3/WORKLOG.jsonl。
- [x] **S0.2** [P0] 创建 `.env.example`（占位）+ `.env`（gitignored，SiliconFlow 实际配置）。验收：`git check-ignore .env` 为真。状态：PASSED。
- [x] **S0.3** [P0] `config.go` + `run_main_experiment.py` 增加 `AGNES_*` env 前缀；`application.yml` api-key 置空走 env。验收：`AGNES_*` 生效。状态：PASSED。
- [x] **S0.4** [P0] 记录基线：`openspec list` / `validate --all --strict` / Python 测试 / `go test ./...`。状态：PASSED（15 passed / go ok / openspec 6/6）。
- [x] **S0.5** [P0] 旧表 5/6/7 源复制到 `experiments/legacy/tables/` + README 标注 legacy_exploratory。状态：PASSED。
- [x] **S0.6** [P0] 密钥轮换 + Git 历史清理标记 HUMAN_BLOCKED（人工）。状态：BLOCKED（人工）。

## S1. OpenSpec 变更与 v3 骨架（P0）

- [x] **S1.1** [P0] 创建 `openspec/changes/rebuild-kafarmtwin-sota-evaluation/` 变更目录 + 6 个 spec 目录。验收：`openspec validate` 通过。状态：PASSED（目录创建）。
- [x] **S1.2** [P0] 写 `.openspec.yaml` / `proposal.md` / `design.md`。状态：PASSED。
- [ ] **S1.3** [P0] 写 `tasks.md`（本文件，持续更新）。命令：`openspec validate --all --strict`。状态：PASSED（已校验 7/7）。
- [x] **S1.4** [P0] 写 6 个 spec（benchmark-contract / semantic-evaluator / fair-agent-baselines / typed-repair-loop / evidence-and-replay / sota-gate）。命令：`openspec validate --strict`。状态：PASSED。
- [x] **S1.5** [P0] 创建 `experiments/v3/` 目录骨架 + `STATUS.md` / `WORKLOG.jsonl` / `DECISIONS.md` / `FAILURES.md`。状态：PASSED。
- [x] **S1.6** [P0] 写 `reports/sota_definition.md`（外部参考 vs 项目内 SOTA 定义）。状态：PASSED。
- [ ] **S1.7** [P0] 写 `reports/reproducibility_manifest.json`。命令：`python -m json.tool`。依赖：S4（结果存在后补）。

## S2. 版本化冻结基准（P0）

- [ ] **S2.1** [P0] 写 `benchmark/schema.json`（任务 JSON Schema，对齐总控 §4.1 字段）。命令：`python -c` 校验。依赖：S1.4。
- [ ] **S2.2** [P0] 写 `scripts/benchmark/expand_legacy_tasks.py`（30 条旧任务 → typed gold；repair 任务补真实 initial_state/goal_state/critical_objects）。命令：运行生成 train/dev/test。依赖：S2.1。
- [ ] **S2.3** [P0] 生成 `train.jsonl` / `dev.jsonl` / `test_public_inputs.jsonl` / `test_gold.sealed.jsonl`。命令：`make benchmark-validate`。依赖：S2.2。
- [ ] **S2.4** [P0] 密封测试集：`test_gold.sealed.jsonl` 冻结 + 记录 SHA-256 到 `benchmark_manifest.json`。命令：`sha256sum`。依赖：S2.3。
- [ ] **S2.5** [P0] 写 `annotation_guideline.md` + `adjudication_log.jsonl`。命令：模板可达。依赖：S2.1。
- [ ] **S2.6** [P1] 双标注复核（用户=第二标注者）。状态标记：若未完成 → **BLOCKED_HUMAN_ANNOTATION**，SOTA Gate 挂起。命令：手动。依赖：S2.5。
- [ ] **S2.7** [P3] `benchmark_validate.py`（schema 校验 + SHA-256 核对）。命令：`make benchmark-validate`。依赖：S2.3。

## S3. 独立语义评分器 + 反作弊测试（P0）

- [ ] **S3.0** [P1] 先写反作弊测试 `tests/test_anti_cheat.py`（15 条）。命令：`pytest experiments/v3/tests/ -q` → 预期先红。依赖：无（纯 TDD）。
- [x] **S3.1** [P0] `evaluators/rule_engine.py`（R1–R10 可执行化）。命令：pytest 用例。依赖：S3.0。
- [x] **S3.2** [P0] `evaluators/node_match.py`（约束匹配 + 匈牙利最优匹配 + 等价组）。命令：pytest #5 #6 #10。依赖：S3.0。
- [x] **S3.3** [P0] `evaluators/edge_match.py`（方向/主客校验）。命令：pytest #2 #3。依赖：S3.0。
- [x] **S3.4** [P0] `evaluators/binding_match.py`（主体/目标/类型/元数据）。命令：pytest #4。依赖：S3.0。
- [x] **S3.5** [P0] `evaluators/state_match.py`（repair 状态比对 + critical_objects 被改）。命令：pytest #11 #12。依赖：S3.0。
- [x] **S3.6** [P0] `evaluators/trace_evidence.py`（真实 evidence；declared→0；自动 evidenceId→不通过；规则回退单独标记）。命令：pytest #13 #14 #15。依赖：S3.0。
- [x] **S3.7** [P0] `evaluators/replay.py`（外部 Trace 代理重放）。命令：pytest 回放用例。依赖：S3.6。
- [x] **S3.8** [P0] `evaluators/metrics.py`（CVSR / pass^k / 诊断指标，禁用 min(count)）。命令：pytest #1。依赖：S3.2-S3.7。
- [x] **S3.9** [P1] `evaluators/statistical_tests.py`（配对 bootstrap 95%CI / sign / Wilcoxon / Pareto）。命令：`make statistical-report`。依赖：S3.8。
- [x] **S3.10** [P0] 全部反作弊测试转绿。命令：`make evaluator-test`。依赖：S3.1-S3.8。

## S4. 公平基线协议（P0）

- [x] **S4.1** [P1] `harness/tools.py`（ToolRegistry + 统一工具代理）。命令：pytest 单测。依赖：S2。
- [x] **S4.2** [P1] `harness/validator_api.py`（唯一外部 Validator，对齐 rule_engine）。命令：pytest。依赖：S3.1。
- [x] **S4.3** [P1] `harness/trace_proxy.py`（唯一 Trace 代理，记录真实 agentID/消息/工具调用）。命令：pytest。依赖：无。
- [x] **S4.4** [P1] `harness/budget.py`（BudgetEnforcer：max LLM/tool/repair-rounds/token/费用/超时）。命令：pytest 预算越界。依赖：无。
- [x] **S4.5** [P1] `harness/canonicalizer.py`（单一确定性标准化器）。命令：pytest。依赖：无。
- [x] **S4.6** [P1] `methods/single_agent.py`、`methods/react.py`、`methods/generic_multia_agent.py`、`methods/generic_repair.py`、`methods/deterministic_fallback.py`。命令：pytest 冒烟。依赖：S4.1-S4.5。
- [x] **S4.7** [P1] `methods/kafarmtwin_typed_repair.py`（类型化修复闭环，见 S6）。命令：pytest。依赖：S4.6 + S6。
- [x] **S4.8** [P0] `scripts/run_fair_baselines.py`（每(任务×方法×模型)≥5 次，独立日志）。命令：`make run-dev` 冒烟 → `make run-test`。依赖：S4.6-S4.7 + S2。
- [x] **S4.9** [P0] `make smoke`（3 任务×每方法 1 次 dry-run，真实 LLM）。命令：`make smoke`。依赖：S4.8。

## S5. 修复 Agent 主路径（P0，Go 后端）

- [x] **S5.1** [P0] 修复 `EinoOpenAIChatModel.go` 的 `finish_reason=tool_calls` 解析；DeepAgents 失败显式标记 `agent_failed`。命令：`make backend-test`。依赖：无。
- [x] **S5.2** [P0] 规则回退 trace 显式 `fallback.used=true`；主结果不混入回退。命令：review trace。依赖：S5.1。
- [ ] **S5.3** [P1] 决策多智能体真拆分 or 降级论文定位（写 DECISIONS.md/FAILURES.md）。命令：文档。依赖：无。
- [x] **S5.4** [P1] `initial_state` 注入语义构建入口（repair 任务真实错误状态）。命令：pytest repair。依赖：S5.2。

## S6. 类型化修复闭环（P0）

- [ ] **S6.1** [P1] 冲突结构 + PATCH_OPS + 流程（detect→…→commit/rollback）。命令：pytest。依赖：S3.1（rule_engine）。
- [ ] **S6.2** [P1] 状态快照 + transactional apply + local/global revalidate + rollback。命令：pytest rollback。依赖：S6.1。
- [ ] **S6.3** [P1] 新冲突单独统计；unresolved≠成功。命令：pytest。依赖：S6.1。
- [ ] **S6.4** [P0] T19–T24 验证 specified critical_objects 确实被修改。命令：`make evaluator-test`（#11 #12）。依赖：S6.2。

## S7. 端到端消融（P1）

- [ ] **S7.1** [P1] feature flags（use_ontology/memory/asset_router/validator/typed_repair/multi_agent/evidence_binding）加入方法。命令：pytest。依赖：S4.7。
- [ ] **S7.2** [P1] `scripts/run_ablation_v3.py`（原始 prompt → 重跑 → 独立日志 → 同评分器 → ≥5 次）。命令：`make ablation`。依赖：S7.1 + S4.8。

## S8. 统计与 SOTA Gate（P0）

- [ ] **S8.1** [P0] `scripts/statistical_report.py`（配对 bootstrap 95%CI、pass^k、模型一致性、预算归一化）。命令：`make statistical-report`。依赖：S4.8。
- [ ] **S8.2** [P0] `Makefile` 全部 targets（audit/benchmark-validate/evaluator-test/backend-test/run-dev/run-test/ablation/robustness/statistical-report/reproduce-paper/sota-gate）。命令：`make` 枚举。依赖：前述。
- [ ] **S8.3** [P0] `scripts/run_sota_gate.py` 实现全部 Gate 条件，非零退出直到通过。命令：`make sota-gate`。依赖：S8.1。

## S9. 论文同步（P2，仅当 S8.3 PASS 后）

- [ ] **S9.1** [P2] 从新结果自动生成公平对比表/消融表/错误分析/模型追踪矩阵。命令：`make reproduce-paper`。依赖：S8.3。
- [ ] **S9.2** [P2] 保守策略修正 + 修复案例 + 局限性 + 评审意见逐条回复。命令：文档。依赖：S9.1。
