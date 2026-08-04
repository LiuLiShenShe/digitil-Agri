package service

import (
	"fmt"
	"regexp"
	"strings"
	"time"

	"scene-server-go/vo"
)

const (
	AgentToolCategoryReadOnly        = "read-only"
	AgentToolCategoryControlledWrite = "controlled-write"
	AgentToolCategoryProhibited      = "prohibited"

	AgentTraceStatusSuccess         = "success"
	AgentTraceStatusError           = "error"
	AgentTraceStatusPolicyViolation = "policy_violation"
)

const (
	agentFlowSemanticConstruction = "semantic_construction"
	agentFlowAssetRouting         = "asset_routing"
	agentFlowObjectBinding        = "object_binding"
	agentFlowValidation           = "validation"
)

type agentToolPolicy struct {
	Name     string
	Category string
	Agent    string
	Flow     string
}

type agentRoleDefinition struct {
	Name           string
	Responsibility string
	Tools          []string
}

var agentRoleRegistry = []agentRoleDefinition{
	{Name: "FarmTwinOrchestrator", Responsibility: "接收用户目标、拆解任务、组织 handoff 并汇总结果。", Tools: []string{"scene.current"}},
	{Name: "ScenePlannerAgent", Responsibility: "把用户目标转换为对象组级场景计划。", Tools: []string{"scene.current", "scene.plan"}},
	{Name: "AssetFidelityAgent", Responsibility: "检索模型资产、读取元数据并记录资产选择理由。", Tools: []string{"model.search", "model.metadata", "asset.job.create"}},
	{Name: "LayoutAgent", Responsibility: "把场景计划转换为可加载布局。", Tools: []string{"layout.solve"}},
	{Name: "DataBindingAgent", Responsibility: "查询农业对象关系并准备业务对象绑定。", Tools: []string{"object.lookup", "object.relations", "object.bind", "timeseries.query", "event.query"}},
	{Name: "TimeSeriesAgent", Responsibility: "按对象和时间范围查询时序指标。", Tools: []string{"timeseries.query"}},
	{Name: "GrowthAnalysisAgent", Responsibility: "基于对象记忆和时序摘要分析长势。", Tools: []string{"timeseries.query", "event.query"}},
	{Name: "AlertDiagnosisAgent", Responsibility: "解释告警并生成受控确认建议。", Tools: []string{"event.query", "alert.acknowledge"}},
	{Name: "ReportAgent", Responsibility: "汇总日报和运维建议的数据源。", Tools: []string{"timeseries.query", "event.query"}},
	{Name: "ValidatorAgent", Responsibility: "校验场景绑定、数据绑定、资产元数据和策略违规。", Tools: []string{"layout.validate"}},
}

var agentToolPolicies = map[string]agentToolPolicy{
	"scene.current":    {Name: "scene.current", Category: AgentToolCategoryReadOnly, Agent: "FarmTwinOrchestrator", Flow: agentFlowSemanticConstruction},
	"model.search":     {Name: "model.search", Category: AgentToolCategoryReadOnly, Agent: "AssetFidelityAgent", Flow: agentFlowAssetRouting},
	"model.metadata":   {Name: "model.metadata", Category: AgentToolCategoryReadOnly, Agent: "AssetFidelityAgent", Flow: agentFlowAssetRouting},
	"object.lookup":    {Name: "object.lookup", Category: AgentToolCategoryReadOnly, Agent: "DataBindingAgent", Flow: agentFlowObjectBinding},
	"object.relations": {Name: "object.relations", Category: AgentToolCategoryReadOnly, Agent: "DataBindingAgent", Flow: agentFlowObjectBinding},
	"timeseries.query": {Name: "timeseries.query", Category: AgentToolCategoryReadOnly, Agent: "TimeSeriesAgent", Flow: agentFlowObjectBinding},
	"event.query":      {Name: "event.query", Category: AgentToolCategoryReadOnly, Agent: "ReportAgent", Flow: agentFlowObjectBinding},

	"scene.plan":        {Name: "scene.plan", Category: AgentToolCategoryControlledWrite, Agent: "ScenePlannerAgent", Flow: agentFlowSemanticConstruction},
	"layout.solve":      {Name: "layout.solve", Category: AgentToolCategoryControlledWrite, Agent: "LayoutAgent", Flow: agentFlowSemanticConstruction},
	"scene.applyPlan":   {Name: "scene.applyPlan", Category: AgentToolCategoryControlledWrite, Agent: "FarmTwinOrchestrator", Flow: agentFlowSemanticConstruction},
	"asset.job.create":  {Name: "asset.job.create", Category: AgentToolCategoryControlledWrite, Agent: "AssetFidelityAgent", Flow: agentFlowAssetRouting},
	"object.bind":       {Name: "object.bind", Category: AgentToolCategoryControlledWrite, Agent: "DataBindingAgent", Flow: agentFlowObjectBinding},
	"alert.acknowledge": {Name: "alert.acknowledge", Category: AgentToolCategoryControlledWrite, Agent: "AlertDiagnosisAgent", Flow: agentFlowValidation},
	"layout.validate":   {Name: "layout.validate", Category: AgentToolCategoryControlledWrite, Agent: "ValidatorAgent", Flow: agentFlowValidation},

	"shell.exec":       {Name: "shell.exec", Category: AgentToolCategoryProhibited, Agent: "ValidatorAgent", Flow: agentFlowValidation},
	"filesystem.write": {Name: "filesystem.write", Category: AgentToolCategoryProhibited, Agent: "ValidatorAgent", Flow: agentFlowValidation},
	"http.request":     {Name: "http.request", Category: AgentToolCategoryProhibited, Agent: "ValidatorAgent", Flow: agentFlowValidation},
	"database.write":   {Name: "database.write", Category: AgentToolCategoryProhibited, Agent: "ValidatorAgent", Flow: agentFlowValidation},
	"device.control":   {Name: "device.control", Category: AgentToolCategoryProhibited, Agent: "ValidatorAgent", Flow: agentFlowValidation},
}

