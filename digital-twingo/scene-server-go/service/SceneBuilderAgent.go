package service

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"scene-server-go/config"
	"scene-server-go/vo"

	"github.com/cloudwego/eino/adk"
	"github.com/cloudwego/eino/adk/prebuilt/deep"
	"github.com/cloudwego/eino/components/model"
	"github.com/cloudwego/eino/components/tool"
	"github.com/cloudwego/eino/components/tool/utils"
	"github.com/cloudwego/eino/compose"
	"github.com/cloudwego/eino/schema"
)

const sceneBuilderInstruction = `你是智慧农业数字孪生平台的 SceneBuilderAgent。
你只允许调用白名单业务工具完成场景搭建预览，不允许请求 Shell、文件系统、任意 HTTP 或数据库写入能力。

工作流：
1. 先调用 scene.current 理解当前场景。
2. 调用 model.search / model.metadata 获取可用资产。
3. 调用 scene.plan 生成对象组级场景计划。
4. 调用 layout.solve 生成模型加载队列。
5. 调用 layout.validate 校验结果。
6. 最终只返回严格 JSON，字段为 scenePlan、models、warnings、missingAssets。

不要输出 markdown，不要输出保存或写库指令。`

const sceneAgentModeDeepAgents = "deepagents"
const sceneAgentModePipeline = "tool-pipeline"

var sceneAgentToolWhitelist = []string{
	"scene.current",
	"model.search",
	"model.metadata",
	"object.lookup",
	"object.relations",
	"timeseries.query",
	"event.query",
	"scene.plan",
	"layout.solve",
	"scene.applyPlan",
	"asset.job.create",
	"object.bind",
	"alert.acknowledge",
	"layout.validate",
}

var sceneAgentModelToolNames = map[string]string{
	"model.search":    "model_search",
	"model.metadata":  "model_metadata",
	"scene.current":   "scene_current",
	"scene.plan":      "scene_plan",
	"layout.solve":    "layout_solve",
	"layout.validate": "layout_validate",
}

type SceneBuilderAgent struct {
	semantic *SemanticService
}

type sceneAgentRequest struct {
	Request vo.SemanticBuildRequest
	Context vo.SemanticBuildContext
	Mode    string
	Catalog semanticAssetCatalog
}

type sceneAgentResult struct {
	Response   vo.SemanticBuildResponse
	Trace      vo.SceneAgentTraceVo
	RawLLMPlan string
}

type sceneAgentState struct {
	request        sceneAgentRequest
	trace          *vo.SceneAgentTraceVo
	plan           vo.ScenePlan
	models         []vo.BuildModel
	missing        []vo.MissingAssetVo
	warnings       []string
	source         vo.SemanticPlanSource
	rawLLM         string
	toolNames      []string
	visualTemplate *vo.SemanticVisualTemplateVo
}

type sceneCurrentToolInput struct {
	IncludeObjects bool `json:"includeObjects" jsonschema_description:"是否返回已有对象摘要"`
}

type modelSearchToolInput struct {
	Query      string   `json:"query" jsonschema_description:"用户需求或资产关键词"`
	Categories []string `json:"categories,omitempty" jsonschema_description:"可选资产分类过滤"`
}

type modelMetadataToolInput struct {
	AssetKeys []string `json:"assetKeys,omitempty" jsonschema_description:"需要查询的 assetKey 列表，空值表示返回全部资产元数据"`
}

type scenePlanToolInput struct {
	Message string `json:"message" jsonschema_description:"用户原始自然语言搭建需求"`
	Mode    string `json:"mode" jsonschema_description:"preview 或 append"`
}

type layoutSolveToolInput struct {
	UseCurrentPlan bool `json:"useCurrentPlan" jsonschema_description:"是否使用 scene.plan 已生成的计划"`
}

type layoutValidateToolInput struct {
	UseCurrentLayout bool `json:"useCurrentLayout" jsonschema_description:"是否校验 layout.solve 已生成的布局结果"`
}

