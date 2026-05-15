package service

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"scene-server-go/config"
	"scene-server-go/iot"
	"scene-server-go/mapper"
	"scene-server-go/vo"
)

const assistantSystemPrompt = `你是智慧农业数字孪生平台的只读分析助手。
你只能根据工具返回的当前项目数据、已知建设计划和审计结论回答。
不要声称已经完成未完成的能力；遇到模拟数据、缺失能力、未配置 RAG 或未配置 LLM 时要明确说明。
禁止输出会修改数据库或控制设备的操作指令。`

type AssistantService struct {
	modelMapper  *mapper.ModelMapper
	sceneService *SceneService
	assetMapper  *mapper.AssetMapper
	deviceMapper *iot.DeviceMapper
	dataMapper   *iot.DataMapper
	alertMapper  *iot.AlertMapper
	monitorSvc   *MonitorService
	businessSvc  *BusinessService
	httpClient   *http.Client
}

func NewAssistantService() *AssistantService {
	return &AssistantService{
		modelMapper:  mapper.NewModelMapper(),
		sceneService: NewSceneService(),
		assetMapper:  mapper.NewAssetMapper(),
		deviceMapper: iot.NewDeviceMapper(),
		dataMapper:   iot.NewDataMapper(),
		alertMapper:  iot.NewAlertMapper(),
		monitorSvc:   NewMonitorService(),
		businessSvc:  NewBusinessService(),
		httpClient:   &http.Client{},
	}
}

func (s *AssistantService) Tools() []vo.AssistantToolVo {
	return []vo.AssistantToolVo{
		{Name: "model.stats", Label: "模型统计", Description: "统计模型数量、分类、缩略图和文件健康情况", ReadOnly: true},
		{Name: "model.list", Label: "模型列表", Description: "读取模型树摘要和分类分布", ReadOnly: true},
		{Name: "scene.list", Label: "场景列表", Description: "读取已保存场景列表", ReadOnly: true},
		{Name: "scene.load", Label: "场景详情", Description: "读取指定场景的基础配置和模型对象", ReadOnly: true},
		{Name: "iot.devices", Label: "IoT 设备", Description: "读取设备列表、在线状态和绑定关系", ReadOnly: true},
		{Name: "iot.latest", Label: "IoT 最新指标", Description: "读取设备最近指标数据", ReadOnly: true},
		{Name: "iot.alerts", Label: "告警数据", Description: "读取告警摘要、严重级别和未确认统计", ReadOnly: true},
		{Name: "monitor.dashboard", Label: "监控大屏", Description: "读取监控中心聚合数据", ReadOnly: true},
		{Name: "business.overview", Label: "业务总览", Description: "读取 6 个业务子系统完成度和缺口", ReadOnly: true},
		{Name: "asset.jobs", Label: "AI 资产任务", Description: "读取 AI 资产生成任务状态", ReadOnly: true},
	}
}

func (s *AssistantService) RAGStatus() vo.AssistantRAGStatusVo {
	enabled := config.AppConfig != nil && config.AppConfig.RAG.Enabled
	status := "reserved"
	message := "RAG 暂未启用，本期只预留知识库状态和返回结构。"
	if enabled {
		status = "enabled"
		message = "RAG 已启用，但当前版本尚未接入向量检索实现。"
	}
	return vo.AssistantRAGStatusVo{
		Enabled: enabled,
		Status:  status,
		Message: message,
		DocumentTypes: []string{
			"建设方案",
			"审计报告",
			"接口文档",
			"模型元数据",
			"运维记录",
		},
		Chunks: []vo.AssistantRAGChunkVo{},
	}
}

