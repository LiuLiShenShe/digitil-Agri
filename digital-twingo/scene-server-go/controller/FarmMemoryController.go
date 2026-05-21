package controller

import (
	"net/http"
	"strconv"
	"strings"
	"time"

	"scene-server-go/service"
	"scene-server-go/vo"

	"github.com/gin-gonic/gin"
)

var farmMemoryService = service.NewFarmMemoryService()

func RegisterFarmMemoryRoutes(api *gin.RouterGroup) {
	if err := farmMemoryService.InitDB(); err != nil {
		// Keep optional-module startup behavior consistent with existing object routes.
	}

	memory := api.Group("/memory")
	{
		memory.GET("/metrics", getFarmMetricDictionary)
		memory.GET("/sync-policies", getFarmSyncPolicies)
	}

	objectMemory := api.Group("/objects/:id/memory")
	{
		objectMemory.GET("/sync-policy", getObjectSyncPolicy)
		objectMemory.GET("/latest", getObjectLatestValues)
		objectMemory.GET("/timeseries", getObjectTimeSeries)
		objectMemory.GET("/events", getObjectEvents)
		objectMemory.GET("/daily-archives", getObjectDailyArchives)
		objectMemory.GET("/report-source", getObjectReportSource)
	}
}

func getFarmMetricDictionary(c *gin.Context) {
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: farmMemoryService.MetricDictionary()})
}

func getFarmSyncPolicies(c *gin.Context) {
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: farmMemoryService.SyncPolicies()})
}

func getObjectSyncPolicy(c *gin.Context) {
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: farmMemoryService.SyncPolicyForObject(c.Param("id"))})
}

func getObjectLatestValues(c *gin.Context) {
	result, err := farmMemoryService.LatestValues(vo.FarmLatestQuery{
		ObjectID: c.Param("id"),
		Metrics:  queryList(c, "metric"),
	})
	writeFarmMemoryResult(c, result, err)
}

func getObjectTimeSeries(c *gin.Context) {
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "0"))
	if limit <= 0 {
		limit = 1000
	}
	result, err := farmMemoryService.TimeSeries(vo.TimeSeriesQuery{
		ObjectID: c.Param("id"),
		Range:    c.DefaultQuery("range", "24h"),
		Metrics:  queryList(c, "metric"),
		Limit:    limit,
	})
	writeFarmMemoryResult(c, result, err)
}

func getObjectEvents(c *gin.Context) {
	limit, _ := strconv.Atoi(c.DefaultQuery("limit", "50"))
	result, err := farmMemoryService.Events(vo.EventQuery{
		ObjectID:   c.Param("id"),
		Range:      c.DefaultQuery("range", "24h"),
		EventTypes: queryList(c, "eventType"),
		Limit:      limit,
	})
	writeFarmMemoryResult(c, result, err)
}

func getObjectDailyArchives(c *gin.Context) {
	days, _ := strconv.Atoi(c.DefaultQuery("days", "7"))
	result, err := farmMemoryService.DailyArchives(c.Param("id"), days)
	writeFarmMemoryResult(c, result, err)
}

func getObjectReportSource(c *gin.Context) {
	date := c.Query("date")
	if date != "" {
		if _, err := time.Parse("2006-01-02", date); err != nil {
			c.JSON(http.StatusOK, vo.ResultVo{Code: 400, Data: "date must use YYYY-MM-DD"})
			return
		}
	}
	result, err := farmMemoryService.GreenhouseReportSource(c.Param("id"), date)
	writeFarmMemoryResult(c, result, err)
}

func queryList(c *gin.Context, key string) []string {
	values := c.QueryArray(key)
	if comma := c.Query(key); comma != "" && strings.Contains(comma, ",") {
		values = append(values, strings.Split(comma, ",")...)
	}
	result := make([]string, 0, len(values))
	for _, value := range values {
		value = strings.TrimSpace(value)
		if value != "" {
			result = append(result, value)
		}
	}
	return result
}

func writeFarmMemoryResult(c *gin.Context, data interface{}, err error) {
	if err != nil {
		c.JSON(http.StatusOK, vo.ResultVo{Code: 400, Data: err.Error()})
		return
	}
	c.JSON(http.StatusOK, vo.ResultVo{Code: 200, Data: data})
}
