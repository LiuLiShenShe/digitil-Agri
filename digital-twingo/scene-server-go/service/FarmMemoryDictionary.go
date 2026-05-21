package service

import "scene-server-go/vo"

var farmMetricDictionary = map[string]vo.FarmMetricDefinitionVo{
	"temperature": {
		Key: "temperature", Label: "温度", Unit: "°C", Category: "environment",
		DefaultFrequency: string(vo.SyncFrequencyRealtime),
	},
	"humidity": {
		Key: "humidity", Label: "湿度", Unit: "%", Category: "environment",
		DefaultFrequency: string(vo.SyncFrequencyRealtime),
	},
	"soilMoisture": {
		Key: "soilMoisture", Label: "土壤水分", Unit: "%", Category: "soil",
		DefaultFrequency: string(vo.SyncFrequencyHourly),
	},
	"co2": {
		Key: "co2", Label: "CO2", Unit: "ppm", Category: "environment",
		DefaultFrequency: string(vo.SyncFrequencyRealtime),
	},
	"lightIntensity": {
		Key: "lightIntensity", Label: "光照", Unit: "lux", Category: "environment",
		DefaultFrequency: string(vo.SyncFrequencyRealtime),
	},
	"ph": {
		Key: "ph", Label: "pH", Unit: "pH", Category: "soil",
		DefaultFrequency: string(vo.SyncFrequencyDaily),
	},
	"ec": {
		Key: "ec", Label: "EC", Unit: "mS/cm", Category: "water_quality",
		DefaultFrequency: string(vo.SyncFrequencyDaily),
	},
	"waterPressure": {
		Key: "waterPressure", Label: "水压", Unit: "kPa", Category: "irrigation",
		DefaultFrequency: string(vo.SyncFrequencyRealtime),
	},
	"flow": {
		Key: "flow", Label: "流量", Unit: "L/min", Category: "irrigation",
		DefaultFrequency: string(vo.SyncFrequencyRealtime), Aliases: []string{"waterFlow"},
	},
	"switchState": {
		Key: "switchState", Label: "设备开关状态", Unit: "", Category: "device",
		DefaultFrequency: string(vo.SyncFrequencyRealtime), Aliases: []string{"status"},
	},
}

var farmMetricAliases = map[string]string{
	"waterFlow": "flow",
	"status":    "switchState",
}

var defaultFarmSyncPolicies = map[string]vo.FarmSyncPolicyVo{
	string(ObjectTypeGreenhouse): {
		ObjectType: string(ObjectTypeGreenhouse), SyncFrequency: string(vo.SyncFrequencyHourly),
		MetricKeys: []string{"temperature", "humidity", "soilMoisture", "co2", "lightIntensity", "ph", "waterPressure", "flow", "switchState"},
	},
	string(ObjectTypeParcel): {
		ObjectType: string(ObjectTypeParcel), SyncFrequency: string(vo.SyncFrequencyHourly),
		MetricKeys: []string{"soilMoisture", "temperature", "humidity", "ph", "ec"},
	},
	string(ObjectTypePlant): {
		ObjectType: string(ObjectTypePlant), SyncFrequency: string(vo.SyncFrequencyDaily), GeometryFrequency: string(vo.SyncFrequencyMilestone),
		MetricKeys: []string{"temperature", "humidity", "soilMoisture", "ph"},
	},
	string(ObjectTypeSensor): {
		ObjectType: string(ObjectTypeSensor), SyncFrequency: string(vo.SyncFrequencyRealtime),
		MetricKeys: []string{"temperature", "humidity", "soilMoisture", "co2", "lightIntensity", "ph"},
	},
	string(ObjectTypeDevice): {
		ObjectType: string(ObjectTypeDevice), SyncFrequency: string(vo.SyncFrequencyRealtime),
		MetricKeys: []string{"waterPressure", "flow", "switchState", "soilMoisture"},
	},
	string(ObjectTypeCamera): {
		ObjectType: string(ObjectTypeCamera), SyncFrequency: string(vo.SyncFrequencyRealtime),
		MetricKeys: []string{"switchState"},
	},
}

var defaultObjectDeviceBindings = map[string][]string{
	"gh-tomato-001":         []string{"iot-greenhouse-01", "iot-irrigation-01", "iot-camera-01"},
	"parcel-tomato-a":       []string{"iot-field-01", "iot-greenhouse-01"},
	"sensor-greenhouse-001": []string{"iot-greenhouse-01"},
	"device-irrigation-001": []string{"iot-irrigation-01"},
	"camera-greenhouse-001": []string{"iot-camera-01"},
	"farm-yupont-demo":      []string{"iot-greenhouse-01", "iot-field-01", "iot-weather-01", "iot-irrigation-01", "iot-camera-01"},
}

var validFarmEventTypes = map[string]bool{
	"irrigation":     true,
	"fertilization":  true,
	"alert":          true,
	"inspection":     true,
	"maintenance":    true,
	"agent_analysis": true,
}