func (s *AssistantService) ContextSummary() vo.ResultVo {
	modelCall := s.runTool("model.stats", nil)
	sceneCall := s.runTool("scene.list", nil)
	deviceCall := s.runTool("iot.devices", nil)
	alertCall := s.runTool("iot.alerts", nil)
	businessCall := s.runTool("business.overview", nil)

	sceneCount := 0
	if data, ok := sceneCall.Data.(map[string]interface{}); ok {
		if count, ok := data["count"].(int); ok {
			sceneCount = count
		}
	}

	result := vo.AssistantContextSummaryVo{
		UpdatedAt:       time.Now().Format(time.RFC3339),
		ModelStats:      modelCall.Data,
		SceneCount:      sceneCount,
		DeviceSummary:   asMap(deviceCall.Data),
		AlertSummary:    asMap(alertCall.Data),
		BusinessSummary: businessCall.Data,
		RAG:             s.RAGStatus(),
	}
	return vo.ResultVo{Code: 200, Data: result}
}

func (s *AssistantService) Chat(req vo.AssistantChatRequest) vo.ResultVo {
	message := strings.TrimSpace(req.Message)
	if message == "" {
		return vo.ResultVo{Code: 999, Data: "message is required"}
	}

	sessionID := req.SessionID
	if sessionID == "" {
		sessionID = fmt.Sprintf("asst-%d", time.Now().UnixNano())
	}

	toolNames := s.pickTools(message, req.Context)
	toolCalls := make([]vo.AssistantToolCallVo, 0, len(toolNames))
	for _, name := range toolNames {
		toolCalls = append(toolCalls, s.runTool(name, req.Context))
	}

	citations := buildCitations(toolCalls)
	answer, err := s.callLLM(message, toolCalls)
	if err != nil {
		answer = s.fallbackAnswer(message, toolCalls, err)
	}

	return vo.ResultVo{Code: 200, Data: vo.AssistantChatResponse{
		SessionID: sessionID,
		Answer:    answer,
		ToolCalls: toolCalls,
		Citations: citations,
		RAGUsed:   false,
	}}
}

func (s *AssistantService) pickTools(message string, context map[string]interface{}) []string {
	text := strings.ToLower(message)
	selected := map[string]bool{}
	add := func(names ...string) {
		for _, name := range names {
			selected[name] = true
		}
	}

	if hasAny(text, "模型", "model", "资产", "glb", "缩略图", "风险") {
		add("model.stats", "model.list", "asset.jobs")
	}
	if hasAny(text, "场景", "scene", "孪生", "对象") {
		add("scene.list")
	}
	if hasAny(text, "iot", "设备", "传感器", "在线", "mqtt", "指标") {
		add("iot.devices", "iot.latest")
	}
	if hasAny(text, "告警", "报警", "预警", "未确认", "严重") {
		add("iot.alerts")
	}
	if hasAny(text, "监控", "大屏", "环境", "能耗", "产量") {
		add("monitor.dashboard")
	}
	if hasAny(text, "业务", "子系统", "完成度", "缺口", "缺少", "还缺", "审计", "平台") {
		add("business.overview", "model.stats", "iot.devices", "iot.alerts", "monitor.dashboard")
	}
	if _, ok := context["sceneName"]; ok {
		add("scene.load")
	}
	if _, ok := context["deviceId"]; ok {
		add("iot.latest", "iot.alerts")
	}
	if len(selected) == 0 {
		add("business.overview", "model.stats", "iot.devices", "iot.alerts", "monitor.dashboard")
	}

	order := []string{
		"business.overview",
		"model.stats",
		"model.list",
		"scene.list",
		"scene.load",
		"iot.devices",
		"iot.latest",
		"iot.alerts",
		"monitor.dashboard",
		"asset.jobs",
	}
	result := make([]string, 0, len(selected))
	for _, name := range order {
		if selected[name] {
			result = append(result, name)
		}
	}
	return result
}

