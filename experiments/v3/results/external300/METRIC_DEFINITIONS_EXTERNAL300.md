# External300 指标定义

- **CVSR**（完整有效场景率）：任务级二值——预测场景在冻结 evaluator_v2.3 下无 fatal 且满足该类核心要求记 1，否则 0；overall 为 300 任务均值。
- **Object/Relation/Binding-F1**：evaluator_v2.3 的 node_match/edge_match/binding_match F1 的任务均值。
- **Critical Recall**：gold critical objects 被预测覆盖的比例均值。
- **Fatal violation rate**：fatal_violations 非空的任务比例。
- **Evidence Precision**：trace 引用证据中有效证据占比均值。
- **Replay Success**：离线重放成功比例。
- **token / cost**：来自 provider 返回的逐条累计；token 与成本分别报告，禁止混用（token≠美元）。
- **延迟双口径**：all_tasks（含 llm_calls=0 的确定性任务，其 latency 近零但计入）与 llm_invoking_tasks（仅 llm_calls>0）。分位数算法 nearest-rank（sorted index ceil(q*n)-1）。
- **McNemar exact**：双侧精确二项 min(1, 2·P(X≥max(b,c)))，X~Bin(b+c, .5)；p<1e-6 时显示为 "p<1e-6" 并附精确尾部值，绝不输出 "p=0"。
- **bootstrap**：任务级配对重采样 10,000 次，seed 20260804，百分位法取 [2.5%,97.5%] 索引。
