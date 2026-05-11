package controller

import (
	"net/http"

	"scene-server-go/service"

	"github.com/gin-gonic/gin"
)

var businessService = service.NewBusinessService()

func RegisterBusinessRoutes(api *gin.RouterGroup) {
	business := api.Group("/business")
	{
		business.GET("/overview", getBusinessOverview)
	}
}

// @Summary      农业业务子系统总览
// @Description  聚合土壤墒情、气象、水肥灌溉、大棚控制、视频监控、环境监测 6 个业务子系统的指标、状态、告警和差距
// @Tags         农业业务中心
// @Produce      json
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/business/overview [get]
func getBusinessOverview(c *gin.Context) {
	c.JSON(http.StatusOK, businessService.GetOverview())
}
