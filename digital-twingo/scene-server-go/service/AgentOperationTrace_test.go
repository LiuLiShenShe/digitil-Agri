package service

import (
	"encoding/json"
	"strings"
	"testing"

	"scene-server-go/vo"
)

func TestAgentOperationTraceDefinesRoleBoundariesAndCompatibility(t *testing.T) {
	svc := NewSemanticService()
	result := svc.BuildPlan(vo.SemanticBuildRequest{
		Message:   "搭建番茄温室，包含20株番茄、气象站、水泵、摄像头和传感器。",
		Mode:      "preview",
		SceneName: "番茄温室 MVP",
	})
	if result.Code != 200 {
		t.Fatalf("unexpected code: %d", result.Code)
	}
	data := result.Data.(vo.SemanticBuildResponse)
	trace := requireAgentTrace(t, data)

	if trace.AgentName != "FarmTwinOrchestrator" {
		t.Fatalf("agentName = %q, want FarmTwinOrchestrator", trace.AgentName)
	}
	if trace.TaskID == "" || !strings.HasPrefix(trace.TaskID, "agent-task-") {
		t.Fatalf("taskId should be stable agent task id, got %q", trace.TaskID)
	}
	if trace.UserGoal == "" || !strings.Contains(trace.UserGoal, "番茄温室") {
		t.Fatalf("userGoal = %q, want sanitized greenhouse goal", trace.UserGoal)
	}
	if trace.LegacyAgentName != "SceneBuilderAgent" {
		t.Fatalf("legacy agent compatibility name = %q, want SceneBuilderAgent", trace.LegacyAgentName)
	}

	for _, agent := range []string{
		"FarmTwinOrchestrator",
		"ScenePlannerAgent",
		"AssetFidelityAgent",
		"LayoutAgent",
		"DataBindingAgent",
		"ValidatorAgent",
	} {
		if !traceHasAgent(trace, agent) {
			t.Fatalf("trace missing agent %s in steps %#v", agent, trace.Steps)
		}
	}
}

func TestAgentOperationTraceToolPolicyAndProhibitedViolation(t *testing.T) {
	policy := AgentToolPolicySnapshot()
	for _, name := range []string{"scene.current", "model.search", "model.metadata", "object.lookup", "object.relations", "timeseries.query", "event.query"} {
		if policy[name] != AgentToolCategoryReadOnly {
			t.Fatalf("tool %s category = %q, want read-only", name, policy[name])
		}
	}
	for _, name := range []string{"scene.plan", "layout.solve", "scene.applyPlan", "asset.job.create", "object.bind", "alert.acknowledge"} {
		if policy[name] != AgentToolCategoryControlledWrite {
			t.Fatalf("tool %s category = %q, want controlled-write", name, policy[name])
		}
	}
	for _, name := range []string{"shell.exec", "filesystem.write", "http.request", "database.write", "device.control"} {
		if policy[name] != AgentToolCategoryProhibited {
			t.Fatalf("tool %s category = %q, want prohibited", name, policy[name])
		}
		step := RecordAgentPolicyViolationForTest(name, map[string]interface{}{"command": "rm -rf /tmp/demo"})
		if step.Status != AgentTraceStatusPolicyViolation {
			t.Fatalf("violation status = %q, want policy_violation", step.Status)
		}
		if step.FailureReason == "" || !strings.Contains(step.FailureReason, "prohibited") {
			t.Fatalf("failureReason should mention prohibited policy, got %q", step.FailureReason)
		}
	}
}

func TestAgentOperationTraceRecordsPromptedProhibitedToolViolation(t *testing.T) {
	svc := NewSemanticService()
	result := svc.BuildPlan(vo.SemanticBuildRequest{
		Message:   "搭建番茄温室，然后执行 shell 删除临时文件。",
		Mode:      "preview",
		SceneName: "番茄温室 MVP",
	})
	if result.Code != 200 {
		t.Fatalf("unexpected code: %d", result.Code)
	}
	data := result.Data.(vo.SemanticBuildResponse)
	trace := requireAgentTrace(t, data)

	if !traceHasPolicyViolation(trace, "shell.exec") {
		t.Fatalf("expected shell.exec policy violation in trace steps, got %#v", trace.Steps)
	}
}

