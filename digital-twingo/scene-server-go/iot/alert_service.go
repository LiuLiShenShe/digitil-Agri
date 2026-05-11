package iot

import (
	"encoding/json"
	"fmt"

	"scene-server-go/config"
)

type AlertService struct {
	mapper        *AlertMapper
	deviceMapper  *DeviceMapper
	deviceService *DeviceService
}

func NewAlertService() *AlertService {
	return &AlertService{
		mapper:       NewAlertMapper(),
		deviceMapper: NewDeviceMapper(),
	}
}

func (s *AlertService) SetDeviceService(ds *DeviceService) {
	s.deviceService = ds
}

func (s *AlertService) CheckThreshold(deviceId, metricKey string, value float64) {
	device, err := s.deviceMapper.FindById(deviceId)
	if err != nil {
		return
	}

	var cfg DeviceConfig
	if device.Config != "" {
		if err := json.Unmarshal([]byte(device.Config), &cfg); err != nil {
			return
		}
	}

	thresh, ok := cfg.Thresholds[metricKey]
	if !ok {
		return
	}

	var severity, msg string
	if value < thresh.Min {
		severity = thresh.Severity
		msg = fmt.Sprintf("%s %s=%.2f 低于阈值下限 %.2f", device.DeviceName, metricKey, value, thresh.Min)
	} else if value > thresh.Max {
		severity = thresh.Severity
		msg = fmt.Sprintf("%s %s=%.2f 超过阈值上限 %.2f", device.DeviceName, metricKey, value, thresh.Max)
	} else {
		return
	}

	if severity == "" {
		severity = "warning"
	}

	alert := &AlertLog{
		DeviceId:  deviceId,
		AlertType: "threshold",
		Severity:  severity,
		Message:   msg,
	}

	if err := s.mapper.Insert(alert); err != nil {
		config.Log("ERROR", "Failed to save alert: %v", err)
		return
	}

	config.Log("WARN", "Alert: %s", msg)

	if s.deviceService != nil {
		s.deviceService.PublishAlert(alert)
	}
}

func (s *AlertService) GetRecentAlerts(limit int) ([]AlertLog, error) {
	if limit <= 0 {
		limit = 50
	}
	return s.mapper.FindRecent(limit)
}

func (s *AlertService) GetDeviceAlerts(deviceId string, limit int) ([]AlertLog, error) {
	if limit <= 0 {
		limit = 50
	}
	return s.mapper.FindByDevice(deviceId, limit)
}

func (s *AlertService) AcknowledgeAlert(id int64) error {
	return s.mapper.Acknowledge(id)
}

func (s *AlertService) GetUnackedCount() (int, error) {
	return s.mapper.CountUnacked()
}
