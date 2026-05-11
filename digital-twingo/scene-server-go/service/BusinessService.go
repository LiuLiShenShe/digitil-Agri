package service

import (
	"math"
	"sort"
	"time"

	"scene-server-go/mapper"
	"scene-server-go/vo"
)

type BusinessService struct {
	dao *mapper.MonitorMapper
}

type businessMetricSource struct {
	deviceIds []string
	metrics   []string
}

type metricValue struct {
	value float64
	unit  string
	ok    bool
}

func NewBusinessService() *BusinessService {
	return &BusinessService{
		dao: mapper.NewMonitorMapper(),
	}
}

func (s *BusinessService) GetOverview() vo.ResultVo {
	latestRows, _ := s.dao.FindLatestMetrics()
	alertRows, _ := s.dao.FindRecentAlerts(80)
	unackedCount, _ := s.dao.CountUnackedAlerts()

	latest := buildLatestMetricMap(latestRows)
	alerts := buildBusinessAlerts(alertRows)
	subsystems := []vo.BusinessSubsystemVo{
		s.buildSoil(latest, alerts),
		s.buildWeather(latest, alerts),
		s.buildIrrigation(latest, alerts),
		s.buildGreenhouse(latest, alerts),
		s.buildVideo(latest, alerts),
		s.buildEnvironment(latest, alerts),
	}

	summary := buildBusinessSummary(subsystems, alerts, unackedCount)
	return vo.ResultVo{
		Code: 200,
		Data: vo.BusinessOverviewVo{
			UpdatedAt:  time.Now(),
			ParkName:   "智慧农业示范园区",
			Summary:    summary,
			Subsystems: subsystems,
		},
	}
}

func (s *BusinessService) buildSoil(latest map[string]map[string]metricValue, alerts map[string][]vo.MonitorAlertVo) vo.BusinessSubsystemVo {
	metrics := []vo.BusinessMetricVo{
		metricFrom(latest, "soilMoisture", "土壤湿度", "%", []string{"iot-field-01", "iot-greenhouse-01", "iot-irrigation-01"}),
		metricFrom(latest, "temperature", "土壤温度", "°C", []string{"iot-field-01"}),
		metricFrom(latest, "ph", "土壤 pH", "pH", []string{"iot-field-01", "iot-greenhouse-01"}),
	}
	return vo.BusinessSubsystemVo{
		Key:                 "soil",
		Name:                "土壤墒情系统",
		Objective:           "掌握地块土壤水分、温度和酸碱度变化，辅助灌溉决策。",
		Status:              subsystemStatus(metrics, pickAlerts(alerts, "iot-field-01", "iot-greenhouse-01")),
		ImplementationLevel: "partial",
		CompletionRate:      68,
		PrimaryDeviceIds:    []string{"iot-field-01", "iot-greenhouse-01"},
		Metrics:             metrics,
		Workflows: []vo.BusinessWorkflowVo{
			{Name: "实时墒情", State: "ready", Description: "已由模拟传感器持续写入并支持最新值查询。"},
			{Name: "分层剖面", State: "partial", Description: "当前只展示表层指标，未区分表层/中层/深层。"},
			{Name: "历史趋势", State: "partial", Description: "已有时序数据，业务页尚未提供 24h/7d/30d 导出。"},
		},
		Alerts: pickAlerts(alerts, "iot-field-01", "iot-greenhouse-01"),
		Gaps: []string{
			"缺少地块分区配置表和土层字段。",
			"缺少墒情热力图与地块对象的双向定位。",
		},
	}
}