type scenePlanToolOutput struct {
	ScenePlan     vo.ScenePlan          `json:"scenePlan"`
	MissingAssets []vo.MissingAssetVo   `json:"missingAssets"`
	Warnings      []string              `json:"warnings"`
	PlanSource    vo.SemanticPlanSource `json:"planSource"`
	RawLLMPlan    string                `json:"rawLlmPlan,omitempty"`
}

type layoutSolveToolOutput struct {
	Models        []vo.BuildModel     `json:"models"`
	MissingAssets []vo.MissingAssetVo `json:"missingAssets"`
	Warnings      []string            `json:"warnings"`
}

type layoutValidateToolOutput struct {
	Valid         bool                `json:"valid"`
	ModelCount    int                 `json:"modelCount"`
	MissingAssets []vo.MissingAssetVo `json:"missingAssets"`
	Warnings      []string            `json:"warnings"`
}

func NewSceneBuilderAgent(semantic *SemanticService) *SceneBuilderAgent {
	return &SceneBuilderAgent{semantic: semantic}
}

func (a *SceneBuilderAgent) Build(req sceneAgentRequest) sceneAgentResult {
	start := time.Now()
	trace := vo.SceneAgentTraceVo{
		InvocationID:    fmt.Sprintf("scene-agent-%d", start.UnixNano()),
		TaskID:          newAgentTaskID(start),
		AgentName:       "FarmTwinOrchestrator",
		LegacyAgentName: "SceneBuilderAgent",
		Framework:       "Eino DeepAgents",
		Mode:            sceneAgentModePipeline,
		StartedAt:       start.Format(time.RFC3339),
		UserInput:       sanitizeTraceSummary(strings.TrimSpace(req.Request.Message)),
		UserGoal:        sanitizeTraceSummary(strings.TrimSpace(req.Request.Message)),
	}
	state := &sceneAgentState{
		request: req,
		trace:   &trace,
	}

	a.recordTraceStep(state, "scene.current", sceneCurrentToolInput{IncludeObjects: true}, state.request.Context, nil, nil)
	a.recordPromptedPolicyViolations(state)

	// Repair tasks (T19-T24) seed a REAL faulty scene from initial_state. The plan is
	// constructed FROM these objects so the agent must actually modify the specified
	// objects (never the gold). If the LLM produces nothing, the initial objects remain
	// the baseline that later repair steps act on.
	if initState := state.request.Context.InitialState; initState != nil && len(initState.Objects) > 0 {
		if len(state.plan.Objects) == 0 {
			for _, o := range initState.Objects {
				state.plan.Objects = append(state.plan.Objects, vo.ScenePlanObject{
					ID:       o.ID,
					AssetKey: firstNonEmpty(o.AssetKey, firstNonEmpty(o.Type, o.ID)),
					Label:    o.ID,
					Count:    1,
				})
			}
			state.source = vo.SemanticPlanSource{Mode: "repair-initial-state", Provider: "initial_state", Reason: "seeded from initial_state for repair task"}
		}
	}

	usedDeepAgents, err := a.tryRunDeepAgents(state)
	if err != nil {
		trace.Error = sanitizeTraceSummary(err.Error())
		// Explicit agent_failed marker: LLM/DeepAgents failed. The deterministic
		// pipeline below is a SEPARATE fallback path and must not be confused with
		// a successful LLM/multi-agent run (fairness contract S5.1/S5.2).
		trace.AgentFailed = true
		trace.AgentFailedReason = sanitizeTraceSummary(err.Error())
		state.warnings = append(state.warnings, "Eino DeepAgents 调用失败，已切换为白名单工具流水线。")
		state.warnings = append(state.warnings, err.Error())
	} else if usedDeepAgents {
		trace.Mode = sceneAgentModeDeepAgents
	}

	if len(state.models) == 0 && len(state.plan.Objects) == 0 {
		state.trace.Fallback = makeTraceFallback("LLM 未配置、失败或未生成完整计划", "deterministic-tool-pipeline")
		a.runDeterministicPipeline(state)
	} else if len(state.models) == 0 {
		a.runLayoutSolve(state)
		a.runLayoutValidate(state)
	}

	response := a.finalizeResponse(state)
	trace.FinishedAt = time.Now().Format(time.RFC3339)
	trace.DurationMs = time.Since(start).Milliseconds()
	trace.FinalSummary = summarizeSemanticResponse(response)
	logSceneAgentTrace(trace)
	response.AgentTrace = &trace

	return sceneAgentResult{
		Response:   response,
		Trace:      trace,
		RawLLMPlan: state.rawLLM,
	}
}