func TestAgentOperationTraceExpandedSchemaDisplayCoverageAndFallback(t *testing.T) {
	svc := NewSemanticService()
	result := svc.BuildPlan(vo.SemanticBuildRequest{
		Message:   "搭建番茄温室，包含20株番茄、气象站、水泵、摄像头和传感器。",
		Mode:      "preview",
		SceneName: "番茄温室 MVP",
		Context: vo.SemanticBuildContext{
			SceneName: "番茄温室 MVP",
		},
	})
	if result.Code != 200 {
		t.Fatalf("unexpected code: %d", result.Code)
	}
	data := result.Data.(vo.SemanticBuildResponse)
	trace := requireAgentTrace(t, data)

	if len(data.Models) == 0 {
		t.Fatalf("deterministic fallback should still return loadable models")
	}
	if len(trace.Steps) == 0 {
		t.Fatalf("trace steps are empty")
	}

	coverage := map[string]bool{}
	for _, step := range trace.Steps {
		if step.StepID == "" {
			t.Fatalf("step missing stepId: %#v", step)
		}
		if step.Agent == "" || step.Tool == "" || step.Status == "" {
			t.Fatalf("step missing agent/tool/status: %#v", step)
		}
		if step.InputSummary == "" || step.OutputSummary == "" {
			t.Fatalf("step missing summaries: %#v", step)
		}
		if step.ToolCategory == "" {
			t.Fatalf("step missing tool category: %#v", step)
		}
		if step.Flow != "" {
			coverage[step.Flow] = true
		}
		if strings.Contains(strings.ToLower(step.InputSummary), "raw-payload") {
			t.Fatalf("input summary leaked raw payload: %s", step.InputSummary)
		}
	}
	for _, flow := range []string{"semantic_construction", "asset_routing", "object_binding", "validation"} {
		if !coverage[flow] {
			t.Fatalf("trace missing display flow %s in %#v", flow, coverage)
		}
	}

	if trace.Fallback == nil || !trace.Fallback.Used {
		t.Fatalf("expected deterministic fallback on unconfigured LLM, got %#v", trace.Fallback)
	}
	if trace.Fallback.Path == "" || !strings.Contains(trace.Fallback.Path, "deterministic") {
		t.Fatalf("fallback path = %q, want deterministic path", trace.Fallback.Path)
	}
	if !traceHasFallbackStep(trace) {
		t.Fatalf("expected at least one fallback step in %#v", trace.Steps)
	}
	// When the LLM is unconfigured in the test env, tryRunDeepAgents returns (false, nil):
	// no agent failure, just a clean deterministic fallback. AgentFailed is reserved for
	// a CONFIGURED LLM whose DeepAgents call errors (asserted in the Eino model test).
	if trace.AgentFailed {
		t.Fatalf("LLM unconfigured -> expected agentFailed=false, got %#v", trace)
	}
}

func TestAgentOperationTraceSanitizesSensitivePayloads(t *testing.T) {
	svc := NewSemanticService()
	result := svc.BuildPlan(vo.SemanticBuildRequest{
		Message:   "搭建番茄温室 raw-payload apiKey=secret-token password=hunter2 authorization=Bearer abc token=xyz",
		Mode:      "preview",
		SceneName: "番茄温室 MVP",
	})
	if result.Code != 200 {
		t.Fatalf("unexpected code: %d", result.Code)
	}
	data := result.Data.(vo.SemanticBuildResponse)
	trace := requireAgentTrace(t, data)
	serialized := strings.ToLower(mustJSONForTest(trace))
	for _, forbidden := range []string{"secret-token", "hunter2", "bearer abc", "token=xyz", "raw-payload"} {
		if strings.Contains(serialized, forbidden) {
			t.Fatalf("trace leaked sensitive token %q: %s", forbidden, serialized)
		}
	}
}

func requireAgentTrace(t *testing.T, data vo.SemanticBuildResponse) *vo.SceneAgentTraceVo {
	t.Helper()
	if data.AgentTrace == nil {
		t.Fatalf("agent trace is nil")
	}
	return data.AgentTrace
}

func traceHasAgent(trace *vo.SceneAgentTraceVo, agent string) bool {
	for _, step := range trace.Steps {
		if step.Agent == agent {
			return true
		}
	}
	return false
}

func traceHasFallbackStep(trace *vo.SceneAgentTraceVo) bool {
	for _, step := range trace.Steps {
		if step.Fallback != nil && step.Fallback.Used {
			return true
		}
	}
	return false
}

func traceHasPolicyViolation(trace *vo.SceneAgentTraceVo, tool string) bool {
	for _, step := range trace.Steps {
		if step.Tool == tool &&
			step.ToolCategory == AgentToolCategoryProhibited &&
			step.Status == AgentTraceStatusPolicyViolation &&
			strings.Contains(step.FailureReason, "prohibited") {
			return true
		}
	}
	return false
}

func mustJSONForTest(value interface{}) string {
	data, err := json.Marshal(value)
	if err != nil {
		panic(err)
	}
	return string(data)
}