func (s *AssistantService) runTool(name string, context map[string]interface{}) vo.AssistantToolCallVo {
	start := time.Now()
	call := vo.AssistantToolCallVo{
		Name:   name,
		Label:  s.toolLabel(name),
		Status: "success",
	}

	var (
		data interface{}
		err  error
	)
	switch name {
	case "model.stats":
		data, err = s.modelStats()
	case "model.list":
		data, err = s.modelList()
	case "scene.list":
		data, err = s.sceneList()
	case "scene.load":
		data, err = s.sceneLoad(context)
	case "iot.devices":
		data, err = s.iotDevices()
	case "iot.latest":
		data, err = s.iotLatest(context)
	case "iot.alerts":
		data, err = s.iotAlerts(context)
	case "monitor.dashboard":
		data = s.monitorSvc.GetDashboard().Data
	case "business.overview":
		data = s.businessSvc.GetOverview().Data
	case "asset.jobs":
		data, err = s.assetJobs()
	default:
		err = fmt.Errorf("unknown tool: %s", name)
	}

	call.Duration = time.Since(start).Milliseconds()
	if err != nil {
		call.Status = "error"
		call.Error = err.Error()
		call.Summary = "数据源暂不可用"
		return call
	}

	call.Data = compactData(data, 6000)
	call.Summary = summarizeTool(name, data)
	return call
}

func (s *AssistantService) modelStats() (map[string]interface{}, error) {
	list, err := s.modelMapper.SelectAll()
	if err != nil {
		return nil, err
	}

	byCategory := map[string]int{}
	missingURL := 0
	missingThumbnail := 0
	missingCategory := 0
	fileMissing := 0
	leafCount := 0
	folderCount := 0
	samples := make([]map[string]interface{}, 0, 8)

	for _, m := range list {
		if m.Leaf {
			leafCount++
			if m.URL == nil || strings.TrimSpace(*m.URL) == "" {
				missingURL++
			} else if isSceneAssetURL(*m.URL) && !assetFileExists(*m.URL) {
				fileMissing++
			}
			if strings.TrimSpace(m.Thumbnail) == "" {
				missingThumbnail++
			}
		} else {
			folderCount++
		}
		if strings.TrimSpace(m.Category) == "" {
			missingCategory++
		} else {
			byCategory[m.Category]++
		}
		if len(samples) < 8 && m.Leaf {
			url := ""
			if m.URL != nil {
				url = *m.URL
			}
			samples = append(samples, map[string]interface{}{
				"id":        m.Id,
				"name":      m.Name,
				"category":  m.Category,
				"url":       url,
				"thumbnail": m.Thumbnail,
			})
		}
	}

	return map[string]interface{}{
		"total":            len(list),
		"leafNodes":        leafCount,
		"folders":          folderCount,
		"byCategory":       byCategory,
		"missingURL":       missingURL,
		"missingThumbnail": missingThumbnail,
		"missingCategory":  missingCategory,
		"missingFile":      fileMissing,
		"sampleModels":     samples,
		"healthNotes": []string{
			"模型数量不等于模型质量，仍需补齐缩略图、版权、尺寸、面数、贴图大小、适用业务等元数据。",
			"前端 public/models 与后端 scene-assets/models 仍需统一资产来源。",
		},
	}, nil
}

func (s *AssistantService) modelList() (map[string]interface{}, error) {
	list, err := s.modelMapper.SelectAll()
	if err != nil {
		return nil, err
	}
	sort.Slice(list, func(i, j int) bool {
		if list[i].ParentId == list[j].ParentId {
			return list[i].Id < list[j].Id
		}
		return list[i].ParentId < list[j].ParentId
	})

	limit := 80
	items := make([]map[string]interface{}, 0, minInt(len(list), limit))
	for i, m := range list {
		if i >= limit {
			break
		}
		url := ""
		if m.URL != nil {
			url = *m.URL
		}
		items = append(items, map[string]interface{}{
			"id":       m.Id,
			"parentId": m.ParentId,
			"name":     m.Name,
			"leaf":     m.Leaf,
			"category": m.Category,
			"tags":     m.Tags,
			"url":      url,
		})
	}

	return map[string]interface{}{
		"count":     len(list),
		"returned":  len(items),
		"truncated": len(list) > limit,
		"items":     items,
	}, nil
}

func (s *AssistantService) sceneList() (map[string]interface{}, error) {
	result := s.sceneService.SceneList()
	if result.Code != 200 {
		return nil, fmt.Errorf("%v", result.Data)
	}
	list, _ := result.Data.([]string)
	return map[string]interface{}{
		"count": len(list),
		"items": list,
	}, nil
}

