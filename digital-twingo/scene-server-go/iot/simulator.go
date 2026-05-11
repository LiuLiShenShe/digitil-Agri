package iot

import (
	"math"
	"math/rand"
	"sync"
	"time"
)

type Simulator struct {
	devices  map[string]*SimulatedDevice
	mu       sync.RWMutex
	running  bool
	stopCh   chan struct{}
	onData   func(data SensorData)
}

type SimulatedDevice struct {
	DeviceId   string
	DeviceType string
	Metrics    []SimulatedMetric
}

type SimulatedMetric struct {
	Key       string
	Unit      string
	Base      float64
	Amp       float64
	Min       float64
	Max       float64
	prevValue float64
}

func NewSimulator() *Simulator {
	return &Simulator{
		devices: make(map[string]*SimulatedDevice),
		stopCh:  make(chan struct{}),
	}
}

func (s *Simulator) SetDataCallback(cb func(data SensorData)) {
	s.onData = cb
}

func (s *Simulator) AddDevice(device *SimulatedDevice) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.devices[device.DeviceId] = device
}

func (s *Simulator) RemoveDevice(deviceId string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.devices, deviceId)
}

func (s *Simulator) Start(intervalMs int) {
	s.mu.Lock()
	if s.running {
		s.mu.Unlock()
		return
	}
	s.running = true
	s.mu.Unlock()

	ticker := time.NewTicker(time.Duration(intervalMs) * time.Millisecond)
	defer ticker.Stop()

	for {
		select {
		case <-s.stopCh:
			return
		case <-ticker.C:
			s.generateData()
		}
	}
}

func (s *Simulator) Stop() {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.running {
		s.running = false
		close(s.stopCh)
	}
}

func (s *Simulator) generateData() {
	s.mu.RLock()
	devices := make([]*SimulatedDevice, 0, len(s.devices))
	for _, d := range s.devices {
		devices = append(devices, d)
	}
	s.mu.RUnlock()

	for _, dev := range devices {
		metrics := make(map[string]float64)
		for i := range dev.Metrics {
			m := &dev.Metrics[i]
			walk := 0.0
			if m.prevValue != 0 {
				walk = (m.prevValue - m.Base) * 0.85
			}
			noise := (rand.Float64() - 0.5) * 2 * m.Amp
			val := math.Round((m.Base+walk+noise)*100) / 100
			val = math.Max(m.Min, math.Min(m.Max, val))
			m.prevValue = val
			metrics[m.Key] = val
		}

		data := SensorData{
			DeviceId:  dev.DeviceId,
			Timestamp: time.Now().UnixMilli(),
			Metrics:   metrics,
		}
		if s.onData != nil {
			s.onData(data)
		}
	}
}

func DefaultDevices() []*SimulatedDevice {
	return []*SimulatedDevice{
		{
			DeviceId: "iot-greenhouse-01", DeviceType: "sensor",
			Metrics: []SimulatedMetric{
				{Key: "temperature", Unit: "°C", Base: 26, Amp: 3, Min: 10, Max: 45},
				{Key: "humidity", Unit: "%", Base: 65, Amp: 5, Min: 20, Max: 100},
				{Key: "soilMoisture", Unit: "%", Base: 55, Amp: 3, Min: 0, Max: 100},
				{Key: "co2", Unit: "ppm", Base: 800, Amp: 80, Min: 300, Max: 2000},
				{Key: "lightIntensity", Unit: "lux", Base: 40000, Amp: 8000, Min: 0, Max: 100000},
				{Key: "ph", Unit: "pH", Base: 6.5, Amp: 0.2, Min: 4, Max: 9},
			},
		},
		{
			DeviceId: "iot-field-01", DeviceType: "sensor",
			Metrics: []SimulatedMetric{
				{Key: "soilMoisture", Unit: "%", Base: 45, Amp: 4, Min: 0, Max: 100},
				{Key: "temperature", Unit: "°C", Base: 22, Amp: 3, Min: -5, Max: 40},
				{Key: "ph", Unit: "pH", Base: 6.8, Amp: 0.2, Min: 4, Max: 9},
				{Key: "humidity", Unit: "%", Base: 60, Amp: 5, Min: 20, Max: 100},
			},
		},
		{
			DeviceId: "iot-weather-01", DeviceType: "weather_station",
			Metrics: []SimulatedMetric{
				{Key: "temperature", Unit: "°C", Base: 24, Amp: 4, Min: -10, Max: 45},
				{Key: "humidity", Unit: "%", Base: 58, Amp: 6, Min: 20, Max: 100},
				{Key: "windSpeed", Unit: "m/s", Base: 3, Amp: 2, Min: 0, Max: 30},
				{Key: "rainfall", Unit: "mm/h", Base: 0, Amp: 1, Min: 0, Max: 50},
				{Key: "lightIntensity", Unit: "lux", Base: 50000, Amp: 15000, Min: 0, Max: 120000},
			},
		},
		{
			DeviceId: "iot-irrigation-01", DeviceType: "controller",
			Metrics: []SimulatedMetric{
				{Key: "waterFlow", Unit: "L/min", Base: 30, Amp: 10, Min: 0, Max: 80},
				{Key: "waterPressure", Unit: "kPa", Base: 250, Amp: 30, Min: 0, Max: 400},
				{Key: "soilMoisture", Unit: "%", Base: 50, Amp: 6, Min: 0, Max: 100},
			},
		},
		{
			DeviceId: "iot-solar-01", DeviceType: "sensor",
			Metrics: []SimulatedMetric{
				{Key: "powerOutput", Unit: "KW", Base: 250, Amp: 100, Min: 0, Max: 500},
				{Key: "temperature", Unit: "°C", Base: 35, Amp: 5, Min: -10, Max: 70},
				{Key: "lightIntensity", Unit: "W/m²", Base: 600, Amp: 200, Min: 0, Max: 1200},
			},
		},
		{
			DeviceId: "iot-wind-01", DeviceType: "sensor",
			Metrics: []SimulatedMetric{
				{Key: "powerOutput", Unit: "KW", Base: 300, Amp: 150, Min: 0, Max: 800},
				{Key: "windSpeed", Unit: "m/s", Base: 8, Amp: 4, Min: 0, Max: 30},
				{Key: "temperature", Unit: "°C", Base: 28, Amp: 3, Min: -20, Max: 60},
			},
		},
		{
			DeviceId: "iot-camera-01", DeviceType: "camera",
			Metrics: []SimulatedMetric{
				{Key: "status", Unit: "", Base: 1, Amp: 0, Min: 0, Max: 1},
			},
		},
		{
			DeviceId: "iot-camera-02", DeviceType: "camera",
			Metrics: []SimulatedMetric{
				{Key: "status", Unit: "", Base: 1, Amp: 0, Min: 0, Max: 1},
			},
		},
	}
}
