package service

import (
	"math"
	"sort"
	"time"

	"scene-server-go/iot"
	"scene-server-go/mapper"
	"scene-server-go/vo"
)

type MonitorService struct {
	dao *mapper.MonitorMapper
}

type metricSnapshot struct {
	value     float64
	unit      string
	timestamp *time.Time
}

var metricMeta = map[string]struct {
	label string
	unit  string
	min   float64
	max   float64
}{
	"temperature":    {"平均温度", "°C", -10, 45},
	"humidity":       {"空气湿度", "%", 20, 100},
	"soilMoisture":   {"土壤墒情", "%", 0, 100},
	"co2":            {"CO2 浓度", "ppm", 300, 2000},
	"lightIntensity": {"光照强度", "lux", 0, 100000},
	"ph":             {"土壤 pH", "pH", 4, 9},
	"windSpeed":      {"风速", "m/s", 0, 30},
	"rainfall":       {"降雨量", "mm/h", 0, 50},
	"waterFlow":      {"灌溉流量", "L/min", 0, 80},
	"waterPressure":  {"管网压力", "kPa", 0, 400},
	"powerOutput":    {"绿色发电", "KW", 0, 800},
}

func NewMonitorService() *MonitorService {
	return &MonitorService{
		dao: mapper.NewMonitorMapper(),
	}
}

func (s *MonitorService) GetDashboard() vo.ResultVo {
	now := time.Now()
	devices, err := s.loadDevices()
	if err != nil {
		return vo.ResultVo{Code: 999, Data: err.Error()}
	}

	latestMetrics, _ := s.loadLatestMetrics()
	recentAverages, _ := s.loadRecentAverages()
	alerts, _ := s.loadRecentAlerts(12)
	unackedCount, _ := s.dao.CountUnackedAlerts()

	for i := range devices {
		if metrics, ok := latestMetrics[devices[i].DeviceId]; ok {
			for key, snap := range metrics {
				devices[i].Metrics[key] = round2(snap.value)
			}
		}
	}

	dashboard := vo.MonitorDashboardVo{
		UpdatedAt:       now,
		Overview:        s.buildOverview(devices, alerts, unackedCount, recentAverages),
		KeyMetrics:      s.buildKeyMetrics(recentAverages, latestMetrics),
		DeviceStatus:    devices,
		Energy:          s.buildEnergy(latestMetrics),
		YieldAnalysis:   s.buildYield(recentAverages),
		Environment:     s.buildEnvironment(recentAverages),
		RecentAlerts:    alerts,
		RealtimeMetrics: s.buildRealtimeMetrics(latestMetrics),
	}
	dashboard.Overview.EnvironmentScore = dashboard.Environment.Score

	return vo.ResultVo{Code: 200, Data: dashboard}
}

func (s *MonitorService) loadDevices() ([]vo.MonitorDeviceVo, error) {
	rows, err := s.dao.FindDevices()
	if err != nil || len(rows) == 0 {
		return s.defaultDevices(time.Now()), nil
	}

	devices := make([]vo.MonitorDeviceVo, 0, len(rows))
	for _, row := range rows {
		status := row.Status
		if status == "" {
			status = "offline"
		}
		lastDataTime := ""
		if row.LastDataTime != nil {
			lastDataTime = row.LastDataTime.Format(time.RFC3339)
		}
		devices = append(devices, vo.MonitorDeviceVo{
			DeviceId:     row.DeviceId,
			DeviceName:   firstNonEmpty(row.DeviceName, row.DeviceId),
			DeviceType:   firstNonEmpty(row.DeviceType, "sensor"),
			Status:       status,
			LastDataTime: lastDataTime,
			Metrics:      map[string]float64{},
		})
	}
	return devices, nil
}

func (s *MonitorService) loadLatestMetrics() (map[string]map[string]metricSnapshot, error) {
	rows, err := s.dao.FindLatestMetrics()
	result := make(map[string]map[string]metricSnapshot)
	if err != nil || len(rows) == 0 {
		return s.defaultLatestMetrics(), err
	}
	for _, row := range rows {
		if result[row.DeviceId] == nil {
			result[row.DeviceId] = map[string]metricSnapshot{}
		}
		result[row.DeviceId][row.MetricKey] = metricSnapshot{
			value:     row.MetricValue,
			unit:      row.Unit,
			timestamp: row.Timestamp,
		}
	}
	return result, nil
}