func (s *AssistantService) sceneLoad(context map[string]interface{}) (interface{}, error) {
	sceneName, _ := context["sceneName"].(string)
	if sceneName == "" {
		listData, err := s.sceneList()
		if err != nil {
			return nil, err
		}
		items, _ := listData["items"].([]string)
		if len(items) == 0 {
			return map[string]interface{}{"message": "暂无已保存场景"}, nil
		}
		sceneName = items[0]
	}

	result := s.sceneService.LoadScene(sceneName)
	if result.Code != 200 {
		return nil, fmt.Errorf("%v", result.Data)
	}
	return result.Data, nil
}

func (s *AssistantService) iotDevices() (map[string]interface{}, error) {
	devices, err := s.deviceMapper.FindAll()
	if err != nil {
		return nil, err
	}
	byType := map[string]int{}
	byStatus := map[string]int{}
	items := make([]map[string]interface{}, 0, len(devices))
	for _, d := range devices {
		byType[d.DeviceType]++
		byStatus[d.Status]++
		modelId := interface{}(nil)
		if d.ModelId != nil {
			modelId = *d.ModelId
		}
		items = append(items, map[string]interface{}{
			"deviceId":     d.DeviceId,
			"deviceName":   d.DeviceName,
			"deviceType":   d.DeviceType,
			"status":       d.Status,
			"modelId":      modelId,
			"mqttTopic":    d.MqttTopic,
			"lastDataTime": d.LastDataTime,
		})
	}
	return map[string]interface{}{
		"count":    len(devices),
		"byType":   byType,
		"byStatus": byStatus,
		"items":    items,
		"note":     "当前系统保留模拟器；真实 MQTT 接入仍需单独验收。",
	}, nil
}

func (s *AssistantService) iotLatest(context map[string]interface{}) (map[string]interface{}, error) {
	devices, err := s.deviceMapper.FindAll()
	if err != nil {
		return nil, err
	}
	deviceID, _ := context["deviceId"].(string)
	limitDevices := devices
	if deviceID != "" {
		limitDevices = nil
		for _, d := range devices {
			if d.DeviceId == deviceID {
				limitDevices = append(limitDevices, d)
				break
			}
		}
	}
	if len(limitDevices) > 8 {
		limitDevices = limitDevices[:8]
	}

	result := map[string]interface{}{}
	for _, d := range limitDevices {
		points, err := s.dataMapper.FindByDevice(d.DeviceId, 20)
		if err != nil {
			continue
		}
		metrics := map[string]interface{}{}
		for _, p := range points {
			if _, ok := metrics[p.MetricKey]; ok {
				continue
			}
			metrics[p.MetricKey] = map[string]interface{}{
				"value":     p.MetricValue,
				"unit":      p.Unit,
				"timestamp": p.Timestamp,
			}
		}
		result[d.DeviceId] = metrics
	}
	return map[string]interface{}{
		"devices": result,
		"note":    "每个设备只返回最近一批指标，避免把大量时序数据直接交给 LLM。",
	}, nil
}

func (s *AssistantService) iotAlerts(context map[string]interface{}) (map[string]interface{}, error) {
	deviceID, _ := context["deviceId"].(string)
	var (
		alerts []iot.AlertLog
		err    error
	)
	if deviceID != "" {
		alerts, err = s.alertMapper.FindByDevice(deviceID, 50)
	} else {
		alerts, err = s.alertMapper.FindRecent(50)
	}
	if err != nil {
		return nil, err
	}
	unacked, _ := s.alertMapper.CountUnacked()
	bySeverity := map[string]int{}
	items := make([]map[string]interface{}, 0, len(alerts))
	for _, a := range alerts {
		bySeverity[a.Severity]++
		items = append(items, map[string]interface{}{
			"id":           a.Id,
			"deviceId":     a.DeviceId,
			"severity":     a.Severity,
			"alertType":    a.AlertType,
			"message":      a.Message,
			"acknowledged": a.Acknowledged,
			"createdAt":    a.CreatedAt,
		})
	}
	return map[string]interface{}{
		"recentCount": len(alerts),
		"unacked":     unacked,
		"bySeverity":  bySeverity,
		"items":       items,
	}, nil
}