func (a *SceneBuilderAgent) tryRunDeepAgents(state *sceneAgentState) (bool, error) {
	if !isSemanticLLMConfigured() {
		return false, nil
	}

	timeout := 30 * time.Second
	if config.AppConfig != nil && config.AppConfig.LLM.TimeoutSeconds > 0 {
		timeout = time.Duration(config.AppConfig.LLM.TimeoutSeconds) * time.Second
	}
	ctx, cancel := newEinoRunContext(timeout)
	defer cancel()

	tools, err := a.tools(ctx, state)
	if err != nil {
		return false, err
	}
	chatModel := newEinoOpenAIChatModel(a.semantic.httpClient)
	agent, err := deep.New(ctx, &deep.Config{
		Name:                   "SceneBuilderAgent",
		Description:            "智慧农业数字孪生场景规划、资产检索、布局求解和结果校验 Agent",
		ChatModel:              chatModel,
		Instruction:            sceneBuilderInstruction,
		ToolsConfig:            adk.ToolsConfig{ToolsNodeConfig: compose.ToolsNodeConfig{Tools: tools, ExecuteSequentially: true}},
		MaxIteration:           maxSemanticAgentIterations(),
		WithoutWriteTodos:      true,
		WithoutGeneralSubAgent: true,
	})
	if err != nil {
		return false, err
	}

	iterator := agent.Run(ctx, &adk.AgentInput{
		Messages: []adk.Message{schema.UserMessage(buildSceneAgentUserPrompt(state.request))},
	}, adk.WithChatModelOptions([]model.Option{model.WithTemperature(0.05), model.WithMaxTokens(1800)}))

	var finalContent string
	for {
		event, ok := iterator.Next()
		if !ok {
			break
		}
		if event == nil {
			continue
		}
		if event.Err != nil {
			return true, event.Err
		}
		if event.Output == nil || event.Output.MessageOutput == nil {
			continue
		}
		msg, err := event.Output.MessageOutput.GetMessage()
		if err != nil {
			return true, err
		}
		if msg != nil && msg.Role == schema.Assistant && strings.TrimSpace(msg.Content) != "" {
			finalContent = msg.Content
		}
	}

	if strings.TrimSpace(finalContent) != "" {
		if parsed, err := a.parseFinalAgentJSON(finalContent, state); err == nil {
			state.plan = parsed.ScenePlan
			state.models = parsed.Models
			state.missing = mergeMissingAssets(state.missing, parsed.MissingAssets)
			state.warnings = append(state.warnings, parsed.Warnings...)
			return true, nil
		}
	}

	return true, nil
}

func (a *SceneBuilderAgent) runDeterministicPipeline(state *sceneAgentState) {
	a.recordToolCall(state, "model.search", modelSearchToolInput{Query: state.request.Request.Message}, func() (interface{}, error) {
		return searchCatalogAssets(state.request.Request.Message, nil, state.request.Catalog), nil
	})
	a.recordToolCall(state, "model.metadata", modelMetadataToolInput{}, func() (interface{}, error) {
		return semanticCatalogSummary(state.request.Catalog), nil
	})
	a.runScenePlan(state)
	a.runLayoutSolve(state)
	a.runLayoutValidate(state)
}

