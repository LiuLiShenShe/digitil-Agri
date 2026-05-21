package controller

import (
	"net/http"
	"scene-server-go/service"
	"scene-server-go/vo"

	"github.com/gin-gonic/gin"
)

var sceneService = service.NewSceneService()
var sysConfigureService = service.NewSysConfigureService()
var sceneBusinessBindingService = service.NewDefaultSceneBusinessBindingService()

// RegisterSceneRoutes registers scene-related routes.
func RegisterSceneRoutes(api *gin.RouterGroup) {
	scene := api.Group("/scene")
	{
		scene.POST("/saveScene", saveScene)
		scene.GET("/sceneList", sceneList)
		scene.GET("/loadScene", loadScene)
		scene.GET("/defaultScene", defaultScene)
		scene.GET("/bindings/by-scene-object", getSceneBindingBySceneObject)
		scene.GET("/bindings/by-business-object", getSceneBindingByBusinessObject)
		scene.PUT("/bindings", updateSceneBinding)
		scene.DELETE("/bindings", deleteSceneBinding)
		scene.GET("/bindings/validate", validateSceneBindings)
	}
}

// @Summary      保存场景
// @Description  关键字sceneName保存场景，如场景存在则更新覆盖，不存在则新建
// @Tags         场景保存加载接口
// @Accept       json
// @Produce      json
// @Param        sceneData body interface{} true "场景配置信息"
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/scene/saveScene [post]
func saveScene(c *gin.Context) {
	var sceneData map[string]interface{}
	if err := c.ShouldBindJSON(&sceneData); err != nil {
		c.JSON(http.StatusOK, gin.H{"code": 999, "data": err.Error()})
		return
	}
	result := sceneService.SaveScene(sceneData)
	c.JSON(http.StatusOK, result)
}

// @Summary      场景列表
// @Description  获取当前系统中场景列表
// @Tags         场景保存加载接口
// @Produce      json
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/scene/sceneList [get]
func sceneList(c *gin.Context) {
	result := sceneService.SceneList()
	c.JSON(http.StatusOK, result)
}

// @Summary      加载场景
// @Description  根据场景名加载场景
// @Tags         场景保存加载接口
// @Produce      json
// @Param        scene query string true "场景名称"
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/scene/loadScene [get]
func loadScene(c *gin.Context) {
	sceneName := c.Query("scene")
	result := sceneService.LoadScene(sceneName)
	c.JSON(http.StatusOK, result)
}

// @Summary      缺省场景名
// @Description  读取缺省场景名，如果没有指定缺省场景返回库中第一条记录，如果库中没有记录，返回scene001
// @Tags         场景保存加载接口
// @Produce      json
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/scene/defaultScene [get]
func defaultScene(c *gin.Context) {
	sname := sysConfigureService.GetConfig("defaultScene")
	if sname == "" {
		result := sceneService.SceneList()
		if result.Code == 200 {
			if list, ok := result.Data.([]string); ok && len(list) > 0 {
				sname = list[0]
			}
		}
		if sname == "" {
			sname = "scene001"
		}
		sysConfigureService.SetConfig("defaultScene", sname)
	}
	c.JSON(http.StatusOK, gin.H{"code": 200, "data": sname})
}

func getSceneBindingBySceneObject(c *gin.Context) {
	result := sceneBusinessBindingService.LookupBySceneObject(c.Query("scene"), c.Query("sceneObjectId"))
	writeSceneBindingResult(c, result)
}

func getSceneBindingByBusinessObject(c *gin.Context) {
	result := sceneBusinessBindingService.LookupByBusinessObject(c.Query("scene"), c.Query("businessObjectId"))
	writeSceneBindingResult(c, result)
}

func updateSceneBinding(c *gin.Context) {
	var req vo.SceneBindingUpdateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusOK, vo.ResultVo{Code: 400, Data: err.Error()})
		return
	}
	result := sceneBusinessBindingService.UpdateBinding(req)
	writeSceneBindingResult(c, result)
}

func deleteSceneBinding(c *gin.Context) {
	result := sceneBusinessBindingService.ClearBinding(c.Query("scene"), c.Query("sceneObjectId"))
	writeSceneBindingResult(c, result)
}

func validateSceneBindings(c *gin.Context) {
	result := sceneBusinessBindingService.ValidateScene(c.Query("scene"))
	if result.Code != 200 {
		c.JSON(http.StatusOK, vo.ResultVo{Code: result.Code, Data: result.Error})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: result.Summary})
}

func writeSceneBindingResult(c *gin.Context, result vo.SceneBindingLookupResponse) {
	if result.Code != 200 {
		c.JSON(http.StatusOK, vo.ResultVo{Code: result.Code, Data: result.Error})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: result})
}