func (s *MonitorService) loadRecentAverages() (map[string]metricSnapshot, error) {
	rows, err := s.dao.FindRecentMetricAverages(24)
	result := make(map[string]metricSnapshot)
	if err == nil {
		for _, row := range rows {
			result[row.MetricKey] = metricSnapshot{value: row.Value, unit: row.Unit}
		}
	}
	if len(result) == 0 {
		for _, deviceMetrics := range s.defaultLatestMetrics() {
			for key, snap := range deviceMetrics {
				acc := result[key]
				if acc.unit == "" {
					acc.unit = snap.unit
				}
				acc.value += snap.value
				acc.timestamp = snap.timestamp
				result[key] = acc
			}
		}
		counts := map[string]int{}
		for _, deviceMetrics := range s.defaultLatestMetrics() {
			for key := range deviceMetrics {
				counts[key]++
			}
		}
		for key, count := range counts {
			if count > 0 {
				snap := result[key]
				snap.value = snap.value / float64(count)
				result[key] = snap
			}
		}
	}
	return result, err
}

func (s *MonitorService) loadRecentAlerts(limit int) ([]vo.MonitorAlertVo, error) {
	rows, err := s.dao.FindRecentAlerts(limit)
	if err != nil || len(rows) == 0 {
		return s.defaultAlerts(), err
	}
	alerts := make([]vo.MonitorAlertVo, 0, len(rows))
	for _, row := range rows {
		alerts = append(alerts, vo.MonitorAlertVo{
			Id:           row.Id,
			DeviceId:     row.DeviceId,
			AlertType:    row.AlertType,
			Severity:     row.Severity,
			Message:      row.Message,
			Acknowledged: row.Acknowledged,
			CreatedAt:    row.CreatedAt.Format(time.RFC3339),
		})
	}
	return alerts, nil
}

func (s *MonitorService) buildOverview(devices []vo.MonitorDeviceVo, alerts []vo.MonitorAlertVo, unackedCount int, averages map[string]metricSnapshot) vo.MonitorOverviewVo {
	overview := vo.MonitorOverviewVo{
		ParkName:      "智慧农业示范园区",
		DeviceTotal:   len(devices),
		UnackedAlerts: unackedCount,
	}
	for _, device := range devices {
		switch device.Status {
		case "online":
			overview.OnlineCount++
		case "warning":
			overview.WarningCount++
		case "critical":
			overview.CriticalCount++
		default:
			overview.OfflineCount++
		}
	}
	if overview.DeviceTotal > 0 {
		overview.OnlineRate = round2(float64(overview.OnlineCount+overview.WarningCount+overview.CriticalCount) / float64(overview.DeviceTotal) * 100)
	}
	for _, alert := range alerts {
		if !alert.Acknowledged && unackedCount == 0 {
			overview.UnackedAlerts++
		}
	}
	if overview.WarningCount == 0 {
		overview.WarningCount = countAlertsBySeverity(alerts, "warning")
	}
	if overview.CriticalCount == 0 {
		overview.CriticalCount = countAlertsBySeverity(alerts, "critical")
	}
	_ = averages
	return overview
}

func (s *MonitorService) buildKeyMetrics(averages map[string]metricSnapshot, latest map[string]map[string]metricSnapshot) []vo.MonitorMetricCardVo {
	keys := []string{"soilMoisture", "temperature", "humidity", "co2", "waterFlow", "powerOutput"}
	cards := make([]vo.MonitorMetricCardVo, 0, len(keys))
	for i, key := range keys {
		snap, ok := averages[key]
		if !ok || snap.value == 0 {
			snap = averageLatestMetric(latest, key)
		}
		if snap.value == 0 {
			snap = averageLatestMetric(s.defaultLatestMetrics(), key)
		}
		meta := metricMeta[key]
		unit := firstNonEmpty(snap.unit, meta.unit)
		cards = append(cards, vo.MonitorMetricCardVo{
			Key:       key,
			Label:     firstNonEmpty(meta.label, key),
			Value:     round2(snap.value),
			Unit:      unit,
			Delta:     round2(math.Sin(float64(i)+float64(time.Now().Hour())) * 4.8),
			Status:    metricStatus(key, snap.value),
			UpdatedAt: time.Now().Format(time.RFC3339),
		})
	}
	return cards
}

