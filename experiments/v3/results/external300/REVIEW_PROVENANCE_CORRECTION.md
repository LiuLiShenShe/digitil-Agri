# External300 审核身份修正说明（REVIEW_PROVENANCE_CORRECTION）

日期：2026-08-25 ｜ 配套 JSON：`REVIEW_PROVENANCE_CORRECTION.json`

## 发生了什么

2026-08-24，用户一句统一指令（"unified execution directive 2026-08-24 (user)"）被同时写入了
`external300_review_queue.csv` 全部 300 行的 **reviewer_a_decision、reviewer_b_decision、
adjudicator_decision** 三列。当时的 freeze-check 据此输出
"review_queue_independently_reviewed: 300/300 PASS"——这一命名和表述**不准确**，
会误导读者以为存在两名独立审核者加一名裁决者。

## 正确认定

| 字段 | 值 |
|---|---|
| human_review_mode | **author_confirmation**（作者/用户单一确认） |
| human_reviewer_count | **1** |
| double_human_review | false |
| independent_review | false |
| gold_standard | false |
| benchmark_role | **author-generated / author-reviewed controlled benchmark** |

300 条任务确实都经过了用户逐一内容核验并获统一放行确认，但这是**一个人的确认**，
不构成两名独立审核者的分别审查，更不构成双盲评审。

## 允许与禁止的表述

✅ 允许：author-generated、author-reviewed、controlled benchmark、受控比较实验
❌ 禁止：independent review、double-blind、private held-out、gold standard、独立外部评测、盲测

## 影响范围（重要）

**未改变**：300 条任务内容、public/gold 文件字节、已封存的 600 条方法输出
（raw SHA `b52f00c4…d91`）、全部性能指标。
**仅改变**：审核过程的语义标签；freeze-check 门控语义拆分为三项：
- `review_records_complete`（结构完整性）— 可 PASS
- `author_confirmation_present`（作者确认存在）— 可 PASS
- `independent_human_review_evidence`(独立人审证据) — **必须 FAIL / NOT_ESTABLISHED**，
  只有出现具名独立 Reviewer A/B 与裁决者的真实记录才可翻为 PASS。

## 工件索引

- 原始 review queue：保留原样，不改造成"真双人审核"
  （`benchmark/external300_candidate/external300_review_queue.csv`）
- 运行前 freeze-check 存档：`archive/FREEZE_CHECK_pre_run_20260825.json`
  （SHA-256 `2c7ddb098d6362ead6d58ddd380db1f11fc468078ec29e303073274026511e94`，
  含旧的 "independently reviewed PASS" 表述，留作审计证据）
- 修正后 freeze-check：`FREEZE_CHECK_POSTRUN_CORRECTED.json`
- 协议偏离记录：`PROTOCOL_DEVIATION_EXTERNAL300.md`
