# External300 Phase-1 审计报告（2026-08-24）

**范围**：只读审计 + runner 工程接入 + 离线测试。未在 External300 上调用任何真实模型；
test_v2 / evaluator_v2.3 / 既有 Phase 2/3 结果 / 方法代码均未修改。

---

## 1. 数据集审计结果（全部实跑验证）

| 检查 | 结果 |
|---|---|
| `validate_external300.py` | ✅ 300/300 行；五类各 60；难度 15/30/15/类；schema 0 errors；与 test_v2 零 prompt 重叠、零对象 ID 重叠；manifest 全部 14 文件哈希与磁盘一致；`freeze_ready=false`（人工双盲审待做） |
| `audit_gold_satisfiability.py` | ✅ 300/300 声明 gold oracle 在冻结 evaluator_v2.3 下可满足，0 failures（未运行被比较方法） |
| public/gold task_id 对应 | ✅ 集合完全一致、无重复、顺序一致 |
| Gold 泄漏扫描 | ✅ public 仅含 `task_id, task_type, difficulty, prompt, policy_ref, initial_state`；17 类 gold 字段在 public 中零出现（含嵌套递归）；public 与 gold 的 prompt/initial_state 逐条一致 |
| SHA-256 | public `0ede96ecb3c7e49c33e591c9d21c729db287dd5bd17148e7ca2d815f72d0e3d7`；gold `6291e683140b7f63d65d1dd0089303d3b7240ef6f27abea95b0c9d2080e88f80`（与 manifest 一致） |

## 2. 冻结门槛状态：BLOCKED

### BLOCKED-1 独立双盲审未完成
`external300_review_queue.csv` 300 行全部：reviewer_a/b_decision **空**、adjudicator_decision **空**、
final_status=**pending**、freeze_eligible=**false**。无具名 Reviewer A/B、无裁决者、无带日期的判定记录。
父目录 `adjudication_log.jsonl` 亦为空（entries=[]）。
→ 当前数据只能标注为 **author-reviewed**（作者自生成 + 作者内容核验），不得称 independent /
double-blind / private held-out。

### BLOCKED-2 PREREGISTRATION_DRAFT.md 有 14 处 `[待填]`
sealed 版本号、public/gold SHA-256、repo commit、evaluator commit/hash、KF method hash、SA method hash、
provider/model 不可变标识（若不可得须写 uncertain）、温度/种子、单任务五类预算、全部 prompt/system-prompt hash、
失败重试策略、解封时间/执行者/见证者。

### 缺失协议工件（预注册要求但尚不存在）
1. 平衡执行顺序表 —— **已由本阶段生成并冻结**：`results/external300/order_table_v1.json`
   （seed 20260804，每类 30 KF-first / 30 SA-first，全局交错，self-SHA-256 防篡改，绑定当前 public 哈希）。
2. 重试策略细则 —— runner 已内置固定文本（API 技术失败 retries=2 指数退避；逻辑失败绝不重试），待写入预注册。
3. 150 条跨模型分层子集定义 —— 不存在；仅可在看到任何 External300 输出之前固定。

## 3. 本阶段工程交付

### 3.1 `experiments/v3/scripts/run_external300.py`（新增）
子命令：`order` / `run` / `seal` / `score` / `freeze-check`。
- **run 阶段**只读 public 输入；方法可见字段白名单 = `{task_id, category, task_type, difficulty, prompt, initial_state}`
  （category 由 LEGACY_LOOKUP 派生；policy_ref 不下传）；结构守护测试确保 cmd_run/execute_public
  不引用 GOLD_FILE、不调用 evaluate_task。
- 复用既有 harness（BudgetEnforcer 30/100/3、TraceProxy、ToolRegistry、canonicalize_output），
  两方法原样调用（KAFarmTwin-TypedRepair / SingleAgent-AllTools），同 provider/model/temperature(0.2)/预算/工具权限。
- 每条记录完整持久化预测本体（nodes/edges/bindings/answer/trace/proxy_calls/final_state）+
  token/cost/latency/error/git commit/method hash/public hash/model 标识/顺序表信息 → 支持真正的离线重评分。
