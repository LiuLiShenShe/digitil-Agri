package service

import (
	"strings"
	"testing"

	"scene-server-go/vo"
)

func TestRulePlanMapsGreenhouseSynonyms(t *testing.T) {
	svc := NewSemanticService()
	result := svc.BuildPlan(vo.SemanticBuildRequest{
		Message: "搭一个玻璃房园区，右侧三个大棚，中央放气象站。",
		Mode:    "preview",
	})
	if result.Code != 200 {
		t.Fatalf("unexpected code: %d", result.Code)
	}

	data, ok := result.Data.(vo.SemanticBuildResponse)
	if !ok {
		t.Fatalf("unexpected data type: %T", result.Data)
	}

	found := false
	for _, obj := range data.ScenePlan.Objects {
		if obj.AssetKey == "greenhouse" {
			found = true
			if obj.Count != 3 {
				t.Fatalf("greenhouse count = %d, want 3", obj.Count)
			}
		}
	}
	if !found {
		t.Fatalf("greenhouse object not found: %#v", data.ScenePlan.Objects)
	}
}

func TestSceneBuilderAgentReturnsTraceAndWhitelistTools(t *testing.T) {
	svc := NewSemanticService()
	result := svc.BuildPlan(vo.SemanticBuildRequest{
		Message: "搭一个智慧农业示范园区，左侧六块玉米地，右侧三个温室，中间一条道路。",
		Mode:    "preview",
	})
	if result.Code != 200 {
		t.Fatalf("unexpected code: %d", result.Code)
	}

	data, ok := result.Data.(vo.SemanticBuildResponse)
	if !ok {
		t.Fatalf("unexpected data type: %T", result.Data)
	}
	if data.AgentTrace == nil {
		t.Fatalf("agent trace is nil")
	}
	if data.ScenePlan.SceneName != "智慧农业示范园区" {
		t.Fatalf("sceneName = %s, want 智慧农业示范园区", data.ScenePlan.SceneName)
	}

	allowed := map[string]bool{}
	for _, name := range sceneAgentToolWhitelist {
		allowed[name] = true
	}
	for _, call := range data.AgentTrace.Tools {
		if !allowed[call.Name] {
			t.Fatalf("unexpected tool call: %s", call.Name)
		}
	}
}

func TestSemanticTomatoPromptHonorsExplicitMVPCounts(t *testing.T) {
	svc := NewSemanticService()
	result := svc.BuildPlan(vo.SemanticBuildRequest{
		Message:  TomatoGreenhouseAcceptancePrompt,
		Mode:     "preview",
		OwnerKey: "phase6-semantic-counts",
	})
	if result.Code != 200 {
		t.Fatalf("unexpected code: %d", result.Code)
	}

	data, ok := result.Data.(vo.SemanticBuildResponse)
	if !ok {
		t.Fatalf("unexpected data type: %T", result.Data)
	}

	counts := semanticModelCounts(data.Models)
	want := map[string]int{
		"tomato":          20,
		"greenhouse":      1,
		"weather_station": 1,
		"irrigation":      1,
		"camera":          1,
		"sensor":          1,
	}
	for assetKey, expected := range want {
		if counts[assetKey] != expected {
			t.Fatalf("%s count = %d, want %d; all counts=%#v plan=%#v", assetKey, counts[assetKey], expected, counts, data.ScenePlan.Objects)
		}
	}
	for _, missingKey := range []string{"camera", "sensor"} {
		missing := findMissingAsset(data.MissingAssets, missingKey)
		if missing == nil {
			t.Fatalf("missing asset %s not found: %#v", missingKey, data.MissingAssets)
		}
		if missing.Generation == nil || missing.Generation.TaskID == "" {
			t.Fatalf("missing asset %s should expose generation task: %#v", missingKey, missing)
		}
	}
}

