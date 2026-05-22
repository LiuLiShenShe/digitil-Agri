package controller

import (
	"net/http"

	"scene-server-go/service"
	"scene-server-go/vo"

	"github.com/gin-gonic/gin"
)

var acceptanceService = service.NewAcceptanceService()

func RegisterAcceptanceRoutes(api *gin.RouterGroup) {
	acceptance := api.Group("/acceptance")
	{
		acceptance.GET("/tomato-greenhouse", getTomatoGreenhouseAcceptance)
	}
}

// @Summary      番茄温室 Phase 6 综合验收
// @Description  聚合语义搭建、Agent trace、资产路由、业务绑定、对象记忆和日报数据源
// @Tags         综合验收
// @Produce      json
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/acceptance/tomato-greenhouse [get]
func getTomatoGreenhouseAcceptance(c *gin.Context) {
	result, err := acceptanceService.TomatoGreenhouseAcceptance()
	if err != nil {
		c.JSON(http.StatusOK, vo.ResultVo{Code: 500, Data: err.Error()})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: result})
}
