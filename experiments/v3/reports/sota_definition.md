# SOTA 定义（experiments/v3/reports/sota_definition.md）

## 1. 背景

本项目没有与外部论文完全一致的"设施农业对象图构建"公共基准。因此不得声称超过跨论文 SOTA，除非找到任务定义、数据划分、工具权限、指标与预算完全一致的外部公开结果。

## 2. 外部参考（不作为数字比较对象）

相关工作中：3D 场景生成、文本场景图生成、工具智能体评价等。它们只能作为**方法与评测设计参考**，不能直接作为本项目数字对比对象。详见论文相关工作中表（由 S9 论文同步生成）。

## 3. 项目内当前 SOTA（本文唯一比较基准）

项目内 SOTA 定义为：**在冻结测试集、同底座模型、同工具集合、同知识、同最大轮数、同 Token/费用上限、同外部 Trace 记录器、同评分器下，所有公平基线中主指标最高的方法。**

主指标：**CVSR**（Complete-and-Valid Scene Rate）。

必须实现并比较的公平基线：
1. `SingleAgent-AllTools`
2. `ReAct-AllTools`
3. `GenericMultiAgent-AllTools`
4. `GenericRepair-AllTools`
5. `KAFarmTwin-TypedRepair`（本文）
6. `DeterministicFallback`（可选，单独列报回退率）

可额外加入公开可复现方法，但不得降低上述基线能力。

## 4. 旧表 5/6/7 地位

旧表 5/6/7（`experiments/legacy/tables/`）标记 **legacy_exploratory**：
- 不覆盖原文件
- 不再作为 SOTA 证据
- 不作废可复现性事实，但数字由 v3 新结果取代

## 5. 候选宣称的边界

- 跨论文 SOTA 宣称：仅当有完全一致外部基准时允许（当前无）。
- 项目内 SOTA 宣称：仅在 `make sota-gate` 全部通过后允许。
- 若只能证明某一底座模型成立，结论须明确限定该模型。
