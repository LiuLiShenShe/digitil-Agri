# 多模型泛化最终报告 v2（MULTIMODEL_FINAL_REPORT_v2）

日期：2026-08-25 至 2026-08-26（CST）｜ 授权链：用户"同意"→ `MULTIMODEL_SMOKE_APPROVED`；用户"ok，正式启动"→ `MULTIMODEL_RUN_APPROVED MAX_TOTAL_CNY=500`
统计工件：`MULTIMODEL_CANONICAL_STATISTICS_v2.json` + `MULTIMODEL_SUMMARY_v2.csv`（由 `experiments/v3/scripts/multimodel_canonical_stats.py` 从 sealed raw 离线重算，脚本内逐区块校验 SEAL SHA）

## 1. 判定结论（预注册规则，第八节）

**MODEL_GENERALIZATION_PASS**：四个新模型 KF−SA CVSR 配对差值全部 >0，且 **4/4 个**模型 95% bootstrap CI 下界 >0（PASS 仅要求 ≥3）。

| 模型 | run_id | sealed raw SHA-256（前16） | 记录数 | 技术失败 |
|---|---|---|---:|---:|
| DeepSeek-V4-Flash（冻结基线，未动） | ext300_formal_20260825 | `b52f00c4bee3b437` | 600 | 0 |
| Pro/moonshotai/Kimi-K2.6 | ext300_mm1_kimi_20260825 | 见 SEAL.json | 600 | 0 |
| MiniMaxAI/MiniMax-M2.5 | ext300_mm2_minimax_20260825 | 见 SEAL.json | 600 | 1 |
| Qwen/Qwen3.6-27B | ext300_mm3_qwen_20260825 | 见 SEAL.json | 600 | 0 |
| zai-org/GLM-5.2 | ext300_mm4_glm_20260825 | 见 SEAL.json | 600 | 0 |

合计 3,000 条方法—任务记录。DeepSeek 冻结 raw SHA 复验仍为 `b52f00c4…d91`，未被触碰。

## 2. 主结果：CVSR 与配对统计

| 模型 | KF CVSR | SA CVSR | Δ=KF−SA | bootstrap 95% CI | McNemar exact (b,c) |
|---|---:|---:|---:|---|---|
| DeepSeek-V4-Flash（基线） | 0.7167 | 0.4800 | +0.2367 | [0.1833, 0.2900] | p<1e-6 (tail 8.45e-17; 77,6) |
| Kimi-K2.6 (Pro) | 0.6733 | 0.4933 | **+0.1800** | [0.1300, 0.2333] | p<1e-6 (tail 4.18e-11; 63,9) |
| MiniMax-M2.5 | 0.6067 | 0.3500 | **+0.2567** | [0.1967, 0.3167] | p<1e-6 (tail 5.32e-15; 91,14) |
| Qwen3.6-27B | 0.6967 | 0.4800 | **+0.2167** | [0.1667, 0.2667] | p<1e-6 (tail 2.44e-16; 69,4) |
| GLM-5.2 | 0.7367 | 0.4933 | **+0.2433** | [0.1833, 0.3033] | p<1e-6 (tail 9.65e-14; 88,15) |

McNemar 显示规则执行：无任何 "p=0" 表述，全部给出精确尾概率量级与 b/c 计数。

跨模型聚合（**探索性标注**）：按 task_id 聚类 cluster bootstrap（2,000 次重采样），四新模型平均配对差 = **+0.2242，CI95 [0.1792, 0.2700]**。同一批 300 任务被五个模型复用，绝不作为 1,500（或 1,200）个独立样本表述。

## 3. 次级指标（KF / SA）

| 模型 | Obj-F1 | Rel-F1 | Bind-F1 | Crit-Recall | Fatal率 | Evidence-P | Replay |
|---|---|---|---|---|---|---|---|
| 基线 DeepSeek | .690/.635 | .700/.379 | .594/.200 | 1.00/.95 | .000/.250 | 1.00/.947 | .808/.455 |
| Kimi-K2.6 | .657/.622 | .759/.419 | .597/.198 | 1.00/.947 | .000/.290 | 1.00/.933 | .808/.442 |
| MiniMax-M2.5 | .705/.595 | .711/.417 | .529/.140 | 1.00/.973 | .003/.293 | .990/.957 | .798/.475 |
| Qwen3.6-27B | .658/.635 | .771/.468 | .600/.200 | 1.00/.963 | .000/.250 | 1.00/.953 | .808/.458 |
| GLM-5.2 | .715/.619 | .717/.368 | .574/.188 | 1.00/.883 | .000/.227 | .997/.853 | .805/.383 |