func (s *BusinessService) buildWeather(latest map[string]map[string]metricValue, alerts map[string][]vo.MonitorAlertVo) vo.BusinessSubsystemVo {
	metrics := []vo.BusinessMetricVo{
		metricFrom(latest, "temperature", "空气温度", "°C", []string{"iot-weather-01"}),
		metricFrom(latest, "humidity", "空气湿度", "%", []string{"iot-weather-01"}),
		metricFrom(latest, "windSpeed", "风速", "m/s", []string{"iot-weather-01"}),
		metricFrom(latest, "rainfall", "降雨量", "mm/h", []string{"iot-weather-01"}),
		metricFrom(latest, "lightIntensity", "光照", "lux", []string{"iot-weather-01"}),
	}
	return vo.BusinessSubsystemVo{
		Key:                 "weather",
		Name:                "气候/气象监测",
		Objective:           "汇聚园区气象站数据，为种植、通风、灌溉和预警提供依据。",
		Status:              subsystemStatus(metrics, pickAlerts(alerts, "iot-weather-01")),
		ImplementationLevel: "partial",
		CompletionRate:      72,
		PrimaryDeviceIds:    []string{"iot-weather-01"},
		Metrics:             metrics,
		Workflows: []vo.BusinessWorkflowVo{
			{Name: "气象站接入", State: "ready", Description: "温湿度、风速、降雨、光照已接入模拟数据通道。"},
			{Name: "趋势分析", State: "partial", Description: "监控大屏已有趋势图，业务页需补多指标对比。"},
			{Name: "外部天气", State: "missing", Description: "尚未接入第三方天气预报 API。"},
		},
		Alerts: pickAlerts(alerts, "iot-weather-01"),
		Gaps: []string{
			"未实现天气预报卡片。",
			"未将天气状态驱动 3D 雨雪、雾效或风向箭头。",
		},
	}
}

func (s *BusinessService) buildIrrigation(latest map[string]map[string]metricValue, alerts map[string][]vo.MonitorAlertVo) vo.BusinessSubsystemVo {
	metrics := []vo.BusinessMetricVo{
		metricFrom(latest, "waterFlow", "瞬时流量", "L/min", []string{"iot-irrigation-01"}),
		metricFrom(latest, "waterPressure", "管网压力", "kPa", []string{"iot-irrigation-01"}),
		metricFrom(latest, "soilMoisture", "关联墒情", "%", []string{"iot-irrigation-01", "iot-field-01"}),
	}
	return vo.BusinessSubsystemVo{
		Key:                 "irrigation",
		Name:                "水肥灌溉系统",
		Objective:           "可视化灌溉管网、阀门、水泵和施肥设备状态，形成计划闭环。",
		Status:              subsystemStatus(metrics, pickAlerts(alerts, "iot-irrigation-01")),
		ImplementationLevel: "partial",
		CompletionRate:      58,
		PrimaryDeviceIds:    []string{"iot-irrigation-01"},
		Metrics:             metrics,
		Workflows: []vo.BusinessWorkflowVo{
			{Name: "设备监测", State: "ready", Description: "灌溉控制器流量、压力和墒情已接入。"},
			{Name: "计划执行", State: "partial", Description: "有控制入口雏形，缺少计划表和执行状态机。"},
			{Name: "远程控制", State: "missing", Description: "未持久化控制指令和操作日志。"},
		},
		Alerts: pickAlerts(alerts, "iot-irrigation-01"),
		Gaps: []string{
			"缺少灌溉计划、分区和阀门对象建模。",
			"缺少水流方向动画和控制审计日志。",
		},
	}
}

func (s *BusinessService) buildGreenhouse(latest map[string]map[string]metricValue, alerts map[string][]vo.MonitorAlertVo) vo.BusinessSubsystemVo {
	metrics := []vo.BusinessMetricVo{
		metricFrom(latest, "temperature", "棚内温度", "°C", []string{"iot-greenhouse-01"}),
		metricFrom(latest, "humidity", "棚内湿度", "%", []string{"iot-greenhouse-01"}),
		metricFrom(latest, "co2", "CO2", "ppm", []string{"iot-greenhouse-01"}),
		metricFrom(latest, "lightIntensity", "补光/光照", "lux", []string{"iot-greenhouse-01"}),
	}
	return vo.BusinessSubsystemVo{
		Key:                 "greenhouse",
		Name:                "大棚智能控制",
		Objective:           "集中监控温室环境和执行设备，实现温湿度、光照、CO2 精细调节。",
		Status:              subsystemStatus(metrics, pickAlerts(alerts, "iot-greenhouse-01")),
		ImplementationLevel: "partial",
		CompletionRate:      55,
		PrimaryDeviceIds:    []string{"iot-greenhouse-01"},
		Metrics:             metrics,
		Workflows: []vo.BusinessWorkflowVo{
			{Name: "环境监测", State: "ready", Description: "棚内温湿度、CO2、光照已有实时数据。"},
			{Name: "设备联动", State: "partial", Description: "有设备状态展示，缺少卷帘/风机/湿帘状态模型。"},
			{Name: "自动控制", State: "missing", Description: "未实现控制策略、模式切换和 PID/规则过程。"},
		},
		Alerts: pickAlerts(alerts, "iot-greenhouse-01"),
		Gaps: []string{
			"缺少温室内部视角和执行设备绑定。",
			"缺少自动/手动控制策略配置。",
		},
	}
}

