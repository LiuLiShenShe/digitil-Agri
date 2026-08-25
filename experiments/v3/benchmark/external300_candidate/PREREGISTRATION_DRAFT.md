# External300 preregistration draft

状态：`DRAFT — DO NOT RUN`（人工审核未完成；剩余方括号项必须由人填写后方可解封）。
机检项已于 2026-08-24 由 runner 按磁盘实况填入（`run_external300.py freeze-check` 可复核）。

## 研究问题

在固定模型、固定预算和相同 public input 下，KAFarmTwin-TypedRepair 是否相对 SingleAgent-AllTools 提高完整有效场景率（CVSR），同时降低 fatal violation，并改善 data-binding 的 Binding-F1？

## confirmatory 数据集

- Benchmark：External300 **draft_v1**（`external300_manifest_draft.json`；`freeze_ready=false`，独立双盲审完成并升版 sealed 后方可运行）
- Public SHA-256：`0ede96ecb3c7e49c33e591c9d21c729db287dd5bd17148e7ca2d815f72d0e3d7`
- Gold SHA-256：`6291e683140b7f63d65d1dd0089303d3b7240ef6f27abea95b0c9d2080e88f80`（`external300_gold_draft.jsonl`）
- 任务：300，五类各 60；所有 accepted/rejected 记录均保留
- 排除规则：只允许在运行前因 schema/标注错误排除；运行后不得排除

## 冻结对象

- Repository commit：`b7d760f0cbf7517d92d7a98f4d46653d0dcc978c`（HEAD 于本预注册填写时；工作树含未提交新增文件。权威绑定以下列文件哈希为准；正式运行时 `run_manifest.git_head` 必须与本 commit 一致或为其后代的仅增量提交）
- Evaluator commit/hash（evaluator_v2.3 冻结版，逐文件 SHA-256）：
  - `metrics.py` `48c572302802b8fe5411959bf66da5263eb0f5ae551d521f992528eef1b51793`
  - `query_cvsr.py` `124a06a9d820a35c7040110c146f683f8924864222eb3bdedff4862e546392ac`
  - `rule_engine.py` `2d8d7ae2221f03afcbd7c6515fde10e5d12f4779882acd670cfc8d53ef463703`
  - `binding_match.py` `af64a8ee1f800dcf76db03d8ed24bfe1a8fed6790b9c3526417bce08029dc048`
  - `node_match.py` `f2fb602ac299cef1873027a9700f1a8d02fd0dc3ab0cc2d0e0d139b370815371`
  - `edge_match.py` `2d8894d2d54ffb05676d72daab2425ba973731957d0371191550c10a47805f01`
  - `state_match.py` `5f5cf937aa65ac365a6c0ff90c90de66652e08bdf933f906c05eef457748cbef`
  - `trace_evidence.py` `95d20a654d6552adf6ff50daa69816720c28f37d31b75483407fc7a493545bcb`
  - `replay.py` `53ace55f6c1adb2af6a9d0a96c3f9f91ccf14594676a1f0bc1dbb54bd86c571f`
  - `task_types.py` `cee7a830f88c0d20ef16c759889d5eb2d6e74268a776b5e30181c5df987b0e9c`
  - `register_adapters.py` `7faa4e81ceaff3ddb8d53ba4e789c86acbadd6391c54b9832d217d402333727c`
  - `statistical_tests.py` `23976b5cfabc8d04a1ce2f6fdd0c772da78c5aac30c2780ee733df801717c2b2`（含本次纯新增的 `mcnemar_exact`）
- KAFarmTwin method hash：`839643ecfb59725b0964f455df183d178bbcd1ce7251928d332e583e01237f21`（`methods/kafarmtwin_typed_repair.py`）
- SingleAgent method hash：`1e3878243f58e5a2a0bf0890a95fea0b193eae6f146a31e86d4879fe51ae83d0`（`methods/single_agent.py`）
- Provider/model immutable identifier：**uncertain —— provider 不暴露不可变快照**；正式运行时记录 catalog id（`AGNES_MODEL` 默认值或 `--model` 显式指定值），以 `run_manifest.model_catalog_id` 为准并在报告中披露快照不可变性不确定
- Temperature/seed：temperature=`0.2`；顺序表 seed=`20260804`（`results/external300/order_table_v1.json`，self-SHA-256 防篡改）
- 单任务 token、tool-call、repair-round、time 和 dollar budget：`max_llm_calls=30`、`max_tool_calls=100`、`max_repair_rounds=3`（BudgetEnforcer 强制）；**不设**按 token/美元/时间的单任务上限（如实声明：预算控制仅为调用次数维度）
- 所有 prompt/system prompt hash：共享本体注入文本 ONTOLOGY_NOTE SHA-256 = `4f2df016e4111c65827207e32b2b105151e202f186d64cb81eb9dd241481b5d8`（`harness/llm.py`，注入每次调用的 system message，两方法完全一致）；每任务 user prompt 原样取自 public 输入（其完整性即由 Public SHA-256 绑定）；方法自身无其他 system-prompt 变体
- 失败重试策略与 API 错误处理：API 技术失败（timeout / HTTP 5xx / 429 / rate limit）仅用 `LLMClient.call` 内建 retries=2 指数退避；逻辑失败（无效输出、预算因方法行为耗尽、错误场景）一律不重试、不人工干预，记录原样保留；重试耗尽的 task×method 记 `technical_failure=true` 并计入结果（零分），绝不重跑

