package service

import (
	"fmt"
	"math"
	"sort"
	"strings"
	"time"

	"scene-server-go/mapper"
	"scene-server-go/vo"
)

type FarmMemoryService struct {
	objectStore AgriculturalObjectStore
	memoryStore FarmMemoryStore
	now         func() time.Time
}

func NewFarmMemoryService() *FarmMemoryService {
	return NewFarmMemoryServiceWithStore(mapper.NewAgriculturalObjectMapper(), mapperFarmMemoryStore())
}

func NewFarmMemoryServiceWithStore(objectStore AgriculturalObjectStore, memoryStore FarmMemoryStore) *FarmMemoryService {
	return NewFarmMemoryServiceWithClock(objectStore, memoryStore, time.Now)
}

func NewFarmMemoryServiceWithClock(objectStore AgriculturalObjectStore, memoryStore FarmMemoryStore, now func() time.Time) *FarmMemoryService {
	if now == nil {
		now = time.Now
	}
	return &FarmMemoryService{objectStore: objectStore, memoryStore: memoryStore, now: now}
}

func (s *FarmMemoryService) InitDB() error {
	if err := s.memoryStore.EnsureSchema(); err != nil {
		return err
	}
	return nil
}

func (s *FarmMemoryService) MetricDictionary() map[string]vo.FarmMetricDefinitionVo {
	result := make(map[string]vo.FarmMetricDefinitionVo, len(farmMetricDictionary))
	for key, metric := range farmMetricDictionary {
		result[key] = metric
	}
	return result
}

func (s *FarmMemoryService) SyncPolicies() map[string]vo.FarmSyncPolicyVo {
	result := make(map[string]vo.FarmSyncPolicyVo, len(defaultFarmSyncPolicies))
	for key, policy := range defaultFarmSyncPolicies {
		result[key] = copySyncPolicy(policy)
	}
	return result
}

func (s *FarmMemoryService) NormalizeMetricKey(key string) (string, bool) {
	key = strings.TrimSpace(key)
	if key == "" {
		return "", false
	}
	if _, ok := farmMetricDictionary[key]; ok {
		return key, true
	}
	if normalized, ok := farmMetricAliases[key]; ok {
		return normalized, true
	}
	return "", false
}

func (s *FarmMemoryService) SyncPolicyForObject(objectID string) vo.FarmSyncPolicyVo {
	obj, err := s.objectStore.FindByID(objectID)
	if err != nil || obj == nil {
		return vo.FarmSyncPolicyVo{ObjectID: objectID, ObjectType: "", SyncFrequency: string(vo.SyncFrequencyStatic), DataQuality: string(DataQualityMissing)}
	}
	policy, ok := defaultFarmSyncPolicies[obj.Type]
	if !ok {
		policy = vo.FarmSyncPolicyVo{ObjectType: obj.Type, SyncFrequency: string(vo.SyncFrequencyStatic), MetricKeys: []string{}}
	}
	policy = copySyncPolicy(policy)
	policy.ObjectID = objectID
	policy.ObjectType = obj.Type
	policy.DataQuality = obj.DataQuality
	if devices := s.deviceIDsForObject(objectID); len(devices) > 0 {
		policy.SourceDeviceIDs = devices
	}
	return policy
}