func (a *SceneBuilderAgent) runScenePlan(state *sceneAgentState) {
	input := scenePlanToolInput{Message: state.request.Request.Message, Mode: state.request.Mode}
	a.recordToolCall(state, "scene.plan", input, func() (interface{}, error) {
		attempt := a.semantic.tryBuildPlanWithLLM(state.request.Request, state.request.Context, state.request.Mode, state.request.Catalog)
		plan := attempt.plan
		warnings := append([]string{}, attempt.warnings...)
		source := attempt.source
		raw := attempt.raw
		if len(plan.Objects) == 0 {
			rulePlan, ruleWarnings := a.semantic.buildRulePlan(state.request.Request.Message, state.request.Context.SceneName, state.request.Mode)
			plan = rulePlan
			warnings = append(warnings, ruleWarnings...)
			source = vo.SemanticPlanSource{
				Mode:     "rule",
				Provider: "scene-agent",
				Attempt:  attempt.source.Attempt,
				Reason:   "SceneBuilderAgent scene.plan 回退到规则规划器",
			}
			raw = ""
		}
		normalizeScenePlan(&plan, state.request.Context.SceneName, state.request.Request.Message, state.request.Mode)
		template := a.semantic.visualTemplateForMessage(state.request.Request.Message)
		if template != nil {
			state.visualTemplate = template
			plan.Ground = vo.GroundPlan{Width: 980, Height: 720, Color: template.Lighting.GroundColor, Terrain: "greenhouse_daylight"}
			plan.SceneName = "番茄温室 MVP"
			applyTemplateScenePlanObjects(&plan, *template)
		}
		state.plan = plan
		state.source = source
		state.rawLLM = raw
		state.missing = mergeMissingAssets(state.missing, attempt.missingAssets)
		state.warnings = append(state.warnings, warnings...)
		return scenePlanToolOutput{
			ScenePlan:     plan,
			MissingAssets: attempt.missingAssets,
			Warnings:      uniqueStrings(warnings),
			PlanSource:    source,
			RawLLMPlan:    raw,
		}, nil
	})
}

func (a *SceneBuilderAgent) runLayoutSolve(state *sceneAgentState) {
	a.recordToolCall(state, "layout.solve", layoutSolveToolInput{UseCurrentPlan: true}, func() (interface{}, error) {
		if len(state.plan.Objects) == 0 {
			return nil, fmt.Errorf("scene.plan has no objects")
		}
		models, missing, warnings := solveLayout(state.plan.Objects, state.plan.Ground)
		if state.visualTemplate != nil {
			resp := vo.SemanticBuildResponse{Models: models}
			applyTemplateModelLayout(&resp, *state.visualTemplate)
			models = resp.Models
		}
		state.models = models
		state.missing = mergeMissingAssets(state.missing, missing)
		state.warnings = append(state.warnings, warnings...)
		return layoutSolveToolOutput{
			Models:        models,
			MissingAssets: missing,
			Warnings:      warnings,
		}, nil
	})
}

func (a *SceneBuilderAgent) runAssetRoutingTrace(state *sceneAgentState) {
	if len(state.plan.Objects) == 0 {
		return
	}
	type routeSummary struct {
		AssetKey      string `json:"assetKey"`
		Strategy      string `json:"strategy"`
		RoutingReason string `json:"routingReason"`
	}
	a.recordToolCall(state, "asset.job.create", map[string]interface{}{"mode": state.request.Mode, "scope": "missing-assets"}, func() (interface{}, error) {
		routes := make([]routeSummary, 0)
		missingRoutes := make([]routeSummary, 0)
		missingByKey := map[string]vo.MissingAssetVo{}
		for _, item := range state.missing {
			missingByKey[item.AssetKey] = item
		}
		for _, obj := range state.plan.Objects {
			req := vo.AssetFidelityRoutingRequest{
				AssetKey:      obj.AssetKey,
				ObjectType:    objectTypeForAsset(obj.AssetKey, obj.Category),
				BusinessValue: "ordinary",
			}
			if obj.AssetKey == "tomato" {
				req.BusinessValue = "research_sample"
				req.IsKeyPlant = true
				req.RequiredFidelity = "trustworthy_geometry"
			}
			decision := a.semantic.assetRouter.Decide(req)
			if missing, ok := missingByKey[obj.AssetKey]; ok {
				decision.RequiresGenerationTask = true
				decision.PlaceholderAssetKey = firstNonEmptySemanticAsset(missing.FallbackModelKey, decision.PlaceholderAssetKey, "placeholder.device")
				missingRoutes = append(missingRoutes, routeSummary{AssetKey: obj.AssetKey, Strategy: decision.Strategy, RoutingReason: decision.RoutingReason})
			}
			routes = append(routes, routeSummary{AssetKey: obj.AssetKey, Strategy: decision.Strategy, RoutingReason: decision.RoutingReason})
		}
		return map[string]interface{}{
			"missingStrategy": missingRoutes,
			"mode":            "preview-only",
			"summary":         "AssetFidelityAgent 输出资产选择理由；缺失资产使用 TRELLIS.2 任务契约并保留占位模型。",
			"strategy":        routes,
		}, nil
	})
}

