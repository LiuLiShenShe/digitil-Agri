package controller

import (
	"net/http"
	"scene-server-go/service"

	"github.com/gin-gonic/gin"
)

var skyboxService = service.NewSkyboxService()
var gdTextureService = service.NewGdTextureService()

// RegisterBackgroundRoutes registers background-related routes.
func RegisterBackgroundRoutes(api *gin.RouterGroup) {
	bg := api.Group("/background")
	{
		bg.GET("/list", skyboxList)
		bg.GET("/gdTextures", gdTextures)
	}
}

// @Summary      天空盒子
// @Description  获取当前系统中支持的天空盒子背景列表
// @Tags         背景纹理接口
// @Produce      json
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/background/list [get]
func skyboxList(c *gin.Context) {
	result := skyboxService.QueryAll()
	c.JSON(http.StatusOK, result)
}

// @Summary      地面纹理
// @Description  获取当前系统中支持的地面纹理列表
// @Tags         背景纹理接口
// @Produce      json
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/background/gdTextures [get]
func gdTextures(c *gin.Context) {
	result := gdTextureService.QueryAll()
	c.JSON(http.StatusOK, result)
}