func (s *MonitorService) buildEnergy(latest map[string]map[string]metricSnapshot) vo.MonitorEnergyVo {
	power := sumLatestMetric(latest, "powerOutput")
	waterFlow := sumLatestMetric(latest, "waterFlow")
	if power == 0 {
		power = 428
	}
	if waterFlow == 0 {
		waterFlow = 36
	}

	bars := []vo.MonitorEnergyBarVo{
		{Name: "北区温室", Water: round2(waterFlow * 0.32), Electricity: round2(power * 0.28), Gas: 18},
		{Name: "东区水肥", Water: round2(waterFlow * 0.46), Electricity: round2(power * 0.18), Gas: 8},
		{Name: "南区大田", Water: round2(waterFlow * 0.22), Electricity: round2(power * 0.22), Gas: 6},
		{Name: "综合能源", Water: 12, Electricity: round2(power * 0.32), Gas: 22},
	}

	waterTotal := 0.0
	electricityTotal := 0.0
	gasTotal := 0.0
	for _, bar := range bars {
		waterTotal += bar.Water
		electricityTotal += bar.Electricity
		gasTotal += bar.Gas
	}

	return vo.MonitorEnergyVo{
		TodayTotal:       round2(waterTotal + electricityTotal + gasTotal),
		WaterTotal:       round2(waterTotal),
		ElectricityTotal: round2(electricityTotal),
		GasTotal:         round2(gasTotal),
		Bars:             bars,
		Trend:            s.buildEnergyTrend(electricityTotal),
	}
}

func (s *MonitorService) buildEnergyTrend(base float64) []vo.MonitorTrendPointVo {
	if base <= 0 {
		base = 220
	}
	points := make([]vo.MonitorTrendPointVo, 0, 12)
	now := time.Now()
	for i := 11; i >= 0; i-- {
		t := now.Add(-time.Duration(i) * time.Hour)
		factor := 0.78 + 0.24*math.Sin(float64(t.Hour())/24*math.Pi*2)
		points = append(points, vo.MonitorTrendPointVo{
			Time:  t.Format("15:04"),
			Value: round2(base * factor),
		})
	}
	return points
}

func (s *MonitorService) buildYield(averages map[string]metricSnapshot) vo.MonitorYieldVo {
	soil := averages["soilMoisture"].value
	temp := averages["temperature"].value
	if soil == 0 {
		soil = 52
	}
	if temp == 0 {
		temp = 25
	}
	baseRate := clamp(0.72+(soil-45)/180-(math.Abs(temp-24)/160), 0.58, 0.96)
	areas := []vo.MonitorYieldAreaVo{
		{Name: "A 区番茄", Target: 13.8, Rate: round2(baseRate + 0.04)},
		{Name: "B 区水稻", Target: 16.5, Rate: round2(baseRate - 0.01)},
		{Name: "C 区玉米", Target: 12.2, Rate: round2(baseRate + 0.02)},
		{Name: "D 区叶菜", Target: 9.6, Rate: round2(baseRate - 0.04)},
	}
	total := 0.0
	for i := range areas {
		areas[i].Rate = clamp(areas[i].Rate, 0.55, 1.08)
		areas[i].Yield = round2(areas[i].Target * areas[i].Rate)
		total += areas[i].Yield
	}

	heatmap := make([]vo.MonitorYieldHeatVo, 0, 36)
	for y := 0; y < 6; y++ {
		for x := 0; x < 6; x++ {
			value := clamp(55+baseRate*35+math.Sin(float64(x+y))*8+float64((x*y)%5), 40, 100)
			heatmap = append(heatmap, vo.MonitorYieldHeatVo{
				X:     x,
				Y:     y,
				Value: round2(value),
				Area:  []string{"A 区", "B 区", "C 区", "D 区"}[(x+y)%4],
			})
		}
	}

	return vo.MonitorYieldVo{
		Total:   round2(total),
		Unit:    "吨",
		Areas:   areas,
		Heatmap: heatmap,
	}
}

