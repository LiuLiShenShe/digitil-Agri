package service

import (
	"fmt"
	"strings"
	"time"

	"scene-server-go/vo"
)

const TomatoGreenhouseAcceptancePrompt = "搭建番茄温室，包含 20 株番茄、气象站、水泵、摄像头和传感器"

type TomatoGreenhouseAcceptanceVo = vo.TomatoGreenhouseAcceptanceVo
type AcceptanceMissingAssetVo = vo.AcceptanceMissingAssetVo

type AcceptanceService struct {
	semantic       *SemanticService
	objectService  *AgriculturalObjectService
	memoryService  *FarmMemoryService
	bindingService *SceneBusinessBindingService
	now            func() time.Time
}

func NewAcceptanceService() *AcceptanceService {
	return newAcceptanceServiceWithDemoStores(time.Now)
}

func NewAcceptanceServiceForTest() *AcceptanceService {
	return newAcceptanceServiceWithDemoStores(func() time.Time {
		return time.Date(2026, 5, 22, 8, 30, 0, 0, time.UTC)
	})
}

func newAcceptanceServiceWithDemoStores(now func() time.Time) *AcceptanceService {
	if now == nil {
		now = time.Now
	}
	objectStore := NewMemoryAgriculturalObjectStore()
	objectService := NewAgriculturalObjectServiceWithStore(objectStore)
	_ = objectService.SeedTomatoGreenhouseMVP()
	memoryStore := NewMemoryFarmMemoryStore()
	seedAcceptanceMemory(memoryStore, now())
	memoryService := NewFarmMemoryServiceWithClock(objectStore, memoryStore, now)
	bindingService := NewSceneBusinessBindingService(newAcceptanceSceneBindingStore(), objectService)
	return &AcceptanceService{
		semantic:       NewSemanticService(),
		objectService:  objectService,
		memoryService:  memoryService,
		bindingService: bindingService,
		now:            now,
	}
}