func (s *FarmMemoryService) LatestValues(query vo.FarmLatestQuery) (vo.FarmLatestResponseVo, error) {
	if strings.TrimSpace(query.ObjectID) == "" {
		return vo.FarmLatestResponseVo{}, fmt.Errorf("objectId is required")
	}
	objectIDs := s.objectScope(query.ObjectID)
	metrics, err := s.normalizeRequestedMetrics(query.Metrics, s.SyncPolicyForObject(query.ObjectID).MetricKeys)
	if err != nil {
		return vo.FarmLatestResponseVo{}, err
	}
	points, err := s.memoryStore.FindLatestMetricPoints(objectIDs, expandMetricAliases(metrics))
	if err != nil {
		return vo.FarmLatestResponseVo{}, err
	}
	response := vo.FarmLatestResponseVo{ObjectID: query.ObjectID, Values: map[string]vo.FarmMetricLatestValueVo{}, Missing: []string{}}
	for _, point := range points {
		normalized, ok := s.NormalizeMetricKey(point.MetricKey)
		if !ok {
			continue
		}
		if len(metrics) > 0 && !containsString(metrics, normalized) {
			continue
		}
		existing, exists := response.Values[normalized]
		if exists {
			parsed, _ := time.Parse(time.RFC3339, existing.Timestamp)
			if !point.Timestamp.After(parsed) {
				continue
			}
		}
		def := farmMetricDictionary[normalized]
		unit := firstNonEmpty(point.Unit, def.Unit)
		response.Values[normalized] = vo.FarmMetricLatestValueVo{
			MetricKey: normalized, Label: def.Label, Value: round2(point.Value), Unit: unit,
			Timestamp: point.Timestamp.UTC().Format(time.RFC3339), DataQuality: dataQualityOrDefault(point.DataQuality), SourceDeviceID: point.SourceDeviceID,
		}
	}
	for _, metric := range metrics {
		if _, ok := response.Values[metric]; !ok {
			response.Missing = append(response.Missing, metric)
		}
	}
	sort.Strings(response.Missing)
	return response, nil
}

func (s *FarmMemoryService) TimeSeries(query vo.TimeSeriesQuery) (vo.TimeSeriesResponseVo, error) {
	if strings.TrimSpace(query.ObjectID) == "" {
		return vo.TimeSeriesResponseVo{}, fmt.Errorf("objectId is required")
	}
	start, end, err := s.resolveRange(query.Range)
	if err != nil {
		return vo.TimeSeriesResponseVo{}, err
	}
	metrics, err := s.normalizeRequestedMetrics(query.Metrics, s.SyncPolicyForObject(query.ObjectID).MetricKeys)
	if err != nil {
		return vo.TimeSeriesResponseVo{}, err
	}
	points, err := s.memoryStore.FindMetricPoints(s.objectScope(query.ObjectID), expandMetricAliases(metrics), start, end, query.Limit)
	if err != nil {
		return vo.TimeSeriesResponseVo{}, err
	}
	response := vo.TimeSeriesResponseVo{
		ObjectID: query.ObjectID, Range: query.Range, StartAt: start.UTC().Format(time.RFC3339), EndAt: end.UTC().Format(time.RFC3339),
		Series: map[string]vo.FarmMetricSeriesVo{}, Missing: []string{},
	}
	for _, metric := range metrics {
		def := farmMetricDictionary[metric]
		response.Series[metric] = vo.FarmMetricSeriesVo{MetricKey: metric, Label: def.Label, Unit: def.Unit, Points: []vo.FarmMetricPointVo{}, Aggregate: vo.FarmMetricAggregateVo{}, DataQuality: string(DataQualityMissing)}
	}
	for _, point := range points {
		normalized, ok := s.NormalizeMetricKey(point.MetricKey)
		if !ok || !containsString(metrics, normalized) {
			continue
		}
		series := response.Series[normalized]
		point.MetricKey = normalized
		point.Value = round2(point.Value)
		point.DataQuality = dataQualityOrDefault(point.DataQuality)
		if point.Unit == "" {
			point.Unit = series.Unit
		}
		series.Points = append(series.Points, point)
		series.Unit = firstNonEmpty(point.Unit, series.Unit)
		series.DataQuality = mergeQuality(series.DataQuality, point.DataQuality)
		response.Series[normalized] = series
	}
	for key, series := range response.Series {
		if len(series.Points) == 0 {
			response.Missing = append(response.Missing, key)
			continue
		}
		series.Aggregate = aggregatePoints(series.Points)
		response.Series[key] = series
	}
	sort.Strings(response.Missing)
	return response, nil
}

