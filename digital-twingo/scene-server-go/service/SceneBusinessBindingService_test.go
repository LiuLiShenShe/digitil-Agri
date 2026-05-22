package service

import (
	"testing"

	"scene-server-go/vo"
)

func TestSceneBusinessBindingUpdatesAndLooksUpSceneObject(t *testing.T) {
	sceneStore := newMemorySceneBindingStore([]vo.SceneModelVo{
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "tomato-demo", ModelId: 0}, SceneObjectId: "scene-gh-001", AssetKey: "greenhouse", URL: "/scene-assets/models/Silo_House.glb"},
	})
	objectSvc := seededAgriculturalObjectService(t)
	svc := NewSceneBusinessBindingService(sceneStore, objectSvc)

	result := svc.UpdateBinding(vo.SceneBindingUpdateRequest{
		SceneName:        "tomato-demo",
		SceneObjectId:    "scene-gh-001",
		BusinessObjectId: "gh-tomato-001",
		AssetKey:         "greenhouse",
		IsDefaultBinding: true,
	})
	if result.Code != 200 {
		t.Fatalf("update binding failed: %#v", result)
	}

	lookup := svc.LookupBySceneObject("tomato-demo", "scene-gh-001")
	if lookup.Code != 200 || lookup.Binding == nil {
		t.Fatalf("lookup by scene object failed: %#v", lookup)
	}
	if lookup.Binding.BusinessObjectId != "gh-tomato-001" {
		t.Fatalf("businessObjectId = %q, want gh-tomato-001", lookup.Binding.BusinessObjectId)
	}
	if lookup.Object == nil || lookup.Object.ID != "gh-tomato-001" {
		t.Fatalf("lookup did not include bound agricultural object: %#v", lookup.Object)
	}
	if !lookup.Binding.IsDefaultBinding {
		t.Fatalf("binding should preserve default flag")
	}
}

func TestSceneBusinessBindingSupportsMultipleSceneObjectsForOneBusinessObject(t *testing.T) {
	sceneStore := newMemorySceneBindingStore([]vo.SceneModelVo{
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "tomato-demo", ModelId: 1}, SceneObjectId: "scene-gh-shell", BusinessObjectId: "gh-tomato-001", AssetKey: "greenhouse", IsDefaultBinding: true},
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "tomato-demo", ModelId: 2}, SceneObjectId: "scene-gh-interior", BusinessObjectId: "gh-tomato-001", AssetKey: "greenhouse", IsDefaultBinding: false},
	})
	objectSvc := seededAgriculturalObjectService(t)
	svc := NewSceneBusinessBindingService(sceneStore, objectSvc)

	lookup := svc.LookupByBusinessObject("tomato-demo", "gh-tomato-001")
	if lookup.Code != 200 {
		t.Fatalf("lookup by business object failed: %#v", lookup)
	}
	if len(lookup.Bindings) != 2 {
		t.Fatalf("bindings count = %d, want 2: %#v", len(lookup.Bindings), lookup.Bindings)
	}
	if lookup.Bindings[0].SceneObjectId != "scene-gh-shell" || !lookup.Bindings[0].IsDefaultBinding {
		t.Fatalf("default binding should be first: %#v", lookup.Bindings)
	}
}

func TestSceneBusinessBindingUsesStableFallbackIdAndCanClearBinding(t *testing.T) {
	sceneStore := newMemorySceneBindingStore([]vo.SceneModelVo{
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "番茄温室", ModelId: 7}, AssetKey: "sensor", URL: "/scene-assets/models/sensor.glb"},
	})
	objectSvc := seededAgriculturalObjectService(t)
	svc := NewSceneBusinessBindingService(sceneStore, objectSvc)
	sceneObjectId := FallbackSceneObjectID("番茄温室", 7)

	update := svc.UpdateBinding(vo.SceneBindingUpdateRequest{
		SceneName:        "番茄温室",
		SceneObjectId:    sceneObjectId,
		BusinessObjectId: "sensor-greenhouse-001",
		AssetKey:         "sensor",
	})
	if update.Code != 200 {
		t.Fatalf("fallback id update failed: %#v", update)
	}

	cleared := svc.ClearBinding("番茄温室", sceneObjectId)
	if cleared.Code != 200 {
		t.Fatalf("clear binding failed: %#v", cleared)
	}

	lookup := svc.LookupBySceneObject("番茄温室", sceneObjectId)
	if lookup.Code != 200 || lookup.Binding == nil {
		t.Fatalf("lookup after clear failed: %#v", lookup)
	}
	if lookup.Binding.SceneObjectId != sceneObjectId {
		t.Fatalf("sceneObjectId should remain stable after clear: %#v", lookup.Binding)
	}
	if lookup.Binding.BusinessObjectId != "" || lookup.Binding.IsDefaultBinding {
		t.Fatalf("binding should be cleared but scene object kept: %#v", lookup.Binding)
	}
}

