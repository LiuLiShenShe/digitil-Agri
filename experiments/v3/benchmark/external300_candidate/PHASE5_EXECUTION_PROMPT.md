# Phase 5 execution prompt — use only after human freeze

把下面内容作为后续执行代理的提示词。当前不要执行，因为 External300 仍是 pending candidate。

```text
你负责 External300 的一次性 confirmatory evaluation。先做只读审计，不得修改 benchmark、方法、evaluator、prompt、预算或阈值。

硬门槛：
1. 读取 PREREGISTRATION_DRAFT.md；若仍有任何 [待填]，立即停止并报告。
2. 检查 300 条 review queue：Reviewer A/B 均有独立结论，分歧均有 adjudicator，final_status 全为 approved，freeze_eligible 全为 true。
3. 只接受 sealed public/gold 和 frozen manifest；校验 SHA-256、method/evaluator commit、prompt hash、provider/model、预算。
4. Gold 不得进入 method task/context/log；方法只看 public whitelist 字段。
5. 首次运行前保存 git status、环境、依赖、模型披露和命令；不自动 commit/push。

执行：
- 对全部 300 条任务，按预注册的固定顺序各运行 KAFarmTwin-TypedRepair 与 SingleAgent-AllTools 一次。
- API 技术失败只按预注册规则处理；不得因逻辑失败重试。
- 保存逐 run 原始 JSONL、费用、token、延迟、trace、evaluator hash 和 benchmark hash。
- scorer 只在两方法的原始输出全部落盘后解封 Gold。

报告：
- overall 与五类分别报告 CVSR、Fatal、Binding-F1、Object-F1、Critical Recall、Evidence Precision、Replay、成本和延迟。
- 报告 300 个配对任务的 KF−SA 差值、10,000 次 paired bootstrap 95% CI、McNemar exact test。
- 给出失败类型矩阵和逐类差异；无论结果好坏均保留。
- 禁止写 SOTA；若没有真正独立人员和多模型复现，明确保留该限制。

完成主实验后才按预注册执行另外两个模型家族的泛化矩阵；每个模型内两个方法必须使用同一模型和相同预算。不要挑选最有利模型。
```