func (s *AcceptanceService) TomatoGreenhouseAcceptance() (vo.TomatoGreenhouseAcceptanceVo, error) {
	if s == nil {
		return vo.TomatoGreenhouseAcceptanceVo{}, fmt.Errorf("acceptance service is nil")
	}
	buildResult := s.semantic.BuildPlan(vo.SemanticBuildRequest{
		Message:  TomatoGreenhouseAcceptancePrompt,
		Mode:     "preview",
		OwnerKey: "phase6-acceptance",
	})
	if buildResult.Code != 200 {
		return vo.TomatoGreenhouseAcceptanceVo{}, fmt.Errorf("semantic build failed: %v", buildResult.Data)
	}
	build, ok := buildResult.Data.(vo.SemanticBuildResponse)
	if !ok {
		return vo.TomatoGreenhouseAcceptanceVo{}, fmt.Errorf("unexpected semantic build type: %T", buildResult.Data)
	}

	modelCounts := acceptanceModelCounts(build.Models)
	expectedCounts := map[string]acceptanceExpectedCount{
		"tomato":          {Label: "番茄植株", Expected: 20},
		"greenhouse":      {Label: "温室", Expected: 1},
		"weather_station": {Label: "气象站", Expected: 1},
		"irrigation":      {Label: "水泵/灌溉设备", Expected: 1},
		"camera":          {Label: "摄像头占位", Expected: 1},
		"sensor":          {Label: "传感器占位", Expected: 1},
	}
	counts := map[string]vo.AcceptanceCountVo{}
	for key, expected := range expectedCounts {
		actual := modelCounts[key]
		counts[key] = vo.AcceptanceCountVo{
			Label: expected.Label, Expected: expected.Expected, Actual: actual, Passed: actual == expected.Expected,
		}
	}

	greenhouseLookup := s.objectService.Lookup(vo.ObjectLookupRequest{ObjectID: "gh-tomato-001"})
	greenhouseRelations := s.objectService.Relations(vo.ObjectRelationsRequest{ObjectID: "gh-tomato-001"})
	deviceLookup := s.objectService.Lookup(vo.ObjectLookupRequest{ObjectID: "device-irrigation-001"})
	deviceMemory := s.acceptanceObjectMemory("device-irrigation-001")
	report, _ := s.memoryService.GreenhouseReportSource("gh-tomato-001", s.now().UTC().Format("2006-01-02"))
	validation := s.bindingService.ValidateScene("番茄温室 MVP")
	semanticBuild := acceptanceSemanticBuild(build)
	metrics := acceptanceMetrics(counts, build, validation, report)
	steps := acceptanceSteps(counts, build, validation, greenhouseRelations, deviceMemory, report)
	issues := acceptanceIssues(counts, steps, metrics, validation)

	result := vo.TomatoGreenhouseAcceptanceVo{
		Prompt:            TomatoGreenhouseAcceptancePrompt,
		SceneName:         firstNonEmptyAcceptance(build.ScenePlan.SceneName, "番茄温室 MVP"),
		RunAt:             s.now().UTC().Format(time.RFC3339),
		ModelCounts:       counts,
		Steps:             steps,
		SuccessMetrics:    metrics,
		Issues:            issues,
		SemanticBuild:     semanticBuild,
		BindingValidation: validation,
		GreenhouseContext: greenhouseRelations,
		AbnormalContext:   deviceMemory,
		ReportSource:      report,
		ArchiveReadiness: vo.AcceptanceArchiveReadinessVo{
			Ready: true,
			Changes: []string{
				"add-agricultural-object-model",
				"bind-scene-objects-to-business-objects",
				"add-farm-memory-layer",
				"add-agent-operation-trace",
				"add-asset-metadata-and-fidelity-routing",
			},
			NextAction: "review 后按 OpenSpec archive 流程归档 Phase 1-5 changes",
		},
	}
	if greenhouseLookup.Code == 200 {
		result.GreenhouseObject = greenhouseLookup.Object
	}
	if deviceLookup.Code == 200 {
		result.AbnormalDevice = deviceLookup.Object
	}
	result.OverallPassed = acceptancePassed(result)
	return result, nil
}

func (s *AcceptanceService) acceptanceObjectMemory(objectID string) vo.AcceptanceObjectMemoryVo {
	latest, _ := s.memoryService.LatestValues(vo.FarmLatestQuery{ObjectID: objectID, Metrics: []string{"waterPressure", "flow", "switchState"}})
	events, _ := s.memoryService.Events(vo.EventQuery{ObjectID: objectID, Range: "24h", EventTypes: []string{"alert", "maintenance"}, Limit: 20})
	recommendation := "维持当前灌溉策略，继续观察水压波动。"
	if len(events.Events) > 0 {
		recommendation = "检查水泵压力曲线和阀门状态，确认告警是否需要维护处置。"
	}
	return vo.AcceptanceObjectMemoryVo{ObjectID: objectID, Latest: latest, Events: events, Recommendation: recommendation}
}

type acceptanceExpectedCount struct {
	Label    string
	Expected int
}

func acceptanceModelCounts(models []vo.BuildModel) map[string]int {
	counts := map[string]int{}
	for _, model := range models {
		key := model.Meta.AssetKey
		if model.Meta.Placeholder && model.Meta.MissingAssetKey != "" {
			key = model.Meta.MissingAssetKey
		}
		counts[key]++
	}
	return counts
}

