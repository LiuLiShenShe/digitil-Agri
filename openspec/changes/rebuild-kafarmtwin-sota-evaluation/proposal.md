# Proposal — Rebuild KAFarmTwin SOTA Evaluation (experiments/v3)

## 问题陈述

分支 `paper/knowledge-agent-experiments` 的 KAFarmTwin 实验（旧表 5/6/7）存在实质方法学缺陷，不能作为公平、可复现的 SOTA 证据：

1. 评分器用 `min(generated_count, required_count)` 计"正确数"（objects/relations/bindings）。
2. 评分阶段替 "Ours" 事后伪造关系/绑定（`build_ours_relations/bindings`）。
3. 自动铸 `exec-{idx:03d}` evidenceId，无真实响应也计 Evidence。
4. ETF 结构性偏差：基线被系统 prompt 禁止 `traceType="executed"`，ETF 恒 0 而 Ours 恒 1。
5. 基准任务只有裸计数（`required_objects`），无 typed gold 图、无 `initial_state`/`goal_state`；修正任务 T19–T24 的错误只写在自然语言里。
6. "多智能体"为单循环 + 角色标签，非独立智能体。
7. 无类型化冲突修复闭环（无 `conflict_id/rule_id/severity`）。
8. 消融非端到端（对已保存输出的确定性降级，无运行时 feature flag）。
9. 无统计（无 bootstrap/CI/配对检验），每任务仅 1 次运行。
10. 无版本化基准、无密封测试集、无 OpenSpec 变更。

## 目标

- 建立 `experiments/v3`：版本化冻结基准（train/dev/test，Gold 密封 + SHA-256）。
- 重写独立语义评分器（约束匹配 + 匈牙利最优匹配 + 可执行规则引擎 + 证据/回放），先写反作弊单测。
- 冻结公平基线协议：SingleAgent-AllTools / ReAct-AllTools / GenericMultiAgent-AllTools / GenericRepair-AllTools / KAFarmTwin-TypedRepair / DeterministicFallback，同模型同工具同预算。
- 修复 Agent 主路径：禁止静默规则回退；`agent_failed` 显式标记；真实多智能体或降级论文定位。
- 实现类型化冲突修复闭环（detect→classify→route→patch→revalidate→commit/rollback）。
- 真正端到端消融（运行时 feature flags）。
- 统计：按任务配对 bootstrap 95%CI、pass^k、成本归一化/Pareto。
- 唯一出口：`make sota-gate` 全部条件满足（Mean CVSR 差 ≥3pp、CI 下界>0、pass^5、Critical Object Recall、Fatal Violation Rate、成本护栏）。

## 非目标

- 不改写旧表 5/6/7 的数字，也不删除它们（标记 legacy_exploratory）。
- 不修改测试集/Gold/评分器/基线预算来提高本文方法排名。
- 不把规则回退/提示词模拟/多调用预算/专用后处理伪装成算法增益。
- 不把"无错误输出但大量漏对象"当成功，不把按数量计分称语义 F1。
- 不把只有本文方法能产生的字段作为公平对比指标。
