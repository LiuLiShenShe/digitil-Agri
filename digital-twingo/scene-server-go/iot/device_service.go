package iot

import (
	"encoding/json"
	"math"
	"sync"
	"time"

	"scene-server-go/config"
)

type DeviceService struct {
	mapper     *DeviceMapper
	dataMapper *DataMapper
	alertSvc   *AlertService
	mqtt       *MqttAdapter
	simulator  *Simulator
	mu         sync.RWMutex
}

var deviceServiceInstance *DeviceService

func InitDeviceService(alertSvc *AlertService) *DeviceService {
	if deviceServiceInstance != nil {
		return deviceServiceInstance
	}

	svc := &DeviceService{
		mapper:     NewDeviceMapper(),
		dataMapper: NewDataMapper(),
		alertSvc:   alertSvc,
		simulator:  NewSimulator(),
	}

	deviceServiceInstance = svc
	return svc
}

func GetDeviceService() *DeviceService {
	return deviceServiceInstance
}

func (s *DeviceService) InitMqtt() {
	cfg := config.AppConfig
	broker := cfg.Iot.MqttBroker
	if broker == "" {
		broker = "tcp://127.0.0.1:1883"
	}
	clientId := cfg.Iot.MqttClientId
	if clientId == "" {
		clientId = "scene-server-go"
	}

	s.mqtt = NewMqttAdapter(broker, clientId)
	if err := s.mqtt.Connect(); err != nil {
		config.Log("WARN", "MQTT connection failed, using simulator only: %v", err)
	} else {
		config.Log("INFO", "MQTT connected to %s", broker)
	}
}

func (s *DeviceService) StartSimulator() {
	s.simulator.SetDataCallback(func(data SensorData) {
		s.HandleSensorData(data)
	})

	for _, dev := range DefaultDevices() {
		if err := s.ensureDefaultDevice(dev); err != nil {
			config.Log("WARN", "Failed to upsert default IoT device %s: %v", dev.DeviceId, err)
		}
		s.simulator.AddDevice(dev)
	}

	go s.simulator.Start(2000)
	config.Log("INFO", "IoT Simulator started with %d devices", len(DefaultDevices()))
}

func (s *DeviceService) HandleSensorData(data SensorData) {
	for metricKey, metricValue := range data.Metrics {
		dp := &IotDataPoint{
			DeviceId:    data.DeviceId,
			MetricKey:   metricKey,
			MetricValue: metricValue,
			Timestamp:   time.Now(),
		}

		unit := ""
		simDev := s.getSimulatedDevice(data.DeviceId)
		if simDev != nil {
			for _, m := range simDev.Metrics {
				if m.Key == metricKey {
					unit = m.Unit
					break
				}
			}
		}
		dp.Unit = unit

		if err := s.dataMapper.InsertDataPoint(dp); err != nil {
			config.Log("ERROR", "Failed to save IoT data: %v", err)
		}

		s.alertSvc.CheckThreshold(data.DeviceId, metricKey, metricValue)
	}

	if err := s.mapper.UpdateStatus(data.DeviceId, "online"); err != nil {
		config.Log("WARN", "Failed to update IoT device status: %v", err)
	}

	s.broadcastData(data)
}

func (s *DeviceService) getSimulatedDevice(deviceId string) *SimulatedDevice {
	for _, d := range DefaultDevices() {
		if d.DeviceId == deviceId {
			return d
		}
	}
	return nil
}

var wsClients = make(map[chan []byte]bool)
var wsClientsMu sync.Mutex

func RegisterWsClient(ch chan []byte) {
	wsClientsMu.Lock()
	wsClients[ch] = true
	wsClientsMu.Unlock()
}

func UnregisterWsClient(ch chan []byte) {
	wsClientsMu.Lock()
	delete(wsClients, ch)
	close(ch)
	wsClientsMu.Unlock()
}

func (s *DeviceService) broadcastData(data SensorData) {
	msg := map[string]interface{}{
		"type":      "iotData",
		"deviceId":  data.DeviceId,
		"timestamp": data.Timestamp,
		"metrics":   data.Metrics,
	}
	jsonData, err := json.Marshal(msg)
	if err != nil {
		return
	}

	wsClientsMu.Lock()
	defer wsClientsMu.Unlock()
	for ch := range wsClients {
		select {
		case ch <- jsonData:
		default:
		}
	}
}

func (s *DeviceService) GetAllDevices() ([]IotDevice, error) {
	return s.mapper.FindAll()
}

func (s *DeviceService) GetDevice(deviceId string) (*IotDevice, error) {
	return s.mapper.FindById(deviceId)
}

