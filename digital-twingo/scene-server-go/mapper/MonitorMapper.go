package mapper

import "time"

type MonitorMapper struct{}

type MonitorDeviceRow struct {
	DeviceId     string     `db:"deviceId"`
	DeviceName   string     `db:"deviceName"`
	DeviceType   string     `db:"deviceType"`
	Status       string     `db:"status"`
	LastDataTime *time.Time `db:"lastDataTime"`
}

type MonitorLatestMetricRow struct {
	DeviceId    string     `db:"deviceId"`
	MetricKey   string     `db:"metricKey"`
	MetricValue float64    `db:"metricValue"`
	Unit        string     `db:"unit"`
	Timestamp   *time.Time `db:"timestamp"`
}

type MonitorAverageMetricRow struct {
	MetricKey string  `db:"metricKey"`
	Value     float64 `db:"value"`
	Unit      string  `db:"unit"`
}

type MonitorAlertRow struct {
	Id           int64     `db:"id"`
	DeviceId     string    `db:"deviceId"`
	AlertType    string    `db:"alertType"`
	Severity     string    `db:"severity"`
	Message      string    `db:"message"`
	Acknowledged bool      `db:"acknowledged"`
	CreatedAt    time.Time `db:"createdAt"`
}

type MonitorHourMetricRow struct {
	HourLabel string  `db:"hourLabel"`
	Value     float64 `db:"value"`
}

func NewMonitorMapper() *MonitorMapper {
	return &MonitorMapper{}
}

func (m *MonitorMapper) FindDevices() ([]MonitorDeviceRow, error) {
	var rows []MonitorDeviceRow
	err := db.Select(&rows, `SELECT deviceId, deviceName, deviceType, status, lastDataTime
		FROM iot_device ORDER BY deviceType, deviceName`)
	return rows, err
}

func (m *MonitorMapper) FindLatestMetrics() ([]MonitorLatestMetricRow, error) {
	var rows []MonitorLatestMetricRow
	err := db.Select(&rows, `SELECT d.deviceId, d.metricKey, d.metricValue, d.unit, d.timestamp
		FROM iot_data d
		INNER JOIN (
			SELECT deviceId, metricKey, MAX(timestamp) AS maxTime
			FROM iot_data
			GROUP BY deviceId, metricKey
		) latest ON d.deviceId = latest.deviceId
			AND d.metricKey = latest.metricKey
			AND d.timestamp = latest.maxTime
		ORDER BY d.deviceId, d.metricKey`)
	return rows, err
}

func (m *MonitorMapper) FindRecentMetricAverages(hours int) ([]MonitorAverageMetricRow, error) {
	var rows []MonitorAverageMetricRow
	err := db.Select(&rows, `SELECT metricKey, AVG(metricValue) AS value, MAX(unit) AS unit
		FROM iot_data
		WHERE timestamp >= DATE_SUB(NOW(), INTERVAL ? HOUR)
		GROUP BY metricKey`, hours)
	return rows, err
}

func (m *MonitorMapper) FindHourlyMetricAverage(metricKey string, hours int) ([]MonitorHourMetricRow, error) {
	var rows []MonitorHourMetricRow
	err := db.Select(&rows, `SELECT DATE_FORMAT(timestamp, '%H:00') AS hourLabel, AVG(metricValue) AS value
		FROM iot_data
		WHERE metricKey = ? AND timestamp >= DATE_SUB(NOW(), INTERVAL ? HOUR)
		GROUP BY DATE_FORMAT(timestamp, '%Y-%m-%d %H')
		ORDER BY MIN(timestamp)`, metricKey, hours)
	return rows, err
}

func (m *MonitorMapper) FindRecentAlerts(limit int) ([]MonitorAlertRow, error) {
	var rows []MonitorAlertRow
	err := db.Select(&rows, `SELECT id, deviceId, alertType, severity, message, acknowledged, createdAt
		FROM alert_log ORDER BY createdAt DESC LIMIT ?`, limit)
	return rows, err
}

func (m *MonitorMapper) CountUnackedAlerts() (int, error) {
	var count int
	err := db.Get(&count, `SELECT COUNT(*) FROM alert_log WHERE acknowledged = FALSE`)
	return count, err
}
