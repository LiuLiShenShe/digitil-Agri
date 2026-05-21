package vo

import "time"

type SyncFrequency string

const (
	SyncFrequencyRealtime  SyncFrequency = "realtime"
	SyncFrequencyHourly    SyncFrequency = "hourly"
	SyncFrequencyDaily     SyncFrequency = "daily"
	SyncFrequencyMilestone SyncFrequency = "milestone"
	SyncFrequencyStatic    SyncFrequency = "static"
)

type FarmMetricDefinitionVo struct {
	Key              string   `json:"key"`
	Label            string   `json:"label"`
	Unit             string   `json:"unit"`
	Category         string   `json:"category"`
	DefaultFrequency string   `json:"defaultFrequency"`
	Aliases          []string `json:"aliases,omitempty"`
}

type FarmSyncPolicyVo struct {
	ObjectID          string   `json:"objectId,omitempty"`
	ObjectType        string   `json:"objectType"`
	SyncFrequency     string   `json:"syncFrequency"`
	GeometryFrequency string   `json:"geometryFrequency,omitempty"`
	MetricKeys        []string `json:"metricKeys"`
	SourceDeviceIDs   []string `json:"sourceDeviceIds"`
	DataQuality       string   `json:"dataQuality"`
}

type FarmMetricPointVo struct {
	ID             int64     `json:"id" db:"id"`
	ObjectID       string    `json:"objectId" db:"objectId"`
	SourceDeviceID string    `json:"sourceDeviceId" db:"sourceDeviceId"`
	MetricKey      string    `json:"metricKey" db:"metricKey"`
	Value          float64   `json:"value" db:"metricValue"`
	Unit           string    `json:"unit" db:"unit"`
	Timestamp      time.Time `json:"timestamp" db:"timestamp"`
	DataQuality    string    `json:"dataQuality" db:"dataQuality"`
}

type FarmMetricLatestValueVo struct {
	MetricKey      string  `json:"metricKey"`
	Label          string  `json:"label"`
	Value          float64 `json:"value"`
	Unit           string  `json:"unit"`
	Timestamp      string  `json:"timestamp"`
	DataQuality    string  `json:"dataQuality"`
	SourceDeviceID string  `json:"sourceDeviceId,omitempty"`
}

type FarmLatestQuery struct {
	ObjectID string   `json:"objectId"`
	Metrics  []string `json:"metrics,omitempty"`
}

type FarmLatestResponseVo struct {
	ObjectID string                             `json:"objectId"`
	Values   map[string]FarmMetricLatestValueVo `json:"values"`
	Missing  []string                           `json:"missing"`
}

type TimeSeriesQuery struct {
	ObjectID string   `json:"objectId"`
	Range    string   `json:"range"`
	Metrics  []string `json:"metrics,omitempty"`
	Limit    int      `json:"limit,omitempty"`
}

type FarmMetricAggregateVo struct {
	Min   float64 `json:"min"`
	Max   float64 `json:"max"`
	Avg   float64 `json:"avg"`
	Count int     `json:"count"`
}

type FarmMetricSeriesVo struct {
	MetricKey   string                `json:"metricKey"`
	Label       string                `json:"label"`
	Unit        string                `json:"unit"`
	Points      []FarmMetricPointVo   `json:"points"`
	Aggregate   FarmMetricAggregateVo `json:"aggregate"`
	DataQuality string                `json:"dataQuality"`
}

type TimeSeriesResponseVo struct {
	ObjectID string                        `json:"objectId"`
	Range    string                        `json:"range"`
	StartAt  string                        `json:"startAt"`
	EndAt    string                        `json:"endAt"`
	Series   map[string]FarmMetricSeriesVo `json:"series"`
	Missing  []string                      `json:"missing"`
}

type FarmEventVo struct {
	ID              int64                  `json:"id" db:"id"`
	EventID         string                 `json:"eventId" db:"eventId"`
	ObjectID        string                 `json:"objectId" db:"objectId"`
	RelatedObjectID string                 `json:"relatedObjectId" db:"relatedObjectId"`
	EventType       string                 `json:"eventType" db:"eventType"`
	Severity        string                 `json:"severity" db:"severity"`
	Summary         string                 `json:"summary" db:"summary"`
	Timestamp       time.Time              `json:"timestamp" db:"timestamp"`
	DataQuality     string                 `json:"dataQuality" db:"dataQuality"`
	Metadata        map[string]interface{} `json:"metadata" db:"-"`
}

type EventQuery struct {
	ObjectID   string   `json:"objectId"`
	Range      string   `json:"range"`
	EventTypes []string `json:"eventTypes,omitempty"`
	Limit      int      `json:"limit,omitempty"`
}

type EventQueryResponseVo struct {
	ObjectID string        `json:"objectId"`
	Range    string        `json:"range"`
	StartAt  string        `json:"startAt"`
	EndAt    string        `json:"endAt"`
	Events   []FarmEventVo `json:"events"`
	Missing  []string      `json:"missing"`
}

type FarmDailyArchiveVo struct {
	ID              int64                            `json:"id" db:"id"`
	ObjectID        string                           `json:"objectId" db:"objectId"`
	ArchiveDate     string                           `json:"archiveDate" db:"archiveDate"`
	MetricSummaries map[string]FarmMetricAggregateVo `json:"metricSummaries" db:"-"`
	EventCounts     map[string]int                   `json:"eventCounts" db:"-"`
	DataQuality     string                           `json:"dataQuality" db:"dataQuality"`
	CreatedAt       time.Time                        `json:"createdAt" db:"createdAt"`
}

type FarmDailyArchivesResponseVo struct {
	ObjectID string               `json:"objectId"`
	Days     int                  `json:"days"`
	Archives []FarmDailyArchiveVo `json:"archives"`
}

type FarmReportSectionVo struct {
	DataQuality string        `json:"dataQuality"`
	Summary     string        `json:"summary"`
	Items       []interface{} `json:"items"`
	Missing     []string      `json:"missing"`
}

type GreenhouseReportSourceVo struct {
	ObjectID          string              `json:"objectId"`
	ObjectName        string              `json:"objectName"`
	Date              string              `json:"date"`
	DataQuality       string              `json:"dataQuality"`
	Environment       FarmReportSectionVo `json:"environment"`
	DeviceStatus      FarmReportSectionVo `json:"deviceStatus"`
	Alerts            []FarmEventVo       `json:"alerts"`
	IrrigationEvents  []FarmEventVo       `json:"irrigationEvents"`
	Recommendations   []string            `json:"recommendations"`
	MissingCategories []string            `json:"missingCategories"`
}

type TimeSeriesToolInput struct {
	ObjectID string   `json:"objectId"`
	Range    string   `json:"range"`
	Metrics  []string `json:"metrics,omitempty"`
	Limit    int      `json:"limit,omitempty"`
}

type TimeSeriesToolOutput struct {
	Query  TimeSeriesToolInput  `json:"query"`
	Result TimeSeriesResponseVo `json:"result"`
}

type EventToolInput struct {
	ObjectID   string   `json:"objectId"`
	Range      string   `json:"range"`
	EventTypes []string `json:"eventTypes,omitempty"`
	Limit      int      `json:"limit,omitempty"`
}

type EventToolOutput struct {
	Query  EventToolInput       `json:"query"`
	Result EventQueryResponseVo `json:"result"`
}
