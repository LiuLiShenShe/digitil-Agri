package service

import (
	"bytes"
	"context"
	"crypto/sha1"
	"encoding/json"
	"errors"
	"fmt"
	"math"
	"net/http"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"

	"scene-server-go/config"
	"scene-server-go/mapper"
	"scene-server-go/vo"
)

const semanticSystemPrompt = `你是数字孪生平台的场景规划器。
你只能输出严格 JSON，不要输出解释、注释、markdown 代码块或多余文本。
你的任务是把用户自然语言转成可执行的语义场景草案。

输出必须是一个 JSON 对象，且只包含以下顶层字段：
{
  "scenePlan": {
    "sceneName": "string",
    "intent": "string",
    "units": "platform",
    "mode": "preview|append",
    "ground": {
      "width": number,
      "height": number,
      "color": "string",
      "terrain": "flat|field|greenhouse_park"
    },
    "objects": [
      {
        "id": "string",
        "label": "string",
        "category": "string",
        "assetKey": "string",
        "url": "string",
        "count": number,
        "layout": "single|row|column|grid|along_path",
        "area": "west|east|north|south|center|left|right|northwest|northeast|southwest|southeast",
        "scale": number,
        "size": { "width": number, "depth": number },
        "aliases": ["string"]
      }
    ],
    "relations": [
      {
        "subject": "string",
        "predicate": "string",
        "object": "string"
      }
    ]
  },
  "missingAssets": [
    {
      "assetKey": "string",
      "name": "string",
      "reason": "string"
    }
  ],
  "warnings": ["string"]
}

要求：
- 必须优先使用给定资产库中的 assetKey 和别名。
- scenePlan 里的对象必须是对象组，不要直接输出最终坐标。
- 不要输出最终保存指令，不要输出数据库操作。
- 不能确定时，把信息放进 warnings。
- 缺失模型时，把信息放进 missingAssets。
- 如果用户是在补全当前场景，优先利用 context 里的已有对象和当前选中对象。`

type SemanticService struct {
	httpClient        *http.Client
	agent             *SceneBuilderAgent
	referenceResolver *ReferenceImageResolver
	assetMapper       *mapper.AssetMapper
	assetRegistry     *AssetRegistryService
	assetRouter       *AssetFidelityRoutingService
}

type semanticLLMResponse struct {
	ScenePlan     vo.ScenePlan        `json:"scenePlan"`
	MissingAssets []vo.MissingAssetVo `json:"missingAssets"`
	Warnings      []string            `json:"warnings"`
}

type semanticLLMPlanAttempt struct {
	plan          vo.ScenePlan
	missingAssets []vo.MissingAssetVo
	warnings      []string
	source        vo.SemanticPlanSource
	raw           string
}

type semanticAssetCatalog struct {
	items   []vo.AssetSemantic
	byKey   map[string]vo.AssetSemantic
	byAlias map[string]string
}

type semanticIntent struct {
	template string
	objects  map[string]objectIntent
	warnings []string
}

type objectIntent struct {
	assetKey string
	count    int
	area     string
	layout   string
}

func NewSemanticService() *SemanticService {
	registry := NewAssetRegistryService()
	svc := &SemanticService{
		httpClient:        &http.Client{},
		referenceResolver: NewReferenceImageResolver(),
		assetMapper:       mapper.NewAssetMapper(),
		assetRegistry:     registry,
		assetRouter:       NewAssetFidelityRoutingService(registry),
	}
	svc.agent = NewSceneBuilderAgent(svc)
	return svc
}

func (s *SemanticService) BuildPlan(req vo.SemanticBuildRequest) vo.ResultVo {
	message := strings.TrimSpace(req.Message)
	if message == "" {
		return vo.ResultVo{Code: 999, Data: "message is required"}
	}

	context := s.normalizeBuildContext(req, message)
	mode := normalizeSemanticMode(req.Mode, context.AppendMode)
	sceneName := strings.TrimSpace(req.SceneName)
	if sceneName == "" {
		sceneName = context.SceneName
	}
	if sceneName == "" {
		sceneName = inferSceneName(message)
	}
	context.SceneName = sceneName

	catalog := semanticCatalog()
	agentResult := s.agent.Build(sceneAgentRequest{
		Request: req,
		Context: context,
		Mode:    mode,
		Catalog: catalog,
	})
	s.enrichMissingAssetWorkflow(&agentResult.Response, req.OwnerKey, catalog)

	return vo.ResultVo{
		Code: 200,
		Data: agentResult.Response,
	}
}

func (s *SemanticService) AssetSemantics() vo.ResultVo {
	return vo.ResultVo{Code: 200, Data: enrichAssetSemanticsWithMetadata(semanticAssets(), s.assetRegistry)}
}

func (s *SemanticService) Samples() []vo.BuildSampleVo {
	return []vo.BuildSampleVo{
		{Title: "智慧农业示范园区", Message: "搭一个智慧农业示范园区，左侧六块玉米地，右侧三个温室，中间一条道路，中央放气象站和灌溉设备。"},
		{Title: "标准温室场景", Message: "创建标准温室场景，两个大棚纵向排列，每个大棚旁边放灌溉设备，入口放摄像头。"},
		{Title: "农田 + 气象站组合", Message: "生成农田和气象站组合，四块小麦田做网格，中间放气象站，南侧放水塔。"},
		{Title: "现有场景补设备", Message: "在现有场景补齐摄像头、气象站、水塔和灌溉系统，设备沿道路布置。"},
		{Title: "综合园区模板", Message: "做一个综合农业园区，西侧农田，东侧温室，北侧仓库和管理楼，中央道路贯穿。"},
		{Title: "温室语义同义词", Message: "帮我搭一个玻璃房园区，左边放 3 个大棚，右边放 2 个温室，中央放监测站。"},
		{Title: "补全当前场景", Message: "继续补几个摄像头和环境传感器，优先放在道路两侧。"},
		{Title: "方位与数量", Message: "左侧放 4 块小麦田，右侧放 2 个水塔，北侧补一个仓库。"},
		{Title: "模板变体", Message: "生成一个智慧农业园区模板，南侧道路贯穿，中间放气象站，东侧摆温室。"},
		{Title: "模糊补充", Message: "把当前场景再完善一下，增加巡检车、无人机和灌溉装置。"},
		{Title: "温室阵列", Message: "在右边做一排温室，按纵向排列，旁边加传感器。"},
		{Title: "田块阵列", Message: "西边做 6 块玉米地，按网格摆放，留出中间通道。"},
		{Title: "中心设备", Message: "中心放一个气象站，周围配摄像头和喷灌设备。"},
		{Title: "仓储补齐", Message: "北侧补仓库和管理楼，南侧放水塔。"},
		{Title: "道路导向", Message: "沿道路两侧布置摄像头和灌溉设备。"},
		{Title: "补全温室", Message: "在现有温室旁边继续补 2 个大棚和 2 个传感器。"},
		{Title: "温室 + 道路", Message: "做一个温室园区，中央道路贯穿，东侧三个温室，西侧四块小麦田。"},
		{Title: "示范园区简版", Message: "帮我搭一个农业示范园区，左边农田，右边温室，中间道路。"},
		{Title: "设备补齐", Message: "在场景里补齐气象站、摄像头、水塔和农机。"},
		{Title: "复杂组合", Message: "左边 3 块玉米地，右边 3 个玻璃房，北边仓库和管理楼，中间放气象站和灌溉系统。"},
	}
}