func (s *BusinessService) buildVideo(latest map[string]map[string]metricValue, alerts map[string][]vo.MonitorAlertVo) vo.BusinessSubsystemVo {
	metrics := []vo.BusinessMetricVo{
		metricFrom(latest, "status", "北区摄像头", "", []string{"iot-camera-01"}),
		metricFrom(latest, "status", "南区摄像头", "", []string{"iot-camera-02"}),
	}
	return vo.BusinessSubsystemVo{
		Key:                 "video",
		Name:                "视频监控系统",
		Objective:           "统一管理摄像头点位、实时画面、录像回放和 AI 识别告警。",
		Status:              subsystemStatus(metrics, pickAlerts(alerts, "iot-camera-01", "iot-camera-02")),
		ImplementationLevel: "partial",
		CompletionRate:      42,
		PrimaryDeviceIds:    []string{"iot-camera-01", "iot-camera-02"},
		Metrics:             metrics,
		Workflows: []vo.BusinessWorkflowVo{
			{Name: "点位管理", State: "partial", Description: "摄像头设备已入库，仍需绑定朝向、覆盖范围和流地址。"},
			{Name: "实时视频", State: "partial", Description: "前端有视频面板，当前以演示流/浏览器摄像头兜底。"},
			{Name: "录像回放", State: "missing", Description: "未接入录像索引和时间轴回放。"},
		},
		Alerts: pickAlerts(alerts, "iot-camera-01", "iot-camera-02"),
		Gaps: []string{
			"缺少 HLS/WebRTC/RTSP 转码服务。",
			"缺少 AI 识别事件、截图和处置流程。",
		},
	}
}

func (s *BusinessService) buildEnvironment(latest map[string]map[string]metricValue, alerts map[string][]vo.MonitorAlertVo) vo.BusinessSubsystemVo {
	metrics := []vo.BusinessMetricVo{
		metricFrom(latest, "humidity", "空气湿度", "%", []string{"iot-weather-01", "iot-greenhouse-01"}),
		metricFrom(latest, "co2", "CO2", "ppm", []string{"iot-greenhouse-01"}),
		metricFrom(latest, "ph", "土壤 pH", "pH", []string{"iot-field-01", "iot-greenhouse-01"}),
		metricFrom(latest, "soilMoisture", "生态墒情", "%", []string{"iot-field-01", "iot-greenhouse-01"}),
	}
	return vo.BusinessSubsystemVo{
		Key:                 "environment",
		Name:                "环境监测",
		Objective:           "监测园区空气、水质、噪声等综合环境指标，支撑安全运营和生态展示。",
		Status:              subsystemStatus(metrics, pickAlerts(alerts, "iot-weather-01", "iot-greenhouse-01", "iot-field-01")),
		ImplementationLevel: "partial",
		CompletionRate:      48,
		PrimaryDeviceIds:    []string{"iot-weather-01", "iot-greenhouse-01", "iot-field-01"},
		Metrics:             metrics,
		Workflows: []vo.BusinessWorkflowVo{
			{Name: "综合评分", State: "partial", Description: "监控大屏已有环境评分，业务页新增可追踪指标明细。"},
			{Name: "空气质量", State: "partial", Description: "已有 CO2/温湿度，缺少 PM2.5、PM10、TVOC。"},
			{Name: "水质噪声", State: "missing", Description: "未接入 pH 以外的水质指标和噪声监测点。"},
		},
		Alerts: pickAlerts(alerts, "iot-weather-01", "iot-greenhouse-01", "iot-field-01"),
		Gaps: []string{
			"缺少 PM2.5、PM10、溶解氧、浊度、噪声等指标。",
			"缺少环境异常点位与 3D 场景高亮联动。",
		},
	}
}

func buildLatestMetricMap(rows []mapper.MonitorLatestMetricRow) map[string]map[string]metricValue {
	latest := make(map[string]map[string]metricValue)
	for _, row := range rows {
		if latest[row.DeviceId] == nil {
			latest[row.DeviceId] = map[string]metricValue{}
		}
		latest[row.DeviceId][row.MetricKey] = metricValue{
			value: row.MetricValue,
			unit:  row.Unit,
			ok:    true,
		}
	}
	return latest
}

