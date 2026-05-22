package service

import (
	"testing"
	"time"

	"scene-server-go/vo"
)

func TestFarmMemoryMetricDictionaryCoversPhase3Metrics(t *testing.T) {
	svc := NewFarmMemoryServiceWithStore(NewMemoryAgriculturalObjectStore(), NewMemoryFarmMemoryStore())

	dict := svc.MetricDictionary()
	required := []string{"temperature", "humidity", "soilMoisture", "co2", "lightIntensity", "ph", "ec", "waterPressure", "flow", "switchState"}
	for _, key := range required {
		if _, ok := dict[key]; !ok {
			t.Fatalf("metric dictionary missing %s", key)
		}
	}

	if normalized, ok := svc.NormalizeMetricKey("waterFlow"); !ok || normalized != "flow" {
		t.Fatalf("waterFlow alias normalized to %q ok=%v, want flow true", normalized, ok)
	}
	if normalized, ok := svc.NormalizeMetricKey("status"); !ok || normalized != "switchState" {
		t.Fatalf("status alias normalized to %q ok=%v, want switchState true", normalized, ok)
	}
	if _, ok := svc.NormalizeMetricKey("unknownMetric"); ok {
		t.Fatalf("unknown metric should be rejected")
	}
}

func TestFarmMemorySyncPolicyDefaultsAndKeyPlantGeometry(t *testing.T) {
	objectStore := NewMemoryAgriculturalObjectStore()
	svc := NewFarmMemoryServiceWithStore(objectStore, NewMemoryFarmMemoryStore())
	if err := NewAgriculturalObjectServiceWithStore(objectStore).SeedTomatoGreenhouseMVP(); err != nil {
		t.Fatalf("seed failed: %v", err)
	}

	sensor := svc.SyncPolicyForObject("sensor-greenhouse-001")
	if sensor.SyncFrequency != string(vo.SyncFrequencyRealtime) {
		t.Fatalf("sensor sync frequency = %s, want realtime", sensor.SyncFrequency)
	}
	if len(sensor.MetricKeys) == 0 || sensor.MetricKeys[0] != "temperature" {
		t.Fatalf("sensor metric bindings not populated: %#v", sensor.MetricKeys)
	}

	plant := svc.SyncPolicyForObject("plant-tomato-001")
	if plant.GeometryFrequency != string(vo.SyncFrequencyMilestone) {
		t.Fatalf("key plant geometry frequency = %s, want milestone", plant.GeometryFrequency)
	}
	if plant.SyncFrequency != string(vo.SyncFrequencyDaily) {
		t.Fatalf("plant status sync frequency = %s, want daily", plant.SyncFrequency)
	}
}