func (s *SemanticService) tryBuildPlanWithLLM(req vo.SemanticBuildRequest, context vo.SemanticBuildContext, mode string, catalog semanticAssetCatalog) semanticLLMPlanAttempt {
	if config.AppConfig == nil || !config.AppConfig.LLM.Enabled {
		return semanticLLMPlanAttempt{
			plan:     vo.ScenePlan{},
			warnings: []string{},
			source: vo.SemanticPlanSource{
				Mode:     "rule",
				Model:    "",
				Provider: "disabled",
				Attempt:  0,
				Reason:   "llm disabled",
			},
		}
	}
	if config.AppConfig.LLM.BaseURL == "" || config.AppConfig.LLM.APIKey == "" || config.AppConfig.LLM.Model == "" {
		return semanticLLMPlanAttempt{
			plan:     vo.ScenePlan{},
			warnings: []string{},
			source: vo.SemanticPlanSource{
				Mode:     "rule",
				Model:    "",
				Provider: "disabled",
				Attempt:  0,
				Reason:   "llm config incomplete",
			},
		}
	}

	maxAttempts := 2
	if config.AppConfig.LLM.MaxToolRounds > 0 {
		maxAttempts = config.AppConfig.LLM.MaxToolRounds
		if maxAttempts < 1 {
			maxAttempts = 1
		}
	}

	var lastErr error
	for attempt := 1; attempt <= maxAttempts; attempt++ {
		raw, err := s.callSemanticLLM(req, context, mode, catalog)
		if err != nil {
			lastErr = err
			if isLLMTimeoutError(err) {
				break
			}
			continue
		}
		parsed, err := s.parseSemanticLLMResponse(raw, catalog)
		if err != nil {
			lastErr = err
			continue
		}
		enrichScenePlanWithCatalog(&parsed.ScenePlan, catalog)
		normalizeScenePlan(&parsed.ScenePlan, req.SceneName, req.Message, mode)
		if parsed.ScenePlan.SceneName == "" {
			parsed.ScenePlan.SceneName = inferSceneName(req.Message)
		}
		return semanticLLMPlanAttempt{
			plan:          parsed.ScenePlan,
			missingAssets: parsed.MissingAssets,
			warnings:      uniqueStrings(parsed.Warnings),
			source: vo.SemanticPlanSource{
				Mode:     "llm",
				Model:    config.AppConfig.LLM.Model,
				Provider: "openai-compatible",
				Attempt:  attempt,
				Reason:   "llm json plan",
			},
			raw: raw,
		}
	}

	warnings := []string{"LLM 解析失败，已回退到规则版。"}
	if lastErr != nil {
		warnings = append(warnings, lastErr.Error())
	}
	return semanticLLMPlanAttempt{
		plan:     vo.ScenePlan{},
		warnings: warnings,
		source: vo.SemanticPlanSource{
			Mode:     "rule",
			Model:    config.AppConfig.LLM.Model,
			Provider: "openai-compatible",
			Attempt:  maxAttempts,
			Reason:   "llm failed",
		},
	}
}