var sensitiveTracePatterns = []*regexp.Regexp{
	regexp.MustCompile(`(?i)raw-payload[^\s,"']*`),
	regexp.MustCompile(`(?i)(api[_-]?key|authorization|password|token)\s*[:=]\s*[^,\s}"']+`),
	regexp.MustCompile(`(?i)bearer\s+[a-z0-9._~+/=-]+`),
}

func AgentToolPolicySnapshot() map[string]string {
	result := make(map[string]string, len(agentToolPolicies))
	for name, policy := range agentToolPolicies {
		result[name] = policy.Category
	}
	return result
}

func agentToolPolicyFor(name string) agentToolPolicy {
	if policy, ok := agentToolPolicies[name]; ok {
		return policy
	}
	return agentToolPolicy{Name: name, Category: AgentToolCategoryProhibited, Agent: "ValidatorAgent", Flow: agentFlowValidation}
}

func promptedProhibitedTools(message string) []string {
	text := strings.ToLower(strings.TrimSpace(message))
	if text == "" {
		return nil
	}
	rules := []struct {
		tool     string
		keywords []string
	}{
		{tool: "shell.exec", keywords: []string{"shell", "bash", "rm -rf", "执行命令", "运行命令", "系统命令", "命令行"}},
		{tool: "filesystem.write", keywords: []string{"写文件", "修改文件", "删除文件", "文件系统写入", "filesystem"}},
		{tool: "http.request", keywords: []string{"http://", "https://", "http 请求", "外部请求", "任意 http", "curl "}},
		{tool: "database.write", keywords: []string{"直接数据库", "直写数据库", "写数据库", "drop table", "delete from", "insert into", "update "}},
		{tool: "device.control", keywords: []string{"控制设备", "真实设备控制", "打开水泵", "关闭水泵", "启动水泵", "停止水泵", "device control"}},
	}
	result := make([]string, 0)
	for _, rule := range rules {
		if containsAnyText(text, rule.keywords...) {
			result = append(result, rule.tool)
		}
	}
	return result
}

func containsAnyText(text string, keywords ...string) bool {
	for _, keyword := range keywords {
		if strings.Contains(text, strings.ToLower(keyword)) {
			return true
		}
	}
	return false
}

func RecordAgentPolicyViolationForTest(toolName string, input interface{}) vo.SceneAgentStepVo {
	return buildAgentTraceStep(1, toolName, summarizeForLog(input, 260), "", 0, fmt.Errorf("prohibited tool blocked: %s", toolName), nil)
}

func buildAgentTraceStep(index int, toolName string, inputSummary string, outputSummary string, durationMs int64, err error, fallback *vo.SceneAgentFallbackVo) vo.SceneAgentStepVo {
	policy := agentToolPolicyFor(toolName)
	stepID := fmt.Sprintf("step-%02d", index)
	evidenceID := fmt.Sprintf("trace-%s-%s", stepID, sanitizeEvidenceToken(toolName))
	status := AgentTraceStatusSuccess
	failureReason := ""
	if policy.Category == AgentToolCategoryProhibited {
		status = AgentTraceStatusPolicyViolation
		failureReason = fmt.Sprintf("prohibited tool blocked by Agent tool policy: %s", toolName)
	} else if err != nil {
		status = AgentTraceStatusError
		failureReason = err.Error()
	}
	return vo.SceneAgentStepVo{
		StepID:        stepID,
		CallID:        evidenceID,
		EvidenceID:    evidenceID,
		Agent:         policy.Agent,
		Tool:          toolName,
		ToolCategory:  policy.Category,
		Status:        status,
		DurationMs:    durationMs,
		InputSummary:  sanitizeTraceSummary(inputSummary),
		OutputSummary: sanitizeTraceSummary(outputSummary),
		FailureReason: sanitizeTraceSummary(failureReason),
		Fallback:      fallback,
		Flow:          policy.Flow,
	}
}

func sanitizeEvidenceToken(text string) string {
	cleaned := strings.Map(func(r rune) rune {
		switch {
		case r >= 'a' && r <= 'z':
			return r
		case r >= 'A' && r <= 'Z':
			return r + ('a' - 'A')
		case r >= '0' && r <= '9':
			return r
		default:
			return '-'
		}
	}, text)
	cleaned = strings.Trim(cleaned, "-")
	if cleaned == "" {
		return "tool"
	}
	return cleaned
}

func sanitizeTraceSummary(text string) string {
	text = strings.TrimSpace(text)
	for _, pattern := range sensitiveTracePatterns {
		text = pattern.ReplaceAllString(text, "[redacted]")
	}
	return text
}

func makeTraceFallback(reason string, path string) *vo.SceneAgentFallbackVo {
	return &vo.SceneAgentFallbackVo{
		Used:   true,
		Reason: sanitizeTraceSummary(reason),
		Path:   sanitizeTraceSummary(path),
	}
}

func newAgentTaskID(start time.Time) string {
	return fmt.Sprintf("agent-task-%d", start.UnixNano())
}
