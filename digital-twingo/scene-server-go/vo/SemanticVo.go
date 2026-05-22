package vo

type SemanticBuildRequest struct {
	Message   string               `json:"message"`
	SceneName string               `json:"sceneName"`
	Mode      string               `json:"mode"`
	OwnerKey  string               `json:"ownerKey,omitempty"`
	Context   SemanticBuildContext `json:"context"`
}

type SemanticBuildResponse struct {
	ScenePlan     ScenePlan            `json:"scenePlan"`
	Models        []BuildModel         `json:"models"`
	Warnings      []string             `json:"warnings"`
	MissingAssets []MissingAssetVo     `json:"missingAssets"`
	Samples       []BuildSampleVo      `json:"samples"`
	PlanSource    SemanticPlanSource   `json:"planSource"`
	Context       SemanticBuildContext `json:"context"`
	RawLLMPlan    string               `json:"rawLlmPlan,omitempty"`
	AgentTrace    *SceneAgentTraceVo   `json:"agentTrace,omitempty"`
}

type ScenePlan struct {
	SceneName string            `json:"sceneName"`
	Intent    string            `json:"intent"`
	Units     string            `json:"units"`
	Mode      string            `json:"mode"`
	Ground    GroundPlan        `json:"ground"`
	Objects   []ScenePlanObject `json:"objects"`
	Relations []SceneRelation   `json:"relations"`
}

type GroundPlan struct {
	Width   float64 `json:"width"`
	Height  float64 `json:"height"`
	Color   string  `json:"color,omitempty"`
	Terrain string  `json:"terrain,omitempty"`
}

type ScenePlanObject struct {
	ID       string       `json:"id"`
	Label    string       `json:"label"`
	Category string       `json:"category"`
	AssetKey string       `json:"assetKey"`
	URL      string       `json:"url,omitempty"`
	Count    int          `json:"count"`
	Layout   string       `json:"layout"`
	Area     string       `json:"area"`
	Scale    float64      `json:"scale"`
	Size     FootprintVo  `json:"size"`
	Aliases  []string     `json:"aliases,omitempty"`
	Items    []BuildModel `json:"items,omitempty"`
}

type SceneRelation struct {
	Subject   string `json:"subject"`
	Predicate string `json:"predicate"`
	Object    string `json:"object"`
}

type BuildModel struct {
	URL     string            `json:"url"`
	Options BuildModelOptions `json:"options"`
	Meta    BuildModelMeta    `json:"meta"`
}

type BuildModelOptions struct {
	Offset OffsetVo `json:"offset"`
	Scale  float64  `json:"scale"`
	Angle  float64  `json:"angle"`
}

type OffsetVo struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

type BuildModelMeta struct {
	ID               string `json:"id"`
	Label            string `json:"label"`
	AssetKey         string `json:"assetKey"`
	Category         string `json:"category"`
	Area             string `json:"area"`
	Layout           string `json:"layout"`
	Placeholder      bool   `json:"placeholder,omitempty"`
	MissingAssetKey  string `json:"missingAssetKey,omitempty"`
	GenerationTaskID string `json:"generationTaskId,omitempty"`
}

type AssetSemantic struct {
	AssetKey     string      `json:"assetKey"`
	Name         string      `json:"name"`
	Aliases      []string    `json:"aliases"`
	Category     string      `json:"category"`
	URL          string      `json:"url"`
	DefaultScale float64     `json:"defaultScale"`
	Footprint    FootprintVo `json:"footprint"`
	LayoutRules  []string    `json:"layoutRules"`
}

type FootprintVo struct {
	Width float64 `json:"width"`
	Depth float64 `json:"depth"`
}

type MissingAssetVo struct {
	AssetKey         string                        `json:"assetKey"`
	Name             string                        `json:"name"`
	Category         string                        `json:"category,omitempty"`
	Reason           string                        `json:"reason"`
	Prompt           string                        `json:"prompt,omitempty"`
	FallbackModelKey string                        `json:"fallbackModelKey,omitempty"`
	PlacementRefs    []string                      `json:"placementRefs,omitempty"`
	ReferenceImage   *MissingAssetReferenceImageVo `json:"referenceImage,omitempty"`
	Generation       *MissingAssetGenerationVo     `json:"generation,omitempty"`
}

type MissingAssetReferenceImageVo struct {
	Status     string                      `json:"status"`
	Source     string                      `json:"source,omitempty"`
	URL        string                      `json:"url,omitempty"`
	Candidates []ReferenceImageCandidateVo `json:"candidates,omitempty"`
}

