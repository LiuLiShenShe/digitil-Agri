# 标注规范 — KAFarmTwin v3 测试集 Gold（annotation_guideline.md）

版本：benchmark_v1 · 创建：2026-08-04

## 目的

为测试集（T27–T30 + 盲测 T031–T035）产出**两名独立标注者一致认可的 Gold**，并经仲裁确认后**冻结密封**。在双标注复核完成前，测试集 Gold 不视为密封，`make sota-gate` 不得通过。

## 标注角色

| 角色 | 人选 | 职责 |
|------|------|------|
| 标注者 1（初版） | 实现者（AI 辅助，基于旧任务派生） | 产出 Gold 初稿：required_nodes/edges/bindings、initial/goal_state、critical_objects、constraints、equivalence_groups、allowed_variants |
| 标注者 2（复核） | **用户本人** | 逐任务独立复核：对每个字段判定"接受 / 需修改"，给出理由 |
| 仲裁者 | 实现者 + 用户协商 | 标注不一致时裁定；记录到 adjudication_log.jsonl |

> 注意：标注者 2 必须**独立**复核，不得直接采纳标注者 1 的输出而不审查。一致性指标（对象/关系/绑定/约束一致性）写入报告。

## 字段判定标准

对每个测试任务，逐字段判定：

1. **required_nodes**：每个节点 `{id, type, role, count, parent?, key_attrs?, asset_policy?}`。判定：类型是否合理？计数是否符合 prompt？父级上下文是否必要且正确？
2. **required_edges**：`{subject, predicate, object}`。判定：谓词是否在允许集（contains/belongs_to/monitors/observes/controls/has_asset/has_trait/has_event/located_in/has_instance/generates_task）内？方向是否正确？
3. **required_bindings**：`{subject, target, type, metadata?}`。判定：绑定主体/目标是否真实存在？类型是否正确？元数据（单位/时间戳）是否必要？
4. **initial_state / goal_state**（repair 任务）：初版必须真实可判定；goal_state 必须能被评分器明确判定"修复完成"。
5. **critical_objects**（repair 任务）：列出必须被实际修改的对象。仅重建新场景而不改这些对象 = 修复失败。
6. **constraints / equivalence_groups / allowed_variants**：是否足以表达多种合法解、又足够约束以排除错误解？

## 一致性指标

报告中将输出：
- 对象一致性 = 两标注者对 required_nodes 的一致比例
- 关系一致性 = 两标注者对 required_edges 的一致比例
- 绑定一致性 = 两标注者对 required_bindings 的一致比例
- 约束一致性 = 两标注者对 constraints 的一致比例

## 密封流程

1. 标注者 1 产出初稿 → `test_gold.sealed.jsonl`
2. 标注者 2（用户）逐任务复核 → 修改/确认
3. 仲裁不一致项 → 记入 `adjudication_log.jsonl`
4. 全部一致后 → `benchmark_validate.py --expect-sealed` 通过 → 更新 `benchmark_manifest.json` 的 SHA-256 → **测试集冻结**
5. 冻结后不得修改；如需修订 → 提升 benchmark_version（v2）并全方法重跑

## 当前状态

- [ ] 标注者 1 初稿（T27–T30 已有派生；T031–T035 盲测为 TODO）
- [ ] 标注者 2（用户）复核
- [ ] 仲裁
- [ ] 密封 + SHA-256
