package iot

func NewDataMapper() *DataMapper {
	return &DataMapper{}
}

type DataMapper struct{}

func (m *DataMapper) InsertDataPoint(dp *IotDataPoint) error {
	_, err := db.Exec(`INSERT INTO iot_data (deviceId, metricKey, metricValue, unit, timestamp)
		VALUES (?, ?, ?, ?, NOW())`,
		dp.DeviceId, dp.MetricKey, dp.MetricValue, dp.Unit)
	return err
}

func (m *DataMapper) FindByDevice(deviceId string, limit int) ([]IotDataPoint, error) {
	var points []IotDataPoint
	err := db.Select(&points,
		"SELECT * FROM iot_data WHERE deviceId = ? ORDER BY timestamp DESC LIMIT ?", deviceId, limit)
	return points, err
}

func (m *DataMapper) FindByDeviceAndMetric(deviceId, metricKey string, limit int) ([]IotDataPoint, error) {
	var points []IotDataPoint
	err := db.Select(&points,
		"SELECT * FROM iot_data WHERE deviceId = ? AND metricKey = ? ORDER BY timestamp DESC LIMIT ?",
		deviceId, metricKey, limit)
	return points, err
}
