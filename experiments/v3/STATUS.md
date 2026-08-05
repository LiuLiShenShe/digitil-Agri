# KAFarmTwin v3 — STATUS

当前阶段：dev 集 5× 统计实验完成，replay/evidence 修复已验证；测试集被 LLM 账户余额耗尽阻断。
状态：BLOCKED（SOTA Gate 未通过，两个硬阻塞：① SiliconFlow 余额不足 ② T031-T035 待人工标注）

## 当前 SOTA / 基线（dev 集 5× 真实 LLM，8 任务 × 2 方法 × 5 次 = 80 run）
| 方法 | CVSR | pass5 | objF1 | critR | fatal率 | evidP | replay |
|------|------|-------|-------|-------|--------|-------|--------|
| KAFarmTwin-TypedRepair | 0.375 | 0.375 | 0.799 | 0.875 | 0.0 | 1.0 | 1.0 |
| SingleAgent-AllTools | 0.250 | 0.250 | 0.510 | 0.525 | 0.15 | 1.0 | 0.727 |

- **配对 bootstrap（KF vs SA）**：mean diff +0.125，95% CI [+0.025, +0.225]，下界>0，p=0.0044。Pareto=[KF]。
- dev 结果有效（80 run 无 LLM error），但 **非 SOTA Gate 证据**（gate 定义在 frozen test split，见 sota-gate/spec.md L15）。
- replay 修复后 KF 全任务 replay=1.0、evidP=1.0（trace_proxy deepcopy 修复，见 FAILURES F-005）。

## 距离 SOTA Gate — 硬阻塞
- **[BLOCKED] LLM 账户余额耗尽（F-006）**：测试集 5× 运行中 SiliconFlow 报 HTTP 402，28/40 test run 是 API 失败伪影，测试证据不完整。需充值后重跑 28 个缺失 run。
- **[BLOCKED] T031-T035 盲 Gold 未标注（F-004）**：第 3 阶段标注者=用户，5 任务待人工复核。
- [x] gate 脚本已加 `split_is_test` 守卫，dev-only 结果不再误判 PASS。

## 完成里程碑
- [x] 阶段0-5 / 评分器-金标准 8/8 dev 对齐 / 反作弊 21 绿
- [x] 修复循环架构：batched ops 修复、add_edge→parent 一致性、trait(23)/memory(25-26) 数据模型
- [x] trace_proxy deepcopy 修复 → replay 全绿（F-005）
- [x] dev 集 5× 统计实验完成（80 run，无 LLM error）
- [ ] 测试集完整 5× 统计（被 F-006 余额阻断）
- [ ] SOTA Gate 通过（含 gold-hash、cost ≤1.5×、pass5、测试集标注）
- [ ] 测试集 T031-T035 盲测 Gold 标注（BLOCKED_HUMAN_ANNOTATION）

## 阻塞项
- `BLOCKED_LLM_BUDGET`（F-006）：SiliconFlow 余额充值后重跑测试集。
- `BLOCKED_HUMAN_ANNOTATION`（F-004）：T031-T035 盲 Gold 待用户复核。

## 下一步（解锁后）
```
# 充值 + 标注完成后，重跑完整测试集（T27-T30 + 标注后的 T031-T035）
python3 experiments/v3/scripts/run_fair_baselines.py --split test --runs 5 \
  --methods KAFarmTwin-TypedRepair,SingleAgent-AllTools
make statistical-report --split test && make sota-gate
```
- [x] 修复循环架构：batched ops 修复、add_edge→parent 一致性、trait(23)/memory(25-26) 数据模型
- [x] 真实 KAFarmTwin T19/T20/T22/T24 ok、T20 修复循环真实收敛 CVSR=1.0
- [ ] 阶段8 ≥5 次/任务×方法 统计实验 + 配对 bootstrap/sign test/Pareto
- [ ] 阶段8 SOTA Gate 通过（含 gold-hash、cost ≤1.5×、pass5、Names 等全部条件）
- [ ] 测试集 T031-T035 盲测 Gold 标注（BLOCKED_HUMAN_ANNOTATION）

## 阻塞项
- `BLOCKED_HUMAN_ANNOTATION`：测试集盲 Gold 待用户复核。
- 真实 LLM 修复循环方差大：单次运行可能不收敛，需多运行统计平均。

## 下一步（下一条可执行命令）
```
# 6 个 repair 任务 × 5 次 × 2 方法（KF vs SA）对比统计
python3 experiments/v3/scripts/run_fair_baselines.py --split dev --runs 5 \
  --methods KAFarmTwin-TypedRepair,SingleAgent-AllTools
# 达标后
make statistical-report && make sota-gate
```
## 2026-08-05 更新：dev vs test 诚实对比（SiliconFlow V4-Flash，same-model）
- **dev**（T19-T26，8 任务）：KF CVSR=0.375 vs SA 0.250，配对 bootstrap +0.125，95%CI [+0.025,+0.225] 下界>0，p=0.0044，Pareto=[KF]。80 run 全部有效。
- **test**（T27-T30，4 记忆查询任务）：**两方法全部 CVSR=0（0/40）**，无 API error。根因是 F-007：test gold 对 memory_query 检索任务要求构建植物场景（T27/T30 各 20 Plant），prompt 与 gold 自相矛盾。
- **Gate 状态**：FAIL（split 为 test 才算数；且 test gold 需先解决 F-007 标注矛盾 + T031-T035 仍未标注）。诚实结论：**当前无法通过 SOTA Gate，dev 优势不能作为 test gate 证据。**

## 2026-08-05 A+ 重建评测协议：F-007 → F-014 完成
- **F-007**: test_v1 归档 + INVALIDATION_REPORT（T27-T30 Prompt-Gold 矛盾，CVSR 恒 0 根因）
- **F-008**: 多任务 Gold Schema v2（task_type + per-type gold，schema.json 重写）+ task_types.py 分发
- **F-009**: memory_query fixture + Oracle（确定性 expected_answer/evidence，不要求建场景）
- **F-010**: Query-CVSR（10 条件二元指标 + 连续诊断）+ 12 单测
- **F-011**: T27-T30 重标注迁至 regression/（oracle 自洽通过）
- **F-012**: T031-T035 标注审查包（5 包，PENDING_HUMAN_REVIEW，T034 用 Query-Gold）
- **F-013**: Gold 静态审计器（能捕获 test_v1 缺陷类）+ 6 单测
- **F-014**: test_v2 候选集（20 任务 × 5 类 × 4，0 审计错误，oracle 自洽，SHA-256 记录）

**Gate 状态**: BLOCKED（两个待人工解锁项）：
1. method/evaluator freeze commit（experiments/v3 未提交）
2. test_v2 20 任务 gold 人工批准（annotator 2 = 用户）+ T031-T035 复核
