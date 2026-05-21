package controller

import (
	"net/http"

	"scene-server-go/service"
	"scene-server-go/vo"

	"github.com/gin-gonic/gin"
)

var agriculturalObjectService = service.NewAgriculturalObjectService()

func RegisterAgriculturalObjectRoutes(api *gin.RouterGroup) {
	if err := agriculturalObjectService.InitDB(); err != nil {
		// Keep startup behavior consistent with existing optional modules: expose the error through endpoints.
	}

	objects := api.Group("/objects")
	{
		objects.GET("", listOrLookupAgriculturalObjects)
		objects.GET("/:id", getAgriculturalObject)
		objects.GET("/:id/relations", getAgriculturalObjectRelations)
	}
}

func listOrLookupAgriculturalObjects(c *gin.Context) {
	result := agriculturalObjectService.Lookup(vo.ObjectLookupRequest{
		ObjectID: c.Query("id"),
		Type:     c.Query("type"),
	})
	writeLookupResult(c, result)
}

func getAgriculturalObject(c *gin.Context) {
	result := agriculturalObjectService.Lookup(vo.ObjectLookupRequest{ObjectID: c.Param("id")})
	writeLookupResult(c, result)
}

func getAgriculturalObjectRelations(c *gin.Context) {
	relationTypes := c.QueryArray("relationType")
	result := agriculturalObjectService.Relations(vo.ObjectRelationsRequest{
		ObjectID:      c.Param("id"),
		RelationTypes: relationTypes,
	})
	if result.Code != 200 {
		c.JSON(http.StatusOK, vo.ResultVo{Code: result.Code, Data: result.Error})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: result})
}

func writeLookupResult(c *gin.Context, result vo.ObjectLookupResponse) {
	if result.Code != 200 {
		c.JSON(http.StatusOK, vo.ResultVo{Code: result.Code, Data: result.Error})
		return
	}
	if result.Object != nil {
		c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: result.Object})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: result.Objects})
}