模式与基线一致且跨家族复现：**KF 的 Fatal 率≈0、Evidence Precision≈1、Replay≈0.80，而 SA 的 Fatal 率 0.23–0.29、Bind-F1≤0.20、Replay≈0.38–0.48**。结构化约束（typed repair + 绑定时间戳契约）的收益不依赖单一模型家族。

## 4. 五类任务分层 CVSR（KF / SA）

| 类型 | 基线 | Kimi | MiniMax | Qwen | GLM |
|---|---|---|---|---|---|
| scene_construction | .50/.40 | .42/.50 | .63/.53 | .48/.40 | .63/.65 |
| data_binding | **1.00/1.00** | .95/.97 | **.27/.22** | **1.00/1.00** | .87/.82 |
| rule_repair | **1.00/0.00** | **1.00/0.00** | **1.00/0.00** | **1.00/0.00** | **1.00/0.00** |
| memory_query | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| asset_routing | .08/.00 | .00/.00 | .13/.00 | .00/.00 | .18/.00 |

关键读数：
- **rule_repair 五模型完全一致**：KF 全部 1.00、SA 全部 0.00 —— 该类型差异是协议性的（修复轮机制），非模型能力。
- **MiniMax-M2.5 的 data_binding 异常**（KF .27 vs 其余四模型 .87–1.00）是唯一明显的家族性退化点，也是其 CVSR 绝对值最低的主因；其 Δ 仍为最大值之一（+0.2567）。已如实报告，不做剔除。
- asset_routing 对所有模型都难（KF ≤0.18，SA=0），是任务本身的难度上限，不是方法差异。

## 5. 成本、延迟与技术失败

| 模型 | tokens 总量 | harness 记账 $ | ≈¥（快照汇率） | 实测延迟 p50/p95（s，含工具全程） |
|---|---:|---:|---:|---|
| DeepSeek（基线） | 1,141,491 | 0.1889 | ~1.27 | 2.5/12.5 |
| Kimi-K2.6 | 1,112,008 | 0.1913 | ~1.29 | 3.8/41.1 |
| MiniMax-M2.5 | 1,699,270 | 0.3517 | ~2.37 | 14.5/131.3 |
| Qwen3.6-27B | 1,165,235 | 0.1991 | ~1.34 | 10.3/64.8 |
| GLM-5.2 | 1,085,281 | 0.1897 | ~1.28 | 5.1/31.8 |

- 四新模型合计 harness 记账 **$0.9318 ≈ ¥6.28**（记账单价为 harness 内置 DeepSeek 价，仅作相对计量）；按 price_snapshot 各模型真实价格计价的期望费用约 ¥37.7（见 smoke 报告），两者口径不同、均已披露。
- 实际总花费远低于授权上限 MAX_TOTAL_CNY=500。
- 唯一技术失败：MiniMax 区块 EXT-SC-049 / SingleAgent-AllTools 读超时（retries=2 耗尽后按预注册记 `technical_failure=true` 零分保留，未逻辑重试）。

## 6. 结论限定语（写入论文的边界）

1. 只宣称**跨模型家族泛化**（GLM/Qwen/Kimi/MiniMax/DeepSeek 五个家族方向一致），五模型均经同一硅基流动 OpenAI 兼容接口，**不宣称跨 provider 泛化**。
2. External300 是同一批任务的重复测试，非各模型独立样本；聚合统计以 cluster bootstrap 给出并标探索性。
3. pass@5 在本协议（每 task×method 单次执行）下未定义，不作报告。
4. catalog 快照与价格为 2026-08-25 时点数据，硅基流动目录/价格可变，非不可变承诺。
5. 所有模型结果无论好坏均保留：MiniMax 的 data_binding 退化、asset_routing 的普遍低分均在报告中。

## 7. 工件清单（已提交于 commit 753b455）

- `multimodel/MULTIMODEL_CANONICAL_STATISTICS_v2.json`（全指标机器可读）
- `multimodel/MULTIMODEL_SUMMARY_v2.csv`（10 行汇总表）
- `multimodel/MULTIMODEL_FINAL_REPORT_v2.md`（本文件）
- 四个封存运行目录：`ext300_mm{1..4}_*_20260825/{raw/runs.jsonl, run_manifest.json, SEAL.json, scored/*}`