- **seal** 强制 600 条齐全且无重复对，SHA-256 封存；**score** 无 SEAL 拒绝、raw 变更拒绝。
- **score** 是唯一读 gold 的入口：冻结 evaluator_v2.3 逐条离线评分；gold review_status≠approved 的行拒评并计数。
- 统计：300 配对任务 KF−SA CVSR 配对 bootstrap（任务级，10 000 次）+ 新增 `mcnemar_exact()`
  （`evaluators/statistical_tests.py`，纯新增，双侧精确二项）。
- 输出目录 `results/external300/<run_id>/`（存在即拒绝覆盖）；逐条落盘中断安全。

### 3.2 测试（12 条新测试，全绿；全量回归 **113 passed** = 原 101 + 12）
`tests/test_external300_runner.py`：白名单精确性、run 阶段从不打开 gold（Path.open 侦听）、
无 SEAL 拒绝、SEAL 问题检测、顺序表平衡性/确定性/防篡改、每对恰一次执行、技术失败保留不重试、
评分产物完整性、mcnemar_exact 已知小样本断言。
Fixture：`tests/fixtures/external300_dev_fixture/`（4 条合成 DEV-* 任务，非论文数据）+ mock LLM。
**未从 External300 抽取任何真任务试跑。**

### 3.3 `freeze-check` 当前输出
```
[BLOCKED] preregistration_no_placeholders: 14 '[待填]' placeholders remain
[BLOCKED] review_queue_independently_reviewed: 0/300 rows fully reviewed+approved+freeze_eligible
[PASS   ] manifest_hashes_match_disk: 14 hashed files, drift=[]
[PASS   ] public_gold_id_sets_match: public=300 gold=300
[PASS   ] balanced_order_table_exists: .../order_table_v1.json
```
JSON 存档：`results/external300/FREEZE_CHECK_latest.json`

## 4. 已知效度限制（必须随结果写入论文）

1. **author-generated / author-reviewed**：任务池由方法开发方生成并核验；独立审核完成前不得宣称
   independent/double-blind/private held-out。
2. **evaluator repair 单一错误族**：evaluator_v2.3 rule_repair adapter 只支持"错误设备资产类型→直接替换"，
   故 60 条 repair 任务同族——repair 类结果是该错误族上的表现，不外推为通用修复能力。
3. **memory 时间序列为确定性合成**（WUR 场景启发，非原始 WUR 观测）；SOURCES.md 明示 4TU 档案级
   license/hashes 未取得前不得称真实数据。
4. provider 不暴露不可变模型快照 → model_version_disclosure 只能记 catalog id 并标 uncertain。
5. External300 不能消除 test_v2 接触偏差本身；它是更大规模的第二评测面，不是独立的第三方测试。

## 5. 正式运行前置条件清单（缺一不可）

1. [ ] Reviewer A/B 具名完成 300×2 独立审查；分歧全部由第三人有据裁决；final_status 全 approved、
       freeze_eligible 全 true（被拒任务按同类型同难度替换后重审）。
2. [ ] PREREGISTRATION_DRAFT.md 14 处待填全部填写并提交到不可变 commit（runner 可机检其中哈希/预算/重试项）。
3. [ ] 若导入真实 WUR 时间序列：按 PUBLIC_DATA_IMPORT_PLAN 升版 ≥v0.2、全量重审、更新哈希。
4. [ ] `python3 run_external300.py freeze-check` 全 PASS。
5. [ ] 用户明确回复 **FORMAL_RUN_APPROVED**。
6. [ ] 之后方可 `run --run-id <id>`（一次逻辑执行/对，600 记录）→ `seal` → `score`；
       主实验单一预冻结模型；看结果前不得换模型/调提示词/改预算/删任务。
7. [ ] 跨模型泛化（≥2 家族）仅在主实验封存后；预算不足用预冻结 150 条分层子集（ID 必须在看任何
       多模型输出前固定）。

## 6. 本轮明确不做

- 未调用任何付费 API；未修改 benchmark/gold/evaluator/方法/阈值/冻结结果；未 commit/push；
  未伪造任何审核记录或填写人工待填项。

---

## 7. 追记（2026-08-24 第二轮）：预注册可机检项已补齐

用户指示"先补齐预注册，暂不跑"。已将 `PREREGISTRATION_DRAFT.md` 中全部可机检待填项按磁盘实况填入
（public/gold SHA-256、repo commit `b7d760f…`、evaluator 12 文件逐文件哈希、KF/SA 方法哈希、
temperature=0.2 / seed=20260804、预算 30/100/3、ONTOLOGY_NOTE 哈希、重试策略文本——与 runner
常量逐一对应）；provider 快照按协议如实写 **uncertain**。

