# 多模型泛化实验最终交付报告 v2（MULTIMODEL DELIVERY REPORT，用户指令第十节）

日期：2026-08-26（CST）｜ 授权链：零付费阶段完成 → 用户"同意"（=MULTIMODEL_SMOKE_APPROVED）→ smoke 完成 → 用户"ok，正式启动"（=MULTIMODEL_RUN_APPROVED MAX_TOTAL_CNY=500）→ 四区块正式运行+封存+评分 → 统计判定 → 论文同步。全程未 commit、未 push。

## 1. Git 状态（前/后）

| 项目 | 值 |
|---|---|
| 分支 | `paper/knowledge-agent-experiments` |
| 开始前 HEAD | `3ad70bc8552e79d8fea4d6b4a5514036b87c540b`（CI passing，runs/32808312273） |
| 结束时 HEAD | 同上（**无新 commit**） |
| 工作树 | 2 个修改 + 16 个未跟踪路径（见第 9 节） |

## 2. 测试与冻结完整性

- `pytest experiments/v3/tests/ -q` → **126 passed**（运行前后各一次，全绿）。
- 五区块封存校验（raw SHA == SEAL.json 内 SHA）：

| run_id | 记录数 | sealed raw SHA-256（前16） | 校验 |
|---|---:|---|---|
| ext300_formal_20260825（冻结基线，未动） | 600 | `b52f00c4bee3b437` | ✅ 且等于预注册冻结值全串 |
| ext300_mm1_kimi_20260825 | 600 | `1e4586f857121572` | ✅ |
| ext300_mm2_minimax_20260825 | 600 | `54659bbad58d5842` | ✅ |
| ext300_mm3_qwen_20260825 | 600 | `eaeefdbdc14ad5de` | ✅ |
| ext300_mm4_glm_20260825 | 600 | `378474f46a6deeec` | ✅ |

- 2,400 条新记录唯一性（task×method 各一次）、600×4 完整性由统计脚本加载时断言通过。
- FREEZE_CHECK_latest.json：7 PASS + 1 BLOCKED（`independent_human_review_evidence`——既有的 author-reviewed 身份披露项，非本轮引入；diff 仅时间戳变化）。

## 3. 模型与协议

精确 catalog ID（禁止替换，全部按原样运行成功）：`Pro/moonshotai/Kimi-K2.6`、`MiniMaxAI/MiniMax-M2.5`、`Qwen/Qwen3.6-27B`、`zai-org/GLM-5.2`；base_url `https://api.siliconflow.cn/v1`；温度 0.2；预算 30 LLM/100 工具/3 修复轮/超时 300s。预注册哈希：`MULTIMODEL_PREREGISTRATION_v2.md` 与 `model_matrix_config_v2.json`（内含 runner/harness/method/evaluator/prompt/order_table 全部 SHA-256，执行前后比对一致）。任务顺序与 KF/SA 配对复用 `order_table_v1.json`（150 KF 先/150 SA 先）。区块顺序 seed 20260825：Kimi→MiniMax→Qwen→GLM。

thinking 开关披露：顶层 `enable_thinking=false` 被四模型接受（无 400）但仅部分模型生效；MiniMax-M2.5 无论开关均输出 reasoning_content（provider default，按预注册 §3 记录，未做任何模型专属调参）。

## 4. 主结果与泛化判定

**MODEL_GENERALIZATION_PASS**（预注册规则 §6：四 Δ>0 且 ≥3 个 CI 下界 >0；实际 4/4 与 4/4）：

| 模型 | KF CVSR | SA CVSR | Δ(pp) | CI95 | McNemar (b,c) |
|---|---:|---:|---:|---|---|
| DeepSeek（基线） | .7167 | .4800 | +23.67 | [18.33, 29.00] | p<10⁻⁶ (77,6) |
| Kimi-K2.6 | .6733 | .4933 | +18.00 | [13.00, 23.33] | p<10⁻⁶ (63,9) |
| MiniMax-M2.5 | .6067 | .3500 | +25.67 | [19.67, 31.67] | p<10⁻⁶ (91,14) |
| Qwen3.6-27B | .6967 | .4800 | +21.67 | [16.67, 26.67] | p<10⁻⁶ (69,4) |
| GLM-5.2 | .7367 | .4933 | +24.33 | [18.33, 30.33] | p<10⁻⁶ (88,15) |