func TestSceneBusinessBindingValidationReportsMissingBusinessDataAndAssetMetadata(t *testing.T) {
	sceneStore := newMemorySceneBindingStore([]vo.SceneModelVo{
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "tomato-demo", ModelId: 0}, SceneObjectId: "scene-gh", BusinessObjectId: "gh-tomato-001", AssetKey: "greenhouse"},
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "tomato-demo", ModelId: 1}, SceneObjectId: "scene-parcel", BusinessObjectId: "parcel-tomato-a"},
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "tomato-demo", ModelId: 2}, SceneObjectId: "scene-plant", AssetKey: "tomato"},
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "tomato-demo", ModelId: 3}, SceneObjectId: "scene-sensor", BusinessObjectId: "sensor-greenhouse-001", AssetKey: "sensor"},
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "tomato-demo", ModelId: 4}, SceneObjectId: "scene-device", BusinessObjectId: "device-irrigation-001", AssetKey: "irrigation"},
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "tomato-demo", ModelId: 5}, SceneObjectId: "scene-camera", BusinessObjectId: "camera-greenhouse-001", AssetKey: "camera"},
	})
	objectSvc := seededAgriculturalObjectService(t)
	svc := NewSceneBusinessBindingService(sceneStore, objectSvc)

	report := svc.ValidateScene("tomato-demo")
	if report.Code != 200 {
		t.Fatalf("validation failed: %#v", report)
	}
	if report.Summary.TotalSceneObjects != 6 || report.Summary.BoundSceneObjects != 5 {
		t.Fatalf("unexpected validation counts: %#v", report.Summary)
	}
	assertHasIssue(t, report.Summary.Issues, "missing_business_binding", "scene-plant")
	assertHasIssue(t, report.Summary.Issues, "missing_data_binding", "scene-camera")
	assertHasIssue(t, report.Summary.Issues, "missing_asset_metadata", "scene-parcel")
	if len(report.Summary.MissingObjectTypes) != 1 || report.Summary.MissingObjectTypes[0] != "Plant" {
		t.Fatalf("missing object types = %#v, want Plant only", report.Summary.MissingObjectTypes)
	}
}

func TestSceneBusinessBindingValidationReportsAssetGovernanceIssues(t *testing.T) {
	sceneStore := newMemorySceneBindingStore([]vo.SceneModelVo{
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "tomato-demo", ModelId: 1}, SceneObjectId: "scene-camera", BusinessObjectId: "camera-greenhouse-001", AssetKey: "camera"},
	})
	objectSvc := seededAgriculturalObjectService(t)
	svc := NewSceneBusinessBindingService(sceneStore, objectSvc)

	report := svc.ValidateScene("tomato-demo")
	if report.Code != 200 {
		t.Fatalf("validation failed: %#v", report)
	}
	for _, category := range []string{"missing_asset_thumbnail", "missing_asset_source", "missing_asset_license", "asset_quality_issue"} {
		assertHasIssue(t, report.Summary.Issues, category, "scene-camera")
	}
}

func TestSceneBusinessBindingValidationVerifiesSixCoreObjectTypes(t *testing.T) {
	sceneStore := newMemorySceneBindingStore([]vo.SceneModelVo{
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "tomato-demo", ModelId: 0}, SceneObjectId: "scene-gh", BusinessObjectId: "gh-tomato-001", AssetKey: "greenhouse"},
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "tomato-demo", ModelId: 1}, SceneObjectId: "scene-parcel", BusinessObjectId: "parcel-tomato-a", AssetKey: "parcel"},
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "tomato-demo", ModelId: 2}, SceneObjectId: "scene-plant", BusinessObjectId: "plant-tomato-001", AssetKey: "tomato"},
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "tomato-demo", ModelId: 3}, SceneObjectId: "scene-sensor", BusinessObjectId: "sensor-greenhouse-001", AssetKey: "sensor"},
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "tomato-demo", ModelId: 4}, SceneObjectId: "scene-device", BusinessObjectId: "device-irrigation-001", AssetKey: "irrigation"},
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: "tomato-demo", ModelId: 5}, SceneObjectId: "scene-camera", BusinessObjectId: "camera-greenhouse-001", AssetKey: "camera"},
	})
	objectSvc := seededAgriculturalObjectService(t)
	svc := NewSceneBusinessBindingService(sceneStore, objectSvc)

	report := svc.ValidateScene("tomato-demo")
	if report.Code != 200 {
		t.Fatalf("validation failed: %#v", report)
	}
	wantTypes := []string{"Greenhouse", "Parcel", "Plant", "Sensor", "Device", "Camera"}
	if !sameStringSet(report.Summary.VerifiedObjectTypes, wantTypes) {
		t.Fatalf("verified types = %#v, want %#v", report.Summary.VerifiedObjectTypes, wantTypes)
	}
	if len(report.Summary.MissingObjectTypes) != 0 {
		t.Fatalf("missing object types = %#v, want none", report.Summary.MissingObjectTypes)
	}
}