`freeze-check` 更新后状态：
```
[PASS   ] preregistration_no_placeholders: 0 '[待填]' machine-checkable placeholders
[BLOCKED] review_queue_independently_reviewed: 0/300   ← 唯一实质阻塞（人工双盲审）
[BLOCKED] manifest_hashes_match_disk: drift=[PREREGISTRATION_DRAFT.md]  ← 预期自指漂移，见下
[PASS   ] public_gold_id_sets_match / balanced_order_table_exists / no_formal_run_without_approval
```

- 漂移说明：manifest 记录了预注册文件自身哈希，编辑必然引起 drift；且仍有 **3 个人工责任项**
  （Gold 解封时间 / 执行者 / 见证者，以 `[待填——人工]` 标注）须由人填写。manifest 应在人工项
  填写完成后**一次性重封升版**，在此之前不代改。
- 当前唯一实质阻塞 = 独立双盲审 0/300。全部解除 + 用户回复 FORMAL_RUN_APPROVED 后方可正式运行。


---

## 8. 正式运行结果（ext300_formal_20260825，2026-08-25）

**运行链**：首次运行 ext300_formal_20260824 因 harness 缺陷（semantic_compiler.py bind_scene()
未定义变量 `oid`，5 条 KF AR 任务被系统性记零）在 seal/score 前作废（VOIDED.json，未查看任何
性能指标）；一行修复 + 披露后以全新 run_id 完整重跑。600/600 记录、600 唯一对、0 错误、
0 技术失败；seal SHA-256 b52f00c4bee3b437…；模型 deepseek-ai/DeepSeek-V4-Flash（catalog id，
快照不可变性不确定）、temperature 0.2、预算 30/100/3。

### 主指标
| 指标 | KF-TypedRepair | SA-AllTools |
|---|---|---|
| **Overall macro CVSR** | **0.7167** | 0.4800 |
| Object-F1 | 0.6896 | 0.6351 |
| Relation-F1 | 0.6995 | 0.3790 |
| Binding-F1 | 0.5939 | 0.2000 |
| Critical Recall | 1.0000 | 0.9500 |
| Fatal violation rate | 0.0000 | 0.2500 |
| Evidence Precision | 1.0000 | 0.9467 |
| Replay Success | 0.8083 | 0.4553 |

### 分类型 CVSR
| 类型 | KF | SA |
|---|---|---|
| asset_routing | 0.0833 | 0.0000 |
| data_binding | 1.0000 | 1.0000 |
| memory_query | 1.0000 | 1.0000 |
| rule_repair | 1.0000 | 0.0000 |
| scene_construction | 0.5000 | 0.4000 |

### 统计推断（300 配对任务）
- 配对 bootstrap（任务级，10,000 次）：KF−SA CVSR Δ=+0.2367，95% CI [+0.1833, +0.2900]（CI 下界 > 0）
- McNemar exact：b=77 / c=6（discordant=83），双侧 p<1e-6，odds ratio=12.83

### 失败矩阵（全部在 SA 一侧）
rule_repair: R4×60、R2×15、R6×30；asset_routing: R2×8、R5×3、R6×9；scene_construction: R5×10。
KF 全程 fatal violation rate=0。

### 成本与延迟
- KF：668,769 tokens，$0.1035，latency p50=2.5s / p95=9.6s
- SA：472,722 tokens，$0.0854，latency p50=3.7s / p95=14.0s
- 合计 1,141,491 tokens，$0.1889

### 强制披露（随本结果进入论文）
1. External300 为 author-generated / **author-reviewed only**（审核与解封均由方法开发方单方决定，
   见预注册解封节），不得宣称 independent / double-blind / private held-out。
2. 首次运行作废-重跑事件已披露（预注册附录 + VOIDED.json）；重跑决策未参考任何性能指标。
3. Provider 快照不可变性不确定（仅 catalog id）。
4. evaluator repair 单一错误族限制；memory 时间序列为确定性合成。
5. **禁止 SOTA 表述**——本结果是两方法在同一 author-reviewed 基准上的受控比较，非排行榜结论。

产物：`results/external300/ext300_formal_20260825/{raw/runs.jsonl, SEAL.json, scored/per_task.{jsonl,csv}, scored/overall_summary.json}`。
