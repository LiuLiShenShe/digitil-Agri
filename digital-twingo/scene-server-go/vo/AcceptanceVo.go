package vo

type TomatoGreenhouseAcceptanceVo struct {
	Prompt            string                         `json:"prompt"`
	SceneName         string                         `json:"sceneName"`
	RunAt             string                         `json:"runAt"`
	OverallPassed     bool                           `json:"overallPassed"`
	ModelCounts       map[string]AcceptanceCountVo   `json:"modelCounts"`
	Steps             []AcceptanceStepVo             `json:"steps"`
	SuccessMetrics    []AcceptanceMetricVo           `json:"successMetrics"`
	Issues            []AcceptanceIssueVo            `json:"issues"`
	SemanticBuild     AcceptanceSemanticBuildVo      `json:"semanticBuild"`
	BindingValidation SceneBindingValidationResponse `json:"bindingValidation"`
	GreenhouseObject  *AgriculturalObjectVo          `json:"greenhouseObject,omitempty"`
	GreenhouseContext ObjectRelationsResponse        `json:"greenhouseContext"`
	AbnormalDevice    *AgriculturalObjectVo          `json:"abnormalDevice,omitempty"`
	AbnormalContext   AcceptanceObjectMemoryVo       `json:"abnormalContext"`
	ReportSource      GreenhouseReportSourceVo       `json:"reportSource"`
	ArchiveReadiness  AcceptanceArchiveReadinessVo   `json:"archiveReadiness"`
}

type AcceptanceCountVo struct {
	Label    string `json:"label"`
	Expected int    `json:"expected"`
	Actual   int    `json:"actual"`
	Passed   bool   `json:"passed"`
}

type AcceptanceStepVo struct {
	Key      string `json:"key"`
	Title    string `json:"title"`
	Target   string `json:"target"`
	Actual   string `json:"actual"`
	Passed   bool   `json:"passed"`
	Evidence string `json:"evidence,omitempty"`
}

type AcceptanceMetricVo struct {
	Key      string  `json:"key"`
	Label    string  `json:"label"`
	Target   string  `json:"target"`
	Actual   string  `json:"actual"`
	Value    float64 `json:"value"`
	Passed   bool    `json:"passed"`
	Source   string  `json:"source"`
	Evidence string  `json:"evidence,omitempty"`
}

type AcceptanceIssueVo struct {
	Severity string `json:"severity"`
	Category string `json:"category"`
	Message  string `json:"message"`
	Source   string `json:"source,omitempty"`
}

type AcceptanceSemanticBuildVo struct {
	ScenePlan     ScenePlan                  `json:"scenePlan"`
	Models        []BuildModel               `json:"models"`
	Warnings      []string                   `json:"warnings"`
	MissingAssets []AcceptanceMissingAssetVo `json:"missingAssets"`
	PlanSource    SemanticPlanSource         `json:"planSource"`
	AgentTrace    *SceneAgentTraceVo         `json:"agentTrace,omitempty"`
}

type AcceptanceMissingAssetVo struct {
	AssetKey       string                          `json:"assetKey"`
	Name           string                          `json:"name"`
	Reason         string                          `json:"reason"`
	PlacementRefs  []string                        `json:"placementRefs"`
	Routing        *AssetFidelityRoutingDecisionVo `json:"routing,omitempty"`
	ReferenceImage *MissingAssetReferenceImageVo   `json:"referenceImage,omitempty"`
	Generation     *MissingAssetGenerationVo       `json:"generation,omitempty"`
}

type AcceptanceObjectMemoryVo struct {
	ObjectID       string               `json:"objectId"`
	Latest         FarmLatestResponseVo `json:"latest"`
	Events         EventQueryResponseVo `json:"events"`
	Recommendation string               `json:"recommendation"`
}

type AcceptanceArchiveReadinessVo struct {
	Ready      bool     `json:"ready"`
	Changes    []string `json:"changes"`
	NextAction string   `json:"nextAction"`
}