func (s *FarmMemoryService) Events(query vo.EventQuery) (vo.EventQueryResponseVo, error) {
	if strings.TrimSpace(query.ObjectID) == "" {
		return vo.EventQueryResponseVo{}, fmt.Errorf("objectId is required")
	}
	start, end, err := s.resolveRange(query.Range)
	if err != nil {
		return vo.EventQueryResponseVo{}, err
	}
	eventTypes, err := normalizeEventTypes(query.EventTypes)
	if err != nil {
		return vo.EventQueryResponseVo{}, err
	}
	limit := query.Limit
	if limit <= 0 {
		limit = 50
	}
	events, err := s.memoryStore.FindEvents(s.objectScope(query.ObjectID), eventTypes, start, end, limit)
	if err != nil {
		return vo.EventQueryResponseVo{}, err
	}
	if len(events) == 0 {
		events = s.defaultEvents(query.ObjectID, eventTypes, start, end, limit)
	}
	return vo.EventQueryResponseVo{
		ObjectID: query.ObjectID, Range: query.Range, StartAt: start.UTC().Format(time.RFC3339), EndAt: end.UTC().Format(time.RFC3339),
		Events: events, Missing: missingEventTypes(eventTypes, events),
	}, nil
}

func (s *FarmMemoryService) BuildDailyArchive(objectID string, date time.Time) (vo.FarmDailyArchiveVo, error) {
	dayStart := time.Date(date.UTC().Year(), date.UTC().Month(), date.UTC().Day(), 0, 0, 0, 0, time.UTC)
	dayEnd := dayStart.Add(24*time.Hour - time.Nanosecond)
	policy := s.SyncPolicyForObject(objectID)
	metrics, err := s.normalizeRequestedMetrics(nil, policy.MetricKeys)
	if err != nil {
		return vo.FarmDailyArchiveVo{}, err
	}
	points, err := s.memoryStore.FindMetricPoints(s.objectScope(objectID), expandMetricAliases(metrics), dayStart, dayEnd, 0)
	if err != nil {
		return vo.FarmDailyArchiveVo{}, err
	}
	events, err := s.memoryStore.FindEvents(s.objectScope(objectID), nil, dayStart, dayEnd, 0)
	if err != nil {
		return vo.FarmDailyArchiveVo{}, err
	}
	grouped := map[string][]vo.FarmMetricPointVo{}
	for _, point := range points {
		normalized, ok := s.NormalizeMetricKey(point.MetricKey)
		if ok {
			point.MetricKey = normalized
			grouped[normalized] = append(grouped[normalized], point)
		}
	}
	summaries := map[string]vo.FarmMetricAggregateVo{}
	for key, list := range grouped {
		summaries[key] = aggregatePoints(list)
	}
	eventCounts := map[string]int{}
	for _, event := range events {
		eventCounts[event.EventType]++
	}
	quality := string(DataQualitySimulated)
	if len(points) == 0 && len(events) == 0 {
		quality = string(DataQualityMissing)
	}
	archive := vo.FarmDailyArchiveVo{
		ObjectID: objectID, ArchiveDate: dayStart.Format("2006-01-02"), MetricSummaries: summaries,
		EventCounts: eventCounts, DataQuality: quality, CreatedAt: s.now().UTC(),
	}
	if err := s.memoryStore.UpsertDailyArchive(archive); err != nil {
		return vo.FarmDailyArchiveVo{}, err
	}
	return archive, nil
}

func (s *FarmMemoryService) DailyArchives(objectID string, days int) (vo.FarmDailyArchivesResponseVo, error) {
	if days <= 0 {
		days = 7
	}
	archives, err := s.memoryStore.FindDailyArchives(objectID, days, s.now().UTC().Format("2006-01-02"))
	if err != nil {
		return vo.FarmDailyArchivesResponseVo{}, err
	}
	return vo.FarmDailyArchivesResponseVo{ObjectID: objectID, Days: days, Archives: archives}, nil
}