func (s *MonitorService) buildEnvironment(averages map[string]metricSnapshot) vo.MonitorEnvironmentVo {
	keys := []string{"temperature", "humidity", "soilMoisture", "co2", "ph", "lightIntensity"}
	items := make([]vo.MonitorMetricCardVo, 0, len(keys))
	scoreSum := 0.0
	for _, key := range keys {
		meta := metricMeta[key]
		snap := averages[key]
		value := snap.value
		if value == 0 {
			value = averageLatestMetric(s.defaultLatestMetrics(), key).value
		}
		itemScore := metricHealthScore(key, value)
		scoreSum += itemScore
		items = append(items, vo.MonitorMetricCardVo{
			Key:    key,
			Label:  firstNonEmpty(meta.label, key),
			Value:  round2(value),
			Unit:   firstNonEmpty(snap.unit, meta.unit),
			Delta:  round2((itemScore - 82) / 8),
			Status: metricStatus(key, value),
		})
	}
	score := round2(scoreSum / float64(len(keys)))
	level := "优"
	if score < 70 {
		level = "需关注"
	} else if score < 85 {
		level = "良"
	}
	return vo.MonitorEnvironmentVo{
		Score:   score,
		Level:   level,
		Summary: "今日温湿度、墒情和光照处于适宜区间，灌溉系统负荷平稳。",
		Items:   items,
		Hourly:  s.buildEnvironmentHourly(score),
		Recommendations: []string{
			"午后光照增强时段保持温室侧窗联动通风。",
			"B 区土壤墒情接近下限，建议提前校验水肥计划。",
			"夜间降低巡检频率，保留严重告警实时推送。",
		},
	}
}

func (s *MonitorService) buildEnvironmentHourly(score float64) []vo.MonitorTrendPointVo {
	rows, err := s.dao.FindHourlyMetricAverage("soilMoisture", 12)
	if err == nil && len(rows) > 0 {
		points := make([]vo.MonitorTrendPointVo, 0, len(rows))
		for _, row := range rows {
			points = append(points, vo.MonitorTrendPointVo{Time: row.HourLabel, Value: round2(row.Value)})
		}
		return points
	}
	points := make([]vo.MonitorTrendPointVo, 0, 12)
	now := time.Now()
	for i := 11; i >= 0; i-- {
		t := now.Add(-time.Duration(i) * time.Hour)
		points = append(points, vo.MonitorTrendPointVo{
			Time:  t.Format("15:04"),
			Value: round2(score + math.Sin(float64(i))*4),
		})
	}
	return points
}

func (s *MonitorService) buildRealtimeMetrics(latest map[string]map[string]metricSnapshot) []vo.MonitorRealtimeVo {
	rows := make([]vo.MonitorRealtimeVo, 0, len(latest))
	for deviceId, metrics := range latest {
		values := make(map[string]float64)
		latestTime := time.Time{}
		for key, snap := range metrics {
			values[key] = round2(snap.value)
			if snap.timestamp != nil && snap.timestamp.After(latestTime) {
				latestTime = *snap.timestamp
			}
		}
		if latestTime.IsZero() {
			latestTime = time.Now()
		}
		rows = append(rows, vo.MonitorRealtimeVo{
			DeviceId:  deviceId,
			Timestamp: latestTime.Format(time.RFC3339),
			Metrics:   values,
		})
	}
	sort.Slice(rows, func(i, j int) bool { return rows[i].DeviceId < rows[j].DeviceId })
	return rows
}

func (s *MonitorService) defaultDevices(now time.Time) []vo.MonitorDeviceVo {
	defaults := iot.DefaultDevices()
	devices := make([]vo.MonitorDeviceVo, 0, len(defaults))
	for _, dev := range defaults {
		devices = append(devices, vo.MonitorDeviceVo{
			DeviceId:     dev.DeviceId,
			DeviceName:   defaultDeviceName(dev.DeviceId),
			DeviceType:   dev.DeviceType,
			Status:       "online",
			LastDataTime: now.Format(time.RFC3339),
			Metrics:      map[string]float64{},
		})
	}
	return devices
}

func (s *MonitorService) defaultLatestMetrics() map[string]map[string]metricSnapshot {
	now := time.Now()
	result := map[string]map[string]metricSnapshot{}
	for _, dev := range iot.DefaultDevices() {
		result[dev.DeviceId] = map[string]metricSnapshot{}
		for _, metric := range dev.Metrics {
			value := metric.Base + math.Sin(float64(len(dev.DeviceId)+len(metric.Key)+now.Minute()))*metric.Amp*0.35
			result[dev.DeviceId][metric.Key] = metricSnapshot{
				value:     clamp(value, metric.Min, metric.Max),
				unit:      metric.Unit,
				timestamp: &now,
			}
		}
	}
	return result
}