func (s *SemanticService) callSemanticLLM(req vo.SemanticBuildRequest, context vo.SemanticBuildContext, mode string, catalog semanticAssetCatalog) (string, error) {
	timeout := 30 * time.Second
	if config.AppConfig != nil && config.AppConfig.LLM.TimeoutSeconds > 0 {
		timeout = time.Duration(config.AppConfig.LLM.TimeoutSeconds) * time.Second
	}
	ctx, cancel := contextWithTimeout(timeout)
	defer cancel()

	payload := map[string]interface{}{
		"model": config.AppConfig.LLM.Model,
		"messages": []map[string]string{
			{"role": "system", "content": semanticSystemPrompt},
			{"role": "user", "content": buildSemanticUserContent(req.Message, req.SceneName, mode, context, catalog)},
		},
		"temperature":     0.1,
		"max_tokens":      1200,
		"response_format": map[string]string{"type": "json_object"},
		"stream":          false,
	}
	if isDeepSeekLLM() {
		payload["thinking"] = map[string]string{"type": "disabled"}
	}
	body, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}

	url := config.LLMChatCompletionsURL()
	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return "", err
	}
	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Authorization", "Bearer "+config.AppConfig.LLM.APIKey)

	resp, err := s.httpClient.Do(httpReq)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	var result struct {
		Choices []struct {
			Message struct {
				Content string `json:"content"`
			} `json:"message"`
		} `json:"choices"`
		Error *struct {
			Message string `json:"message"`
		} `json:"error"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", err
	}
	if resp.StatusCode >= 300 {
		if result.Error != nil && result.Error.Message != "" {
			return "", fmt.Errorf("LLM error %d: %s", resp.StatusCode, result.Error.Message)
		}
		return "", fmt.Errorf("LLM error status: %d", resp.StatusCode)
	}
	if len(result.Choices) == 0 || strings.TrimSpace(result.Choices[0].Message.Content) == "" {
		return "", fmt.Errorf("LLM 返回为空")
	}
	return strings.TrimSpace(result.Choices[0].Message.Content), nil
}

func (s *SemanticService) parseSemanticLLMResponse(raw string, catalog semanticAssetCatalog) (semanticLLMResponse, error) {
	jsonText := extractJSONBlock(raw)
	var parsed semanticLLMResponse
	decoder := json.NewDecoder(strings.NewReader(jsonText))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&parsed); err != nil {
		return semanticLLMResponse{}, err
	}
	enrichScenePlanWithCatalog(&parsed.ScenePlan, catalog)
	normalizeScenePlan(&parsed.ScenePlan, parsed.ScenePlan.SceneName, parsed.ScenePlan.Intent, parsed.ScenePlan.Mode)
	if err := validateSemanticPlan(parsed.ScenePlan, catalog); err != nil {
		return semanticLLMResponse{}, err
	}
	return parsed, nil
}

func isDeepSeekLLM() bool {
	if config.AppConfig == nil {
		return false
	}
	return strings.Contains(strings.ToLower(config.AppConfig.LLM.BaseURL), "deepseek")
}

func isLLMTimeoutError(err error) bool {
	if err == nil {
		return false
	}
	if errors.Is(err, context.DeadlineExceeded) {
		return true
	}
	return strings.Contains(strings.ToLower(err.Error()), "context deadline exceeded")
}

func (s *SemanticService) buildRulePlan(message string, sceneName string, mode string) (vo.ScenePlan, []string) {
	intent := parseSemanticIntent(message)
	objects := s.expandPlanObjects(intent)
	ground := inferGround(intent.template, len(objects))
	relations := inferRelations(objects, message)
	warnings := append([]string{}, intent.warnings...)

	plan := vo.ScenePlan{
		SceneName: sceneName,
		Intent:    message,
		Units:     "platform",
		Mode:      mode,
		Ground:    ground,
		Objects:   objects,
		Relations: relations,
	}
	return plan, warnings
}

func (s *SemanticService) normalizeBuildContext(req vo.SemanticBuildRequest, message string) vo.SemanticBuildContext {
	context := req.Context
	if strings.TrimSpace(context.SceneName) == "" {
		context.SceneName = inferSceneName(message)
	}
	if len(context.ExistingObjects) == 0 && len(context.SelectedObjects) > 0 {
		context.ExistingObjects = append([]vo.SemanticObjectSummary{}, context.SelectedObjects...)
	}
	if context.SceneSummary.ObjectCount == 0 {
		context.SceneSummary.ObjectCount = len(context.ExistingObjects)
	}
	if context.SceneSummary.ModelCount == 0 {
		context.SceneSummary.ModelCount = len(context.ExistingObjects)
	}
	return context
}

func normalizeSemanticMode(mode string, appendMode bool) string {
	m := strings.ToLower(strings.TrimSpace(mode))
	switch m {
	case "append", "add", "continue":
		return "append"
	case "preview", "plan", "":
		if appendMode {
			return "append"
		}
		return "preview"
	default:
		if appendMode {
			return "append"
		}
		return "preview"
	}
}

func normalizeScenePlan(plan *vo.ScenePlan, fallbackSceneName string, intent string, mode string) {
	if plan == nil {
		return
	}
	if strings.TrimSpace(plan.SceneName) == "" {
		plan.SceneName = fallbackSceneName
	}
	if strings.TrimSpace(plan.SceneName) == "" {
		plan.SceneName = inferSceneName(intent)
	}
	if strings.TrimSpace(plan.Intent) == "" {
		plan.Intent = intent
	}
	if strings.TrimSpace(plan.Units) == "" {
		plan.Units = "platform"
	}
	if strings.TrimSpace(plan.Mode) == "" {
		plan.Mode = mode
	}
	if plan.Ground.Width <= 0 || plan.Ground.Height <= 0 {
		plan.Ground = inferGround("", len(plan.Objects))
	} else {
		plan.Ground.Width = clampFloat(plan.Ground.Width, 300, 3000)
		plan.Ground.Height = clampFloat(plan.Ground.Height, 300, 3000)
		if strings.TrimSpace(plan.Ground.Color) == "" {
			plan.Ground.Color = "#88aa66"
		}
		if strings.TrimSpace(plan.Ground.Terrain) == "" {
			plan.Ground.Terrain = "field"
		}
	}
	for i := range plan.Objects {
		obj := &plan.Objects[i]
		if strings.TrimSpace(obj.ID) == "" {
			obj.ID = fmt.Sprintf("%s_group", obj.AssetKey)
		}
		if strings.TrimSpace(obj.Label) == "" {
			obj.Label = obj.AssetKey
		}
		if strings.TrimSpace(obj.Layout) == "" {
			obj.Layout = inferLayout(intent, obj.AssetKey, obj.Count)
		}
		if strings.TrimSpace(obj.Area) == "" {
			obj.Area = defaultArea(obj.AssetKey)
		}
		if obj.Count <= 0 {
			obj.Count = 1
		}
		obj.Count = clampInt(obj.Count, 1, 24)
		if obj.Scale <= 0 {
			obj.Scale = 1
		}
		obj.Scale = clampFloat(obj.Scale, 0.05, 10)
	}
}

func enrichScenePlanWithCatalog(plan *vo.ScenePlan, catalog semanticAssetCatalog) {
	if plan == nil {
		return
	}
	for i := range plan.Objects {
		obj := &plan.Objects[i]
		assetKey := resolveCatalogAssetKey(*obj, catalog)
		item, ok := catalog.byKey[assetKey]
		if !ok {
			continue
		}
		obj.AssetKey = item.AssetKey
		if strings.TrimSpace(obj.Label) == "" || strings.TrimSpace(obj.Label) == assetKey {
			obj.Label = item.Name
		}
		if strings.TrimSpace(obj.Category) == "" {
			obj.Category = item.Category
		}
		if strings.TrimSpace(item.URL) != "" {
			obj.URL = item.URL
		}
		if obj.Scale <= 0 {
			obj.Scale = item.DefaultScale
		}
		if obj.Size.Width <= 0 || obj.Size.Depth <= 0 {
			obj.Size = item.Footprint
		}
		if len(obj.Aliases) == 0 {
			obj.Aliases = item.Aliases
		}
	}
}

func resolveCatalogAssetKey(obj vo.ScenePlanObject, catalog semanticAssetCatalog) string {
	candidates := []string{
		obj.AssetKey,
		obj.Label,
		obj.ID,
		obj.URL,
		modelURLBase(obj.URL),
		modelURLStem(obj.URL),
	}
	for _, candidate := range candidates {
		if itemKey, ok := catalog.byAlias[normalizeText(candidate)]; ok {
			return itemKey
		}
	}
	return strings.TrimSpace(obj.AssetKey)
}

func semanticCatalog() semanticAssetCatalog {
	items := enrichAssetSemanticsWithMetadata(semanticAssets(), NewAssetRegistryService())
	catalog := semanticAssetCatalog{
		items:   items,
		byKey:   map[string]vo.AssetSemantic{},
		byAlias: map[string]string{},
	}
	for _, item := range items {
		catalog.byKey[item.AssetKey] = item
		registerAssetAlias(catalog.byAlias, item.AssetKey, item.AssetKey)
		registerAssetAlias(catalog.byAlias, item.Name, item.AssetKey)
		registerAssetAlias(catalog.byAlias, item.URL, item.AssetKey)
		registerAssetAlias(catalog.byAlias, modelURLBase(item.URL), item.AssetKey)
		registerAssetAlias(catalog.byAlias, modelURLStem(item.URL), item.AssetKey)
		for _, alias := range item.Aliases {
			registerAssetAlias(catalog.byAlias, alias, item.AssetKey)
		}
	}
	return catalog
}

func enrichAssetSemanticsWithMetadata(items []vo.AssetSemantic, registry *AssetRegistryService) []vo.AssetSemantic {
	if registry == nil {
		registry = NewAssetRegistryService()
	}
	result := make([]vo.AssetSemantic, len(items))
	for i, item := range items {
		result[i] = item
		if meta, ok := registry.Get(item.AssetKey); ok {
			result[i].Source = meta.Source
			result[i].License = meta.License
			result[i].FidelityLevel = meta.FidelityLevel
			result[i].ThumbnailURL = meta.ThumbnailURL
			result[i].GLBURL = meta.GLBURL
			result[i].ApplicableObjectTypes = append([]string{}, meta.ApplicableObjectTypes...)
			result[i].Quality = meta.Quality
			result[i].Version = meta.Version
			result[i].MetadataComplete = meta.MetadataComplete
			result[i].RoutingReason = defaultRoutingReasonForAsset(meta)
		}
	}
	return result
}

func defaultRoutingReasonForAsset(meta vo.AssetMetadataVo) string {
	if strings.TrimSpace(meta.GLBURL) == "" {
		return "资产库暂无可用 GLB，使用占位模型并进入补资产生成流程。"
	}
	if meta.FidelityLevel == "procedural_ready" {
		return "规则几何可由程序化生成或已有低面数模型承担。"
	}
	return "资产库已有可加载 GLB，优先复用已有资产。"
}

func registerAssetAlias(index map[string]string, alias string, assetKey string) {
	normalized := normalizeText(alias)
	if normalized == "" {
		return
	}
	index[normalized] = assetKey
}

func modelURLBase(url string) string {
	url = strings.TrimSpace(url)
	if url == "" {
		return ""
	}
	if idx := strings.IndexAny(url, "?#"); idx >= 0 {
		url = url[:idx]
	}
	url = strings.ReplaceAll(url, "\\", "/")
	if idx := strings.LastIndex(url, "/"); idx >= 0 {
		return url[idx+1:]
	}
	return url
}

func modelURLStem(url string) string {
	base := modelURLBase(url)
	if idx := strings.LastIndex(base, "."); idx > 0 {
		return base[:idx]
	}
	return base
}

func semanticCatalogSummary(catalog semanticAssetCatalog) []map[string]interface{} {
	result := make([]map[string]interface{}, 0, len(catalog.items))
	for _, item := range catalog.items {
		result = append(result, map[string]interface{}{
			"assetKey":      item.AssetKey,
			"name":          item.Name,
			"aliases":       item.Aliases,
			"category":      item.Category,
			"modelUrl":      item.URL,
			"modelFile":     modelURLBase(item.URL),
			"defaultScale":  item.DefaultScale,
			"footprint":     item.Footprint,
			"fidelity":      item.FidelityLevel,
			"source":        item.Source,
			"license":       item.License,
			"quality":       item.Quality.QualityStatus,
			"routingReason": item.RoutingReason,
		})
	}
	return result
}

func buildSemanticUserContent(message string, sceneName string, mode string, context vo.SemanticBuildContext, catalog semanticAssetCatalog) string {
	contextJSON, _ := json.MarshalIndent(context, "", "  ")
	assetsJSON, _ := json.MarshalIndent(semanticCatalogSummary(catalog), "", "  ")
	return fmt.Sprintf("用户原始需求：%s\n当前场景名：%s\n当前模式：%s\n\n当前上下文：\n%s\n\n模型库摘要：\n%s\n\n请只输出符合 schema 的 JSON。", message, sceneName, mode, string(contextJSON), string(assetsJSON))
}

func validateSemanticPlan(plan vo.ScenePlan, catalog semanticAssetCatalog) error {
	if strings.TrimSpace(plan.SceneName) == "" {
		return fmt.Errorf("sceneName is required")
	}
	if strings.TrimSpace(plan.Intent) == "" {
		return fmt.Errorf("intent is required")
	}
	if strings.TrimSpace(plan.Units) == "" {
		return fmt.Errorf("units is required")
	}
	if len(plan.Objects) == 0 {
		return fmt.Errorf("objects is required")
	}
	if plan.Ground.Width < 300 || plan.Ground.Height < 300 || plan.Ground.Width > 3000 || plan.Ground.Height > 3000 {
		return fmt.Errorf("ground size out of range")
	}
	allowedLayouts := map[string]bool{"single": true, "row": true, "column": true, "grid": true, "along_path": true}
	allowedAreas := map[string]bool{
		"west": true, "east": true, "north": true, "south": true, "center": true,
		"left": true, "right": true,
		"northwest": true, "northeast": true, "southwest": true, "southeast": true,
	}
	for _, obj := range plan.Objects {
		if strings.TrimSpace(obj.AssetKey) == "" {
			return fmt.Errorf("object assetKey is required")
		}
		if _, ok := catalog.byKey[obj.AssetKey]; !ok {
			return fmt.Errorf("unknown assetKey: %s", obj.AssetKey)
		}
		if strings.TrimSpace(obj.Label) == "" {
			return fmt.Errorf("label is required for %s", obj.AssetKey)
		}
		if strings.TrimSpace(obj.Category) == "" {
			return fmt.Errorf("category is required for %s", obj.AssetKey)
		}
		if obj.Count < 1 || obj.Count > 24 {
			return fmt.Errorf("invalid count for %s", obj.AssetKey)
		}
		if !allowedLayouts[obj.Layout] {
			return fmt.Errorf("invalid layout for %s", obj.AssetKey)
		}
		if !allowedAreas[obj.Area] {
			return fmt.Errorf("invalid area for %s", obj.AssetKey)
		}
		if obj.Scale <= 0 {
			return fmt.Errorf("invalid scale for %s", obj.AssetKey)
		}
		if obj.Size.Width <= 0 || obj.Size.Depth <= 0 {
			return fmt.Errorf("invalid size for %s", obj.AssetKey)
		}
	}
	return nil
}

func extractJSONBlock(raw string) string {
	trimmed := strings.TrimSpace(raw)
	if strings.HasPrefix(trimmed, "```") {
		trimmed = strings.TrimPrefix(trimmed, "```json")
		trimmed = strings.TrimPrefix(trimmed, "```")
		trimmed = strings.TrimSpace(trimmed)
		if idx := strings.LastIndex(trimmed, "```"); idx >= 0 {
			trimmed = strings.TrimSpace(trimmed[:idx])
		}
	}
	start := strings.Index(trimmed, "{")
	end := strings.LastIndex(trimmed, "}")
	if start >= 0 && end > start {
		return trimmed[start : end+1]
	}
	return trimmed
}

