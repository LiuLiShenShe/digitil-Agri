# 多模型泛化零付费预检报告 v2（PREFLIGHT_REPORT_v2）

日期：2026-08-25（CST）｜ 阶段：**一至五（零付费）已完成，停止等待 `MULTIMODEL_SMOKE_APPROVED`**

## 1. 仓库健康状态

- 分支 `paper/knowledge-agent-experiments`，HEAD `3ad70bc`，工作树在本次预检前干净（0 未提交）。
- 用户指令第三节第 2–4 点已在本轮之前完成并提交：`71940cd`（194 个 pyc 移出追踪 + `.gitignore` 三条规则）、`3ad70bc`（CI 依赖 `pytest requests jsonschema`）。当前 `git ls-files` 中 pyc/pycache 计数为 **0**。
- GitHub Actions：`3ad70bc` 上 v3-evidence-integrity **success**（runs/32808312273；此前两次失败系 jsonschema 缺失，已修复）。
- pytest：`experiments/v3/tests/ -q` → **126 passed**。

## 2. 冻结完整性（前后双验）

| 文件 | SHA-256 |
|---|---|
| raw runs.jsonl | `b52f00c4bee3b43723689c3556300e0754a8ab9564b96341d05e88b591d40d91` = SEAL 值 ✅ |
| SEAL.json | `86f88f278dec22e9c82f44cf906cf591246cffa35bba0fec2d50b9f58d81c731` |
| scored/per_task.jsonl | `43e7750e5ae1e127b5b4d12083c5d48f8db1dcf177870013b2eacd3c61a0bf12` |
| order_table_v1.json | `fceca2f6818c117327c12baf2d569fe49072ab0d8fc61cb2d7f30da6267bfa39` |
| VOIDED.json (20260824) | `5884302aa87cd4c7b50cd0a0669e312044adf677ad59b2c42a19c2d0efa4e8e4` |
| public inputs | `0ede96ecb3c7e49c33e591c9d21c729db287dd5bd17148e7ca2d815f72d0e3d7` |
| gold draft | `a07964f6d3cc03f2561d51a9d097596ad52fd3345cde2e0ef317001c87c88891` |

前置与后置校验一致（见第 7 节后验），冻结文件零改动。

## 3. 精确模型可用性（非计费 GET /v1/models，2026-08-25）

四个精确 catalog ID **全部存在**：`zai-org/GLM-5.2`、`Qwen/Qwen3.6-27B`、`Pro/moonshotai/Kimi-K2.6`、`MiniMaxAI/MiniMax-M2.5`（目录共列 95 个模型；详见 model_catalog_snapshot.json）。无需任何替换。环境变量 `AGNES_BASE_URL / AGNES_API_KEY / AGNES_MODEL` 均 SET（仅检查存在性，值未打印）。

## 4. 实时价格快照（官方价格中心 siliconflow.cn/pricing，¥/M tokens）

| 模型 | 输入 | 输出 | 缓存命中 |
|---|---:|---:|---:|
| GLM-5.2 (`zai-org/GLM-5.2`) | ¥8.00 | ¥28.00 | ¥2.00 |
| Qwen3.6-27B (`Qwen/Qwen3.6-27B`) | ¥3.00 | ¥18.00 | —（页面无缓存价） |
| Kimi-K2.6 (`Pro/moonshotai/Kimi-K2.6`) | ¥6.50 | ¥27.00 | ¥1.10（Pro 档） |
| MiniMax-M2.5 (`MiniMaxAI/MiniMax-M2.5`) | ¥2.10 | ¥8.40 | ¥0.21 |

对照：页面 DeepSeek-V4-Flash ¥1.00/¥2.00 与冻结运行记账价 $0.14/$0.28 一致（≈7.15 CNY/USD），交叉验证通过。汇率 CNY→USD 0.148398（open.er-api.com，2026-08-25）。

## 5. Token 基线与拆分可得性（sealed raw 重算）

- KF 总 668,769 tokens / 514 LLM 调用（2229 tokens/run）；SA 总 472,722 / 388 次（1576/run）；合计 1,141,491 tokens/模型区块。
- 分类型：KF scene 256,152 / bind 178,471 / asset 153,401 / repair 80,745 / mem 0（确定性）；SA asset 206,299 / scene 194,896 / bind 71,527 / 其余 0。
- **拆分披露**：冻结 raw 仅存 total，prompt/completion/reasoning/cached 全文扫描 0 命中——估算按区间给出，smoke 实测 usage 形状后可收窄。

## 6. 费用估算（每模型 600 条；三档：乐观=全输入价 / 期望=输入:输出 4:1 / 保守=2:1；安全=期望×1.5）

| 模型 | 乐观 | 期望 | 安全(×1.5) |
|---|---:|---:|---:|
| GLM-5.2 | ¥9.13 | ¥13.70 | ¥20.55 |
| Qwen3.6-27B | ¥3.42 | ¥6.85 | ¥10.27 |
| Kimi-K2.6 (Pro) | ¥7.42 | ¥12.10 | ¥18.15 |
| MiniMax-M2.5 | ¥2.40 | ¥3.84 | ¥5.75 |
| **四模型合计** | **≈¥150.8** | **≈¥245.8 ($36.48)** | **≈¥368.8 ($54.72)** |

**Smoke 费用预估**（16 次方法运行 × ≤2500 tokens，最坏情形按各模型保守档）：GLM ≤¥3.95、Qwen ≤¥2.16、Kimi ≤¥3.59、MiniMax ≤¥1.13，**合计 ≲ ¥11**。

**建议 `MAX_TOTAL_CNY`：500 元**（安全档 ¥368.8 再上浮约 35%，吸收 token 量漂移与新模型输出更长的风险；如需更紧可取 450）。

## 7. 后验（报告生成前复跑）

冻结文件 SHA 与第 2 节完全一致；pytest 126 passed 维持；新增文件全部位于 `multimodel/` 目录。

## 8. 本阶段新增文件（未 commit、未 push）

- `multimodel/MULTIMODEL_PREREGISTRATION_v2.md`
- `multimodel/model_matrix_config_v2.json`（含全部代码/prompt/gold/public/order_table SHA）
- `multimodel/model_catalog_snapshot.json`
- `multimodel/price_snapshot.json`
- `multimodel/PREFLIGHT_REPORT_v2.md`（本文件）

v1 预注册与 example 配置原样保留。

## 9. 是否满足开始 smoke 的条件

**满足**：仓库健康 ✅、四精确 ID 可用 ✅、价格与费用已估 ✅、预注册 v2 已冻结 ✅、测试全绿 ✅、冻结完整性双验一致 ✅。
已知待办（smoke 授权后处理并披露+补测试）：`llm.py` 的 `enable_thinking` 硬编码需按模型参数化；`budget.py` 单价硬编码 DeepSeek 需按 price_snapshot 注入（默认值不变则行为不变）。

**等待授权字符串：`MULTIMODEL_SMOKE_APPROVED`**