type ReferenceImageCandidateVo struct {
	ID     string  `json:"id"`
	Source string  `json:"source"`
	URL    string  `json:"url"`
	Score  float64 `json:"score"`
}

type MissingAssetGenerationVo struct {
	Enabled      bool   `json:"enabled"`
	TaskID       string `json:"taskId,omitempty"`
	Status       string `json:"status"`
	Progress     int    `json:"progress,omitempty"`
	ResultURL    string `json:"resultUrl,omitempty"`
	ThumbnailURL string `json:"thumbnailUrl,omitempty"`
	ErrorMessage string `json:"errorMessage,omitempty"`
	ReviewStatus string `json:"reviewStatus,omitempty"`
}

type BuildSampleVo struct {
	Title   string `json:"title"`
	Message string `json:"message"`
}

type SemanticPlanSource struct {
	Mode     string `json:"mode"`
	Model    string `json:"model"`
	Provider string `json:"provider,omitempty"`
	Attempt  int    `json:"attempt"`
	Reason   string `json:"reason,omitempty"`
}

type SceneAgentTraceVo struct {
	InvocationID    string                 `json:"invocationId"`
	TaskID          string                 `json:"taskId"`
	AgentName       string                 `json:"agentName"`
	LegacyAgentName string                 `json:"legacyAgentName,omitempty"`
	Framework       string                 `json:"framework"`
	Mode            string                 `json:"mode"`
	StartedAt       string                 `json:"startedAt"`
	FinishedAt      string                 `json:"finishedAt"`
	DurationMs      int64                  `json:"durationMs"`
	UserInput       string                 `json:"userInput,omitempty"`
	UserGoal        string                 `json:"userGoal"`
	Tools           []SceneAgentToolCallVo `json:"tools"`
	Steps           []SceneAgentStepVo     `json:"steps"`
	Fallback        *SceneAgentFallbackVo  `json:"fallback,omitempty"`
	FinalSummary    string                 `json:"finalSummary"`
	Error           string                 `json:"error,omitempty"`
}

type SceneAgentToolCallVo struct {
	Name          string                `json:"name"`
	Agent         string                `json:"agent,omitempty"`
	ToolCategory  string                `json:"toolCategory,omitempty"`
	Status        string                `json:"status"`
	DurationMs    int64                 `json:"durationMs"`
	InputSummary  string                `json:"inputSummary,omitempty"`
	OutputSummary string                `json:"outputSummary,omitempty"`
	FailureReason string                `json:"failureReason,omitempty"`
	Error         string                `json:"error,omitempty"`
	Fallback      *SceneAgentFallbackVo `json:"fallback,omitempty"`
	Flow          string                `json:"flow,omitempty"`
}

type SceneAgentStepVo struct {
	StepID        string                `json:"stepId"`
	Agent         string                `json:"agent"`
	Tool          string                `json:"tool"`
	ToolCategory  string                `json:"toolCategory"`
	Status        string                `json:"status"`
	DurationMs    int64                 `json:"durationMs"`
	InputSummary  string                `json:"inputSummary,omitempty"`
	OutputSummary string                `json:"outputSummary,omitempty"`
	FailureReason string                `json:"failureReason,omitempty"`
	Fallback      *SceneAgentFallbackVo `json:"fallback,omitempty"`
	Flow          string                `json:"flow,omitempty"`
}

type SceneAgentFallbackVo struct {
	Used   bool   `json:"used"`
	Reason string `json:"reason,omitempty"`
	Path   string `json:"path,omitempty"`
}

type SemanticBuildContext struct {
	SceneName       string                  `json:"sceneName"`
	AppendMode      bool                    `json:"appendMode"`
	SceneSummary    SemanticSceneSummary    `json:"sceneSummary"`
	SelectedObject  *SemanticObjectSummary  `json:"selectedObject,omitempty"`
	SelectedObjects []SemanticObjectSummary `json:"selectedObjects,omitempty"`
	ExistingObjects []SemanticObjectSummary `json:"existingObjects,omitempty"`
}

type SemanticSceneSummary struct {
	ObjectCount int `json:"objectCount"`
	ModelCount  int `json:"modelCount"`
}

type SemanticObjectSummary struct {
	ID       string    `json:"id,omitempty"`
	Label    string    `json:"label"`
	AssetKey string    `json:"assetKey,omitempty"`
	Category string    `json:"category,omitempty"`
	URL      string    `json:"url,omitempty"`
	Count    int       `json:"count,omitempty"`
	Area     string    `json:"area,omitempty"`
	Layout   string    `json:"layout,omitempty"`
	Scale    float64   `json:"scale,omitempty"`
	Offset   *OffsetVo `json:"offset,omitempty"`
}
