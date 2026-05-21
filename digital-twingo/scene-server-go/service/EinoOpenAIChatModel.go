package service

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"scene-server-go/config"

	"github.com/cloudwego/eino/components/model"
	"github.com/cloudwego/eino/schema"
)

type einoOpenAIChatModel struct {
	httpClient *http.Client
	tools      []*schema.ToolInfo
}

type openAIChatMessage struct {
	Role       string           `json:"role"`
	Content    *string          `json:"content,omitempty"`
	Name       string           `json:"name,omitempty"`
	ToolCallID string           `json:"tool_call_id,omitempty"`
	ToolCalls  []openAIToolCall `json:"tool_calls,omitempty"`
}

type openAIToolCall struct {
	ID       string             `json:"id,omitempty"`
	Type     string             `json:"type,omitempty"`
	Function openAIFunctionCall `json:"function"`
}

type openAIFunctionCall struct {
	Name      string `json:"name"`
	Arguments string `json:"arguments"`
}

type openAIChatTool struct {
	Type     string             `json:"type"`
	Function openAIChatFunction `json:"function"`
}

type openAIChatFunction struct {
	Name        string      `json:"name"`
	Description string      `json:"description,omitempty"`
	Parameters  interface{} `json:"parameters,omitempty"`
}

type openAIChatPayload struct {
	Model       string              `json:"model"`
	Messages    []openAIChatMessage `json:"messages"`
	Tools       []openAIChatTool    `json:"tools,omitempty"`
	ToolChoice  string              `json:"tool_choice,omitempty"`
	Temperature *float32            `json:"temperature,omitempty"`
	TopP        *float32            `json:"top_p,omitempty"`
	MaxTokens   *int                `json:"max_tokens,omitempty"`
	Stream      bool                `json:"stream"`
	Thinking    interface{}         `json:"thinking,omitempty"`
}

func newEinoOpenAIChatModel(client *http.Client) *einoOpenAIChatModel {
	if client == nil {
		client = &http.Client{}
	}
	return &einoOpenAIChatModel{httpClient: client}
}

func (m *einoOpenAIChatModel) WithTools(tools []*schema.ToolInfo) (model.ToolCallingChatModel, error) {
	next := *m
	next.tools = append([]*schema.ToolInfo{}, tools...)
	return &next, nil
}

