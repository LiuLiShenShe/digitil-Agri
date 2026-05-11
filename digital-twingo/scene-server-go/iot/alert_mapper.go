package iot

import "time"

type AlertMapper struct{}

func NewAlertMapper() *AlertMapper {
	return &AlertMapper{}
}

func (m *AlertMapper) Insert(alert *AlertLog) error {
	createdAt := alert.CreatedAt
	if createdAt.IsZero() {
		createdAt = time.Now()
	}
	result, err := db.Exec(`INSERT INTO alert_log (deviceId, alertType, severity, message, acknowledged, createdAt)
		VALUES (?, ?, ?, ?, ?, ?)`,
		alert.DeviceId, alert.AlertType, alert.Severity, alert.Message, alert.Acknowledged, createdAt)
	if err != nil {
		return err
	}
	if id, err := result.LastInsertId(); err == nil {
		alert.Id = id
	}
	alert.CreatedAt = createdAt
	return err
}

func (m *AlertMapper) FindRecent(limit int) ([]AlertLog, error) {
	var alerts []AlertLog
	err := db.Select(&alerts,
		"SELECT * FROM alert_log ORDER BY createdAt DESC LIMIT ?", limit)
	return alerts, err
}

func (m *AlertMapper) FindByDevice(deviceId string, limit int) ([]AlertLog, error) {
	var alerts []AlertLog
	err := db.Select(&alerts,
		"SELECT * FROM alert_log WHERE deviceId = ? ORDER BY createdAt DESC LIMIT ?", deviceId, limit)
	return alerts, err
}

func (m *AlertMapper) Acknowledge(id int64) error {
	_, err := db.Exec("UPDATE alert_log SET acknowledged=TRUE WHERE id=?", id)
	return err
}

func (m *AlertMapper) CountUnacked() (int, error) {
	var count int
	err := db.Get(&count, "SELECT COUNT(*) FROM alert_log WHERE acknowledged=FALSE")
	return count, err
}
