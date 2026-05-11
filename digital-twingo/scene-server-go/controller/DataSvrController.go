package controller

import (
	"net/http"
	"scene-server-go/service"

	"github.com/gin-gonic/gin"
)

var dataService = service.NewDataService()

// RegisterDataSvrRoutes registers data service routes.
func RegisterDataSvrRoutes(api *gin.RouterGroup) {
	datasvr := api.Group("/datasvr")
	{
		datasvr.GET("/getData", getData)
	}
}

// @Summary      数据服务
// @Description  根据dataId返回对应数据对象，实际项目中需要扩充此接口，依据不同类型返回具体的数据项目
// @Tags         数据服务接口
// @Produce      json
// @Param        dataId query string true "数据ID"
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/datasvr/getData [get]
func getData(c *gin.Context) {
	dataId := c.Query("dataId")
	result := dataService.GetData(dataId)
	c.JSON(http.StatusOK, result)
}