func mergeMissingAssets(primary []vo.MissingAssetVo, fallback []vo.MissingAssetVo) []vo.MissingAssetVo {
	result := append([]vo.MissingAssetVo{}, primary...)
	result = append(result, fallback...)
	return uniqueMissingAssets(result)
}

func uniqueMissingAssets(items []vo.MissingAssetVo) []vo.MissingAssetVo {
	seen := map[string]bool{}
	result := make([]vo.MissingAssetVo, 0, len(items))
	for _, item := range items {
		assetKey := strings.TrimSpace(item.AssetKey)
		key := assetKey + "|" + strings.TrimSpace(item.Name)
		if key == "|" {
			continue
		}
		if seen[key] {
			if len(result) > 0 && assetKey != "" {
				for i := range result {
					if result[i].AssetKey == assetKey {
						result[i].PlacementRefs = uniqueStrings(append(result[i].PlacementRefs, item.PlacementRefs...))
						break
					}
				}
			}
			continue
		}
		seen[key] = true
		result = append(result, item)
	}
	return result
}

func filterAvailableMissingAssets(items []vo.MissingAssetVo, catalog semanticAssetCatalog) []vo.MissingAssetVo {
	result := make([]vo.MissingAssetVo, 0, len(items))
	for _, item := range uniqueMissingAssets(items) {
		assetKey := strings.TrimSpace(item.AssetKey)
		if itemKey, ok := catalog.byAlias[normalizeText(assetKey)]; ok {
			assetKey = itemKey
		}
		if asset, ok := catalog.byKey[assetKey]; ok && strings.TrimSpace(asset.URL) != "" {
			continue
		}
		if asset, ok := catalog.byKey[assetKey]; ok {
			item.AssetKey = asset.AssetKey
			if strings.TrimSpace(item.Name) == "" {
				item.Name = asset.Name
			}
			if strings.TrimSpace(item.Category) == "" {
				item.Category = asset.Category
			}
		}
		result = append(result, item)
	}
	return result
}

func filterMissingAssetWarnings(warnings []string, missing []vo.MissingAssetVo) []string {
	if len(missing) > 0 {
		return warnings
	}
	result := make([]string, 0, len(warnings))
	for _, warning := range warnings {
		if strings.Contains(warning, "LLM 未启用") ||
			strings.Contains(warning, "LLM 配置不完整") ||
			strings.Contains(warning, "白名单工具流水线") ||
			strings.Contains(warning, "跳过加载") ||
			strings.Contains(warning, "缺失") ||
			strings.Contains(warning, "模型URL") ||
			strings.Contains(warning, "没有可用模型") {
			continue
		}
		result = append(result, warning)
	}
	return result
}

func (s *SemanticService) enrichMissingAssetWorkflow(resp *vo.SemanticBuildResponse, ownerKey string, catalog semanticAssetCatalog) {
	if resp == nil || len(resp.MissingAssets) == 0 {
		return
	}
	ownerKey = strings.TrimSpace(ownerKey)
	jobsByAsset := s.latestAssetJobsByKey(ownerKey)
	for i := range resp.MissingAssets {
		asset := &resp.MissingAssets[i]
		if item, ok := catalog.byKey[asset.AssetKey]; ok {
			if strings.TrimSpace(asset.Name) == "" {
				asset.Name = item.Name
			}
			if strings.TrimSpace(asset.Category) == "" {
				asset.Category = item.Category
			}
		}
		if strings.TrimSpace(asset.Prompt) == "" {
			asset.Prompt = buildMissingAssetPrompt(*asset)
		}
		if strings.TrimSpace(asset.FallbackModelKey) == "" {
			asset.FallbackModelKey = "placeholder.device"
		}
		routing := s.assetRouter.Decide(vo.AssetFidelityRoutingRequest{
			AssetKey:      asset.AssetKey,
			ObjectType:    objectTypeForAsset(asset.AssetKey, asset.Category),
			BusinessValue: "ordinary",
		})
		asset.Routing = &routing

		reference := s.referenceResolver.Resolve(*asset)
		generation := vo.MissingAssetGenerationVo{
			Enabled:      true,
			Status:       missingGenerationStatusWaiting,
			ReviewStatus: "personal_draft",
		}
		if routing.RequiresGenerationTask && reference.Status != missingReferenceStatusMissing {
			generation.TaskID = deterministicGenerationTaskID(ownerKey, asset.AssetKey, asset.PlacementRefs)
			generation.Status = missingGenerationStatusQueued
			generation.Progress = 5
		}
		if reference.Status == missingReferenceStatusResolved {
			generation.Status = missingGenerationStatusQueued
		}
		if job, ok := jobsByAsset[asset.AssetKey]; ok {
			reference.Status = missingReferenceStatusUploaded
			reference.Source = firstNonEmptySemanticAsset(job.ReferenceImageSource, "upload")
			reference.URL = job.SourceImageURL
			generation.TaskID = job.JobID
			generation.Status = mapAssetJobStatus(job.Status)
			generation.Progress = job.Progress
			generation.ResultURL = job.ModelURL
			generation.ThumbnailURL = job.ThumbURL
			generation.ErrorMessage = job.ErrorMsg
			generation.ReviewStatus = reviewStatusForAssetJob(job.Status)
		}
		asset.ReferenceImage = &reference
		asset.Generation = &generation
		for j := range resp.Models {
			model := &resp.Models[j]
			if model.Meta.Placeholder && model.Meta.MissingAssetKey == asset.AssetKey {
				model.Meta.GenerationTaskID = generation.TaskID
			}
		}
	}
}