func acceptanceSemanticBuild(build vo.SemanticBuildResponse) vo.AcceptanceSemanticBuildVo {
	missing := make([]vo.AcceptanceMissingAssetVo, 0, len(build.MissingAssets))
	for _, item := range build.MissingAssets {
		missing = append(missing, vo.AcceptanceMissingAssetVo{
			AssetKey:       item.AssetKey,
			Name:           item.Name,
			Reason:         item.Reason,
			PlacementRefs:  item.PlacementRefs,
			Routing:        item.Routing,
			ReferenceImage: item.ReferenceImage,
			Generation:     item.Generation,
		})
	}
	return vo.AcceptanceSemanticBuildVo{
		ScenePlan:     build.ScenePlan,
		Models:        build.Models,
		Warnings:      build.Warnings,
		MissingAssets: missing,
		PlanSource:    build.PlanSource,
		AgentTrace:    build.AgentTrace,
	}
}

func acceptanceMetrics(counts map[string]vo.AcceptanceCountVo, build vo.SemanticBuildResponse, validation vo.SceneBindingValidationResponse, report vo.GreenhouseReportSourceVo) []vo.AcceptanceMetricVo {
	countsPassed := true
	for _, count := range counts {
		countsPassed = countsPassed && count.Passed
	}
	traceSteps := 0
	if build.AgentTrace != nil {
		traceSteps = len(build.AgentTrace.Steps)
	}
	metadataComplete := 0
	metadataTotal := 0
	for _, asset := range NewAssetRegistryService().List() {
		metadataTotal++
		if asset.MetadataComplete {
			metadataComplete++
		}
	}
	metadataRate := 100.0
	if metadataTotal > 0 {
		metadataRate = float64(metadataComplete) / float64(metadataTotal) * 100
	}
	return []vo.AcceptanceMetricVo{
		{Key: "mvp-counts", Label: "MVP 对象数量", Target: "固定提示词数量全部匹配", Actual: fmt.Sprintf("%d 项对象计数", len(counts)), Value: float64(len(counts)), Passed: countsPassed, Source: "Phase 6"},
		{Key: "binding-rate", Label: "3D 对象业务绑定率", Target: "核心演示场景不低于 90%", Actual: fmt.Sprintf("%.2f%%", validation.Summary.BindingRate), Value: validation.Summary.BindingRate, Passed: validation.Summary.BindingRate >= 90, Source: "Phase 2"},
		{Key: "data-binding", Label: "数据绑定完整率", Target: "核心对象至少有实时或日级指标", Actual: report.DataQuality, Value: qualityScore(report.DataQuality), Passed: report.DataQuality != string(DataQualityMissing), Source: "Phase 3"},
		{Key: "agent-trace", Label: "Agent trace 完整率", Target: "所有 Agent 任务均有可查询 trace", Actual: fmt.Sprintf("%d 个 trace step", traceSteps), Value: float64(traceSteps), Passed: traceSteps > 0, Source: "Phase 4"},
		{Key: "asset-metadata", Label: "资产元数据完整率", Target: "公开资产基础元数据不低于 80%", Actual: fmt.Sprintf("%.2f%%", metadataRate), Value: metadataRate, Passed: metadataRate >= 80, Source: "Phase 5"},
		{Key: "missing-asset-continuity", Label: "缺失资产不中断率", Target: "缺 GLB 时占位模型继续生成场景", Actual: fmt.Sprintf("%d 个缺失资产", len(build.MissingAssets)), Value: float64(len(build.MissingAssets)), Passed: missingAssetsHaveTasks(build.MissingAssets, "camera", "sensor"), Source: "Phase 5"},
		{Key: "report-source", Label: "日报生成成功率", Target: "温室日报可基于对象、指标、事件和告警生成", Actual: report.DataQuality, Value: qualityScore(report.DataQuality), Passed: len(report.Recommendations) > 0, Source: "Phase 3 / Phase 6"},
	}
}

