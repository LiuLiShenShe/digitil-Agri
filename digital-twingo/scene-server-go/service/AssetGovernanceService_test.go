package service

import (
	"strings"
	"testing"

	"scene-server-go/vo"
)

func TestAssetRegistryReturnsGovernanceMetadataForManagedAsset(t *testing.T) {
	registry := NewAssetRegistryService()

	asset, ok := registry.Get("greenhouse")
	if !ok {
		t.Fatalf("greenhouse metadata not found")
	}

	if asset.AssetKey != "greenhouse" {
		t.Fatalf("assetKey = %q, want greenhouse", asset.AssetKey)
	}
	if asset.Category == "" || asset.Source == "" || asset.License == "" || asset.FidelityLevel == "" {
		t.Fatalf("basic governance fields are incomplete: %#v", asset)
	}
	if asset.ThumbnailURL == "" || asset.GLBURL == "" {
		t.Fatalf("asset should expose thumbnail and GLB URLs: %#v", asset)
	}
	if len(asset.ApplicableObjectTypes) == 0 {
		t.Fatalf("applicable object types should be present: %#v", asset)
	}
	if asset.Quality.Loadable != true || asset.Quality.Axis != "Y-up" || asset.Quality.UnitScale <= 0 {
		t.Fatalf("quality metadata is incomplete: %#v", asset.Quality)
	}
	if asset.Version.Version == "" || asset.Version.UpdatedAt == "" {
		t.Fatalf("version metadata is incomplete: %#v", asset.Version)
	}
}

func TestAssetQualityAuditFlagsIncompletePublicAssetMetadata(t *testing.T) {
	registry := NewAssetRegistryService()
	auditor := NewAssetQualityAuditService(registry)

	report := auditor.AuditAsset("camera")

	if report.AssetKey != "camera" {
		t.Fatalf("assetKey = %q, want camera", report.AssetKey)
	}
	if report.Complete {
		t.Fatalf("camera should be incomplete before generated GLB exists: %#v", report)
	}
	for _, code := range []string{"missing_thumbnail", "missing_source", "missing_license", "missing_quality"} {
		if !auditHasIssue(report, code) {
			t.Fatalf("missing audit issue %s in %#v", code, report.Issues)
		}
	}
}

func TestAssetFidelityRoutingChoosesExpectedStrategies(t *testing.T) {
	router := NewAssetFidelityRoutingService(NewAssetRegistryService())

	keyPlant := router.Decide(vo.AssetFidelityRoutingRequest{
		AssetKey:         "tomato",
		ObjectType:       string(vo.ObjectTypePlant),
		BusinessValue:    "research_sample",
		IsKeyPlant:       true,
		RequiredFidelity: "trustworthy_geometry",
	})
	if keyPlant.Strategy != "F2DMAS" && keyPlant.Strategy != "high_fidelity_reconstruction" {
		t.Fatalf("key plant strategy = %q, want F2DMAS/high_fidelity_reconstruction: %#v", keyPlant.Strategy, keyPlant)
	}
	if !strings.Contains(keyPlant.RoutingReason, "关键") {
		t.Fatalf("key plant routing reason should explain key plant decision: %q", keyPlant.RoutingReason)
	}

	missingEquipment := router.Decide(vo.AssetFidelityRoutingRequest{
		AssetKey:      "camera",
		ObjectType:    string(vo.ObjectTypeCamera),
		BusinessValue: "ordinary",
	})
	if missingEquipment.Strategy != "TRELLIS.2" {
		t.Fatalf("missing equipment strategy = %q, want TRELLIS.2: %#v", missingEquipment.Strategy, missingEquipment)
	}
	if !missingEquipment.RequiresGenerationTask {
		t.Fatalf("missing equipment should require generation task: %#v", missingEquipment)
	}

	procedural := router.Decide(vo.AssetFidelityRoutingRequest{
		AssetKey:      "fence",
		ObjectType:    "Fence",
		BusinessValue: "ordinary",
	})
	if procedural.Strategy != "procedural" {
		t.Fatalf("fence strategy = %q, want procedural: %#v", procedural.Strategy, procedural)
	}

	existing := router.Decide(vo.AssetFidelityRoutingRequest{
		AssetKey:      "greenhouse",
		ObjectType:    string(vo.ObjectTypeGreenhouse),
		BusinessValue: "ordinary",
	})
	if existing.Strategy != "existing_asset" || existing.SelectedAssetKey != "greenhouse" {
		t.Fatalf("greenhouse strategy = %#v, want existing asset", existing)
	}
}

func TestPlantGeometryVersionsContainFiveMilestoneStages(t *testing.T) {
	registry := NewAssetRegistryService()

	versions := registry.PlantGeometryVersions("plant-tomato-001")

	wantStages := []string{"seedling", "vegetative", "flowering", "fruiting", "mature"}
	if len(versions) != len(wantStages) {
		t.Fatalf("stage count = %d, want %d: %#v", len(versions), len(wantStages), versions)
	}
	for i, stage := range wantStages {
		if versions[i].Stage != stage {
			t.Fatalf("stage[%d] = %q, want %q", i, versions[i].Stage, stage)
		}
		if versions[i].GLBURL == "" || versions[i].PhenotypeBinding.MetricKey == "" {
			t.Fatalf("stage %s missing GLB or phenotype binding: %#v", stage, versions[i])
		}
	}
}

func TestSemanticPlanCreatesGenerationTaskAndRoutingReasonForMissingAsset(t *testing.T) {
	svc := NewSemanticService()

	result := svc.BuildPlan(vo.SemanticBuildRequest{
		Message:  "搭建番茄温室，包含20株番茄、气象站、水泵、摄像头和传感器。",
		Mode:     "preview",
		OwnerKey: "phase5-test",
	})
	if result.Code != 200 {
		t.Fatalf("unexpected code: %d", result.Code)
	}
	data := result.Data.(vo.SemanticBuildResponse)

	var camera *vo.MissingAssetVo
	for i := range data.MissingAssets {
		if data.MissingAssets[i].AssetKey == "camera" {
			camera = &data.MissingAssets[i]
			break
		}
	}
	if camera == nil {
		t.Fatalf("camera missing asset not found: %#v", data.MissingAssets)
	}
	if camera.Routing == nil || camera.Routing.Strategy != "TRELLIS.2" {
		t.Fatalf("camera routing missing or wrong: %#v", camera.Routing)
	}
	if camera.Generation == nil || camera.Generation.TaskID == "" {
		t.Fatalf("camera generation task should be created immediately: %#v", camera.Generation)
	}
	if camera.ReferenceImage == nil || camera.ReferenceImage.Status == "missing" {
		t.Fatalf("camera should have a reference image status for generation: %#v", camera.ReferenceImage)
	}

	for _, model := range data.Models {
		if model.Meta.Placeholder && model.Meta.MissingAssetKey == "camera" && model.Meta.GenerationTaskID == "" {
			t.Fatalf("placeholder should be linked to generated task: %#v", model)
		}
	}

	trace := data.AgentTrace
	if trace == nil {
		t.Fatalf("agent trace is nil")
	}
	foundReason := false
	for _, step := range trace.Steps {
		if step.Agent == "AssetFidelityAgent" && strings.Contains(step.OutputSummary, "TRELLIS.2") {
			foundReason = true
			break
		}
	}
	if !foundReason {
		t.Fatalf("AssetFidelityAgent trace should include asset routing reason: %#v", trace.Steps)
	}
}

func auditHasIssue(report vo.AssetQualityAuditReportVo, code string) bool {
	for _, issue := range report.Issues {
		if issue.Code == code {
			return true
		}
	}
	return false
}