func (s *FarmMemoryService) GreenhouseReportSource(objectID string, date string) (vo.GreenhouseReportSourceVo, error) {
	if date == "" {
		date = s.now().UTC().Format("2006-01-02")
	}
	obj, err := s.objectStore.FindByID(objectID)
	if err != nil {
		return vo.GreenhouseReportSourceVo{}, err
	}
	latest, _ := s.LatestValues(vo.FarmLatestQuery{ObjectID: objectID, Metrics: []string{"temperature", "humidity", "soilMoisture", "co2", "lightIntensity", "ph"}})
	deviceLatest, _ := s.LatestValues(vo.FarmLatestQuery{ObjectID: objectID, Metrics: []string{"waterPressure", "flow", "switchState"}})
	events, _ := s.Events(vo.EventQuery{ObjectID: objectID, Range: "24h", Limit: 80})
	alerts := filterEvents(events.Events, "alert")
	irrigation := filterEvents(events.Events, "irrigation")

	environment := reportSectionFromLatest(latest, []string{"temperature", "humidity", "soilMoisture", "co2", "lightIntensity", "ph"}, "环境摘要")
	deviceStatus := reportSectionFromLatest(deviceLatest, []string{"waterPressure", "flow", "switchState"}, "设备状态")
	missing := []string{}
	if environment.DataQuality == string(DataQualityMissing) {
		missing = append(missing, "environment")
	}
	if deviceStatus.DataQuality == string(DataQualityMissing) {
		missing = append(missing, "deviceStatus")
	}
	if len(alerts) == 0 {
		missing = append(missing, "alerts")
	}
	if len(irrigation) == 0 {
		missing = append(missing, "irrigationEvents")
	}
	quality := string(DataQualitySimulated)
	if len(missing) >= 3 {
		quality = string(DataQualityMissing)
	} else if len(missing) > 0 {
		quality = string(DataQualityStale)
	}
	return vo.GreenhouseReportSourceVo{
		ObjectID: objectID, ObjectName: obj.Name, Date: date, DataQuality: quality,
		Environment: environment, DeviceStatus: deviceStatus, Alerts: alerts, IrrigationEvents: irrigation,
		Recommendations: reportRecommendations(environment, deviceStatus, alerts), MissingCategories: missing,
	}, nil
}

func (s *FarmMemoryService) TimeSeriesTool(input vo.TimeSeriesToolInput) (vo.TimeSeriesToolOutput, error) {
	if input.Limit <= 0 {
		input.Limit = 500
	}
	result, err := s.TimeSeries(vo.TimeSeriesQuery{ObjectID: input.ObjectID, Range: input.Range, Metrics: input.Metrics, Limit: input.Limit})
	if err != nil {
		return vo.TimeSeriesToolOutput{}, err
	}
	return vo.TimeSeriesToolOutput{Query: input, Result: result}, nil
}

func (s *FarmMemoryService) EventTool(input vo.EventToolInput) (vo.EventToolOutput, error) {
	if input.Limit <= 0 {
		input.Limit = 50
	}
	result, err := s.Events(vo.EventQuery{ObjectID: input.ObjectID, Range: input.Range, EventTypes: input.EventTypes, Limit: input.Limit})
	if err != nil {
		return vo.EventToolOutput{}, err
	}
	return vo.EventToolOutput{Query: input, Result: result}, nil
}

func (s *FarmMemoryService) normalizeRequestedMetrics(requested []string, defaults []string) ([]string, error) {
	source := requested
	if len(source) == 0 {
		source = defaults
	}
	result := make([]string, 0, len(source))
	seen := map[string]bool{}
	for _, key := range source {
		normalized, ok := s.NormalizeMetricKey(key)
		if !ok {
			return nil, fmt.Errorf("unsupported metric key: %s", key)
		}
		if !seen[normalized] {
			result = append(result, normalized)
			seen[normalized] = true
		}
	}
	sort.Strings(result)
	return result, nil
}

func (s *FarmMemoryService) resolveRange(value string) (time.Time, time.Time, error) {
	if value == "" {
		value = "24h"
	}
	end := s.now().UTC()
	switch value {
	case "24h":
		return end.Add(-24 * time.Hour), end, nil
	case "7d":
		return end.Add(-7 * 24 * time.Hour), end, nil
	default:
		return time.Time{}, time.Time{}, fmt.Errorf("unsupported time range: %s", value)
	}
}

func (s *FarmMemoryService) objectScope(objectID string) []string {
	ids := []string{objectID}
	children, err := s.objectStore.FindChildren(objectID)
	if err == nil {
		for _, child := range children {
			ids = append(ids, child.ID)
		}
	}
	return uniqueFarmMemoryStrings(ids)
}

