## Development Progress

- Phase 0 baseline guard completed on 2026-05-21; see `openspec/development-phases/phase0-baseline-report.md`.
- Phase 3 farm memory layer implemented on 2026-05-21: 10/10 implementation tasks complete.
- Object-scoped metrics, time-series/event queries, report data source, frontend entries, and Agent read-only query structures are implemented; archive after review if desired.
- Database migration `digital-twingo/phase3_farm_memory_layer_migration.sql` has been executed in the current development database, creating `farm_event_memory` and `farm_daily_archive`.

## 1. 指标与同步策略

- [x] 1.1 定义同步频率枚举：realtime、hourly、daily、milestone、static。
- [x] 1.2 建立指标字典，覆盖温度、湿度、土壤水分、CO2、光照、pH、EC、水压、流量和设备开关状态。
- [x] 1.3 为 Greenhouse、Parcel、Plant、Sensor、Device、Camera 定义默认同步频率和指标绑定策略。

## 2. 时序与事件查询

- [x] 2.1 实现按对象查询最新值、历史曲线和聚合统计。
- [x] 2.2 支持 24 小时和 7 天两个时间范围。
- [x] 2.3 实现事件查询，覆盖灌溉、施肥、告警、巡检、维护和 Agent 分析记录。
- [x] 2.4 建立日级归档数据结构或任务。

## 3. 日报数据源

- [x] 3.1 聚合同一温室的环境、设备、告警和事件数据。
- [x] 3.2 提供 ReportAgent 或日报生成流程所需的只读数据接口。
- [x] 3.3 验证温室日报能引用环境摘要、设备状态、告警、灌溉事件和建议所需数据。
