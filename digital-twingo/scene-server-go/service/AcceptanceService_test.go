package service

import "testing"

func TestTomatoGreenhouseAcceptanceBuildsMVPCounts(t *testing.T) {
	svc := NewAcceptanceServiceForTest()

	result, err := svc.TomatoGreenhouseAcceptance()
	if err != nil {
		t.Fatalf("acceptance failed: %v", err)
	}

	if result.Prompt != TomatoGreenhouseAcceptancePrompt {
		t.Fatalf("prompt = %q, want %q", result.Prompt, TomatoGreenhouseAcceptancePrompt)
	}
	want := map[string]int{
		"tomato":          20,
		"greenhouse":      1,
		"weather_station": 1,
		"irrigation":      1,
		"camera":          1,
		"sensor":          1,
	}
	for assetKey, expected := range want {
		actual, ok := result.ModelCounts[assetKey]
		if !ok {
			t.Fatalf("missing model count for %s in %#v", assetKey, result.ModelCounts)
		}
		if actual.Actual != expected || actual.Expected != expected || !actual.Passed {
			t.Fatalf("count %s = %#v, want expected/actual %d and passed", assetKey, actual, expected)
		}
	}
	if !result.OverallPassed {
		t.Fatalf("overall acceptance should pass, issues=%#v steps=%#v", result.Issues, result.Steps)
	}
}

func TestTomatoGreenhouseAcceptanceIncludesTraceRoutingValidationAndReport(t *testing.T) {
	svc := NewAcceptanceServiceForTest()

	result, err := svc.TomatoGreenhouseAcceptance()
	if err != nil {
		t.Fatalf("acceptance failed: %v", err)
	}

	if result.SemanticBuild.AgentTrace == nil || len(result.SemanticBuild.AgentTrace.Steps) == 0 {
		t.Fatalf("acceptance should include agent trace steps: %#v", result.SemanticBuild.AgentTrace)
	}
	for _, key := range []string{"camera", "sensor"} {
		asset := findAcceptanceMissingAsset(result.SemanticBuild.MissingAssets, key)
		if asset == nil || asset.Routing == nil || asset.Generation == nil || asset.Generation.TaskID == "" {
			t.Fatalf("missing asset %s should include routing and generation task: %#v", key, asset)
		}
	}
	if result.BindingValidation.Summary.TotalSceneObjects == 0 || result.BindingValidation.Summary.BindingRate < 90 {
		t.Fatalf("binding validation should show demo scene readiness: %#v", result.BindingValidation.Summary)
	}
	if result.GreenhouseObject == nil || result.GreenhouseObject.ID != "gh-tomato-001" {
		t.Fatalf("greenhouse object missing: %#v", result.GreenhouseObject)
	}
	if result.AbnormalDevice == nil || result.AbnormalDevice.ID != "device-irrigation-001" {
		t.Fatalf("abnormal device context missing: %#v", result.AbnormalDevice)
	}
	if result.ReportSource.ObjectID != "gh-tomato-001" || len(result.ReportSource.Recommendations) == 0 {
		t.Fatalf("report source should include greenhouse recommendations: %#v", result.ReportSource)
	}
	if len(result.SuccessMetrics) < 6 {
		t.Fatalf("success metrics incomplete: %#v", result.SuccessMetrics)
	}
	if !result.ArchiveReadiness.Ready {
		t.Fatalf("archive readiness should be true after Phase 1-5 completion: %#v", result.ArchiveReadiness)
	}
	if !acceptanceHasPassedStep(result, "semantic-build") || !acceptanceHasPassedStep(result, "greenhouse-report") {
		t.Fatalf("required acceptance steps missing or failed: %#v", result.Steps)
	}
}

func findAcceptanceMissingAsset(items []AcceptanceMissingAssetVo, assetKey string) *AcceptanceMissingAssetVo {
	for i := range items {
		if items[i].AssetKey == assetKey {
			return &items[i]
		}
	}
	return nil
}

func acceptanceHasPassedStep(result TomatoGreenhouseAcceptanceVo, key string) bool {
	for _, step := range result.Steps {
		if step.Key == key && step.Passed {
			return true
		}
	}
	return false
}