func (s *FarmMemoryService) deviceIDsForObject(objectID string) []string {
	if devices := defaultObjectDeviceBindings[objectID]; len(devices) > 0 {
		return append([]string{}, devices...)
	}
	return []string{}
}

func (s *FarmMemoryService) defaultEvents(objectID string, eventTypes []string, start, end time.Time, limit int) []vo.FarmEventVo {
	now := s.now().UTC()
	candidates := []vo.FarmEventVo{
		{EventID: "seed-irrigation-001", ObjectID: objectID, RelatedObjectID: "device-irrigation-001", EventType: "irrigation", Severity: "info", Summary: "最近一次灌溉已完成", Timestamp: now.Add(-3 * time.Hour), DataQuality: string(DataQualityReal), Metadata: map[string]interface{}{"durationMin": 18}},
		{EventID: "seed-inspection-001", ObjectID: objectID, EventType: "inspection", Severity: "info", Summary: "巡检记录：温室环境正常", Timestamp: now.Add(-6 * time.Hour), DataQuality: string(DataQualitySimulated)},
		{EventID: "seed-agent-001", ObjectID: objectID, EventType: "agent_analysis", Severity: "info", Summary: "Agent 建议关注午后通风和水压波动", Timestamp: now.Add(-2 * time.Hour), DataQuality: string(DataQualitySimulated)},
	}
	switch objectID {
	case "gh-tomato-001":
		candidates = append(candidates,
			vo.FarmEventVo{EventID: "seed-alert-irrigation-pressure", ObjectID: "device-irrigation-001", RelatedObjectID: objectID, EventType: "alert", Severity: "warning", Summary: "水泵水压短时波动", Timestamp: now.Add(-90 * time.Minute), DataQuality: string(DataQualitySimulated)},
			vo.FarmEventVo{EventID: "seed-maintenance-irrigation", ObjectID: "device-irrigation-001", RelatedObjectID: objectID, EventType: "maintenance", Severity: "info", Summary: "建议巡检过滤器与阀门", Timestamp: now.Add(-60 * time.Minute), DataQuality: string(DataQualitySimulated)},
		)
	case "device-irrigation-001":
		candidates = append(candidates,
			vo.FarmEventVo{EventID: "seed-alert-irrigation-pressure", ObjectID: objectID, RelatedObjectID: "gh-tomato-001", EventType: "alert", Severity: "warning", Summary: "水泵水压短时波动", Timestamp: now.Add(-90 * time.Minute), DataQuality: string(DataQualitySimulated)},
			vo.FarmEventVo{EventID: "seed-maintenance-irrigation", ObjectID: objectID, RelatedObjectID: "gh-tomato-001", EventType: "maintenance", Severity: "info", Summary: "建议巡检过滤器与阀门", Timestamp: now.Add(-60 * time.Minute), DataQuality: string(DataQualitySimulated)},
		)
	}
	eventSet := stringSet(eventTypes)
	result := make([]vo.FarmEventVo, 0, len(candidates))
	for _, event := range candidates {
		if len(eventSet) > 0 && !eventSet[event.EventType] {
			continue
		}
		if event.Timestamp.Before(start) || event.Timestamp.After(end) {
			continue
		}
		result = append(result, event)
	}
	if limit > 0 && len(result) > limit {
		result = result[:limit]
	}
	return result
}

func mapperFarmMemoryStore() FarmMemoryStore {
	return mapper.NewFarmMemoryMapper()
}

func copySyncPolicy(policy vo.FarmSyncPolicyVo) vo.FarmSyncPolicyVo {
	policy.MetricKeys = append([]string{}, policy.MetricKeys...)
	policy.SourceDeviceIDs = append([]string{}, policy.SourceDeviceIDs...)
	return policy
}

func expandMetricAliases(metrics []string) []string {
	result := append([]string{}, metrics...)
	for alias, canonical := range farmMetricAliases {
		if containsString(metrics, canonical) {
			result = append(result, alias)
		}
	}
	return uniqueFarmMemoryStrings(result)
}