func acceptanceSteps(counts map[string]vo.AcceptanceCountVo, build vo.SemanticBuildResponse, validation vo.SceneBindingValidationResponse, greenhouseRelations vo.ObjectRelationsResponse, deviceMemory vo.AcceptanceObjectMemoryVo, report vo.GreenhouseReportSourceVo) []vo.AcceptanceStepVo {
	countsPassed := true
	for _, count := range counts {
		countsPassed = countsPassed && count.Passed
	}
	traceSteps := 0
	if build.AgentTrace != nil {
		traceSteps = len(build.AgentTrace.Steps)
	}
	return []vo.AcceptanceStepVo{
		{Key: "semantic-build", Title: "语义搭建", Target: "固定提示词生成可加载场景", Actual: fmt.Sprintf("%d 个模型", len(build.Models)), Passed: countsPassed && len(build.Models) > 0, Evidence: build.ScenePlan.SceneName},
		{Key: "trace-routing", Title: "资产路由与 trace", Target: "包含资产选择理由、布局结果和 trace", Actual: fmt.Sprintf("%d 个 trace step / %d 个缺失资产", traceSteps, len(build.MissingAssets)), Passed: traceSteps > 0 && missingAssetsHaveTasks(build.MissingAssets, "camera", "sensor"), Evidence: "camera/sensor 使用占位模型与生成任务"},
		{Key: "greenhouse-drilldown", Title: "温室点选详情", Target: "看到温室对象、传感器、设备、指标、告警和事件", Actual: relationSummary(greenhouseRelations), Passed: greenhouseRelations.Code == 200 && len(greenhouseRelations.Relations["sensors"]) > 0 && len(greenhouseRelations.Relations["devices"]) > 0 && len(greenhouseRelations.Relations["events"]) > 0},
		{Key: "abnormal-device", Title: "异常设备详情", Target: "看到最近指标、告警原因和建议动作", Actual: fmt.Sprintf("%d 个最新指标 / %d 个事件", len(deviceMemory.Latest.Values), len(deviceMemory.Events.Events)), Passed: len(deviceMemory.Latest.Values) > 0 && len(deviceMemory.Events.Events) > 0 && deviceMemory.Recommendation != ""},
		{Key: "scene-validation", Title: "完整场景校验", Target: "列出缺绑定、缺数据、缺缩略图和缺元数据问题", Actual: fmt.Sprintf("%d 个问题，绑定率 %.2f%%", len(validation.Summary.Issues), validation.Summary.BindingRate), Passed: validation.Code == 200 && len(validation.Summary.Issues) > 0 && validation.Summary.BindingRate >= 90},
		{Key: "greenhouse-report", Title: "温室日报", Target: "包含环境、设备、告警、灌溉事件和建议", Actual: fmt.Sprintf("%d 条告警 / %d 条灌溉事件 / %d 条建议", len(report.Alerts), len(report.IrrigationEvents), len(report.Recommendations)), Passed: report.Environment.Summary != "" && report.DeviceStatus.Summary != "" && len(report.Alerts) > 0 && len(report.IrrigationEvents) > 0 && len(report.Recommendations) > 0},
	}
}

func acceptanceIssues(counts map[string]vo.AcceptanceCountVo, steps []vo.AcceptanceStepVo, metrics []vo.AcceptanceMetricVo, validation vo.SceneBindingValidationResponse) []vo.AcceptanceIssueVo {
	issues := make([]vo.AcceptanceIssueVo, 0)
	for key, count := range counts {
		if !count.Passed {
			issues = append(issues, vo.AcceptanceIssueVo{Severity: "error", Category: "mvp_count", Source: key, Message: fmt.Sprintf("%s expected %d got %d", count.Label, count.Expected, count.Actual)})
		}
	}
	for _, step := range steps {
		if !step.Passed {
			issues = append(issues, vo.AcceptanceIssueVo{Severity: "error", Category: "acceptance_step", Source: step.Key, Message: step.Title + " 未通过"})
		}
	}
	for _, metric := range metrics {
		if !metric.Passed {
			issues = append(issues, vo.AcceptanceIssueVo{Severity: "warning", Category: "success_metric", Source: metric.Key, Message: metric.Label + " 未达到目标"})
		}
	}
	for _, issue := range validation.Summary.Issues {
		issues = append(issues, vo.AcceptanceIssueVo{Severity: "info", Category: issue.Category, Source: issue.SceneObjectId, Message: issue.Message})
	}
	return issues
}

