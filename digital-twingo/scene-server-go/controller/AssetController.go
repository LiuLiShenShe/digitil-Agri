package controller

import (
	"net/http"

	"scene-server-go/service"
	"scene-server-go/vo"

	"github.com/gin-gonic/gin"
)

var assetService = service.NewAssetService()
var assetRegistryService = service.NewAssetRegistryService()
var assetAuditService = service.NewAssetQualityAuditService(assetRegistryService)
var assetRoutingService = service.NewAssetFidelityRoutingService(assetRegistryService)

// RegisterAssetRoutes registers asset generation routes.
func RegisterAssetRoutes(api *gin.RouterGroup) {
	assetService.InitDB()

	asset := api.Group("/asset")
	{
		asset.POST("/jobs", createJob)
		asset.GET("/jobs/:id", getJob)
		asset.GET("/jobs", listJobs)
		asset.POST("/jobs/:id/approve", approveJob)
		asset.POST("/jobs/:id/reject", rejectJob)
		asset.GET("/metadata", listAssetMetadata)
		asset.GET("/metadata/:assetKey", getAssetMetadata)
		asset.GET("/audit", auditAssets)
		asset.POST("/routing/decide", decideAssetRouting)
		asset.GET("/plant-geometry/:objectId", getPlantGeometryVersions)
	}
}

// @Summary      创建AI生成任务
// @Description  上传图片并创建3D资产生成任务
// @Tags         AI资产生成接口
// @Accept       json
// @Produce      json
// @Param        request body vo.AssetJobRequest true "生成请求"
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/asset/jobs [post]
func createJob(c *gin.Context) {
	var req vo.AssetJobRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusOK, vo.ResultVo{Code: 999, Data: err.Error()})
		return
	}
	if req.OwnerKey == "" {
		req.OwnerKey = "anonymous"
	}
	if req.ImageFileName == "" {
		req.ImageFileName = "image.png"
	}
	if req.ReferenceImageSource == "" {
		req.ReferenceImageSource = "upload"
	}

	result, err := assetService.CreateJob(&req)
	if err != nil {
		c.JSON(http.StatusOK, vo.ResultVo{Code: 999, Data: err.Error()})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: result})
}

// @Summary      查询生成任务状态
// @Description  根据任务ID查询生成任务状态和结果
// @Tags         AI资产生成接口
// @Produce      json
// @Param        id path string true "任务ID"
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/asset/jobs/{id} [get]
func getJob(c *gin.Context) {
	jobID := c.Param("id")
	result, err := assetService.GetJob(jobID)
	if err != nil {
		c.JSON(http.StatusOK, vo.ResultVo{Code: 999, Data: err.Error()})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: result})
}

// @Summary      任务列表
// @Description  获取当前用户的所有生成任务
// @Tags         AI资产生成接口
// @Produce      json
// @Param        ownerKey query string false "用户标识"
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/asset/jobs [get]
func listJobs(c *gin.Context) {
	ownerKey := c.Query("ownerKey")
	if ownerKey == "" {
		ownerKey = "anonymous"
	}
	result, err := assetService.ListJobs(ownerKey)
	if err != nil {
		c.JSON(http.StatusOK, vo.ResultVo{Code: 999, Data: err.Error()})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: result})
}

// @Summary      审核通过资产
// @Description  管理员审核通过生成的资产，加入公共模型库
// @Tags         AI资产生成接口
// @Accept       json
// @Produce      json
// @Param        id path string true "任务ID"
// @Param        request body vo.AssetApproveRequest true "审核请求"
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/asset/jobs/{id}/approve [post]
func approveJob(c *gin.Context) {
	jobID := c.Param("id")
	var req vo.AssetApproveRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		// allow empty body
		req.ModelName = "AI Generated Asset"
	}
	if err := assetService.ApproveJob(jobID, req.ModelName); err != nil {
		c.JSON(http.StatusOK, vo.ResultVo{Code: 999, Data: err.Error()})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: "approved"})
}

// @Summary      驳回资产
// @Description  驳回生成的资产
// @Tags         AI资产生成接口
// @Produce      json
// @Param        id path string true "任务ID"
// @Success      200 {object} vo.ResultVo
// @Router       /sceneApi/asset/jobs/{id}/reject [post]
func rejectJob(c *gin.Context) {
	jobID := c.Param("id")
	if err := assetService.RejectJob(jobID); err != nil {
		c.JSON(http.StatusOK, vo.ResultVo{Code: 999, Data: err.Error()})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: "rejected"})
}

func listAssetMetadata(c *gin.Context) {
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: assetRegistryService.List()})
}

func getAssetMetadata(c *gin.Context) {
	assetKey := c.Param("assetKey")
	result, ok := assetRegistryService.Get(assetKey)
	if !ok {
		c.JSON(http.StatusOK, vo.ResultVo{Code: 404, Data: "asset metadata not found"})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: result})
}

func auditAssets(c *gin.Context) {
	assetKey := c.Query("assetKey")
	if assetKey != "" {
		c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: assetAuditService.AuditAsset(assetKey)})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: assetAuditService.AuditAll()})
}

func decideAssetRouting(c *gin.Context) {
	var req vo.AssetFidelityRoutingRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusOK, vo.ResultVo{Code: 400, Data: err.Error()})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: assetRoutingService.Decide(req)})
}

func getPlantGeometryVersions(c *gin.Context) {
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: assetRegistryService.PlantGeometryVersions(c.Param("objectId"))})
}
