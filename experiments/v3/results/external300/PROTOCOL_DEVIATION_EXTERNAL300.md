# External300 协议偏离记录（PROTOCOL_DEVIATION）

日期：2026-08-25 ｜ 状态：正式记录，随结果进入论文有效性声明

## 偏离 1：独立双人审核未执行（最重大偏离）

- **原预注册计划**（PREREGISTRATION_DRAFT.md / Phase-1 审计报告 §5）：要求具名 Reviewer A/B
  完成 300×2 独立审查、分歧由第三人有据裁决、全部 freeze_eligible 后方可运行。
- **实际情况**：运行前仅有**作者/用户单一确认**（author_confirmation，1 人）。
  该确认于 2026-08-24 由用户明确给出（"全部统一，执行"），并如实写入解封记录
  （解封时间/执行者/见证者三项均指向同一授权来源）。
- **后果**：实验身份降级为 **author-reviewed controlled evaluation**。
  External300 **不是独立 confirmatory 外部测试**，不得在论文或任何场合宣称
  independent external validation / double-blind / private held-out。
- 详见 `REVIEW_PROVENANCE_CORRECTION.md`。

## 偏离 2：20260824 首次运行作废与重跑

- 首次正式运行 `ext300_formal_20260824` 完成后、**seal/score 之前**，
  发现 harness 缺陷：`harness/semantic_compiler.py` 的 `bind_scene()` 引用未赋值变量 `oid`
  （NameError），导致 5 条 KF asset_routing 任务被系统性记 technical_failure 零分——
  属基础设施缺陷而非方法表现，且仅影响 KF 一方，不公平。
- 处置：经用户批准作废该 run（`ext300_formal_20260824/VOIDED.json`，原始 600 条保留备查）；
  修复为一行赋值；修复事件披露于预注册附录。**作废决策未参考任何性能指标**
  （当时只检查了 error 字段，score 从未执行）。
- 重跑 `ext300_formal_20260825`：600/600 记录、0 错误、0 技术失败，
  SEAL SHA-256 `b52f00c4bee3b43723689c3556300e0754a8ab9564b96341d05e88b591d40d91`。

## 未发生的事（同样重要）

- 任务、Gold、阈值、预算、提示词**没有因看到结果方向而被删除或修改**；
- 方法逻辑未因结果调整（唯一代码改动是上述一行 harness 缺陷修复，发生在 seal 前）；
- 未伪造任何审核人员身份（本轮已把此前被夸大的三列同源标注降级为 author_confirmation）；
- 未做事后子集挑选（多模型泛化默认跑完整 300 条，见 `multimodel/MULTIMODEL_PREREGISTRATION.md`）。

## 运行时环境说明

正式运行的 run_manifest 记录 `git_head=b7d760f…, git_dirty=7 entries`；
归档提交为 `5ad8e2d…`（工作树干净）。无法严格证明归档提交与当时的 dirty tree 完全一致
（`exact_dirty_tree_reconstruction = uncertain`）——权威绑定以文件级 SHA-256 为准，
见 `EXECUTION_SOURCE_PROVENANCE_POSTHOC.json`。
