package iot

import (
	"database/sql"
	"time"

	"github.com/jmoiron/sqlx"
)

var db *sqlx.DB

func SetDB(database *sqlx.DB) {
	db = database
}

type DeviceMapper struct{}

func NewDeviceMapper() *DeviceMapper {
	return &DeviceMapper{}
}

func (m *DeviceMapper) FindAll() ([]IotDevice, error) {
	var devices []IotDevice
	err := db.Select(&devices, `SELECT deviceId, deviceName, deviceType, modelId,
		COALESCE(CAST(position AS CHAR), '') AS position,
		mqttTopic, status, lastDataTime,
		COALESCE(CAST(config AS CHAR), '') AS config,
		createdAt
		FROM iot_device ORDER BY createdAt DESC`)
	return devices, err
}

func (m *DeviceMapper) FindById(deviceId string) (*IotDevice, error) {
	var device IotDevice
	err := db.Get(&device, `SELECT deviceId, deviceName, deviceType, modelId,
		COALESCE(CAST(position AS CHAR), '') AS position,
		mqttTopic, status, lastDataTime,
		COALESCE(CAST(config AS CHAR), '') AS config,
		createdAt
		FROM iot_device WHERE deviceId = ?`, deviceId)
	if err != nil {
		return nil, err
	}
	return &device, nil
}

func (m *DeviceMapper) Insert(device *IotDevice) error {
	_, err := db.Exec(`INSERT INTO iot_device (deviceId, deviceName, deviceType, modelId, position, mqttTopic, status, config)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
		device.DeviceId, device.DeviceName, device.DeviceType,
		device.ModelId, device.Position, device.MqttTopic, device.Status, device.Config)
	return err
}

func (m *DeviceMapper) Upsert(device *IotDevice) error {
	position := jsonOrNull(device.Position)
	config := jsonOrNull(device.Config)
	lastDataTime := device.LastDataTime
	if lastDataTime == nil {
		now := time.Now()
		lastDataTime = &now
	}
	_, err := db.Exec(`INSERT INTO iot_device (deviceId, deviceName, deviceType, modelId, position, mqttTopic, status, config, lastDataTime)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
		ON DUPLICATE KEY UPDATE
			deviceName = VALUES(deviceName),
			deviceType = VALUES(deviceType),
			position = COALESCE(VALUES(position), position),
			mqttTopic = VALUES(mqttTopic),
			status = VALUES(status),
			config = COALESCE(VALUES(config), config),
			lastDataTime = VALUES(lastDataTime)`,
		device.DeviceId, device.DeviceName, device.DeviceType, device.ModelId,
		position, device.MqttTopic, device.Status, config, lastDataTime)
	return err
}

func (m *DeviceMapper) Update(device *IotDevice) error {
	_, err := db.Exec(`UPDATE iot_device SET
			deviceName = COALESCE(NULLIF(?, ''), deviceName),
			deviceType = COALESCE(NULLIF(?, ''), deviceType),
			modelId = COALESCE(?, modelId),
			position = COALESCE(?, position),
			mqttTopic = COALESCE(NULLIF(?, ''), mqttTopic),
			status = COALESCE(NULLIF(?, ''), status),
			config = COALESCE(?, config)
		WHERE deviceId=?`,
		device.DeviceName, device.DeviceType, device.ModelId, jsonOrNull(device.Position),
		device.MqttTopic, device.Status, jsonOrNull(device.Config), device.DeviceId)
	return err
}

func (m *DeviceMapper) UpdateStatus(deviceId, status string) error {
	_, err := db.Exec("UPDATE iot_device SET status=?, lastDataTime=? WHERE deviceId=?", status, time.Now(), deviceId)
	return err
}

func (m *DeviceMapper) Delete(deviceId string) error {
	_, err := db.Exec("DELETE FROM iot_device WHERE deviceId = ?", deviceId)
	return err
}

func (m *DeviceMapper) FindByModelId(modelId int) ([]IotDevice, error) {
	var devices []IotDevice
	err := db.Select(&devices, `SELECT deviceId, deviceName, deviceType, modelId,
		COALESCE(CAST(position AS CHAR), '') AS position,
		mqttTopic, status, lastDataTime,
		COALESCE(CAST(config AS CHAR), '') AS config,
		createdAt
		FROM iot_device WHERE modelId = ?`, modelId)
	return devices, err
}

func jsonOrNull(value string) interface{} {
	if value == "" {
		return sql.NullString{}
	}
	return value
}