func (a *SceneBuilderAgent) runLayoutValidate(state *sceneAgentState) {
	a.recordToolCall(state, "layout.validate", layoutValidateToolInput{UseCurrentLayout: true}, func() (interface{}, error) {
		missing := filterAvailableMissingAssets(state.missing, state.request.Catalog)
		warnings := filterMissingAssetWarnings(state.warnings, missing)
		if len(state.models) == 0 {
			warnings = append(warnings, "没有生成可加载模型，请补充温室、农田、仓库、道路等农业资产描述。")
		}
		state.missing = missing
		state.warnings = warnings
		return layoutValidateToolOutput{
			Valid:         len(state.models) > 0,
			ModelCount:    len(state.models),
			MissingAssets: missing,
			Warnings:      uniqueStrings(warnings),
		}, nil
	})
}

func (a *SceneBuilderAgent) runObjectBindingTrace(state *sceneAgentState) {
	if len(state.plan.Objects) == 0 {
		return
	}
	objectID := "gh-tomato-001"
	for _, obj := range state.plan.Objects {
		if obj.AssetKey == "sensor" {
			objectID = "sensor-greenhouse-001"
			break
		}
	}
	a.recordToolCall(state, "object.lookup", vo.ObjectLookupRequest{ObjectID: objectID}, func() (interface{}, error) {
		return map[string]interface{}{
			"objectId":    objectID,
			"dataSource":  "agricultural-object-model",
			"mode":        "trace-summary",
			"description": "按稳定业务对象 ID 查询对象摘要，未暴露原始数据库 payload。",
		}, nil
	})
	a.recordToolCall(state, "object.relations", vo.ObjectRelationsRequest{ObjectID: objectID, RelationTypes: []string{"sensor", "device", "camera", "metric", "event"}}, func() (interface{}, error) {
		return map[string]interface{}{
			"objectId":       objectID,
			"relationTypes":  []string{"sensor", "device", "camera", "metric", "event"},
			"bindingSummary": "温室核心对象使用 Phase 1/2 对象关系和场景绑定锚点准备绑定。",
		}, nil
	})
	a.recordToolCall(state, "object.bind", vo.SceneBindingUpdateRequest{SceneName: state.request.Context.SceneName, BusinessObjectId: objectID, AssetKey: "greenhouse", IsDefaultBinding: true}, func() (interface{}, error) {
		return map[string]interface{}{
			"mode":             state.request.Mode,
			"controlledWrite":  "preview-only",
			"businessObjectId": objectID,
			"summary":          "受控绑定工具在 preview 模式仅返回绑定计划，不直接写库。",
		}, nil
	})
}

func (a *SceneBuilderAgent) recordPromptedPolicyViolations(state *sceneAgentState) {
	for _, toolName := range promptedProhibitedTools(state.request.Request.Message) {
		a.recordTraceStep(
			state,
			toolName,
			map[string]interface{}{"requestedBy": "user_goal", "policy": "prohibited"},
			map[string]interface{}{"blocked": true, "summary": "禁止工具请求已阻断，未执行任何外部操作。"},
			fmt.Errorf("prohibited tool requested by user goal: %s", toolName),
			nil,
		)
	}
}