func (s *AssistantService) assetJobs() (map[string]interface{}, error) {
	jobs, err := s.assetMapper.ListByOwner("anonymous")
	if err != nil {
		return nil, err
	}
	approved, _ := s.assetMapper.ListApproved()
	byStatus := map[string]int{}
	items := make([]map[string]interface{}, 0, len(jobs))
	for _, j := range jobs {
		byStatus[j.Status]++
		if len(items) < 20 {
			items = append(items, map[string]interface{}{
				"jobId":     j.JobID,
				"status":    j.Status,
				"progress":  j.Progress,
				"modelName": j.ModelName,
				"modelUrl":  j.ModelURL,
				"updatedAt": j.UpdatedAt,
			})
		}
	}
	return map[string]interface{}{
		"owner":         "anonymous",
		"count":         len(jobs),
		"approvedCount": len(approved),
		"byStatus":      byStatus,
		"items":         items,
		"note":          "AI 资产生成依赖外部 Python 服务，当前接口仅汇总任务状态。",
	}, nil
}

func (s *AssistantService) callLLM(message string, toolCalls []vo.AssistantToolCallVo) (string, error) {
	if config.AppConfig == nil || !config.AppConfig.LLM.Enabled {
		return "", fmt.Errorf("LLM 未启用：请配置 llm.enabled/base-url/api-key/model")
	}
	if config.AppConfig.LLM.BaseURL == "" || config.AppConfig.LLM.APIKey == "" || config.AppConfig.LLM.Model == "" {
		return "", fmt.Errorf("LLM 配置不完整：请设置 base-url、api-key 和 model")
	}

	timeout := time.Duration(config.AppConfig.LLM.TimeoutSeconds) * time.Second
	if timeout <= 0 {
		timeout = 30 * time.Second
	}
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	payload := map[string]interface{}{
		"model": config.AppConfig.LLM.Model,
		"messages": []map[string]string{
			{"role": "system", "content": assistantSystemPrompt},
			{"role": "user", "content": buildLLMUserContent(message, toolCalls)},
		},
		"temperature": 0.2,
	}
	body, _ := json.Marshal(payload)

	url := config.LLMChatCompletionsURL()
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+config.AppConfig.LLM.APIKey)

	resp, err := s.httpClient.Do(req)
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

func (s *AssistantService) fallbackAnswer(message string, toolCalls []vo.AssistantToolCallVo, llmErr error) string {
	var b strings.Builder
	b.WriteString("我已读取当前项目的只读数据。")
	if llmErr != nil {
		b.WriteString("当前没有可用的真实 LLM 响应，原因是：")
		b.WriteString(llmErr.Error())
		b.WriteString("。\n\n")
	}
	b.WriteString("基于现有数据，初步结论如下：\n")
	for _, call := range toolCalls {
		b.WriteString("- ")
		b.WriteString(call.Label)
		b.WriteString("：")
		if call.Status == "success" {
			b.WriteString(call.Summary)
		} else {
			b.WriteString("暂不可用")
			if call.Error != "" {
				b.WriteString("（")
				b.WriteString(call.Error)
				b.WriteString("）")
			}
		}
		b.WriteString("\n")
	}
	b.WriteString("\n平台层面仍需重点补齐：模型元数据与缩略图、业务对象层、真实 MQTT 接入、视频流、控制闭环、权限审计、报表和 RAG 知识库。")
	return b.String()
}

func (s *AssistantService) toolLabel(name string) string {
	for _, tool := range s.Tools() {
		if tool.Name == name {
			return tool.Label
		}
	}
	return name
}

func hasAny(text string, words ...string) bool {
	for _, word := range words {
		if strings.Contains(text, strings.ToLower(word)) {
			return true
		}
	}
	return false
}

