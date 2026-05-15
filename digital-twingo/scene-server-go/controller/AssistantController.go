package controller

import (
	"net/http"

	"scene-server-go/service"
	"scene-server-go/vo"

	"github.com/gin-gonic/gin"
)

var assistantService = service.NewAssistantService()

func RegisterAssistantRoutes(api *gin.RouterGroup) {
	assistant := api.Group("/assistant")
	{
		assistant.POST("/chat", assistantChat)
		assistant.GET("/tools", assistantTools)
		assistant.GET("/context/summary", assistantContextSummary)
		assistant.GET("/rag/status", assistantRAGStatus)
	}
}

// @Summary      AI 助手聊天
// @Description  基于只读工具调用当前项目数据，并通过 OpenAI 兼容接口生成回答
// @Tags         AI助手
// @Accept       json
// @Produce      json
// @Param        request body vo.AssistantChatRequest true "聊天请求"
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/assistant/chat [post]
func assistantChat(c *gin.Context) {
	var req vo.AssistantChatRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusOK, vo.ResultVo{Code: 999, Data: err.Error()})
		return
	}
	c.JSON(http.StatusOK, assistantService.Chat(req))
}

// @Summary      AI 助手工具列表
// @Description  返回 LLM 可调用的只读项目数据工具
// @Tags         AI助手
// @Produce      json
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/assistant/tools [get]
func assistantTools(c *gin.Context) {
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: assistantService.Tools()})
}

// @Summary      AI 助手上下文摘要
// @Description  返回模型、场景、IoT、告警、业务等聚合摘要
// @Tags         AI助手
// @Produce      json
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/assistant/context/summary [get]
func assistantContextSummary(c *gin.Context) {
	c.JSON(http.StatusOK, assistantService.ContextSummary())
}

// @Summary      RAG 状态
// @Description  返回 RAG 预留状态和文档类型
// @Tags         AI助手
// @Produce      json
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/assistant/rag/status [get]
func assistantRAGStatus(c *gin.Context) {
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: assistantService.RAGStatus()})
}