func TestFarmMemoryObjectTimeSeriesSupportsLatestHistoryAggregatesAndRanges(t *testing.T) {
	now := time.Date(2026, 5, 21, 10, 0, 0, 0, time.UTC)
	objectStore := NewMemoryAgriculturalObjectStore()
	memoryStore := NewMemoryFarmMemoryStore()
	svc := NewFarmMemoryServiceWithClock(objectStore, memoryStore, func() time.Time { return now })
	if err := NewAgriculturalObjectServiceWithStore(objectStore).SeedTomatoGreenhouseMVP(); err != nil {
		t.Fatalf("seed failed: %v", err)
	}

	memoryStore.InsertMetricPoint(vo.FarmMetricPointVo{ObjectID: "gh-tomato-001", SourceDeviceID: "iot-greenhouse-01", MetricKey: "temperature", Value: 24, Unit: "°C", Timestamp: now.Add(-2 * time.Hour), DataQuality: string(DataQualitySimulated)})
	memoryStore.InsertMetricPoint(vo.FarmMetricPointVo{ObjectID: "gh-tomato-001", SourceDeviceID: "iot-greenhouse-01", MetricKey: "temperature", Value: 26, Unit: "°C", Timestamp: now.Add(-1 * time.Hour), DataQuality: string(DataQualitySimulated)})
	memoryStore.InsertMetricPoint(vo.FarmMetricPointVo{ObjectID: "gh-tomato-001", SourceDeviceID: "iot-greenhouse-01", MetricKey: "waterFlow", Value: 31, Unit: "L/min", Timestamp: now.Add(-90 * time.Minute), DataQuality: string(DataQualitySimulated)})
	memoryStore.InsertMetricPoint(vo.FarmMetricPointVo{ObjectID: "gh-tomato-001", SourceDeviceID: "iot-greenhouse-01", MetricKey: "temperature", Value: 12, Unit: "°C", Timestamp: now.Add(-30 * 24 * time.Hour), DataQuality: string(DataQualityStale)})

	latest, err := svc.LatestValues(vo.FarmLatestQuery{ObjectID: "gh-tomato-001", Metrics: []string{"temperature", "waterFlow"}})
	if err != nil {
		t.Fatalf("latest query failed: %v", err)
	}
	if latest.Values["temperature"].Value != 26 {
		t.Fatalf("latest temperature = %#v, want value 26", latest.Values["temperature"])
	}
	if _, ok := latest.Values["flow"]; !ok {
		t.Fatalf("waterFlow should be normalized to flow in latest values: %#v", latest.Values)
	}

	series, err := svc.TimeSeries(vo.TimeSeriesQuery{ObjectID: "gh-tomato-001", Range: "24h", Metrics: []string{"temperature"}})
	if err != nil {
		t.Fatalf("24h time series failed: %v", err)
	}
	if len(series.Series["temperature"].Points) != 2 {
		t.Fatalf("24h temperature points = %d, want 2", len(series.Series["temperature"].Points))
	}
	if series.Series["temperature"].Aggregate.Min != 24 || series.Series["temperature"].Aggregate.Max != 26 || series.Series["temperature"].Aggregate.Avg != 25 {
		t.Fatalf("unexpected aggregate: %#v", series.Series["temperature"].Aggregate)
	}
	if _, err := svc.TimeSeries(vo.TimeSeriesQuery{ObjectID: "gh-tomato-001", Range: "30d", Metrics: []string{"temperature"}}); err == nil {
		t.Fatalf("unsupported range should be rejected")
	}
}

func TestFarmMemoryEventQueryCoversRequiredEventTypes(t *testing.T) {
	now := time.Date(2026, 5, 21, 10, 0, 0, 0, time.UTC)
	objectStore := NewMemoryAgriculturalObjectStore()
	memoryStore := NewMemoryFarmMemoryStore()
	svc := NewFarmMemoryServiceWithClock(objectStore, memoryStore, func() time.Time { return now })
	if err := NewAgriculturalObjectServiceWithStore(objectStore).SeedTomatoGreenhouseMVP(); err != nil {
		t.Fatalf("seed failed: %v", err)
	}

	for _, eventType := range []string{"irrigation", "fertilization", "alert", "inspection", "maintenance", "agent_analysis"} {
		memoryStore.UpsertEvent(vo.FarmEventVo{
			EventID:     "evt-" + eventType,
			ObjectID:    "gh-tomato-001",
			EventType:   eventType,
			Severity:    "info",
			Summary:     eventType + " summary",
			Timestamp:   now.Add(-time.Hour),
			DataQuality: string(DataQualitySimulated),
		})
	}

	result, err := svc.Events(vo.EventQuery{ObjectID: "gh-tomato-001", Range: "24h", Limit: 20})
	if err != nil {
		t.Fatalf("event query failed: %v", err)
	}
	seen := map[string]bool{}
	for _, event := range result.Events {
		seen[event.EventType] = true
	}
	for _, eventType := range []string{"irrigation", "fertilization", "alert", "inspection", "maintenance", "agent_analysis"} {
		if !seen[eventType] {
			t.Fatalf("event type %s missing from result %#v", eventType, seen)
		}
	}
}