func (a *SceneBuilderAgent) tools(ctx context.Context, state *sceneAgentState) ([]tool.BaseTool, error) {
	toolDefs := []struct {
		name string
		desc string
		make func() (tool.InvokableTool, error)
	}{
		{
			name: "model.search",
			desc: "只读检索业务模型白名单，按自然语言需求返回可用农业资产。",
			make: func() (tool.InvokableTool, error) {
				return utils.InferTool(sceneAgentModelToolNames["model.search"], "只读检索业务模型白名单，禁止外部 HTTP 和数据库写入。", func(ctx context.Context, input modelSearchToolInput) (interface{}, error) {
					return a.recordToolCall(state, "model.search", input, func() (interface{}, error) {
						return searchCatalogAssets(input.Query, input.Categories, state.request.Catalog), nil
					}), nil
				})
			},
		},
		{
			name: "model.metadata",
			desc: "读取指定 assetKey 的模型元数据、默认比例、占地和模型 URL。",
			make: func() (tool.InvokableTool, error) {
				return utils.InferTool(sceneAgentModelToolNames["model.metadata"], "读取指定 assetKey 的模型元数据、默认比例、占地和模型 URL。", func(ctx context.Context, input modelMetadataToolInput) (interface{}, error) {
					return a.recordToolCall(state, "model.metadata", input, func() (interface{}, error) {
						return catalogMetadata(input.AssetKeys, state.request.Catalog), nil
					}), nil
				})
			},
		},
		{
			name: "scene.current",
			desc: "读取当前前端传入的场景上下文摘要。",
			make: func() (tool.InvokableTool, error) {
				return utils.InferTool(sceneAgentModelToolNames["scene.current"], "读取当前前端传入的场景上下文摘要，只读。", func(ctx context.Context, input sceneCurrentToolInput) (interface{}, error) {
					return a.recordToolCall(state, "scene.current", input, func() (interface{}, error) {
						return state.request.Context, nil
					}), nil
				})
			},
		},
		{
			name: "scene.plan",
			desc: "调用语义规划器生成对象组级 scenePlan，不生成最终坐标。",
			make: func() (tool.InvokableTool, error) {
				return utils.InferTool(sceneAgentModelToolNames["scene.plan"], "调用语义规划器生成对象组级 scenePlan，不写数据库。", func(ctx context.Context, input scenePlanToolInput) (interface{}, error) {
					a.runScenePlan(state)
					return scenePlanToolOutput{
						ScenePlan:     state.plan,
						MissingAssets: state.missing,
						Warnings:      uniqueStrings(state.warnings),
						PlanSource:    state.source,
						RawLLMPlan:    state.rawLLM,
					}, nil
				})
			},
		},
		{
			name: "layout.solve",
			desc: "把 scenePlan 对象组求解成前端可加载模型队列。",
			make: func() (tool.InvokableTool, error) {
				return utils.InferTool(sceneAgentModelToolNames["layout.solve"], "把 scenePlan 对象组求解成前端可加载模型队列。", func(ctx context.Context, input layoutSolveToolInput) (interface{}, error) {
					a.runLayoutSolve(state)
					return layoutSolveToolOutput{Models: state.models, MissingAssets: state.missing, Warnings: uniqueStrings(state.warnings)}, nil
				})
			},
		},
		{
			name: "layout.validate",
			desc: "校验布局结果、缺失资产和告警信息。",
			make: func() (tool.InvokableTool, error) {
				return utils.InferTool(sceneAgentModelToolNames["layout.validate"], "校验布局结果、缺失资产和告警信息。", func(ctx context.Context, input layoutValidateToolInput) (interface{}, error) {
					a.runLayoutValidate(state)
					return layoutValidateToolOutput{Valid: len(state.models) > 0, ModelCount: len(state.models), MissingAssets: state.missing, Warnings: uniqueStrings(state.warnings)}, nil
				})
			},
		},
	}

	result := make([]tool.BaseTool, 0, len(toolDefs))
	for _, item := range toolDefs {
		t, err := item.make()
		if err != nil {
			return nil, fmt.Errorf("build tool %s: %w", item.name, err)
		}
		result = append(result, t)
	}
	_ = ctx
	return result, nil
}