func (s *DeviceService) CreateDevice(device *IotDevice) error {
	if device.Status == "" {
		device.Status = "offline"
	}
	err := s.mapper.Insert(device)
	if err != nil {
		return err
	}

	simDev := s.findAndCopySimDevice(device.DeviceId)
	if simDev != nil {
		s.simulator.AddDevice(simDev)
	}

	if device.MqttTopic != "" && s.mqtt != nil && s.mqtt.IsConnected() {
		s.mqtt.Subscribe(device.DeviceId, device.MqttTopic, func(deviceId string, data SensorData) {
			s.HandleSensorData(data)
		})
	}

	config.Log("INFO", "IoT device created: %s (%s)", device.DeviceId, device.DeviceName)
	return nil
}

func (s *DeviceService) UpdateDevice(device *IotDevice) error {
	return s.mapper.Update(device)
}

func (s *DeviceService) DeleteDevice(deviceId string) error {
	s.simulator.RemoveDevice(deviceId)
	return s.mapper.Delete(deviceId)
}

func (s *DeviceService) GetDeviceData(deviceId string, limit int) ([]IotDataPoint, error) {
	if limit <= 0 {
		limit = 100
	}
	return s.dataMapper.FindByDevice(deviceId, limit)
}

func (s *DeviceService) GetDeviceMetricData(deviceId, metricKey string, limit int) ([]IotDataPoint, error) {
	if limit <= 0 {
		limit = 100
	}
	return s.dataMapper.FindByDeviceAndMetric(deviceId, metricKey, limit)
}

func (s *DeviceService) BindModel(deviceId string, modelId int) error {
	device, err := s.mapper.FindById(deviceId)
	if err != nil {
		return err
	}
	device.ModelId = &modelId
	return s.mapper.Update(device)
}

func (s *DeviceService) findAndCopySimDevice(deviceId string) *SimulatedDevice {
	for _, d := range DefaultDevices() {
		if d.DeviceId == deviceId {
			metrics := make([]SimulatedMetric, len(d.Metrics))
			copy(metrics, d.Metrics)
			return &SimulatedDevice{
				DeviceId:   d.DeviceId,
				DeviceType: d.DeviceType,
				Metrics:    metrics,
			}
		}
	}
	return nil
}

func (s *DeviceService) PublishAlert(alert *AlertLog) {
	msg := map[string]interface{}{
		"type":      "alert",
		"id":        alert.Id,
		"deviceId":  alert.DeviceId,
		"alertType": alert.AlertType,
		"severity":  alert.Severity,
		"message":   alert.Message,
		"createdAt": alert.CreatedAt.Format(time.RFC3339),
	}
	jsonData, err := json.Marshal(msg)
	if err != nil {
		return
	}

	wsClientsMu.Lock()
	defer wsClientsMu.Unlock()
	for ch := range wsClients {
		select {
		case ch <- jsonData:
		default:
		}
	}
}

func (s *DeviceService) GetSimulatorDevices() []SimulatedDevice {
	var result []SimulatedDevice
	for _, d := range DefaultDevices() {
		result = append(result, SimulatedDevice{
			DeviceId:   d.DeviceId,
			DeviceType: d.DeviceType,
			Metrics:    d.Metrics,
		})
	}
	return result
}

func (s *DeviceService) ensureDefaultDevice(dev *SimulatedDevice) error {
	device := &IotDevice{
		DeviceId:   dev.DeviceId,
		DeviceName: defaultDeviceName(dev.DeviceId),
		DeviceType: dev.DeviceType,
		Status:     "online",
		MqttTopic:  "agri/" + dev.DeviceId + "/telemetry",
		Config:     defaultDeviceConfig(dev),
	}
	return s.mapper.Upsert(device)
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
	if name, ok := names[deviceId]; ok {
		return name
	}
	return deviceId
}

func defaultDeviceConfig(dev *SimulatedDevice) string {
	cfg := DeviceConfig{
		Thresholds:     map[string]ThresholdConfig{},
		UpdateInterval: 2000,
	}
	for _, metric := range dev.Metrics {
		if metric.Key == "status" {
			continue
		}
		span := metric.Max - metric.Min
		margin := math.Max(metric.Amp*2.5, span*0.08)
		severity := "warning"
		if metric.Key == "co2" || metric.Key == "waterPressure" {
			severity = "critical"
		}
		cfg.Thresholds[metric.Key] = ThresholdConfig{
			Min:      math.Max(metric.Min, metric.Base-margin),
			Max:      math.Min(metric.Max, metric.Base+margin),
			Severity: severity,
		}
	}
	data, err := json.Marshal(cfg)
	if err != nil {
		return `{"thresholds":{},"updateInterval":2000}`
	}
	return string(data)
}
