# External300 candidate benchmark

External300 是一个面向 KAFarmTwin v3 的候选外部评测池，共 300 条任务，五类各 60 条。它解决现有 `test_v2` 仅 20 条、每类 4 条导致区间过宽的问题，但当前版本**不是**可直接写入论文的独立私有测试结果。

## 当前状态

- 状态：`CANDIDATE_NOT_FROZEN_NOT_EVALUATED`
- 任务数：300
- 每类难度：15 easy / 30 medium / 15 hard
- Gold：机器生成的草案，`review_status=pending`
- 方法运行：未运行；生成器和校验器都不导入 KAFarmTwin、SingleAgent 或 LLM 客户端
- 冻结条件：独立双人盲审、分歧裁决、方法/提示词/模型/预算/evaluator 预冻结后才能首次运行

| task_type | 数量 | ID 范围 |
|---|---:|---|
| `scene_construction` | 60 | `EXT-SC-001`–`EXT-SC-060` |
| `asset_routing` | 60 | `EXT-AR-001`–`EXT-AR-060` |
| `data_binding` | 60 | `EXT-DB-001`–`EXT-DB-060` |
| `rule_repair` | 60 | `EXT-RR-001`–`EXT-RR-060` |
| `memory_query` | 60 | `EXT-MQ-001`–`EXT-MQ-060` |

## 文件

- `external300_public_inputs.jsonl`：唯一可传给方法的输入。
- `external300_gold_draft.jsonl`：Gold 草案，只能由标注者和 scorer 访问。
- `external300_catalog.csv`：任务类型、难度、场景族和来源依据目录。
- `external300_review_queue.csv`：双人盲审与第三人裁决工作表。
- `external300_manifest_draft.json`：数量、来源声明、文件哈希和未冻结状态。
- `external300_schema.json`：候选集独立 schema；不修改冻结的 v2 schema/evaluator。
- `generate_external300.py`：确定性生成器。
- `validate_external300.py`：结构、泄漏、Oracle、重复、哈希和来源边界校验。
- `audit_gold_satisfiability.py`：用声明的 Gold oracle 检查每条契约在 evaluator_v2.3 下至少存在一个通过解；不运行被比较方法。
- `ANNOTATION_GUIDELINE.md`：人工审查规范。
- `PREREGISTRATION_DRAFT.md`：首次运行前必须填写并冻结的预注册草案。
- `SOURCES.md`：公开标准与数据集出处、实际使用范围和许可边界。
- `PUBLIC_DATA_IMPORT_PLAN.md`：将 WUR 原始时间序列替换进 memory 子集的受控流程。
- `PHASE5_EXECUTION_PROMPT.md`：人工审查完成后可使用的执行提示词。

## 生成与验证

```bash
python3 experiments/v3/benchmark/external300_candidate/generate_external300.py
python3 experiments/v3/benchmark/external300_candidate/validate_external300.py
PYTHONDONTWRITEBYTECODE=1 python3 experiments/v3/benchmark/external300_candidate/audit_gold_satisfiability.py
```

校验通过不代表可以冻结。正常候选状态应为 `errors=0`、`warnings=0`、`freeze_ready=false`；`freeze_ready=false` 是因为人工盲审尚未完成，不是程序错误。

## 科研诚信边界

1. 本候选池由参与方法开发的一方生成，因此不能直接称为“由独立人员构建的 private held-out test”。
2. 公开输入没有 Gold 顶层字段；`initial_state` 是任务输入，不是答案。
3. memory 记录是公开温室数据集启发下的确定性合成记录，不是 WUR 原始观测值。
4. 任何看过方法输出后对任务、Gold、阈值或预算的修改都必须升级 benchmark 版本，并使此前结果失去 confirmatory 身份。
5. 若人工审查拒绝任何任务，应先补充同类同难度替代题并重新盲审，保持五类各 60 条；不得静默删除失败题。

## 兼容性限制

External300 保持 `evaluator_v2.3` 的五类数据形状。该 evaluator 的 `rule_repair` 适配器只对“设备资产类型错绑→直接替换”有明确、可执行的成功契约，因此 60 条 repair 候选均属于这一错误族，只在设备类型、干扰对象和难度上变化。论文必须把这一点写成外部有效性限制，不能把它表述为覆盖所有温室规则修复。
