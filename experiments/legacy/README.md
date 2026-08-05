# experiments/legacy — 旧实验归档（legacy_exploratory）

本目录是 **KAFarmTwin 旧实验结果的只读归档**，对应论文旧表 5 / 表 6 / 表 7（`*_paper_table.csv`）及其报告（`*_report.md`）。

## 状态：LEGACY_EXPLORATORY — 不再作为 SOTA 证据

这些结果**不得**再被当作公平、可复现的 SOTA 证据使用。原因（由 v3 重建审计确认）：

1. **评分器违规**：`score_record()` 对 objects/relations/bindings 使用 `min(generated_count, required_count)` 计"正确数"，正是被禁止的公式。
2. **方法专属补料**：`build_ours_relations()` / `build_ours_bindings()` 在评分阶段替 "Ours" 事后伪造关系/绑定，非公平对比。
3. **证据自动铸造**：`build_tool_evidence(fill_missing_executed_evidence=True)` 为缺失 evidence 自动铸 `exec-{idx:03d}`，无真实响应也计 Evidence。
4. **ETF 结构性偏差**：基线系统 prompt 被禁止输出 `traceType="executed"` 且禁止伪造 evidenceId → 所有基线 ETF=0.000，Ours ETF=1.000。
5. **消融非端到端**：`run_ablation_experiment.py` 是对已保存 Ours 输出的确定性降级，无运行时 feature flag。
6. **无统计**：无 bootstrap/CI/配对检验；每任务仅 1 次运行。

## 文件清单（均为 originals 的副本；原文件保留在 experiments/results/）

- `ablation_experiment_paper_table.csv` / `_report.md` — 旧表 6（消融）
- `main_experiment_paper_table.csv` / `_report.md` — 旧 v1 表 5
- `main_experiment_v2_paper_table.csv` / `_report.md` — 旧 v2 表 5（公平基线）
- `model_pair_{deepseek_v4_flash,glm_5_1,kimi_2_6,minimax_m2_5}_paper_table.csv` / `_report.md` — 旧表 7（多模型配对）

## 取代方案

新的权威实验位于 `experiments/v3/`（版本化冻结基准 + 独立语义评分器 + 公平基线协议 + 类型化修复闭环 + 端到端消融 + 统计），以 `make sota-gate` 为唯一通过门槛。