func TestFarmMemoryDefaultDeviceEventsIncludeAlertContext(t *testing.T) {
	now := time.Date(2026, 5, 21, 10, 0, 0, 0, time.UTC)
	objectStore := NewMemoryAgriculturalObjectStore()
	svc := NewFarmMemoryServiceWithClock(objectStore, NewMemoryFarmMemoryStore(), func() time.Time { return now })
	if err := NewAgriculturalObjectServiceWithStore(objectStore).SeedTomatoGreenhouseMVP(); err != nil {
		t.Fatalf("seed failed: %v", err)
	}

	result, err := svc.Events(vo.EventQuery{ObjectID: "device-irrigation-001", Range: "24h", EventTypes: []string{"alert", "maintenance"}, Limit: 20})
	if err != nil {
		t.Fatalf("event query failed: %v", err)
	}

	seen := map[string]vo.FarmEventVo{}
	for _, event := range result.Events {
		seen[event.EventType] = event
	}
	alert, ok := seen["alert"]
	if !ok {
		t.Fatalf("default device events should include alert: %#v", result.Events)
	}
	if alert.ObjectID != "device-irrigation-001" || alert.RelatedObjectID != "gh-tomato-001" {
		t.Fatalf("alert should preserve device and related greenhouse context: %#v", alert)
	}
	if _, ok := seen["maintenance"]; !ok {
		t.Fatalf("default device events should include maintenance: %#v", result.Events)
	}
}

func TestFarmMemoryDefaultGreenhouseReportIncludesAlertContext(t *testing.T) {
	now := time.Date(2026, 5, 21, 10, 0, 0, 0, time.UTC)
	objectStore := NewMemoryAgriculturalObjectStore()
	svc := NewFarmMemoryServiceWithClock(objectStore, NewMemoryFarmMemoryStore(), func() time.Time { return now })
	if err := NewAgriculturalObjectServiceWithStore(objectStore).SeedTomatoGreenhouseMVP(); err != nil {
		t.Fatalf("seed failed: %v", err)
	}

	report, err := svc.GreenhouseReportSource("gh-tomato-001", "2026-05-21")
	if err != nil {
		t.Fatalf("report source failed: %v", err)
	}

	if len(report.Alerts) == 0 {
		t.Fatalf("default greenhouse report should include alert context: %#v", report)
	}
	if containsString(report.MissingCategories, "alerts") {
		t.Fatalf("alerts should not be marked missing when default alert context exists: %#v", report.MissingCategories)
	}
}

func TestFarmMemoryDailyArchiveAndGreenhouseReportSource(t *testing.T) {
	now := time.Date(2026, 5, 21, 10, 0, 0, 0, time.UTC)
	objectStore := NewMemoryAgriculturalObjectStore()
	memoryStore := NewMemoryFarmMemoryStore()
	svc := NewFarmMemoryServiceWithClock(objectStore, memoryStore, func() time.Time { return now })
	if err := NewAgriculturalObjectServiceWithStore(objectStore).SeedTomatoGreenhouseMVP(); err != nil {
		t.Fatalf("seed failed: %v", err)
	}

	memoryStore.InsertMetricPoint(vo.FarmMetricPointVo{ObjectID: "gh-tomato-001", SourceDeviceID: "iot-greenhouse-01", MetricKey: "temperature", Value: 25, Unit: "°C", Timestamp: now.Add(-2 * time.Hour), DataQuality: string(DataQualitySimulated)})
	memoryStore.InsertMetricPoint(vo.FarmMetricPointVo{ObjectID: "device-irrigation-001", SourceDeviceID: "iot-irrigation-01", MetricKey: "waterPressure", Value: 250, Unit: "kPa", Timestamp: now.Add(-time.Hour), DataQuality: string(DataQualitySimulated)})
	memoryStore.UpsertEvent(vo.FarmEventVo{EventID: "evt-irrigation-1", ObjectID: "gh-tomato-001", RelatedObjectID: "device-irrigation-001", EventType: "irrigation", Severity: "info", Summary: "A区灌溉18分钟", Timestamp: now.Add(-3 * time.Hour), DataQuality: string(DataQualityReal)})
	memoryStore.UpsertEvent(vo.FarmEventVo{EventID: "evt-alert-1", ObjectID: "device-irrigation-001", RelatedObjectID: "gh-tomato-001", EventType: "alert", Severity: "warning", Summary: "水压波动", Timestamp: now.Add(-2 * time.Hour), DataQuality: string(DataQualitySimulated)})

	archive, err := svc.BuildDailyArchive("gh-tomato-001", now)
	if err != nil {
		t.Fatalf("build archive failed: %v", err)
	}
	if archive.ObjectID != "gh-tomato-001" || archive.ArchiveDate != "2026-05-21" {
		t.Fatalf("unexpected archive identity: %#v", archive)
	}
	if archive.MetricSummaries["temperature"].Avg != 25 {
		t.Fatalf("archive temperature avg = %#v, want 25", archive.MetricSummaries["temperature"])
	}

	report, err := svc.GreenhouseReportSource("gh-tomato-001", "2026-05-21")
	if err != nil {
		t.Fatalf("report source failed: %v", err)
	}
	if report.ObjectID != "gh-tomato-001" || report.Environment.DataQuality == string(DataQualityMissing) {
		t.Fatalf("report missing environment summary: %#v", report.Environment)
	}
	if len(report.DeviceStatus.Items) == 0 {
		t.Fatalf("report missing device status: %#v", report.DeviceStatus)
	}
	if len(report.IrrigationEvents) == 0 || len(report.Alerts) == 0 {
		t.Fatalf("report missing irrigation or alert events: irrigation=%d alerts=%d", len(report.IrrigationEvents), len(report.Alerts))
	}
	if len(report.Recommendations) == 0 {
		t.Fatalf("report should include recommendations context")
	}
}