func (a *SceneBuilderAgent) recordToolCall(state *sceneAgentState, name string, input interface{}, fn func() (interface{}, error)) interface{} {
	start := time.Now()
	call := vo.SceneAgentToolCallVo{
		Name:         name,
		Status:       AgentTraceStatusSuccess,
		InputSummary: sanitizeTraceSummary(summarizeForLog(input, 260)),
	}
	output, err := fn()
	call.DurationMs = time.Since(start).Milliseconds()
	policy := agentToolPolicyFor(name)
	call.Agent = policy.Agent
	call.ToolCategory = policy.Category
	call.Flow = policy.Flow
	if err != nil {
		call.Status = AgentTraceStatusError
		call.Error = sanitizeTraceSummary(err.Error())
		call.FailureReason = call.Error
	} else {
		call.OutputSummary = sanitizeTraceSummary(summarizeForLog(output, 420))
	}
	if state.trace.Fallback != nil && name == "scene.plan" && state.trace.Fallback.Used {
		call.Fallback = state.trace.Fallback
	}
	step := buildAgentTraceStep(len(state.trace.Steps)+1, name, call.InputSummary, call.OutputSummary, call.DurationMs, err, call.Fallback)
	call.CallID = step.CallID
	call.EvidenceID = step.EvidenceID
	state.trace.Tools = append(state.trace.Tools, call)
	state.trace.Steps = append(state.trace.Steps, step)
	state.toolNames = append(state.toolNames, name)
	if err != nil {
		return map[string]interface{}{"error": err.Error()}
	}
	return output
}

func (a *SceneBuilderAgent) recordTraceStep(state *sceneAgentState, name string, input interface{}, output interface{}, err error, fallback *vo.SceneAgentFallbackVo) {
	start := time.Now()
	inputSummary := sanitizeTraceSummary(summarizeForLog(input, 260))
	outputSummary := sanitizeTraceSummary(summarizeForLog(output, 420))
	step := buildAgentTraceStep(len(state.trace.Steps)+1, name, inputSummary, outputSummary, time.Since(start).Milliseconds(), err, fallback)
	state.trace.Steps = append(state.trace.Steps, step)
}

func (a *SceneBuilderAgent) parseFinalAgentJSON(raw string, state *sceneAgentState) (vo.SemanticBuildResponse, error) {
	jsonText := extractJSONBlock(raw)
	var parsed vo.SemanticBuildResponse
	decoder := json.NewDecoder(strings.NewReader(jsonText))
	if err := decoder.Decode(&parsed); err != nil {
		return vo.SemanticBuildResponse{}, err
	}
	if len(parsed.ScenePlan.Objects) == 0 {
		return vo.SemanticBuildResponse{}, fmt.Errorf("agent final JSON has no objects")
	}
	enrichScenePlanWithCatalog(&parsed.ScenePlan, state.request.Catalog)
	normalizeScenePlan(&parsed.ScenePlan, state.request.Context.SceneName, state.request.Request.Message, state.request.Mode)
	return parsed, nil
}

func (a *SceneBuilderAgent) finalizeResponse(state *sceneAgentState) vo.SemanticBuildResponse {
	plan := state.plan
	normalizeScenePlan(&plan, state.request.Context.SceneName, state.request.Request.Message, state.request.Mode)
	missing := filterAvailableMissingAssets(state.missing, state.request.Catalog)
	warnings := filterMissingAssetWarnings(state.warnings, missing)
	if len(state.models) == 0 {
		warnings = append(warnings, "没有生成可加载模型，请补充温室、农田、仓库、道路等农业资产描述。")
	}
	source := state.source
	if source.Mode == "" {
		source = vo.SemanticPlanSource{
			Mode:     "agent",
			Model:    configuredLLMModel(),
			Provider: "eino-deepagents",
			Attempt:  1,
			Reason:   "SceneBuilderAgent 白名单工具编排",
		}
	}
	if state.trace.Mode == sceneAgentModeDeepAgents {
		source.Mode = "agent"
		source.Provider = "eino-deepagents"
		source.Model = configuredLLMModel()
		source.Reason = "Eino DeepAgents 调度白名单工具"
	}
	a.runAssetRoutingTrace(state)
	a.runObjectBindingTrace(state)

	return vo.SemanticBuildResponse{
		ScenePlan:      plan,
		Models:         state.models,
		Warnings:       uniqueStrings(warnings),
		MissingAssets:  uniqueMissingAssets(missing),
		Samples:        a.semantic.Samples(),
		PlanSource:     source,
		Context:        state.request.Context,
		VisualTemplate: state.visualTemplate,
		RawLLMPlan:     state.rawLLM,
	}
}