func buildCitations(toolCalls []vo.AssistantToolCallVo) []vo.AssistantCitationVo {
	citations := make([]vo.AssistantCitationVo, 0, len(toolCalls))
	for _, call := range toolCalls {
		if call.Status != "success" {
			continue
		}
		citations = append(citations, vo.AssistantCitationVo{
			Source:  call.Name,
			Title:   call.Label,
			Excerpt: call.Summary,
		})
	}
	return citations
}

func buildLLMUserContent(message string, toolCalls []vo.AssistantToolCallVo) string {
	toolJSON, _ := json.MarshalIndent(toolCalls, "", "  ")
	return fmt.Sprintf("用户问题：%s\n\n当前项目只读工具结果：\n%s\n\n请用中文回答，先给直接结论，再列证据和下一步建议。", message, string(toolJSON))
}

func summarizeTool(name string, data interface{}) string {
	switch name {
	case "model.stats":
		m := asMap(data)
		return fmt.Sprintf("共 %v 个模型节点，叶子模型 %v 个，缺缩略图 %v 个，缺 URL %v 个，文件缺失 %v 个。",
			m["total"], m["leafNodes"], m["missingThumbnail"], m["missingURL"], m["missingFile"])
	case "model.list":
		m := asMap(data)
		return fmt.Sprintf("返回 %v/%v 个模型树节点。", m["returned"], m["count"])
	case "scene.list":
		m := asMap(data)
		return fmt.Sprintf("当前保存场景 %v 个。", m["count"])
	case "scene.load":
		return "已读取场景配置和模型对象。"
	case "iot.devices":
		m := asMap(data)
		return fmt.Sprintf("当前 IoT 设备 %v 个，状态分布 %v。", m["count"], m["byStatus"])
	case "iot.latest":
		return "已读取设备最近指标快照。"
	case "iot.alerts":
		m := asMap(data)
		return fmt.Sprintf("最近告警 %v 条，未确认告警 %v 条，严重级别分布 %v。", m["recentCount"], m["unacked"], m["bySeverity"])
	case "monitor.dashboard":
		if d, ok := data.(vo.MonitorDashboardVo); ok {
			return fmt.Sprintf("监控大屏设备 %d 个，在线率 %.1f%%，未确认告警 %d，环境评分 %.1f。",
				d.Overview.DeviceTotal, d.Overview.OnlineRate, d.Overview.UnackedAlerts, d.Overview.EnvironmentScore)
		}
	case "business.overview":
		if d, ok := data.(vo.BusinessOverviewVo); ok {
			return fmt.Sprintf("业务子系统 %d 个，可演示 %d 个，部分完成 %d 个，完成度 %.1f%%。",
				d.Summary.SystemTotal, d.Summary.DemoReadyCount, d.Summary.PartialCount, d.Summary.CompletionRate)
		}
	case "asset.jobs":
		m := asMap(data)
		return fmt.Sprintf("anonymous 用户 AI 资产任务 %v 个，已审核公共资产 %v 个。", m["count"], m["approvedCount"])
	}
	return "工具调用成功。"
}

func compactData(data interface{}, limit int) interface{} {
	raw, err := json.Marshal(data)
	if err != nil || len(raw) <= limit {
		return data
	}
	return map[string]interface{}{
		"truncated": true,
		"preview":   string(raw[:limit]),
	}
}

func asMap(data interface{}) map[string]interface{} {
	if data == nil {
		return map[string]interface{}{}
	}
	if m, ok := data.(map[string]interface{}); ok {
		return m
	}
	raw, err := json.Marshal(data)
	if err != nil {
		return map[string]interface{}{}
	}
	var result map[string]interface{}
	if err := json.Unmarshal(raw, &result); err != nil {
		return map[string]interface{}{}
	}
	return result
}

func isSceneAssetURL(url string) bool {
	return strings.HasPrefix(url, "/scene-assets/")
}

func assetFileExists(url string) bool {
	rel := strings.TrimPrefix(url, "/")
	_, err := os.Stat(filepath.Clean(rel))
	return err == nil
}

func minInt(a, b int) int {
	if a < b {
		return a
	}
	return b
}