func TestFarmMemoryAgentQueriesValidateReadOnlyInputs(t *testing.T) {
	now := time.Date(2026, 5, 21, 10, 0, 0, 0, time.UTC)
	objectStore := NewMemoryAgriculturalObjectStore()
	svc := NewFarmMemoryServiceWithClock(objectStore, NewMemoryFarmMemoryStore(), func() time.Time { return now })
	if err := NewAgriculturalObjectServiceWithStore(objectStore).SeedTomatoGreenhouseMVP(); err != nil {
		t.Fatalf("seed failed: %v", err)
	}

	if _, err := svc.TimeSeriesTool(vo.TimeSeriesToolInput{ObjectID: "gh-tomato-001", Range: "7d", Metrics: []string{"temperature"}, Limit: 200}); err != nil {
		t.Fatalf("valid timeseries tool input failed: %v", err)
	}
	if _, err := svc.TimeSeriesTool(vo.TimeSeriesToolInput{ObjectID: "gh-tomato-001", Range: "365d", Metrics: []string{"temperature"}}); err == nil {
		t.Fatalf("invalid tool range should be rejected")
	}
	if _, err := svc.TimeSeriesTool(vo.TimeSeriesToolInput{ObjectID: "gh-tomato-001", Range: "24h", Metrics: []string{"DROP TABLE"}}); err == nil {
		t.Fatalf("unknown metric should be rejected")
	}
	if _, err := svc.EventTool(vo.EventToolInput{ObjectID: "gh-tomato-001", Range: "24h", EventTypes: []string{"irrigation"}, Limit: 20}); err != nil {
		t.Fatalf("valid event tool input failed: %v", err)
	}
	if _, err := svc.EventTool(vo.EventToolInput{ObjectID: "gh-tomato-001", Range: "24h", EventTypes: []string{"shell.exec"}}); err == nil {
		t.Fatalf("unsupported event type should be rejected")
	}
}

func TestAssistantExposesFarmMemoryReadOnlyTools(t *testing.T) {
	svc := NewAssistantService()

	tools := svc.Tools()
	seen := map[string]bool{}
	for _, tool := range tools {
		if (tool.Name == "timeseries.query" || tool.Name == "event.query") && !tool.ReadOnly {
			t.Fatalf("farm memory tool %s must be read-only", tool.Name)
		}
		seen[tool.Name] = true
	}
	if !seen["timeseries.query"] || !seen["event.query"] {
		t.Fatalf("assistant tools missing farm memory read-only tools: %#v", seen)
	}
}
