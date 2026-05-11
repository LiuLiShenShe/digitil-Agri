package controller

import (
	"net/http"

	"scene-server-go/mapper"
	"scene-server-go/vo"

	"github.com/gin-gonic/gin"
)

// RegisterAdminRoutes registers admin utility routes.
func RegisterAdminRoutes(api *gin.RouterGroup) {
	admin := api.Group("/admin")
	{
		admin.POST("/import-models", importModels)
		admin.GET("/stats", modelStats)
	}
}

// @Summary      批量导入模型
// @Description  扫描 scene-assets/import/ 目录下的 GLB 文件并入库
// @Tags         管理接口
// @Produce      json
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/admin/import-models [post]
func importModels(c *gin.Context) {
	count, err := mapper.BatchImportModels("./scene-assets/import")
	if err != nil {
		c.JSON(http.StatusOK, vo.ResultVo{Code: 999, Data: err.Error()})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: gin.H{"imported": count}})
}

// @Summary      模型统计
// @Description  返回模型库统计信息
// @Tags         管理接口
// @Produce      json
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/admin/stats [get]
func modelStats(c *gin.Context) {
	modelMapper := mapper.NewModelMapper()
	list, err := modelMapper.SelectAll()
	if err != nil {
		c.JSON(http.StatusOK, vo.ResultVo{Code: 999, Data: err.Error()})
		return
	}

	byCategory := map[string]int{}
	leafCount := 0
	folderCount := 0
	for _, m := range list {
		if m.Leaf {
			leafCount++
		} else {
			folderCount++
		}
		if m.Category != "" {
			byCategory[m.Category]++
		}
	}

	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: gin.H{
		"total":      len(list),
		"leafNodes":  leafCount,
		"folders":    folderCount,
		"byCategory": byCategory,
	}})
}