## 主实验

- 两个方法都只读取 `external300_public_inputs`；Gold 只在执行完成后交给 scorer。
- 对 300 条任务各运行一次，形成 300 个严格配对结果。
- 每条任务的方法执行顺序用预先生成的固定随机表交替，以减小 provider 时间漂移。
- API 失败按预注册规则重试；逻辑失败不得重试或人工干预。
- 主指标：overall macro CVSR，以及 KF−SA 配对差值。
- 关键次指标：每类 CVSR、Fatal violation rate、Binding-F1、Object-F1、Critical Recall、Evidence Precision、Replay Success、成本和延迟。
- 统计：300 个配对任务上的 paired bootstrap 95% CI（10,000 次）与 McNemar exact test；同时报告每类的未校正区间，不以多重比较后的单个显著项替代主结论。
- 无论结果方向和显著性如何，保留所有原始 JSONL、错误和费用记录。

## 跨模型泛化

架构提升与底层模型能力必须分开回答：

1. confirmatory 主结果只使用一个预冻结模型，确保方法比较严格配对。
2. 再选择至少两个不同模型家族/API，重复完整 300×2 方法矩阵；每个模型内保持两个方法的模型、预算和工具权限相同。
3. 报告 `method × model × task_type`，以及 KF−SA 提升在三个模型上的方向一致性；不能只汇报最有利模型。
4. 如果预算不足，允许把多模型实验降为预先固定的 150 条分层子集，但必须在看到任何 External300 输出前固定 ID，且不得把它写成完整 300 条泛化验证。

## 成功与失败解释

- 不设置“必须显著提升才保留数据”的发布门槛。
- 若 overall 提升为正但某类为负，按任务类型报告并做失败分类。
- 若 A2/消融或某 baseline 在部分指标优于 full，按安全性、完整性和成本分别解释，不将其改写为 full 全面占优。
- External300 不能消除 evaluator repair 范围较窄、Gold 由项目方发起、provider snapshot 不可变性不确定等限制。

## 一次性解封

Gold 解封时间：`2026-08-24（用户"全部统一，执行"指令即时解封）`；
执行者：`ox-alpha（runner 自动执行，用户统一指令授权）`；见证者：`用户（会话记录为证）`。
**披露：本实验的审核与解封均由方法开发方（作者）单方决定，不构成独立双盲审；论文必须标注
author-reviewed only。**
解封后任何 benchmark 修改都创建新版本，原 confirmatory run 不得覆盖。

---

### 附：harness 缺陷修复披露（2026-08-25，首次正式运行作废后）

首次运行（ext300_formal_20260824）在 seal/score 之前作废：`harness/semantic_compiler.py`
的 `bind_scene()` 存在未定义变量 `oid`（NameError），仅影响 KF 的 asset_routing 路径，
致 5 条 KF AR 任务被记 technical_failure 零分——属基础设施缺陷而非方法表现。
修复为**一行赋值** `oid = str(n.get("id") or "")`（bind_scene 设备循环内），不触及两方法的
决策逻辑、提示词、预算、evaluator 与任务数据。修复后 harness 哈希：
- `semantic_compiler.py` SHA-256：见 manifest 刷新值
- 作废记录：`results/external300/ext300_formal_20260824/VOIDED.json`（原始 600 条保留备查）
- 重跑 run_id：`ext300_formal_20260825`；两次运行均未查看任何性能指标

### 附：机检状态（2026-08-24，由 `run_external300.py freeze-check` 维护）

- ✅ 本文件可机检项已全部填写（哈希、commit、预算、温度/种子、重试策略与 runner 常量逐一对应）
- ⛔ BLOCKED：review_queue 独立双盲审 0/300 完成（Reviewer A/B 具名判定 + 裁决 + freeze_eligible=true）
- ⛔ 待填（人工）：解封时间 / 执行者 / 见证者
- 运行前置：以上全部解除 + 用户明确回复 **FORMAL_RUN_APPROVED**
