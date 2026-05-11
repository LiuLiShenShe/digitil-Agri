package vo

import "time"

type BusinessOverviewVo struct {
	UpdatedAt  time.Time             `json:"updatedAt"`
	ParkName   string                `json:"parkName"`
	Summary    BusinessSummaryVo     `json:"summary"`
	Subsystems []BusinessSubsystemVo `json:"subsystems"`
}

type BusinessSummaryVo struct {
	SystemTotal    int     `json:"systemTotal"`
	DemoReadyCount int     `json:"demoReadyCount"`
	PartialCount   int     `json:"partialCount"`
	MissingCount   int     `json:"missingCount"`
	WarningAlerts  int     `json:"warningAlerts"`
	CriticalAlerts int     `json:"criticalAlerts"`
	UnackedAlerts  int     `json:"unackedAlerts"`
	OverallScore   float64 `json:"overallScore"`
	CompletionRate float64 `json:"completionRate"`
}

type BusinessSubsystemVo struct {
	Key                 string               `json:"key"`
	Name                string               `json:"name"`
	Objective           string               `json:"objective"`
	Status              string               `json:"status"`
	ImplementationLevel string               `json:"implementationLevel"`
	CompletionRate      float64              `json:"completionRate"`
	PrimaryDeviceIds    []string             `json:"primaryDeviceIds"`
	Metrics             []BusinessMetricVo   `json:"metrics"`
	Workflows           []BusinessWorkflowVo `json:"workflows"`
	Alerts              []MonitorAlertVo     `json:"alerts"`
	Gaps                []string             `json:"gaps"`
}

type BusinessMetricVo struct {
	Key    string  `json:"key"`
	Label  string  `json:"label"`
	Value  float64 `json:"value"`
	Unit   string  `json:"unit"`
	Status string  `json:"status"`
}

type BusinessWorkflowVo struct {
	Name        string `json:"name"`
	State       string `json:"state"`
	Description string `json:"description"`
}
