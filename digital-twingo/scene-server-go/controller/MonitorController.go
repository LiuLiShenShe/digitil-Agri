package controller

import (
	"net/http"

	"scene-server-go/service"

	"github.com/gin-gonic/gin"
)

var monitorService = service.NewMonitorService()

func RegisterMonitorRoutes(api *gin.RouterGroup) {
	monitor := api.Group("/monitor")
	{
		monitor.GET("/dashboard", getMonitorDashboard)
	}
}

// @Summary      监控中心大屏
// @Description  聚合园区概览、设备矩阵、能耗、产量、环境日报和告警
// @Tags         监控中心
// @Produce      json
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/monitor/dashboard [get]
func getMonitorDashboard(c *gin.Context) {
	c.JSON(http.StatusOK, monitorService.GetDashboard())
}
