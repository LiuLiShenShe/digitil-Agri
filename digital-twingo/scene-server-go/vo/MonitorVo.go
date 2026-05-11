package vo

import "time"

type MonitorDashboardVo struct {
	UpdatedAt       time.Time             `json:"updatedAt"`
	Overview        MonitorOverviewVo     `json:"overview"`
	KeyMetrics      []MonitorMetricCardVo `json:"keyMetrics"`
	DeviceStatus    []MonitorDeviceVo     `json:"deviceStatus"`
	Energy          MonitorEnergyVo       `json:"energy"`
	YieldAnalysis   MonitorYieldVo        `json:"yieldAnalysis"`
	Environment     MonitorEnvironmentVo  `json:"environment"`
	RecentAlerts    []MonitorAlertVo      `json:"recentAlerts"`
	RealtimeMetrics []MonitorRealtimeVo   `json:"realtimeMetrics"`
}

type MonitorOverviewVo struct {
	ParkName         string  `json:"parkName"`
	DeviceTotal      int     `json:"deviceTotal"`
	OnlineCount      int     `json:"onlineCount"`
	OfflineCount     int     `json:"offlineCount"`
	WarningCount     int     `json:"warningCount"`
	CriticalCount    int     `json:"criticalCount"`
	OnlineRate       float64 `json:"onlineRate"`
	UnackedAlerts    int     `json:"unackedAlerts"`
	EnvironmentScore float64 `json:"environmentScore"`
}

type MonitorMetricCardVo struct {
	Key       string  `json:"key"`
	Label     string  `json:"label"`
	Value     float64 `json:"value"`
	Unit      string  `json:"unit"`
	Delta     float64 `json:"delta"`
	Status    string  `json:"status"`
	UpdatedAt string  `json:"updatedAt"`
}

type MonitorDeviceVo struct {
	DeviceId     string             `json:"deviceId"`
	DeviceName   string             `json:"deviceName"`
	DeviceType   string             `json:"deviceType"`
	Status       string             `json:"status"`
	LastDataTime string             `json:"lastDataTime"`
	Metrics      map[string]float64 `json:"metrics"`
}

type MonitorEnergyVo struct {
	TodayTotal       float64               `json:"todayTotal"`
	WaterTotal       float64               `json:"waterTotal"`
	ElectricityTotal float64               `json:"electricityTotal"`
	GasTotal         float64               `json:"gasTotal"`
	Bars             []MonitorEnergyBarVo  `json:"bars"`
	Trend            []MonitorTrendPointVo `json:"trend"`
}

type MonitorEnergyBarVo struct {
	Name        string  `json:"name"`
	Water       float64 `json:"water"`
	Electricity float64 `json:"electricity"`
	Gas         float64 `json:"gas"`
}

type MonitorTrendPointVo struct {
	Time  string  `json:"time"`
	Value float64 `json:"value"`
}

type MonitorYieldVo struct {
	Total   float64              `json:"total"`
	Unit    string               `json:"unit"`
	Areas   []MonitorYieldAreaVo `json:"areas"`
	Heatmap []MonitorYieldHeatVo `json:"heatmap"`
}

type MonitorYieldAreaVo struct {
	Name   string  `json:"name"`
	Yield  float64 `json:"yield"`
	Target float64 `json:"target"`
	Rate   float64 `json:"rate"`
}

type MonitorYieldHeatVo struct {
	X     int     `json:"x"`
	Y     int     `json:"y"`
	Value float64 `json:"value"`
	Area  string  `json:"area"`
}

type MonitorEnvironmentVo struct {
	Score           float64               `json:"score"`
	Level           string                `json:"level"`
	Summary         string                `json:"summary"`
	Items           []MonitorMetricCardVo `json:"items"`
	Hourly          []MonitorTrendPointVo `json:"hourly"`
	Recommendations []string              `json:"recommendations"`
}

type MonitorAlertVo struct {
	Id           int64  `json:"id"`
	DeviceId     string `json:"deviceId"`
	Severity     string `json:"severity"`
	AlertType    string `json:"alertType"`
	Message      string `json:"message"`
	Acknowledged bool   `json:"acknowledged"`
	CreatedAt    string `json:"createdAt"`
}

type MonitorRealtimeVo struct {
	DeviceId  string             `json:"deviceId"`
	Timestamp string             `json:"timestamp"`
	Metrics   map[string]float64 `json:"metrics"`
}
