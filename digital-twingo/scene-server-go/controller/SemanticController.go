package controller

import (
	"net/http"

	"scene-server-go/service"
	"scene-server-go/vo"

	"github.com/gin-gonic/gin"
)

var semanticService = service.NewSemanticService()

func RegisterSemanticRoutes(api *gin.RouterGroup) {
	semantic := api.Group("/semantic")
	{
		semantic.POST("/build/plan", semanticBuildPlan)
		semantic.GET("/assets", semanticAssets)
		semantic.GET("/samples", semanticSamples)
	}
}

// @Summary      规则版语义搭建计划
// @Description  不依赖 LLM/Eino，根据关键词、模板和规则布局生成 ScenePlan 与可加载模型列表
// @Tags         语义搭建
// @Accept       json
// @Produce      json
// @Param        request body vo.SemanticBuildRequest true "语义搭建请求"
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/semantic/build/plan [post]
func semanticBuildPlan(c *gin.Context) {
	var req vo.SemanticBuildRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusOK, vo.ResultVo{Code: 999, Data: err.Error()})
		return
	}
	c.JSON(http.StatusOK, semanticService.BuildPlan(req))
}

// @Summary      语义资产 mock 表
// @Description  返回规则版语义搭建使用的资产 key、中文名、别名、分类和模型映射
// @Tags         语义搭建
// @Produce      json
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/semantic/assets [get]
func semanticAssets(c *gin.Context) {
	c.JSON(http.StatusOK, semanticService.AssetSemantics())
}

// @Summary      语义搭建测试样例
// @Description  返回第一周 MVP 的 5 条演示输入
// @Tags         语义搭建
// @Produce      json
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/semantic/samples [get]
func semanticSamples(c *gin.Context) {
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: semanticService.Samples()})
}