func TestSceneBusinessBindingAcceptsCanonicalSceneNameForMojibakeLegacyRows(t *testing.T) {
	legacySceneName := mojibakeSceneName("番茄温室 MVP")
	sceneStore := newMemorySceneBindingStore([]vo.SceneModelVo{
		{SceneModelVoKey: vo.SceneModelVoKey{SceneName: legacySceneName, ModelId: 0}, SceneObjectId: "scene-gh-tomato-001", BusinessObjectId: "gh-tomato-001", AssetKey: "greenhouse"},
	})
	objectSvc := seededAgriculturalObjectService(t)
	svc := NewSceneBusinessBindingService(sceneStore, objectSvc)

	lookup := svc.LookupBySceneObject("番茄温室 MVP", "scene-gh-tomato-001")
	if lookup.Code != 200 || lookup.Binding == nil {
		t.Fatalf("lookup by canonical scene name failed for legacy row: %#v", lookup)
	}
	if lookup.Binding.SceneName != legacySceneName {
		t.Fatalf("binding should preserve stored legacy scene name, got %q want %q", lookup.Binding.SceneName, legacySceneName)
	}

	report := svc.ValidateScene("番茄温室 MVP")
	if report.Code != 200 {
		t.Fatalf("validation failed for canonical scene name: %#v", report)
	}
	if report.Summary.TotalSceneObjects != 1 || report.Summary.BoundSceneObjects != 1 {
		t.Fatalf("unexpected validation counts: %#v", report.Summary)
	}
}

func seededAgriculturalObjectService(t *testing.T) *AgriculturalObjectService {
	t.Helper()
	objectSvc := NewAgriculturalObjectServiceWithStore(NewMemoryAgriculturalObjectStore())
	if err := objectSvc.SeedTomatoGreenhouseMVP(); err != nil {
		t.Fatalf("seed objects failed: %v", err)
	}
	return objectSvc
}

func assertHasIssue(t *testing.T, issues []vo.SceneBindingValidationIssueVo, category string, sceneObjectId string) {
	t.Helper()
	for _, issue := range issues {
		if issue.Category == category && issue.SceneObjectId == sceneObjectId {
			return
		}
	}
	t.Fatalf("missing issue category=%s sceneObjectId=%s in %#v", category, sceneObjectId, issues)
}

func sameStringSet(got []string, want []string) bool {
	if len(got) != len(want) {
		return false
	}
	seen := map[string]int{}
	for _, item := range got {
		seen[item]++
	}
	for _, item := range want {
		if seen[item] != 1 {
			return false
		}
	}
	return true
}

func mojibakeSceneName(value string) string {
	return utf8BytesAsWindows1252Text(value)
}

type memorySceneBindingStore struct {
	models []vo.SceneModelVo
}

func newMemorySceneBindingStore(models []vo.SceneModelVo) *memorySceneBindingStore {
	copied := make([]vo.SceneModelVo, len(models))
	copy(copied, models)
	return &memorySceneBindingStore{models: copied}
}

func (s *memorySceneBindingStore) ListSceneModels(sceneName string) ([]vo.SceneModelVo, error) {
	result := make([]vo.SceneModelVo, 0)
	for _, model := range s.models {
		if model.SceneName == sceneName {
			result = append(result, model)
		}
	}
	return result, nil
}

func (s *memorySceneBindingStore) UpdateSceneModelBinding(sceneName string, modelId int, sceneObjectId string, businessObjectId string, assetKey string, isDefaultBinding bool) (int, error) {
	for i := range s.models {
		if s.models[i].SceneName == sceneName && s.models[i].ModelId == modelId {
			s.models[i].SceneObjectId = sceneObjectId
			s.models[i].BusinessObjectId = businessObjectId
			s.models[i].AssetKey = assetKey
			s.models[i].IsDefaultBinding = isDefaultBinding
			return 1, nil
		}
	}
	return 0, nil
}

func (s *memorySceneBindingStore) ClearSceneModelBinding(sceneName string, modelId int, sceneObjectId string) (int, error) {
	for i := range s.models {
		if s.models[i].SceneName == sceneName && s.models[i].ModelId == modelId {
			s.models[i].SceneObjectId = sceneObjectId
			s.models[i].BusinessObjectId = ""
			s.models[i].IsDefaultBinding = false
			return 1, nil
		}
	}
	return 0, nil
}
