# PREREGISTRATION_POSTRUN_ADDENDUM — External300

日期：2026-08-25 ｜ 性质：**事后追加说明（post-run addendum）**，不是对原预注册的追溯修改

原 `PREREGISTRATION_DRAFT.md` 保持运行时的原样，不做倒改。本附录如实追加记录
运行时与原计划的两处偏离及其处置：

## 1. 审核身份：author_confirmation，非独立双盲

原计划要求独立双人审核 + 第三方裁决后方可解封。实际执行以用户 2026-08-24 的单一明确授权
（"全部统一，执行"）替代了这一前置条件。因此：

- External300 的实验身份为 **author-generated / author-reviewed controlled benchmark**；
- 不构成 independent confirmatory external test；
- 论文表述受 `REVIEW_PROVENANCE_CORRECTION.md` 中允许/禁止清单约束。

## 2. 运行作废与重跑链

- `ext300_formal_20260824`：因 harness NameError 缺陷在 seal/score 前作废（VOIDED.json）；
- 一行修复 + 预注册附录披露（见原文件"附：harness 缺陷修复披露"节）；
- `ext300_formal_20260825`：完整重跑并 seal（SHA `b52f00c4…d91`），为本轮唯一有效结果。

两处偏离的完整叙述见 `PROTOCOL_DEVIATION_EXTERNAL300.md`。
