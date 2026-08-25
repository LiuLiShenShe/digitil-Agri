# Public greenhouse data import plan

目标：把 External300 中部分 `memory_query` 的确定性合成记录替换为许可、版本和哈希均可核验的真实温室观测，同时保持任务在首次运行前一次性冻结。

## 候选来源

优先顺序：

1. WUR Autonomous Greenhouse Challenge 2024 dwarf tomato（5 分钟气候、控制、天气和产量记录）。
2. WUR Autonomous Greenhouse Challenge 2022 lettuce。
3. WUR Autonomous Greenhouse Challenge 2019 cherry tomato。
4. WUR Autonomous Greenhouse Challenge 2018 cucumber。

具体 DOI 与官方页面见 `SOURCES.md`。

## 导入门槛

- 从官方 DOI 页面下载，记录版本号、下载时间、许可文本和每个原始文件 SHA-256。
- 原始文件放在不提交 Git 的只读 external-data 目录；仓库只提交派生窗口、数据字典、许可证引用和哈希。
- 不得先运行方法再选择“能拉开差距”的窗口。
- 先按固定规则抽样：作物×compartment×metric×月份分层，使用公开 seed 选择连续窗口。
- 只使用数据集明确提供的单位；所有单位映射需双人复核。
- 真实记录的 `record_id` 由 `source DOI + file hash + row index` 派生，保证可追溯且不暴露 Gold。
- 所有聚合 Gold 由独立 Oracle 从 public records 重算，禁止手填均值。

## 推荐替换规模

在 60 条 memory_query 中，建议 40 条使用真实 WUR 窗口、20 条保留可控合成边界案例。四个 WUR 来源各 10 条真实窗口；每个来源覆盖 temperature、humidity、CO2/light/soil/root-zone 中实际存在的变量。若某来源缺某变量，不得伪造补齐。

## 版本策略

真实数据导入会把候选版本从 `external300-candidate-v0.1` 升级为至少 `v0.2`，触发全部 300 条重新双盲审和新的 public/gold 哈希。旧 v0.1 不得与新版本结果混用。