func (s *MonitorService) defaultAlerts() []vo.MonitorAlertVo {
	now := time.Now()
	return []vo.MonitorAlertVo{
		{Id: 1, DeviceId: "iot-irrigation-01", AlertType: "threshold", Severity: "warning", Message: "东区水肥管网压力波动，建议巡检过滤器。", Acknowledged: false, CreatedAt: now.Add(-18 * time.Minute).Format(time.RFC3339)},
		{Id: 2, DeviceId: "iot-greenhouse-01", AlertType: "anomaly", Severity: "info", Message: "1号温室 CO2 浓度回落至适宜区间。", Acknowledged: true, CreatedAt: now.Add(-42 * time.Minute).Format(time.RFC3339)},
	}
}

func defaultDeviceName(deviceId string) string {
	names := map[string]string{
		"iot-greenhouse-01": "1号温室传感器组",
		"iot-field-01":      "智慧示范田传感器",
		"iot-weather-01":    "园区气象站",
		"iot-irrigation-01": "智能灌溉控制器",
		"iot-solar-01":      "光伏阵列监测",
		"iot-wind-01":       "风力发电机组",
		"iot-camera-01":     "北区视频监控",
		"iot-camera-02":     "南区视频监控",
	}
	return firstNonEmpty(names[deviceId], deviceId)
}

func metricStatus(key string, value float64) string {
	switch key {
	case "temperature":
		if value < 12 || value > 36 {
			return "critical"
		}
		if value < 18 || value > 32 {
			return "warning"
		}
	case "humidity", "soilMoisture":
		if value < 25 || value > 88 {
			return "critical"
		}
		if value < 38 || value > 78 {
			return "warning"
		}
	case "co2":
		if value > 1500 {
			return "critical"
		}
		if value > 1100 || value < 400 {
			return "warning"
		}
	case "ph":
		if value < 5.2 || value > 8.1 {
			return "critical"
		}
		if value < 5.8 || value > 7.5 {
			return "warning"
		}
	case "waterPressure":
		if value < 120 || value > 340 {
			return "critical"
		}
		if value < 180 || value > 300 {
			return "warning"
		}
	}
	return "normal"
}

func metricHealthScore(key string, value float64) float64 {
	targets := map[string]float64{
		"temperature":    24,
		"humidity":       62,
		"soilMoisture":   56,
		"co2":            820,
		"ph":             6.7,
		"lightIntensity": 45000,
	}
	ranges := map[string]float64{
		"temperature":    18,
		"humidity":       45,
		"soilMoisture":   55,
		"co2":            1200,
		"ph":             2.4,
		"lightIntensity": 70000,
	}
	target := targets[key]
	rng := ranges[key]
	if rng <= 0 {
		return 85
	}
	return clamp(100-math.Abs(value-target)/rng*100, 45, 99)
}

func averageLatestMetric(latest map[string]map[string]metricSnapshot, key string) metricSnapshot {
	total := 0.0
	count := 0
	unit := ""
	var ts *time.Time
	for _, metrics := range latest {
		if snap, ok := metrics[key]; ok {
			total += snap.value
			count++
			if unit == "" {
				unit = snap.unit
			}
			if snap.timestamp != nil {
				ts = snap.timestamp
			}
		}
	}
	if count == 0 {
		return metricSnapshot{unit: metricMeta[key].unit}
	}
	return metricSnapshot{value: total / float64(count), unit: unit, timestamp: ts}
}

func sumLatestMetric(latest map[string]map[string]metricSnapshot, key string) float64 {
	total := 0.0
	for _, metrics := range latest {
		if snap, ok := metrics[key]; ok {
			total += snap.value
		}
	}
	return total
}

func countAlertsBySeverity(alerts []vo.MonitorAlertVo, severity string) int {
	count := 0
	for _, alert := range alerts {
		if !alert.Acknowledged && alert.Severity == severity {
			count++
		}
	}
	return count
}

func firstNonEmpty(values ...string) string {
	for _, value := range values {
		if value != "" {
			return value
		}
	}
	return ""
}

func round2(value float64) float64 {
	return math.Round(value*100) / 100
}

func clamp(value, min, max float64) float64 {
	if value < min {
		return min
	}
	if value > max {
		return max
	}
	return value
}