func deterministicGenerationTaskID(ownerKey string, assetKey string, placementRefs []string) string {
	seed := strings.TrimSpace(ownerKey) + "|" + strings.TrimSpace(assetKey) + "|" + strings.Join(placementRefs, ",")
	if seed == "||" {
		seed = "anonymous|asset|placeholder"
	}
	sum := sha1.Sum([]byte(seed))
	return fmt.Sprintf("asset-job-%x", sum[:6])
}

func objectTypeForAsset(assetKey string, category string) string {
	switch strings.TrimSpace(assetKey) {
	case "greenhouse":
		return string(vo.ObjectTypeGreenhouse)
	case "tomato", "corn", "wheat", "rice", "lettuce", "pumpkin":
		return string(vo.ObjectTypePlant)
	case "sensor", "weather_station":
		return string(vo.ObjectTypeSensor)
	case "camera":
		return string(vo.ObjectTypeCamera)
	case "irrigation", "water_tower":
		return string(vo.ObjectTypeDevice)
	case "road", "fence":
		return "Infrastructure"
	default:
		if strings.TrimSpace(category) == "device" {
			return string(vo.ObjectTypeDevice)
		}
		return "SceneObject"
	}
}

func (s *SemanticService) latestAssetJobsByKey(ownerKey string) map[string]mapper.AssetJobRecord {
	result := map[string]mapper.AssetJobRecord{}
	if ownerKey == "" || s.assetMapper == nil {
		return result
	}
	jobs, err := s.assetMapper.ListByOwner(ownerKey)
	if err != nil {
		return result
	}
	for _, job := range jobs {
		assetKey := strings.TrimSpace(job.AssetKey)
		if assetKey == "" {
			continue
		}
		if _, ok := result[assetKey]; !ok {
			result[assetKey] = job
		}
	}
	return result
}

func mapAssetJobStatus(status string) string {
	switch strings.TrimSpace(status) {
	case "queued":
		return missingGenerationStatusQueued
	case "running":
		return missingGenerationStatusRunning
	case "completed", "approved":
		return missingGenerationStatusDone
	case "failed", "rejected":
		return missingGenerationStatusFailed
	default:
		return missingGenerationStatusWaiting
	}
}

func reviewStatusForAssetJob(status string) string {
	switch strings.TrimSpace(status) {
	case "approved":
		return "approved"
	case "rejected":
		return "rejected"
	case "completed":
		return "personal_draft"
	default:
		return ""
	}
}

func firstNonEmptySemanticAsset(items ...string) string {
	for _, item := range items {
		if strings.TrimSpace(item) != "" {
			return strings.TrimSpace(item)
		}
	}
	return ""
}

func contextWithTimeout(timeout time.Duration) (context.Context, context.CancelFunc) {
	return context.WithTimeout(context.Background(), timeout)
}

func semanticAssets() []vo.AssetSemantic {
	return []vo.AssetSemantic{
		asset("greenhouse", "温室大棚", []string{"温室", "大棚", "玻璃温室", "暖棚"}, "facility", "/scene-assets/models/Silo_House.glb", 0.9, 140, 90, "row", "column", "grid", "east", "west"),
		asset("corn", "玉米地", []string{"玉米", "玉米田", "玉米地", "农田"}, "crop", "/scene-assets/models/Corn_Crop.glb", 1.1, 90, 90, "grid", "row", "west", "east"),
		asset("wheat", "小麦田", []string{"小麦", "麦田", "小麦田"}, "crop", "/scene-assets/models/Wheat_Crop.glb", 1.1, 90, 90, "grid", "row", "west", "east"),
		asset("rice", "水稻田", []string{"水稻", "稻田", "水田"}, "crop", "/scene-assets/models/Rice_Crop.glb", 1.0, 90, 90, "grid", "row", "west", "east"),
		asset("tomato", "番茄种植区", []string{"番茄", "西红柿", "番茄田"}, "crop", "/scene-assets/models/Tomato_Crop.glb", 1.0, 80, 80, "grid", "row"),
		asset("lettuce", "生菜种植区", []string{"生菜", "叶菜", "蔬菜地"}, "crop", "/scene-assets/models/Lettuce_Crop.glb", 1.0, 80, 80, "grid", "row"),
		asset("pumpkin", "南瓜种植区", []string{"南瓜", "南瓜地"}, "crop", "/scene-assets/models/Pumpkin_Crop.glb", 1.0, 80, 80, "grid", "row"),
		asset("weather_station", "气象站", []string{"气象站", "环境监测站", "气象设备", "监测站"}, "device", "/scene-assets/models/TowerWindmill.glb", 0.7, 60, 60, "center", "single"),
		asset("irrigation", "灌溉设备", []string{"灌溉", "灌溉设备", "水泵", "喷灌", "滴灌"}, "device", "/scene-assets/models/Well.glb", 0.8, 50, 50, "center", "along_path", "row"),
		asset("water_tower", "水塔", []string{"水塔", "蓄水塔", "供水塔"}, "facility", "/scene-assets/models/WaterTower.glb", 0.8, 70, 70, "north", "south", "single"),
		asset("warehouse", "仓库", []string{"仓库", "农资仓库", "库房"}, "building", "/scene-assets/models/BigBarn.glb", 0.95, 130, 100, "north", "south", "single"),
		asset("admin_building", "管理楼", []string{"管理楼", "办公楼", "办公区", "管理中心"}, "building", "/scene-assets/models/building-type-i.glb", 0.9, 110, 110, "north", "south", "single"),
		asset("road", "道路", []string{"道路", "主路", "道路贯穿", "路"}, "infrastructure", "/scene-assets/models/path-long.glb", 1.2, 80, 220, "center", "along_path", "column"),
		asset("fence", "围栏", []string{"围栏", "栅栏", "围挡"}, "infrastructure", "/scene-assets/models/fence-3x3.glb", 1.0, 100, 30, "row", "along_path"),
		asset("windmill", "风车", []string{"风车", "风力", "风机"}, "facility", "/scene-assets/models/Windmill.glb", 0.9, 70, 70, "north", "single"),
		asset("solar", "光伏板", []string{"光伏", "太阳能", "太阳能板"}, "energy", "/models/solar.glb", 0.8, 100, 70, "row", "grid", "south"),
		asset("camera", "摄像头", []string{"摄像头", "监控", "监控杆", "摄像机"}, "device", "", 0.5, 35, 35, "along_path", "row"),
		asset("sensor", "传感器", []string{"传感器", "土壤传感器", "环境传感器"}, "device", "", 0.45, 35, 35, "row", "grid"),
		asset("tractor", "农机", []string{"拖拉机", "农机", "巡检车"}, "vehicle", "", 0.7, 80, 50, "single", "along_path"),
		asset("drone", "无人机", []string{"无人机", "巡检无人机"}, "vehicle", "", 0.4, 40, 40, "center", "single"),
	}
}