func aggregatePoints(points []vo.FarmMetricPointVo) vo.FarmMetricAggregateVo {
	if len(points) == 0 {
		return vo.FarmMetricAggregateVo{}
	}
	minValue := points[0].Value
	maxValue := points[0].Value
	total := 0.0
	for _, point := range points {
		minValue = math.Min(minValue, point.Value)
		maxValue = math.Max(maxValue, point.Value)
		total += point.Value
	}
	return vo.FarmMetricAggregateVo{Min: round2(minValue), Max: round2(maxValue), Avg: round2(total / float64(len(points))), Count: len(points)}
}

func normalizeEventTypes(eventTypes []string) ([]string, error) {
	result := make([]string, 0, len(eventTypes))
	seen := map[string]bool{}
	for _, eventType := range eventTypes {
		eventType = strings.TrimSpace(eventType)
		if eventType == "" {
			continue
		}
		if !validFarmEventTypes[eventType] {
			return nil, fmt.Errorf("unsupported event type: %s", eventType)
		}
		if !seen[eventType] {
			result = append(result, eventType)
			seen[eventType] = true
		}
	}
	sort.Strings(result)
	return result, nil
}

func missingEventTypes(requested []string, events []vo.FarmEventVo) []string {
	if len(requested) == 0 {
		return []string{}
	}
	seen := map[string]bool{}
	for _, event := range events {
		seen[event.EventType] = true
	}
	missing := []string{}
	for _, eventType := range requested {
		if !seen[eventType] {
			missing = append(missing, eventType)
		}
	}
	return missing
}

func reportSectionFromLatest(latest vo.FarmLatestResponseVo, keys []string, title string) vo.FarmReportSectionVo {
	items := make([]interface{}, 0, len(keys))
	quality := string(DataQualityMissing)
	for _, key := range keys {
		if item, ok := latest.Values[key]; ok {
			items = append(items, item)
			quality = mergeQuality(quality, item.DataQuality)
		}
	}
	missing := []string{}
	for _, key := range keys {
		if _, ok := latest.Values[key]; !ok {
			missing = append(missing, key)
		}
	}
	summary := fmt.Sprintf("%s包含 %d 项指标", title, len(items))
	if len(items) == 0 {
		summary = title + "暂无可用数据"
	}
	return vo.FarmReportSectionVo{DataQuality: quality, Summary: summary, Items: items, Missing: missing}
}

func filterEvents(events []vo.FarmEventVo, eventType string) []vo.FarmEventVo {
	result := make([]vo.FarmEventVo, 0)
	for _, event := range events {
		if event.EventType == eventType {
			result = append(result, event)
		}
	}
	return result
}

func reportRecommendations(environment, deviceStatus vo.FarmReportSectionVo, alerts []vo.FarmEventVo) []string {
	recommendations := []string{
		"保持温室环境指标按对象查询，日报引用同一温室的指标与事件。",
		"灌溉设备只做状态读取，控制动作需进入后续受控工具链。",
	}
	if environment.DataQuality == string(DataQualityMissing) {
		recommendations = append(recommendations, "补齐温室环境传感器数据后再生成正式日报。")
	}
	if deviceStatus.DataQuality == string(DataQualityMissing) {
		recommendations = append(recommendations, "补齐水泵、水压和流量数据以提升设备状态判断。")
	}
	if len(alerts) > 0 {
		recommendations = append(recommendations, "优先复核未确认告警，并在报告中保留处置上下文。")
	}
	return recommendations
}

func dataQualityOrDefault(value string) string {
	if value == "" {
		return string(DataQualitySimulated)
	}
	return value
}

func mergeQuality(current, next string) string {
	rank := map[string]int{
		string(DataQualityMissing):   0,
		string(DataQualityStale):     1,
		string(DataQualitySimulated): 2,
		string(DataQualityReal):      3,
	}
	if rank[next] > rank[current] {
		return next
	}
	return current
}

func containsString(values []string, target string) bool {
	for _, value := range values {
		if value == target {
			return true
		}
	}
	return false
}

func uniqueFarmMemoryStrings(values []string) []string {
	seen := map[string]bool{}
	result := []string{}
	for _, value := range values {
		if value == "" || seen[value] {
			continue
		}
		seen[value] = true
		result = append(result, value)
	}
	sort.Strings(result)
	return result
}
