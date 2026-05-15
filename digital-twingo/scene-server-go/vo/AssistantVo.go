package vo

type AssistantChatRequest struct {
	Message   string                 `json:"message"`
	SessionID string                 `json:"sessionId"`
	Context   map[string]interface{} `json:"context"`
}

type AssistantChatResponse struct {
	SessionID string                `json:"sessionId"`
	Answer    string                `json:"answer"`
	ToolCalls []AssistantToolCallVo `json:"toolCalls"`
	Citations []AssistantCitationVo `json:"citations"`
	RAGUsed   bool                  `json:"ragUsed"`
}

type AssistantToolVo struct {
	Name        string `json:"name"`
	Label       string `json:"label"`
	Description string `json:"description"`
	ReadOnly    bool   `json:"readOnly"`
}

type AssistantToolCallVo struct {
	Name     string      `json:"name"`
	Label    string      `json:"label"`
	Status   string      `json:"status"`
	Duration int64       `json:"durationMs"`
	Summary  string      `json:"summary"`
	Data     interface{} `json:"data,omitempty"`
	Error    string      `json:"error,omitempty"`
}

type AssistantCitationVo struct {
	Source  string `json:"source"`
	Title   string `json:"title"`
	Excerpt string `json:"excerpt"`
}

type AssistantContextSummaryVo struct {
	UpdatedAt       string                 `json:"updatedAt"`
	ModelStats      interface{}            `json:"modelStats"`
	SceneCount      int                    `json:"sceneCount"`
	DeviceSummary   map[string]interface{} `json:"deviceSummary"`
	AlertSummary    map[string]interface{} `json:"alertSummary"`
	BusinessSummary interface{}            `json:"businessSummary"`
	RAG             AssistantRAGStatusVo   `json:"rag"`
}

type AssistantRAGStatusVo struct {
	Enabled       bool                  `json:"enabled"`
	Status        string                `json:"status"`
	Message       string                `json:"message"`
	DocumentTypes []string              `json:"documentTypes"`
	Chunks        []AssistantRAGChunkVo `json:"chunks"`
}

type AssistantRAGChunkVo struct {
	Source  string  `json:"source"`
	Score   float64 `json:"score"`
	Title   string  `json:"title"`
	Excerpt string  `json:"excerpt"`
}
