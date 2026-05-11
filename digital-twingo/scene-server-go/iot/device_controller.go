package iot

import (
	"net/http"
	"strconv"

	"scene-server-go/vo"

	"github.com/gin-gonic/gin"
)

func RegisterIotRoutes(api *gin.RouterGroup) {
	iot := api.Group("/iot")
	{
		iot.GET("/devices", getDevices)
		iot.GET("/devices/:deviceId", getDevice)
		iot.POST("/devices", createDevice)
		iot.PUT("/devices/:deviceId", updateDevice)
		iot.DELETE("/devices/:deviceId", deleteDevice)
		iot.GET("/devices/:deviceId/data", getDeviceData)
		iot.GET("/devices/:deviceId/metrics/:metricKey", getDeviceMetricData)
		iot.POST("/devices/:deviceId/bind/:modelId", bindModel)

		iot.GET("/alerts", getAlerts)
		iot.GET("/alerts/unacked-count", getUnackedCount)
		iot.PUT("/alerts/:alertId/acknowledge", acknowledgeAlert)

		iot.GET("/simulator/devices", getSimulatorDevices)

		iot.GET("/ws", HandleIoTWebSocket)
	}
}

func getDevices(c *gin.Context) {
	svc := GetDeviceService()
	if svc == nil {
		c.JSON(http.StatusServiceUnavailable, vo.ResultVo{Code: 503, Data: "IoT service not initialized"})
		return
	}
	devices, err := svc.GetAllDevices()
	if err != nil {
		c.JSON(http.StatusInternalServerError, vo.ResultVo{Code: 500, Data: err.Error()})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: devices})
}

func getDevice(c *gin.Context) {
	svc := GetDeviceService()
	if svc == nil {
		c.JSON(http.StatusServiceUnavailable, vo.ResultVo{Code: 503, Data: "IoT service not initialized"})
		return
	}
	device, err := svc.GetDevice(c.Param("deviceId"))
	if err != nil {
		c.JSON(http.StatusNotFound, vo.ResultVo{Code: 404, Data: "Device not found"})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: device})
}

func createDevice(c *gin.Context) {
	svc := GetDeviceService()
	if svc == nil {
		c.JSON(http.StatusServiceUnavailable, vo.ResultVo{Code: 503, Data: "IoT service not initialized"})
		return
	}
	var device IotDevice
	if err := c.ShouldBindJSON(&device); err != nil {
		c.JSON(http.StatusBadRequest, vo.ResultVo{Code: 400, Data: err.Error()})
		return
	}
	if err := svc.CreateDevice(&device); err != nil {
		c.JSON(http.StatusInternalServerError, vo.ResultVo{Code: 500, Data: err.Error()})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: device})
}

func updateDevice(c *gin.Context) {
	svc := GetDeviceService()
	if svc == nil {
		c.JSON(http.StatusServiceUnavailable, vo.ResultVo{Code: 503, Data: "IoT service not initialized"})
		return
	}
	var device IotDevice
	if err := c.ShouldBindJSON(&device); err != nil {
		c.JSON(http.StatusBadRequest, vo.ResultVo{Code: 400, Data: err.Error()})
		return
	}
	device.DeviceId = c.Param("deviceId")
	if err := svc.UpdateDevice(&device); err != nil {
		c.JSON(http.StatusInternalServerError, vo.ResultVo{Code: 500, Data: err.Error()})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: device})
}

func deleteDevice(c *gin.Context) {
	svc := GetDeviceService()
	if svc == nil {
		c.JSON(http.StatusServiceUnavailable, vo.ResultVo{Code: 503, Data: "IoT service not initialized"})
		return
	}
	if err := svc.DeleteDevice(c.Param("deviceId")); err != nil {
		c.JSON(http.StatusInternalServerError, vo.ResultVo{Code: 500, Data: err.Error()})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: "deleted"})
}

func getDeviceData(c *gin.Context) {
	svc := GetDeviceService()
	if svc == nil {
		c.JSON(http.StatusServiceUnavailable, vo.ResultVo{Code: 503, Data: "IoT service not initialized"})
		return
	}
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "100"))
	data, err := svc.GetDeviceData(c.Param("deviceId"), limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, vo.ResultVo{Code: 500, Data: err.Error()})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: data})
}

func getDeviceMetricData(c *gin.Context) {
	svc := GetDeviceService()
	if svc == nil {
		c.JSON(http.StatusServiceUnavailable, vo.ResultVo{Code: 503, Data: "IoT service not initialized"})
		return
	}
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "100"))
	data, err := svc.GetDeviceMetricData(c.Param("deviceId"), c.Param("metricKey"), limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, vo.ResultVo{Code: 500, Data: err.Error()})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: data})
}

func bindModel(c *gin.Context) {
	svc := GetDeviceService()
	if svc == nil {
		c.JSON(http.StatusServiceUnavailable, vo.ResultVo{Code: 503, Data: "IoT service not initialized"})
		return
	}
	modelId, err := strconv.Atoi(c.Param("modelId"))
	if err != nil {
		c.JSON(http.StatusBadRequest, vo.ResultVo{Code: 400, Data: "Invalid modelId"})
		return
	}
	if err := svc.BindModel(c.Param("deviceId"), modelId); err != nil {
		c.JSON(http.StatusInternalServerError, vo.ResultVo{Code: 500, Data: err.Error()})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: "bound"})
}

func getAlerts(c *gin.Context) {
	svc := GetDeviceService()
	if svc == nil {
		c.JSON(http.StatusServiceUnavailable, vo.ResultVo{Code: 503, Data: "IoT service not initialized"})
		return
	}
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "50"))
	alerts, err := svc.alertSvc.GetRecentAlerts(limit)
	if err != nil {
		c.JSON(http.StatusInternalServerError, vo.ResultVo{Code: 500, Data: err.Error()})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: alerts})
}

func getUnackedCount(c *gin.Context) {
	svc := GetDeviceService()
	if svc == nil {
		c.JSON(http.StatusServiceUnavailable, vo.ResultVo{Code: 503, Data: "IoT service not initialized"})
		return
	}
	count, err := svc.alertSvc.GetUnackedCount()
	if err != nil {
		c.JSON(http.StatusInternalServerError, vo.ResultVo{Code: 500, Data: err.Error()})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: map[string]int{"count": count}})
}

func acknowledgeAlert(c *gin.Context) {
	svc := GetDeviceService()
	if svc == nil {
		c.JSON(http.StatusServiceUnavailable, vo.ResultVo{Code: 503, Data: "IoT service not initialized"})
		return
	}
	alertId, err := strconv.ParseInt(c.Param("alertId"), 10, 64)
	if err != nil {
		c.JSON(http.StatusBadRequest, vo.ResultVo{Code: 400, Data: "Invalid alertId"})
		return
	}
	if err := svc.alertSvc.AcknowledgeAlert(alertId); err != nil {
		c.JSON(http.StatusInternalServerError, vo.ResultVo{Code: 500, Data: err.Error()})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: "acknowledged"})
}

func getSimulatorDevices(c *gin.Context) {
	svc := GetDeviceService()
	if svc == nil {
		c.JSON(http.StatusServiceUnavailable, vo.ResultVo{Code: 503, Data: "IoT service not initialized"})
		return
	}
	devices := svc.GetSimulatorDevices()
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: devices})
}
