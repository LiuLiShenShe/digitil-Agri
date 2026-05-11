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
		datasvr.GET("/dataIndex", getDataIndex)
		datasvr.GET("/list", dataIndexList)
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

// @Summary      数据对象详情
// @Description  兼容前端数据面板，根据 dataId 返回模型绑定数据
// @Tags         数据服务接口
// @Produce      json
// @Param        dataId query string true "数据ID"
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/datasvr/dataIndex [get]
func getDataIndex(c *gin.Context) {
	dataId := c.Query("dataId")
	result := dataService.GetData(dataId)
	c.JSON(http.StatusOK, result)
}

// @Summary      数据对象列表
// @Description  获取可绑定到场景模型的数据对象列表
// @Tags         数据服务接口
// @Produce      json
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/datasvr/list [get]
func dataIndexList(c *gin.Context) {
	result := dataService.QueryAll()
	c.JSON(http.StatusOK, result)
}