func buildSceneAgentUserPrompt(req sceneAgentRequest) string {
	contextJSON, _ := json.MarshalIndent(req.Context, "", "  ")
	assetsJSON, _ := json.MarshalIndent(semanticCatalogSummary(req.Catalog), "", "  ")
	return fmt.Sprintf("用户原始需求：%s\n当前模式：%s\n场景名：%s\n\n当前上下文：\n%s\n\n资产白名单：\n%s\n\n请按工具流程执行，并最终只输出 JSON。", req.Request.Message, req.Mode, req.Context.SceneName, string(contextJSON), string(assetsJSON))
}

func maxSemanticAgentIterations() int {
	if config.AppConfig != nil && config.AppConfig.LLM.MaxToolRounds > 0 {
		return clampInt(config.AppConfig.LLM.MaxToolRounds+4, 4, 10)
	}
	return 6
}

func isSemanticLLMConfigured() bool {
	return config.AppConfig != nil &&
		config.AppConfig.LLM.Enabled &&
		strings.TrimSpace(config.AppConfig.LLM.BaseURL) != "" &&
		strings.TrimSpace(config.AppConfig.LLM.APIKey) != "" &&
		strings.TrimSpace(config.AppConfig.LLM.Model) != ""
}

func configuredLLMModel() string {
	if config.AppConfig == nil {
		return ""
	}
	return config.AppConfig.LLM.Model
}

func searchCatalogAssets(query string, categories []string, catalog semanticAssetCatalog) []vo.AssetSemantic {
	text := normalizeText(query)
	categorySet := map[string]bool{}
	for _, category := range categories {
		category = strings.TrimSpace(category)
		if category != "" {
			categorySet[category] = true
		}
	}
	result := make([]vo.AssetSemantic, 0)
	for _, item := range catalog.items {
		if len(categorySet) > 0 && !categorySet[item.Category] {
			continue
		}
		if text == "" || matchesAsset(text, item) || strings.Contains(normalizeText(item.Category), text) {
			result = append(result, item)
			continue
		}
		for _, alias := range item.Aliases {
			if strings.Contains(text, normalizeText(alias)) {
				result = append(result, item)
				break
			}
		}
	}
	if len(result) == 0 {
		result = catalog.items
	}
	return result
}

func catalogMetadata(assetKeys []string, catalog semanticAssetCatalog) []vo.AssetSemantic {
	if len(assetKeys) == 0 {
		return catalog.items
	}
	result := make([]vo.AssetSemantic, 0, len(assetKeys))
	for _, key := range assetKeys {
		assetKey := strings.TrimSpace(key)
		if itemKey, ok := catalog.byAlias[normalizeText(assetKey)]; ok {
			assetKey = itemKey
		}
		if item, ok := catalog.byKey[assetKey]; ok {
			result = append(result, item)
		}
	}
	return result
}

func summarizeSemanticResponse(resp vo.SemanticBuildResponse) string {
	return fmt.Sprintf("objects=%d models=%d missing=%d warnings=%d", len(resp.ScenePlan.Objects), len(resp.Models), len(resp.MissingAssets), len(resp.Warnings))
}

func summarizeForLog(value interface{}, maxLen int) string {
	data, err := json.Marshal(value)
	if err != nil {
		return fmt.Sprintf("%T", value)
	}
	text := string(data)
	if maxLen > 0 && len([]rune(text)) > maxLen {
		runes := []rune(text)
		text = string(runes[:maxLen]) + "..."
	}
	return text
}

func logSceneAgentTrace(trace vo.SceneAgentTraceVo) {
	data, err := json.Marshal(trace)
	if err != nil {
		config.Log("WARN", "scene agent trace marshal failed: %v", err)
		return
	}
	config.Log("INFO", "scene agent trace %s", string(data))
}
