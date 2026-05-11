package iot

import "time"

type IotDevice struct {
	DeviceId     string    `json:"deviceId" db:"deviceId"`
	DeviceName   string    `json:"deviceName" db:"deviceName"`
	DeviceType   string    `json:"deviceType" db:"deviceType"`
	ModelId      *int      `json:"modelId" db:"modelId"`
	Position     string    `json:"position" db:"position"`
	MqttTopic    string    `json:"mqttTopic" db:"mqttTopic"`
	Status       string    `json:"status" db:"status"`
	LastDataTime *time.Time `json:"lastDataTime" db:"lastDataTime"`
	Config       string    `json:"config" db:"config"`
	CreatedAt    time.Time `json:"createdAt" db:"createdAt"`
}

type IotDataPoint struct {
	Id         int64     `json:"id" db:"id"`
	DeviceId   string    `json:"deviceId" db:"deviceId"`
	MetricKey  string    `json:"metricKey" db:"metricKey"`
	MetricValue float64   `json:"metricValue" db:"metricValue"`
	Unit       string    `json:"unit" db:"unit"`
	Timestamp  time.Time `json:"timestamp" db:"timestamp"`
}

type AlertLog struct {
	Id            int64     `json:"id" db:"id"`
	DeviceId      string    `json:"deviceId" db:"deviceId"`
	AlertType     string    `json:"alertType" db:"alertType"`
	Severity      string    `json:"severity" db:"severity"`
	Message       string    `json:"message" db:"message"`
	Acknowledged  bool      `json:"acknowledged" db:"acknowledged"`
	CreatedAt     time.Time `json:"createdAt" db:"createdAt"`
}

type DeviceConfig struct {
	Thresholds map[string]ThresholdConfig `json:"thresholds"`
	UpdateInterval int                    `json:"updateInterval"`
}

type ThresholdConfig struct {
	Min      float64 `json:"min"`
	Max      float64 `json:"max"`
	Severity string  `json:"severity"`
}

type SensorData struct {
	DeviceId  string             `json:"deviceId"`
	Timestamp int64              `json:"timestamp"`
	Metrics   map[string]float64 `json:"metrics"`
}