func TestMissingAssetsBecomePlaceholdersAndGenerationWorkflow(t *testing.T) {
	svc := NewSemanticService()
	result := svc.BuildPlan(vo.SemanticBuildRequest{
		Message: "创建标准温室场景，两个大棚纵向排列，每个大棚旁边放灌溉设备，入口放摄像头。",
		Mode:    "preview",
	})
	if result.Code != 200 {
		t.Fatalf("unexpected code: %d", result.Code)
	}

	data, ok := result.Data.(vo.SemanticBuildResponse)
	if !ok {
		t.Fatalf("unexpected data type: %T", result.Data)
	}

	var cameraMissing *vo.MissingAssetVo
	for i := range data.MissingAssets {
		if data.MissingAssets[i].AssetKey == "camera" {
			cameraMissing = &data.MissingAssets[i]
			break
		}
	}
	if cameraMissing == nil {
		t.Fatalf("camera missing asset not found: %#v", data.MissingAssets)
	}
	if cameraMissing.Generation == nil || cameraMissing.Generation.Status != missingGenerationStatusQueued || cameraMissing.Generation.TaskID == "" {
		t.Fatalf("generation workflow not initialized: %#v", cameraMissing.Generation)
	}
	if cameraMissing.ReferenceImage == nil || cameraMissing.ReferenceImage.Status == missingReferenceStatusMissing {
		t.Fatalf("reference image status = %#v, want resolved/generated", cameraMissing.ReferenceImage)
	}
	if len(cameraMissing.PlacementRefs) == 0 {
		t.Fatalf("missing asset has no placement refs")
	}

	foundPlaceholder := false
	for _, model := range data.Models {
		if model.Meta.Placeholder && model.Meta.MissingAssetKey == "camera" {
			foundPlaceholder = true
			if model.URL == "" {
				t.Fatalf("placeholder model url is empty")
			}
		}
	}
	if !foundPlaceholder {
		t.Fatalf("camera placeholder model not found: %#v", data.Models)
	}
}

func TestLLMResponseValidationRejectsUnknownAsset(t *testing.T) {
	svc := NewSemanticService()
	raw := `{
		"scenePlan": {
			"sceneName": "测试场景",
			"intent": "测试",
			"units": "platform",
			"mode": "preview",
			"ground": { "width": 900, "height": 900, "color": "#88aa66", "terrain": "field" },
			"objects": [
				{
					"id": "bad_group",
					"label": "未知资产",
					"category": "facility",
					"assetKey": "unknown_asset",
					"url": "",
					"count": 1,
					"layout": "single",
					"area": "center",
					"scale": 1,
					"size": { "width": 50, "depth": 50 }
				}
			],
			"relations": []
		},
		"missingAssets": [],
		"warnings": []
	}`

	_, err := svc.parseSemanticLLMResponse(raw, semanticCatalog())
	if err == nil || !strings.Contains(err.Error(), "unknown assetKey") {
		t.Fatalf("expected unknown assetKey error, got %v", err)
	}
}

func TestLLMResponseBackfillsAssetMetadata(t *testing.T) {
	svc := NewSemanticService()
	raw := `{
		"scenePlan": {
			"sceneName": "测试温室",
			"intent": "搭一个大棚",
			"units": "platform",
			"mode": "preview",
			"ground": { "width": 900, "height": 900, "color": "#88aa66", "terrain": "field" },
			"objects": [
				{
					"id": "",
					"label": "",
					"category": "",
					"assetKey": "大棚",
					"url": "",
					"count": 2,
					"layout": "column",
					"area": "east",
					"scale": 0,
					"size": { "width": 0, "depth": 0 }
				}
			],
			"relations": []
		},
		"missingAssets": [],
		"warnings": []
	}`

	parsed, err := svc.parseSemanticLLMResponse(raw, semanticCatalog())
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	obj := parsed.ScenePlan.Objects[0]
	if obj.AssetKey != "greenhouse" {
		t.Fatalf("assetKey = %s, want greenhouse", obj.AssetKey)
	}
	if obj.URL == "" || obj.Category == "" || obj.Scale <= 0 || obj.Size.Width <= 0 {
		t.Fatalf("asset metadata not backfilled: %#v", obj)
	}
}

func TestLLMResponseResolvesModelFileNameToCatalogAsset(t *testing.T) {
	svc := NewSemanticService()
	raw := `{
		"scenePlan": {
			"sceneName": "测试玉米地",
			"intent": "放几块玉米田",
			"units": "platform",
			"mode": "preview",
			"ground": { "width": 900, "height": 900, "color": "#88aa66", "terrain": "field" },
			"objects": [
				{
					"id": "",
					"label": "Corn Crop",
					"category": "",
					"assetKey": "Corn_Crop.glb",
					"url": "./models/crops/Corn_Crop.glb",
					"count": 3,
					"layout": "grid",
					"area": "west",
					"scale": 0,
					"size": { "width": 0, "depth": 0 }
				}
			],
			"relations": []
		},
		"missingAssets": [],
		"warnings": []
	}`

	parsed, err := svc.parseSemanticLLMResponse(raw, semanticCatalog())
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	obj := parsed.ScenePlan.Objects[0]
	if obj.AssetKey != "corn" {
		t.Fatalf("assetKey = %s, want corn", obj.AssetKey)
	}
	if obj.URL != "/scene-assets/models/Corn_Crop.glb" {
		t.Fatalf("url = %s, want catalog URL", obj.URL)
	}
}

func semanticModelCounts(models []vo.BuildModel) map[string]int {
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

func findMissingAsset(items []vo.MissingAssetVo, assetKey string) *vo.MissingAssetVo {
	for i := range items {
		if items[i].AssetKey == assetKey {
			return &items[i]
		}
	}
	return nil
}