func asset(key string, name string, aliases []string, category string, url string, scale float64, width float64, depth float64, rules ...string) vo.AssetSemantic {
	return vo.AssetSemantic{
		AssetKey:     key,
		Name:         name,
		Aliases:      aliases,
		Category:     category,
		URL:          url,
		DefaultScale: scale,
		Footprint:    vo.FootprintVo{Width: width, Depth: depth},
		LayoutRules:  rules,
	}
}

func parseSemanticIntent(message string) semanticIntent {
	text := normalizeText(message)
	intent := semanticIntent{
		template: "custom",
		objects:  map[string]objectIntent{},
	}

	if semanticHasAny(text, "综合园区", "农业园区", "示范园区", "园区") {
		intent.template = "park"
		mergeDefault(intent.objects, "road", 1, "center", "along_path")
		mergeDefault(intent.objects, "greenhouse", 3, "east", "column")
		mergeDefault(intent.objects, "corn", 6, "west", "grid")
		mergeDefault(intent.objects, "weather_station", 1, "center", "single")
		mergeDefault(intent.objects, "irrigation", 2, "center", "along_path")
		mergeDefault(intent.objects, "warehouse", 1, "north", "single")
		mergeDefault(intent.objects, "admin_building", 1, "north", "single")
	}
	if semanticHasAny(text, "标准温室", "温室场景", "大棚场景") {
		intent.template = "greenhouse"
		mergeDefault(intent.objects, "greenhouse", 2, "east", "column")
		mergeDefault(intent.objects, "irrigation", 2, "center", "row")
		mergeDefault(intent.objects, "sensor", 2, "east", "row")
	}
	if semanticHasAny(text, "农田", "田", "种植") {
		mergeDefault(intent.objects, "wheat", 4, "west", "grid")
		mergeDefault(intent.objects, "weather_station", 1, "center", "single")
	}
	if semanticHasAny(text, "补设备", "补齐", "补充设备", "增加设备", "加设备") {
		mergeDefault(intent.objects, "camera", 2, "center", "along_path")
		mergeDefault(intent.objects, "weather_station", 1, "center", "single")
		mergeDefault(intent.objects, "water_tower", 1, "south", "single")
		mergeDefault(intent.objects, "irrigation", 2, "center", "along_path")
	}

	assets := semanticAssets()
	for _, item := range assets {
		if !matchesAsset(text, item) {
			continue
		}
		count := extractCountNear(text, append([]string{item.Name, item.AssetKey}, item.Aliases...))
		if count <= 0 {
			count = defaultCount(item.AssetKey)
		}
		area := inferAreaNear(text, append([]string{item.Name}, item.Aliases...))
		if area == "" {
			area = defaultArea(item.AssetKey)
		}
		layout := inferLayout(text, item.AssetKey, count)
		mergeDefault(intent.objects, item.AssetKey, count, area, layout)
	}

	if len(intent.objects) == 0 {
		intent.template = "park"
		mergeDefault(intent.objects, "road", 1, "center", "along_path")
		mergeDefault(intent.objects, "greenhouse", 2, "east", "column")
		mergeDefault(intent.objects, "corn", 4, "west", "grid")
		mergeDefault(intent.objects, "weather_station", 1, "center", "single")
		intent.warnings = append(intent.warnings, "未识别到明确资产，已使用智慧农业园区默认模板。")
	}

	if _, ok := intent.objects["road"]; !ok && semanticHasAny(text, "沿路", "道路", "主路", "路边", "贯穿") {
		mergeDefault(intent.objects, "road", 1, "center", "along_path")
	}
	applyTomatoGreenhouseMVPPromptOverrides(text, intent.objects)

	return intent
}

func applyTomatoGreenhouseMVPPromptOverrides(text string, objects map[string]objectIntent) {
	if !semanticHasAny(text, "番茄温室") {
		return
	}
	if semanticHasAny(text, "20株番茄", "20个番茄", "20棵番茄", "二十株番茄", "二十个番茄", "二十棵番茄") {
		mergeDefault(objects, "tomato", 20, "west", "grid")
	}
	if semanticHasAny(text, "气象站", "水泵", "摄像头", "传感器") {
		setObjectIntent(objects, "greenhouse", 1, "center", "single")
	}
	if semanticHasAny(text, "气象站") {
		setObjectIntent(objects, "weather_station", 1, "center", "single")
	}
	if semanticHasAny(text, "水泵", "灌溉设备") {
		setObjectIntent(objects, "irrigation", 1, "center", "single")
	}
	if semanticHasAny(text, "摄像头", "摄像机", "监控") {
		setObjectIntent(objects, "camera", 1, "south", "single")
	}
	if semanticHasAny(text, "传感器") {
		setObjectIntent(objects, "sensor", 1, "center", "single")
	}
}

func (s *SemanticService) expandPlanObjects(intent semanticIntent) []vo.ScenePlanObject {
	assetByKey := map[string]vo.AssetSemantic{}
	for _, item := range semanticAssets() {
		assetByKey[item.AssetKey] = item
	}

	keys := make([]string, 0, len(intent.objects))
	for key := range intent.objects {
		keys = append(keys, key)
	}
	sort.SliceStable(keys, func(i, j int) bool {
		return objectOrder(keys[i]) < objectOrder(keys[j])
	})

	objects := make([]vo.ScenePlanObject, 0, len(keys))
	for _, key := range keys {
		item := intent.objects[key]
		assetInfo, ok := assetByKey[key]
		if !ok {
			continue
		}
		count := item.count
		if count <= 0 {
			count = 1
		}
		objects = append(objects, vo.ScenePlanObject{
			ID:       fmt.Sprintf("%s_group", key),
			Label:    assetInfo.Name,
			Category: assetInfo.Category,
			AssetKey: key,
			URL:      assetInfo.URL,
			Count:    clampInt(count, 1, 24),
			Layout:   item.layout,
			Area:     item.area,
			Scale:    assetInfo.DefaultScale,
			Size:     assetInfo.Footprint,
			Aliases:  assetInfo.Aliases,
		})
	}
	return objects
}

func solveLayout(objects []vo.ScenePlanObject, ground vo.GroundPlan) ([]vo.BuildModel, []vo.MissingAssetVo, []string) {
	models := make([]vo.BuildModel, 0)
	missing := make([]vo.MissingAssetVo, 0)
	warnings := make([]string, 0)
	occupied := make([]vo.OffsetVo, 0)

	for idx, obj := range objects {
		if strings.TrimSpace(obj.URL) == "" {
			points := layoutPoints(obj, ground, idx)
			placementRefs := make([]string, 0, len(points))
			for i, point := range points {
				point = avoidCollision(point, occupied, obj.Size)
				occupied = append(occupied, point)
				placeholderID := fmt.Sprintf("%s_placeholder_%02d", obj.AssetKey, i+1)
				placementRefs = append(placementRefs, placeholderID)
				models = append(models, vo.BuildModel{
					URL: "/scene/models/dir.glb",
					Options: vo.BuildModelOptions{
						Offset: point,
						Scale:  obj.Scale,
						Angle:  angleFor(obj, i),
					},
					Meta: vo.BuildModelMeta{
						ID:              placeholderID,
						Label:           numberedLabel(obj.Label+"占位", obj.Count, i),
						AssetKey:        "placeholder.device",
						Category:        obj.Category,
						Area:            obj.Area,
						Layout:          obj.Layout,
						Placeholder:     true,
						MissingAssetKey: obj.AssetKey,
					},
				})
			}
			missing = append(missing, vo.MissingAssetVo{
				AssetKey:         obj.AssetKey,
				Name:             obj.Label,
				Category:         obj.Category,
				Reason:           "mock 语义表已识别该资产，但当前模型库没有可用 GLB，已放置占位模型并等待补资产。",
				FallbackModelKey: "placeholder.device",
				PlacementRefs:    placementRefs,
			})
			continue
		}

		points := layoutPoints(obj, ground, idx)
		for i, point := range points {
			point = avoidCollision(point, occupied, obj.Size)
			occupied = append(occupied, point)
			models = append(models, vo.BuildModel{
				URL: obj.URL,
				Options: vo.BuildModelOptions{
					Offset: point,
					Scale:  obj.Scale,
					Angle:  angleFor(obj, i),
				},
				Meta: vo.BuildModelMeta{
					ID:       fmt.Sprintf("%s_%02d", obj.AssetKey, i+1),
					Label:    numberedLabel(obj.Label, obj.Count, i),
					AssetKey: obj.AssetKey,
					Category: obj.Category,
					Area:     obj.Area,
					Layout:   obj.Layout,
				},
			})
		}
	}

	if len(missing) > 0 {
		warnings = append(warnings, "部分语义资产没有可用 GLB，已放置占位模型并进入补资产流程。")
	}
	return models, missing, warnings
}

