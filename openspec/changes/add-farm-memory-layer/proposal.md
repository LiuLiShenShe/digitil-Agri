## Why

数字孪生不能只保存当前 3D 场景，还需要按对象组织状态、时序、事件和分析记录。PRD 要求温室环境、地块墒情、灌溉设备和摄像头在线状态可按对象查询，并支持 24 小时、7 天和日报生成。

## What Changes

- 新增对象同步频率定义：realtime、hourly、daily、milestone、static。
- 新增指标字典，覆盖温度、湿度、土壤水分、CO2、光照、pH、EC、水压、流量和设备开关状态等。
- 支持按对象查询最新值、历史曲线、聚合统计、日级归档和最近 N 天事件。
- 建立事件层，覆盖灌溉、施肥、告警、巡检、维护和 Agent 分析记录。
- 支持生成温室日报所需的数据源聚合。

## Capabilities

### New Capabilities

- `farm-memory-layer`: 定义农业对象的指标、时序、事件、归档、同步频率和日报数据源能力。

### Modified Capabilities

暂无。

## Impact

- 影响 IoT 数据归档、告警/事件表、对象详情趋势、日报生成、TimeSeriesAgent 和 ReportAgent。
- 依赖农业业务对象 ID 作为时序和事件归属锚点。
- 为告警诊断、长势分析和运营日报提供可追溯历史上下文。

