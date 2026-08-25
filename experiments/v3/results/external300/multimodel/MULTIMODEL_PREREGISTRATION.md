# 多模型泛化预注册（MULTIMODEL PREREGISTRATION）

日期：2026-08-25 ｜ 状态：**TEMPLATE — 未配置模型 ID，禁止调用任何 API**

## 背景

DeepSeek-V4-Flash 主实验（`ext300_formal_20260825`）已完成并封存，**不得重跑**。
由于主结果已被查看，**放弃事后挑选 150 条子集的选项**（那会构成有利子集偏倚）；
两个新模型家族均须运行**完整 300 条 × 2 方法 = 600 记录/模型**。

## 预注册条款

1. **模型**：两个不同 provider/家族；精确 catalog id 填入
   `model_matrix_config.example.json` 并将 status 改为 FROZEN。
   Provider 若不提供 immutable snapshot，须如实标注。
2. **公平性**：每个模型内部，KF 与 SA 使用完全相同的模型、temperature=0.2、
   预算（30 LLM 调用 / 100 工具调用 / 3 修复轮）与工具权限。
3. **输入与顺序**：与主实验相同的 public inputs（SHA `0ede96ec…3d7`）、
   同一固定顺序表 `order_table_v1.json`；每 task×method 恰好一次逻辑执行。
4. **失败策略**：API 技术失败仅 retries=2 指数退避；逻辑失败绝不重试；
   重试耗尽记 technical_failure=true 零分保留。
5. **封存**：每模型独立 run_id → seal（raw SHA 入 SEAL.json）→ score。
6. **保留义务**：无论方向好坏，全部记录、错误与费用原样保留。
7. **报告**：method × model × task_type 全表；检验 KF−SA CVSR 提升方向是否在
   三个模型（含 DeepSeek 主实验）上一致；禁止只汇报最有利模型。
8. **披露**：author-reviewed benchmark 定位、禁 SOTA、provider 快照不确定性。

## 执行门槛（缺一不可）

- [ ] 两个真实且不同家族的 model catalog id 已填入配置
- [ ] 配置 status=FROZEN
- [ ] 用户明确回复 **MULTIMODEL_RUN_APPROVED**

在此之前不得调用任何付费 API。API key 只经环境变量读取，不写入任何文件。