func layoutPoints(obj vo.ScenePlanObject, ground vo.GroundPlan, groupIndex int) []vo.OffsetVo {
	count := clampInt(obj.Count, 1, 24)
	areaCenter := areaCenter(obj.Area, ground, groupIndex)
	spacingX := math.Max(obj.Size.Width+35, 95)
	spacingZ := math.Max(obj.Size.Depth+35, 95)
	layout := obj.Layout
	if layout == "" {
		layout = inferLayout("", obj.AssetKey, count)
	}

	points := make([]vo.OffsetVo, 0, count)
	switch layout {
	case "row":
		start := -float64(count-1) * spacingX / 2
		for i := 0; i < count; i++ {
			points = append(points, vo.OffsetVo{X: areaCenter.X + start + float64(i)*spacingX, Y: 0, Z: areaCenter.Z})
		}
	case "column":
		start := -float64(count-1) * spacingZ / 2
		for i := 0; i < count; i++ {
			points = append(points, vo.OffsetVo{X: areaCenter.X, Y: 0, Z: areaCenter.Z + start + float64(i)*spacingZ})
		}
	case "grid":
		cols := int(math.Ceil(math.Sqrt(float64(count))))
		rows := int(math.Ceil(float64(count) / float64(cols)))
		for i := 0; i < count; i++ {
			col := i % cols
			row := i / cols
			x := areaCenter.X + (float64(col)-float64(cols-1)/2)*spacingX
			z := areaCenter.Z + (float64(row)-float64(rows-1)/2)*spacingZ
			points = append(points, vo.OffsetVo{X: x, Y: 0, Z: z})
		}
	case "along_path":
		start := -float64(count-1) * spacingZ / 2
		x := areaCenter.X
		if obj.AssetKey != "road" {
			x += 70
		}
		for i := 0; i < count; i++ {
			points = append(points, vo.OffsetVo{X: x, Y: 0, Z: areaCenter.Z + start + float64(i)*spacingZ})
		}
	default:
		if count == 1 {
			points = append(points, areaCenter)
		} else {
			return layoutPoints(withLayout(obj, "grid"), ground, groupIndex)
		}
	}
	return clampPoints(points, ground)
}

func withLayout(obj vo.ScenePlanObject, layout string) vo.ScenePlanObject {
	obj.Layout = layout
	return obj
}

func areaCenter(area string, ground vo.GroundPlan, groupIndex int) vo.OffsetVo {
	w := ground.Width
	h := ground.Height
	if w <= 0 {
		w = 1200
	}
	if h <= 0 {
		h = 1000
	}

	switch area {
	case "west", "left":
		return vo.OffsetVo{X: -w * 0.25, Y: 0, Z: 0}
	case "east", "right":
		return vo.OffsetVo{X: w * 0.25, Y: 0, Z: 0}
	case "north":
		return vo.OffsetVo{X: -w*0.16 + float64(groupIndex%3)*w*0.16, Y: 0, Z: -h * 0.32}
	case "south":
		return vo.OffsetVo{X: -w*0.16 + float64(groupIndex%3)*w*0.16, Y: 0, Z: h * 0.32}
	case "northwest":
		return vo.OffsetVo{X: -w * 0.28, Y: 0, Z: -h * 0.28}
	case "northeast":
		return vo.OffsetVo{X: w * 0.28, Y: 0, Z: -h * 0.28}
	case "southwest":
		return vo.OffsetVo{X: -w * 0.28, Y: 0, Z: h * 0.28}
	case "southeast":
		return vo.OffsetVo{X: w * 0.28, Y: 0, Z: h * 0.28}
	default:
		return vo.OffsetVo{X: 0, Y: 0, Z: 0}
	}
}

func avoidCollision(point vo.OffsetVo, occupied []vo.OffsetVo, size vo.FootprintVo) vo.OffsetVo {
	minDistance := math.Max(size.Width, size.Depth) * 0.55
	if minDistance < 70 {
		minDistance = 70
	}
	next := point
	for attempt := 0; attempt < 8; attempt++ {
		collides := false
		for _, item := range occupied {
			if distance2D(next, item) < minDistance {
				collides = true
				break
			}
		}
		if !collides {
			return next
		}
		next.X += minDistance
		next.Z += minDistance * 0.35
	}
	return next
}

func clampPoints(points []vo.OffsetVo, ground vo.GroundPlan) []vo.OffsetVo {
	margin := 60.0
	maxX := ground.Width/2 - margin
	maxZ := ground.Height/2 - margin
	if maxX <= margin {
		maxX = 540
	}
	if maxZ <= margin {
		maxZ = 440
	}
	for i := range points {
		points[i].X = clampFloat(points[i].X, -maxX, maxX)
		points[i].Z = clampFloat(points[i].Z, -maxZ, maxZ)
	}
	return points
}

func angleFor(obj vo.ScenePlanObject, index int) float64 {
	switch obj.AssetKey {
	case "road":
		return 0
	case "greenhouse":
		if obj.Layout == "row" {
			return 90
		}
		return 0
	case "solar":
		return 15
	case "warehouse", "admin_building":
		if obj.Area == "north" {
			return 180
		}
	}
	if obj.Layout == "along_path" && index%2 == 1 {
		return 180
	}
	return 0
}

func inferSceneName(message string) string {
	switch {
	case semanticHasAny(message, "综合园区", "农业园区", "示范园区"):
		return "智慧农业示范园区"
	case semanticHasAny(message, "标准温室", "温室"):
		return "标准温室场景"
	case semanticHasAny(message, "补设备", "补齐"):
		return "设备补齐草稿"
	default:
		return "AI搭建草稿"
	}
}

func inferGround(template string, objectCount int) vo.GroundPlan {
	width := 1200.0
	height := 1000.0
	if template == "park" || objectCount > 5 {
		width = 1500
		height = 1300
	}
	if template == "greenhouse" {
		width = 900
		height = 900
	}
	return vo.GroundPlan{Width: width, Height: height, Color: "#88aa66", Terrain: "field"}
}

func inferRelations(objects []vo.ScenePlanObject, message string) []vo.SceneRelation {
	relations := make([]vo.SceneRelation, 0)
	keys := map[string]bool{}
	for _, obj := range objects {
		keys[obj.AssetKey] = true
	}
	if keys["weather_station"] {
		relations = append(relations, vo.SceneRelation{Subject: "weather_station", Predicate: "near", Object: "field_center"})
	}
	if keys["irrigation"] && (keys["greenhouse"] || keys["corn"] || keys["wheat"]) {
		relations = append(relations, vo.SceneRelation{Subject: "irrigation", Predicate: "serve", Object: "crop_or_greenhouse"})
	}
	if keys["road"] && semanticHasAny(message, "沿路", "道路", "贯穿") {
		relations = append(relations, vo.SceneRelation{Subject: "road", Predicate: "through", Object: "scene_center"})
	}
	return relations
}