func acceptancePassed(result vo.TomatoGreenhouseAcceptanceVo) bool {
	for _, count := range result.ModelCounts {
		if !count.Passed {
			return false
		}
	}
	for _, step := range result.Steps {
		if !step.Passed {
			return false
		}
	}
	for _, metric := range result.SuccessMetrics {
		if !metric.Passed {
			return false
		}
	}
	return result.ArchiveReadiness.Ready
}

func missingAssetsHaveTasks(items []vo.MissingAssetVo, keys ...string) bool {
	required := map[string]bool{}
	for _, key := range keys {
		required[key] = false
	}
	for _, item := range items {
		if _, ok := required[item.AssetKey]; !ok {
			continue
		}
		required[item.AssetKey] = item.Generation != nil && item.Generation.TaskID != ""
	}
	for _, ok := range required {
		if !ok {
			return false
		}
	}
	return true
}

func qualityScore(quality string) float64 {
	switch quality {
	case string(DataQualityReal):
		return 100
	case string(DataQualitySimulated):
		return 80
	case string(DataQualityStale):
		return 60
	default:
		return 0
	}
}

func relationSummary(response vo.ObjectRelationsResponse) string {
	return fmt.Sprintf("sensors=%d devices=%d cameras=%d events=%d metrics=%d",
		len(response.Relations["sensors"]),
		len(response.Relations["devices"]),
		len(response.Relations["cameras"]),
		len(response.Relations["events"]),
		len(response.Relations["metrics"]),
	)
}

func seedAcceptanceMemory(store *MemoryFarmMemoryStore, now time.Time) {
	points := []vo.FarmMetricPointVo{
		{ObjectID: "gh-tomato-001", SourceDeviceID: "iot-greenhouse-01", MetricKey: "temperature", Value: 25.6, Unit: "°C", Timestamp: now.Add(-2 * time.Hour), DataQuality: string(DataQualitySimulated)},
		{ObjectID: "gh-tomato-001", SourceDeviceID: "iot-greenhouse-01", MetricKey: "humidity", Value: 71, Unit: "%", Timestamp: now.Add(-2 * time.Hour), DataQuality: string(DataQualitySimulated)},
		{ObjectID: "gh-tomato-001", SourceDeviceID: "iot-greenhouse-01", MetricKey: "soilMoisture", Value: 63, Unit: "%", Timestamp: now.Add(-90 * time.Minute), DataQuality: string(DataQualitySimulated)},
		{ObjectID: "gh-tomato-001", SourceDeviceID: "iot-greenhouse-01", MetricKey: "co2", Value: 620, Unit: "ppm", Timestamp: now.Add(-90 * time.Minute), DataQuality: string(DataQualitySimulated)},
		{ObjectID: "device-irrigation-001", SourceDeviceID: "iot-irrigation-01", MetricKey: "waterPressure", Value: 248, Unit: "kPa", Timestamp: now.Add(-45 * time.Minute), DataQuality: string(DataQualityReal)},
		{ObjectID: "device-irrigation-001", SourceDeviceID: "iot-irrigation-01", MetricKey: "flow", Value: 28, Unit: "L/min", Timestamp: now.Add(-45 * time.Minute), DataQuality: string(DataQualityReal)},
		{ObjectID: "device-irrigation-001", SourceDeviceID: "iot-irrigation-01", MetricKey: "switchState", Value: 1, Unit: "", Timestamp: now.Add(-30 * time.Minute), DataQuality: string(DataQualityReal)},
	}
	for _, point := range points {
		_ = store.InsertMetricPoint(point)
	}
	events := []vo.FarmEventVo{
		{EventID: "phase6-irrigation-1", ObjectID: "gh-tomato-001", RelatedObjectID: "device-irrigation-001", EventType: "irrigation", Severity: "info", Summary: "A区灌溉18分钟", Timestamp: now.Add(-3 * time.Hour), DataQuality: string(DataQualityReal)},
		{EventID: "phase6-alert-1", ObjectID: "device-irrigation-001", RelatedObjectID: "gh-tomato-001", EventType: "alert", Severity: "warning", Summary: "水泵水压短时波动", Timestamp: now.Add(-2 * time.Hour), DataQuality: string(DataQualitySimulated)},
		{EventID: "phase6-maintenance-1", ObjectID: "device-irrigation-001", RelatedObjectID: "gh-tomato-001", EventType: "maintenance", Severity: "info", Summary: "建议巡检过滤器与阀门", Timestamp: now.Add(-90 * time.Minute), DataQuality: string(DataQualitySimulated)},
	}
	for _, event := range events {
		_ = store.UpsertEvent(event)
	}
}