func (m *einoOpenAIChatModel) Generate(ctx context.Context, input []*schema.Message, opts ...model.Option) (*schema.Message, error) {
	if config.AppConfig == nil || !config.AppConfig.LLM.Enabled {
		return nil, fmt.Errorf("llm disabled")
	}
	if config.AppConfig.LLM.BaseURL == "" || config.AppConfig.LLM.APIKey == "" || config.AppConfig.LLM.Model == "" {
		return nil, fmt.Errorf("llm config incomplete")
	}

	common := model.GetCommonOptions(&model.Options{}, opts...)
	modelName := config.AppConfig.LLM.Model
	if common.Model != nil && strings.TrimSpace(*common.Model) != "" {
		modelName = strings.TrimSpace(*common.Model)
	}

	payload := openAIChatPayload{
		Model:       modelName,
		Messages:    toOpenAIMessages(input),
		Tools:       toOpenAITools(append([]*schema.ToolInfo{}, append(m.tools, common.Tools...)...)),
		Temperature: common.Temperature,
		TopP:        common.TopP,
		MaxTokens:   common.MaxTokens,
		Stream:      false,
	}
	if common.ToolChoice != nil {
		payload.ToolChoice = toOpenAIToolChoice(*common.ToolChoice)
	} else if len(payload.Tools) > 0 {
		payload.ToolChoice = "auto"
	}
	if isDeepSeekLLM() {
		payload.Thinking = map[string]string{"type": "disabled"}
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodPost, config.LLMChatCompletionsURL(), bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+config.AppConfig.LLM.APIKey)

	resp, err := m.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var result struct {
		Choices []struct {
			Message      openAIChatMessage `json:"message"`
			FinishReason string            `json:"finish_reason"`
		} `json:"choices"`
		Usage *struct {
			PromptTokens     int `json:"prompt_tokens"`
			CompletionTokens int `json:"completion_tokens"`
			TotalTokens      int `json:"total_tokens"`
		} `json:"usage"`
		Error *struct {
			Message string `json:"message"`
		} `json:"error"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}
	if resp.StatusCode >= 300 {
		if result.Error != nil && result.Error.Message != "" {
			return nil, fmt.Errorf("LLM error %d: %s", resp.StatusCode, result.Error.Message)
		}
		return nil, fmt.Errorf("LLM error status: %d", resp.StatusCode)
	}
	if len(result.Choices) == 0 {
		return nil, fmt.Errorf("LLM 返回为空")
	}

	choice := result.Choices[0]
	msg := fromOpenAIMessage(choice.Message)
	msg.ResponseMeta = &schema.ResponseMeta{FinishReason: choice.FinishReason}
	if result.Usage != nil {
		msg.ResponseMeta.Usage = &schema.TokenUsage{
			PromptTokens:     result.Usage.PromptTokens,
			CompletionTokens: result.Usage.CompletionTokens,
			TotalTokens:      result.Usage.TotalTokens,
		}
	}
	return msg, nil
}

func (m *einoOpenAIChatModel) Stream(ctx context.Context, input []*schema.Message, opts ...model.Option) (*schema.StreamReader[*schema.Message], error) {
	msg, err := m.Generate(ctx, input, opts...)
	if err != nil {
		return nil, err
	}
	return schema.StreamReaderFromArray([]*schema.Message{msg}), nil
}

func newEinoRunContext(timeout time.Duration) (context.Context, context.CancelFunc) {
	if timeout <= 0 {
		timeout = 30 * time.Second
	}
	return context.WithTimeout(context.Background(), timeout)
}

func toOpenAIMessages(input []*schema.Message) []openAIChatMessage {
	result := make([]openAIChatMessage, 0, len(input))
	for _, msg := range input {
		if msg == nil {
			continue
		}
		item := openAIChatMessage{
			Role:       string(msg.Role),
			Content:    stringPtr(msg.Content),
			Name:       msg.Name,
			ToolCallID: msg.ToolCallID,
		}
		if msg.Role == schema.Tool {
			item.Name = msg.ToolName
		}
		for _, call := range msg.ToolCalls {
			item.ToolCalls = append(item.ToolCalls, openAIToolCall{
				ID:   call.ID,
				Type: defaultString(call.Type, "function"),
				Function: openAIFunctionCall{
					Name:      call.Function.Name,
					Arguments: call.Function.Arguments,
				},
			})
		}
		result = append(result, item)
	}
	return result
}

func fromOpenAIMessage(input openAIChatMessage) *schema.Message {
	msg := &schema.Message{
		Role:    schema.RoleType(defaultString(input.Role, string(schema.Assistant))),
		Content: valueString(input.Content),
		Name:    input.Name,
	}
	for _, call := range input.ToolCalls {
		msg.ToolCalls = append(msg.ToolCalls, schema.ToolCall{
			ID:   defaultString(call.ID, fmt.Sprintf("tool-%d", time.Now().UnixNano())),
			Type: defaultString(call.Type, "function"),
			Function: schema.FunctionCall{
				Name:      call.Function.Name,
				Arguments: call.Function.Arguments,
			},
		})
	}
	return msg
}

func stringPtr(value string) *string {
	return &value
}

func valueString(value *string) string {
	if value == nil {
		return ""
	}
	return *value
}

func toOpenAITools(tools []*schema.ToolInfo) []openAIChatTool {
	seen := map[string]bool{}
	result := make([]openAIChatTool, 0, len(tools))
	for _, item := range tools {
		if item == nil || strings.TrimSpace(item.Name) == "" || seen[item.Name] {
			continue
		}
		seen[item.Name] = true
		parameters, _ := item.ParamsOneOf.ToJSONSchema()
		result = append(result, openAIChatTool{
			Type: "function",
			Function: openAIChatFunction{
				Name:        item.Name,
				Description: item.Desc,
				Parameters:  parameters,
			},
		})
	}
	return result
}

func toOpenAIToolChoice(choice schema.ToolChoice) string {
	switch choice {
	case schema.ToolChoiceForbidden:
		return "none"
	case schema.ToolChoiceForced:
		return "required"
	default:
		return "auto"
	}
}

func defaultString(value string, fallback string) string {
	if strings.TrimSpace(value) == "" {
		return fallback
	}
	return value
}