func mergeDefault(objects map[string]objectIntent, assetKey string, count int, area string, layout string) {
	current, ok := objects[assetKey]
	if ok {
		if count > current.count {
			current.count = count
		}
		if area != "" && current.area == "" || explicitArea(area) {
			current.area = area
		}
		if layout != "" {
			current.layout = layout
		}
		objects[assetKey] = current
		return
	}
	objects[assetKey] = objectIntent{assetKey: assetKey, count: count, area: area, layout: layout}
}

func setObjectIntent(objects map[string]objectIntent, assetKey string, count int, area string, layout string) {
	objects[assetKey] = objectIntent{assetKey: assetKey, count: count, area: area, layout: layout}
}

func matchesAsset(text string, item vo.AssetSemantic) bool {
	for _, alias := range append([]string{item.Name, item.AssetKey}, item.Aliases...) {
		if alias != "" && strings.Contains(text, normalizeText(alias)) {
			return true
		}
	}
	return false
}

func extractCountNear(text string, terms []string) int {
	best := 0
	for _, term := range terms {
		term = normalizeText(term)
		if term == "" {
			continue
		}
		patterns := []string{
			`([一二两三四五六七八九十0-9]+)\s*(个|座|块|条|台|套|株|棵)?\s*` + regexp.QuoteMeta(term),
			regexp.QuoteMeta(term) + `\s*([一二两三四五六七八九十0-9]+)\s*(个|座|块|条|台|套|株|棵)?`,
		}
		for _, pattern := range patterns {
			re := regexp.MustCompile(pattern)
			matches := re.FindAllStringSubmatch(text, -1)
			for _, match := range matches {
				if len(match) > 1 {
					if n := parseChineseNumber(match[1]); n > best {
						best = n
					}
				}
			}
		}
	}
	return clampInt(best, 0, 24)
}

func inferAreaNear(text string, terms []string) string {
	areaTerms := []struct {
		area  string
		words []string
	}{
		{"west", []string{"左侧", "左边", "西侧", "西边"}},
		{"east", []string{"右侧", "右边", "东侧", "东边"}},
		{"north", []string{"北侧", "北边", "上方"}},
		{"south", []string{"南侧", "南边", "下方", "入口"}},
		{"center", []string{"中间", "中央", "中心"}},
	}

	for _, item := range areaTerms {
		for _, areaWord := range item.words {
			areaIndex := strings.Index(text, areaWord)
			if areaIndex < 0 {
				continue
			}
			for _, term := range terms {
				termIndex := strings.Index(text, normalizeText(term))
				if termIndex >= 0 && math.Abs(float64(termIndex-areaIndex)) <= 16 {
					return item.area
				}
			}
		}
	}
	return ""
}

func inferLayout(text string, assetKey string, count int) string {
	if semanticHasAny(text, "沿路", "沿道路", "路边", "贯穿") && (assetKey == "road" || assetKey == "camera" || assetKey == "irrigation" || assetKey == "tractor") {
		return "along_path"
	}
	if semanticHasAny(text, "网格", "矩阵", "方阵") {
		return "grid"
	}
	if semanticHasAny(text, "纵向", "竖排", "一列") {
		return "column"
	}
	if semanticHasAny(text, "横向", "横排", "一行") {
		return "row"
	}
	if assetKey == "road" {
		return "along_path"
	}
	if count == 1 {
		return "single"
	}
	if assetKey == "greenhouse" {
		return "column"
	}
	if assetKey == "camera" || assetKey == "irrigation" {
		return "along_path"
	}
	return "grid"
}

func defaultCount(assetKey string) int {
	switch assetKey {
	case "corn", "wheat", "rice", "tomato", "lettuce", "pumpkin":
		return 4
	case "greenhouse":
		return 2
	case "camera", "sensor", "irrigation":
		return 2
	default:
		return 1
	}
}

func defaultArea(assetKey string) string {
	switch assetKey {
	case "corn", "wheat", "rice", "tomato", "lettuce", "pumpkin":
		return "west"
	case "greenhouse":
		return "east"
	case "warehouse", "admin_building", "windmill":
		return "north"
	case "water_tower":
		return "south"
	default:
		return "center"
	}
}

func explicitArea(area string) bool {
	return area == "west" || area == "east" || area == "north" || area == "south" || area == "center"
}

func objectOrder(key string) int {
	order := map[string]int{
		"road":            0,
		"corn":            10,
		"wheat":           11,
		"rice":            12,
		"tomato":          13,
		"lettuce":         14,
		"pumpkin":         15,
		"greenhouse":      20,
		"weather_station": 30,
		"irrigation":      31,
		"water_tower":     32,
		"warehouse":       40,
		"admin_building":  41,
		"camera":          50,
		"sensor":          51,
	}
	if n, ok := order[key]; ok {
		return n
	}
	return 100
}

func numberedLabel(label string, total int, index int) string {
	if total <= 1 {
		return label
	}
	return fmt.Sprintf("%s %d", label, index+1)
}

func distance2D(a vo.OffsetVo, b vo.OffsetVo) float64 {
	dx := a.X - b.X
	dz := a.Z - b.Z
	return math.Sqrt(dx*dx + dz*dz)
}

func normalizeText(text string) string {
	text = strings.ToLower(text)
	text = strings.ReplaceAll(text, " ", "")
	text = strings.ReplaceAll(text, "_", "")
	text = strings.ReplaceAll(text, "-", "")
	text = strings.ReplaceAll(text, ".", "")
	text = strings.ReplaceAll(text, "/", "")
	text = strings.ReplaceAll(text, "\\", "")
	text = strings.ReplaceAll(text, "，", ",")
	text = strings.ReplaceAll(text, "。", ".")
	return text
}

func semanticHasAny(text string, words ...string) bool {
	normalized := normalizeText(text)
	for _, word := range words {
		if strings.Contains(normalized, normalizeText(word)) {
			return true
		}
	}
	return false
}

func parseChineseNumber(raw string) int {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return 0
	}
	if n, err := strconv.Atoi(raw); err == nil {
		return n
	}
	digits := map[rune]int{
		'零': 0,
		'一': 1,
		'二': 2,
		'两': 2,
		'三': 3,
		'四': 4,
		'五': 5,
		'六': 6,
		'七': 7,
		'八': 8,
		'九': 9,
	}
	if raw == "十" {
		return 10
	}
	if strings.Contains(raw, "十") {
		parts := strings.Split(raw, "十")
		tens := 1
		if parts[0] != "" {
			tens = digits[[]rune(parts[0])[0]]
		}
		ones := 0
		if len(parts) > 1 && parts[1] != "" {
			ones = digits[[]rune(parts[1])[0]]
		}
		return tens*10 + ones
	}
	runes := []rune(raw)
	if len(runes) == 1 {
		return digits[runes[0]]
	}
	return 0
}

func clampInt(value int, minValue int, maxValue int) int {
	if value < minValue {
		return minValue
	}
	if value > maxValue {
		return maxValue
	}
	return value
}

func clampFloat(value float64, minValue float64, maxValue float64) float64 {
	return math.Min(math.Max(value, minValue), maxValue)
}

func uniqueStrings(items []string) []string {
	seen := map[string]bool{}
	result := make([]string, 0, len(items))
	for _, item := range items {
		item = strings.TrimSpace(item)
		if item == "" || seen[item] {
			continue
		}
		seen[item] = true
		result = append(result, item)
	}
	return result
}
