package controller

import (
	"net/http"
	"scene-server-go/service"
	"scene-server-go/vo"

	"github.com/gin-gonic/gin"
)

var modelService = service.NewModelService()

// RegisterModelRoutes registers model-related routes.
func RegisterModelRoutes(api *gin.RouterGroup) {
	model := api.Group("/model")
	{
		model.GET("/list", modelList)
	}
}

// @Summary      模型列表
// @Description  获取当前系统中支持的三维模型列表（含用户的AI生成模型）
// @Tags         三维模型接口
// @Produce      json
// @Param        ownerKey query string false "用户标识，用于获取AI生成模型"
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/model/list [get]
func modelList(c *gin.Context) {
	ownerKey := c.Query("ownerKey")
	var result vo.ResultVo
	if ownerKey != "" {
		result = modelService.QueryAllWithAI(ownerKey)
	} else {
		result = modelService.QueryAll()
	}
	c.JSON(http.StatusOK, result)
}