func buildBusinessAlerts(rows []mapper.MonitorAlertRow) map[string][]vo.MonitorAlertVo {
	alerts := make(map[string][]vo.MonitorAlertVo)
	for _, row := range rows {
		alert := vo.MonitorAlertVo{
			Id:           row.Id,
			DeviceId:     row.DeviceId,
			AlertType:    row.AlertType,
			Severity:     row.Severity,
			Message:      row.Message,
			Acknowledged: row.Acknowledged,
			CreatedAt:    row.CreatedAt.Format(time.RFC3339),
		}
		alerts[row.DeviceId] = append(alerts[row.DeviceId], alert)
	}
	return alerts
}

func metricFrom(latest map[string]map[string]metricValue, key, label, fallbackUnit string, deviceIds []string) vo.BusinessMetricVo {
	total := 0.0
	count := 0
	unit := fallbackUnit
	for _, deviceId := range deviceIds {
		if metrics, ok := latest[deviceId]; ok {
			if item, ok := metrics[key]; ok && item.ok {
				total += item.value
				count++
				if item.unit != "" {
					unit = item.unit
				}
			}
		}
	}

	if count == 0 {
		return vo.BusinessMetricVo{
			Key:    key,
			Label:  label,
			Value:  0,
			Unit:   unit,
			Status: "missing",
		}
	}

	value := math.Round(total/float64(count)*100) / 100
	if key == "status" {
		if value >= 0.5 {
			return vo.BusinessMetricVo{Key: key, Label: label, Value: 1, Unit: unit, Status: "normal"}
		}
		return vo.BusinessMetricVo{Key: key, Label: label, Value: 0, Unit: unit, Status: "critical"}
	}

	return vo.BusinessMetricVo{
		Key:    key,
		Label:  label,
		Value:  value,
		Unit:   unit,
		Status: metricStatus(key, value),
	}
}

func subsystemStatus(metrics []vo.BusinessMetricVo, alerts []vo.MonitorAlertVo) string {
	for _, alert := range alerts {
		if !alert.Acknowledged && alert.Severity == "critical" {
			return "critical"
		}
	}
	for _, metric := range metrics {
		if metric.Status == "critical" {
			return "critical"
		}
	}
	for _, alert := range alerts {
		if !alert.Acknowledged && alert.Severity == "warning" {
			return "warning"
		}
	}
	for _, metric := range metrics {
		if metric.Status == "warning" || metric.Status == "missing" {
			return "warning"
		}
	}
	return "normal"
}

func pickAlerts(alerts map[string][]vo.MonitorAlertVo, deviceIds ...string) []vo.MonitorAlertVo {
	result := make([]vo.MonitorAlertVo, 0)
	for _, deviceId := range deviceIds {
		result = append(result, alerts[deviceId]...)
	}
	sort.Slice(result, func(i, j int) bool {
		return result[i].CreatedAt > result[j].CreatedAt
	})
	if len(result) > 5 {
		return result[:5]
	}
	return result
}

func buildBusinessSummary(subsystems []vo.BusinessSubsystemVo, alerts map[string][]vo.MonitorAlertVo, unackedCount int) vo.BusinessSummaryVo {
	summary := vo.BusinessSummaryVo{
		SystemTotal:    len(subsystems),
		UnackedAlerts:  unackedCount,
		OverallScore:   0,
		CompletionRate: 0,
	}
	for _, subsystem := range subsystems {
		switch subsystem.ImplementationLevel {
		case "ready":
			summary.DemoReadyCount++
		case "partial":
			summary.PartialCount++
		default:
			summary.MissingCount++
		}
		summary.CompletionRate += subsystem.CompletionRate
	}
	for _, deviceAlerts := range alerts {
		for _, alert := range deviceAlerts {
			if alert.Acknowledged {
				continue
			}
			if alert.Severity == "critical" {
				summary.CriticalAlerts++
			} else if alert.Severity == "warning" {
				summary.WarningAlerts++
			}
		}
	}
	if summary.SystemTotal > 0 {
		summary.CompletionRate = math.Round(summary.CompletionRate/float64(summary.SystemTotal)*100) / 100
	}
	summary.OverallScore = math.Round((summary.CompletionRate-float64(summary.CriticalAlerts)*8-float64(summary.WarningAlerts)*2)*100) / 100
	if summary.OverallScore < 0 {
		summary.OverallScore = 0
	}
	return summary
}