type acceptanceSceneBindingStore struct {
	models []vo.SceneModelVo
}

func newAcceptanceSceneBindingStore() *acceptanceSceneBindingStore {
	models := []vo.SceneModelVo{
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "番茄温室 MVP", ModelId: 1}, SceneObjectId: "scene-gh-tomato-001", BusinessObjectId: "gh-tomato-001", AssetKey: "greenhouse", IsDefaultBinding: true, URL: "/scene-assets/models/Silo_House.glb"},
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "番茄温室 MVP", ModelId: 2}, SceneObjectId: "scene-parcel-tomato-a", BusinessObjectId: "parcel-tomato-a", AssetKey: "parcel", IsDefaultBinding: true},
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "番茄温室 MVP", ModelId: 3}, SceneObjectId: "scene-plant-tomato-001", BusinessObjectId: "plant-tomato-001", AssetKey: "tomato", IsDefaultBinding: true, URL: "/scene-assets/models/Tomato_Crop.glb"},
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "番茄温室 MVP", ModelId: 4}, SceneObjectId: "scene-sensor-greenhouse-001", BusinessObjectId: "sensor-greenhouse-001", AssetKey: "sensor", IsDefaultBinding: true},
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "番茄温室 MVP", ModelId: 5}, SceneObjectId: "scene-device-irrigation-001", BusinessObjectId: "device-irrigation-001", AssetKey: "irrigation", IsDefaultBinding: true, URL: "/scene-assets/models/Well.glb"},
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "番茄温室 MVP", ModelId: 6}, SceneObjectId: "scene-camera-greenhouse-001", BusinessObjectId: "camera-greenhouse-001", AssetKey: "camera", IsDefaultBinding: true},
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "番茄温室 MVP", ModelId: 7}, SceneObjectId: "scene-weather-station-001", BusinessObjectId: "sensor-greenhouse-001", AssetKey: "weather_station", IsDefaultBinding: false, URL: "/scene-assets/models/TowerWindmill.glb"},
	}
	return &acceptanceSceneBindingStore{models: models}
}

func (s *acceptanceSceneBindingStore) ListSceneModels(sceneName string) ([]vo.SceneModelVo, error) {
	result := make([]vo.SceneModelVo, 0)
	for _, model := range s.models {
		if model.SceneName == sceneName {
			result = append(result, model)
		}
	}
	return result, nil
}

func (s *acceptanceSceneBindingStore) UpdateSceneModelBinding(sceneName string, modelId int, sceneObjectId string, businessObjectId string, assetKey string, isDefaultBinding bool) (int, error) {
	return 0, nil
}

func (s *acceptanceSceneBindingStore) ClearSceneModelBinding(sceneName string, modelId int, sceneObjectId string) (int, error) {
	return 0, nil
}

func firstNonEmptyAcceptance(values ...string) string {
	for _, value := range values {
		if strings.TrimSpace(value) != "" {
			return value
		}
	}
	return ""
}