探索性聚合（cluster bootstrap by task_id，2000 次）：四新模型平均 Δ=+22.42pp，CI95 [17.92, 27.00]。安全性模式跨家族一致（KF Fatal≈0 / Replay≈0.80 vs SA Fatal 0.23–0.29 / Bind-F1≤0.20 / Replay≤0.48）。rule_repair 类五模型完全一致（KF 1.00 / SA 0.00）。MiniMax 的 data_binding 家族性退化（KF 0.27）如实保留。pass@5 在单次执行协议下不定义、不报告。

完整指标（F1 族/Critical Recall/Evidence Precision/分类型/延迟双口径/token）：见 `MULTIMODEL_CANONICAL_STATISTICS_v2.json`、`MULTIMODEL_SUMMARY_v2.csv`、`MULTIMODEL_FINAL_REPORT_v2.md`。

## 5. 成本对账（授权上限 ¥500）

- harness 记账（内置单价，相对计量口径）：四新区块合计 $0.9318。
- 按 price_snapshot 各模型真实价格估算期望 ≈¥37.7（smoke 报告口径）；实际远低于上限。
- smoke 阶段花费 ≈¥0.26（首次因脚本格式化错误中断重跑，废弃 ≈¥0.12 已披露）。

## 6. 技术失败与偏差记录

- 唯一技术失败：MiniMax 区块 EXT-SC-049 / SingleAgent-AllTools 读超时（retries=2 耗尽，按预注册记 `technical_failure=true` 零分保留，未逻辑重试）。
- 区块链中断一次：mm2 封存后 mm3/mm4 未自动排队，人工补发链式命令续跑（仅顺序问题，无重复采样，ledger 断点校验通过）。
- 无任何按性能中止、选择性重跑或提示词调整。

## 7. 论文变更清单（第九节，`计算机研究与发展专题投稿初稿.md`）

1. 摘要（中/英）：删除"多模型泛化实验尚未完成/left as future work"，替换为四家族方向一致 + PASS 判定 + 单一接口限定语。
2. 引言诚实边界段：同步更新并指向 5.4.6。
3. 新增 **5.4.6 跨模型家族泛化（预注册多模型实验）**：表 5d（五模型 × 配对统计）、安全性模式、分类型读数、cluster bootstrap 聚合（探索性标注）、五点边界声明。
4. 5.8 有效性威胁第 4 条改写："单一底座模型"→"底座模型与推理接口"（保留单一接口限制与快照非不可变披露）。
5. 结论第 2/3 段：加入多模型结果与边界限定；future work 改为独立测试集 + 多独立推理服务重复验证。
- DeepSeek 原有结果数字全部未动；无 SOTA/排行榜/private held-out 表述；McNemar 无 "p=0" 写法。

## 8. 判定的适用范围（再次声明）

仅支持**同一硅基流动接口下的跨模型家族稳健性**；不宣称跨 provider 泛化、不外推为对未见数据的泛化、不构成独立外部验证。

## 9. 未提交文件清单（等待用户审阅决定）

修改（2）：
- `计算机研究与发展专题投稿初稿.md`（论文同步）
- `experiments/v3/results/external300/FREEZE_CHECK_latest.json`（时间戳刷新，检查结果不变）

新增（16 路径）：
- 4 个封存运行目录 `ext300_mm{1..4}_*_20260825/`（各含 raw/runs.jsonl 600 条、run_manifest.json、SEAL.json、scored/*）
- `multimodel/` 下 11 个文件：PREREGISTRATION_v2、model_matrix_config_v2、model_catalog_snapshot、price_snapshot、PREFLIGHT_REPORT_v2、smoke_results_v2、SMOKE_REPORT_v2、CANONICAL_STATISTICS_v2、SUMMARY_v2.csv、FINAL_REPORT_v2、本报告
- 2 个脚本：`scripts/multimodel_smoke.py`、`scripts/multimodel_canonical_stats.py`

`git diff --stat`：
```
 .../results/external300/FREEZE_CHECK_latest.json   |  2 +-
 计算机研究与发展专题投稿初稿.md                      | 34 +++++++++++++++++-----
 2 files changed, 28 insertions(+), 8 deletions(-)
```

## 10. 提交建议

建议拆两次提交：(1) `feat(v3): multimodel generalization — prereg v2 + 4 sealed blocks (2400 records) + canonical stats + PASS verdict`（运行目录+multimodal 工件+两脚本）；(2) `docs(paper): sync cross-model family generalization results (§5.4.6, abstract, threats, conclusion)`（论文+FREEZE_CHECK 时间戳）。**未经用户明确指示不会执行 commit/push。**
