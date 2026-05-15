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
