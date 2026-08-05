package vo

type SemanticBuildRequest struct {
	Message   string               `json:"message"`
	SceneName string               `json:"sceneName"`
	Mode      string               `json:"mode"`
	OwnerKey  string               `json:"ownerKey,omitempty"`
	Context   SemanticBuildContext `json:"context"`
}

type SemanticBuildResponse struct {
	ScenePlan      ScenePlan                 `json:"scenePlan"`
	Models         []BuildModel              `json:"models"`
	Warnings       []string                  `json:"warnings"`
	MissingAssets  []MissingAssetVo          `json:"missingAssets"`
	Samples        []BuildSampleVo           `json:"samples"`
	PlanSource     SemanticPlanSource        `json:"planSource"`
	Context        SemanticBuildContext      `json:"context"`
	VisualTemplate *SemanticVisualTemplateVo `json:"visualTemplate,omitempty"`
	RawLLMPlan     string                    `json:"rawLlmPlan,omitempty"`
	AgentTrace     *SceneAgentTraceVo        `json:"agentTrace,omitempty"`
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
	ScaleMode        string `json:"scaleMode,omitempty"`
	TemplateKey      string `json:"templateKey,omitempty"`
	Placeholder      bool   `json:"placeholder,omitempty"`
	MissingAssetKey  string `json:"missingAssetKey,omitempty"`
	GenerationTaskID string `json:"generationTaskId,omitempty"`
}

type SemanticVisualTemplateVo struct {
	TemplateKey       string                                `json:"templateKey"`
	Label             string                                `json:"label"`
	RenderingMode     string                                `json:"renderingMode"`
	Greenhouse        SemanticGreenhouseEnvelopeVo          `json:"greenhouse"`
	PlantGrid         SemanticPlantGridVo                   `json:"plantGrid"`
	Irrigation        SemanticIrrigationTemplateVo          `json:"irrigation"`
	Lighting          SemanticLightingTemplateVo            `json:"lighting"`
	ScaleCalibrations map[string]SemanticScaleCalibrationVo `json:"scaleCalibrations,omitempty"`
	Acceptance        SemanticVisualAcceptanceVo            `json:"acceptance"`
}

type SemanticGreenhouseEnvelopeVo struct {
	Center OffsetVo `json:"center"`
	Width  float64  `json:"width"`
	Depth  float64  `json:"depth"`
	Height float64  `json:"height"`
}

type SemanticPlantGridVo struct {
	Rows       int     `json:"rows"`
	Columns    int     `json:"columns"`
	SpacingX   float64 `json:"spacingX"`
	SpacingZ   float64 `json:"spacingZ"`
	BedCount   int     `json:"bedCount"`
	InsideOnly bool    `json:"insideOnly"`
}

type SemanticIrrigationTemplateVo struct {
	BedCount       int        `json:"bedCount"`
	DripLineCount  int        `json:"dripLineCount"`
	MainPipeLength float64    `json:"mainPipeLength"`
	PumpPosition   OffsetVo   `json:"pumpPosition"`
	ValvePositions []OffsetVo `json:"valvePositions,omitempty"`
}

type SemanticLightingTemplateVo struct {
	SkyColor              string  `json:"skyColor"`
	GroundColor           string  `json:"groundColor"`
	AmbientIntensity      float64 `json:"ambientIntensity"`
	DirectionalIntensity  float64 `json:"directionalIntensity"`
	MinimumScreenshotLuma float64 `json:"minimumScreenshotLuma"`
}

type SemanticScaleCalibrationVo struct {
	AssetKey          string  `json:"assetKey"`
	ScaleMode         string  `json:"scaleMode"`
	RealWidth         float64 `json:"realWidth"`
	RealDepth         float64 `json:"realDepth"`
	RealHeight        float64 `json:"realHeight"`
	AnchorDescription string  `json:"anchorDescription,omitempty"`
}

type SemanticVisualAcceptanceVo struct {
	ExpectedTomatoesInsideGreenhouse int     `json:"expectedTomatoesInsideGreenhouse"`
	MinimumScreenshotLuma            float64 `json:"minimumScreenshotLuma"`
	MaximumTomatoScale               float64 `json:"maximumTomatoScale"`
	RequiresContinuousIrrigation     bool    `json:"requiresContinuousIrrigation"`
}

type AssetSemantic struct {
	AssetKey              string             `json:"assetKey"`
	Name                  string             `json:"name"`
	Aliases               []string           `json:"aliases"`
	Category              string             `json:"category"`
	URL                   string             `json:"url"`
	DefaultScale          float64            `json:"defaultScale"`
	Footprint             FootprintVo        `json:"footprint"`
	LayoutRules           []string           `json:"layoutRules"`
	Source                string             `json:"source,omitempty"`
	License               string             `json:"license,omitempty"`
	FidelityLevel         string             `json:"fidelityLevel,omitempty"`
	ThumbnailURL          string             `json:"thumbnailUrl,omitempty"`
	GLBURL                string             `json:"glbUrl,omitempty"`
	ApplicableObjectTypes []string           `json:"applicableObjectTypes,omitempty"`
	Quality               AssetQualityInfoVo `json:"quality,omitempty"`
	Version               AssetVersionInfoVo `json:"version,omitempty"`
	MetadataComplete      bool               `json:"metadataComplete,omitempty"`
	RoutingReason         string             `json:"routingReason,omitempty"`
}

type FootprintVo struct {
	Width float64 `json:"width"`
	Depth float64 `json:"depth"`
}

type MissingAssetVo struct {
	AssetKey         string                          `json:"assetKey"`
	Name             string                          `json:"name"`
	Category         string                          `json:"category,omitempty"`
	Reason           string                          `json:"reason"`
	Prompt           string                          `json:"prompt,omitempty"`
	FallbackModelKey string                          `json:"fallbackModelKey,omitempty"`
	PlacementRefs    []string                        `json:"placementRefs,omitempty"`
	Routing          *AssetFidelityRoutingDecisionVo `json:"routing,omitempty"`
	ReferenceImage   *MissingAssetReferenceImageVo   `json:"referenceImage,omitempty"`
	Generation       *MissingAssetGenerationVo       `json:"generation,omitempty"`
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
	Enabled      bool                            `json:"enabled"`
	TaskID       string                          `json:"taskId,omitempty"`
	Status       string                          `json:"status"`
	Progress     int                             `json:"progress,omitempty"`
	ResultURL    string                          `json:"resultUrl,omitempty"`
	ThumbnailURL string                          `json:"thumbnailUrl,omitempty"`
	ErrorMessage string                          `json:"errorMessage,omitempty"`
	ReviewStatus string                          `json:"reviewStatus,omitempty"`
	Pipeline     []AssetGenerationPipelineStepVo `json:"pipeline,omitempty"`
}

type AssetGenerationPipelineStepVo struct {
	Stage       string `json:"stage"`
	Label       string `json:"label"`
	Status      string `json:"status"`
	LocalModel  string `json:"localModel,omitempty"`
	Input       string `json:"input,omitempty"`
	Output      string `json:"output,omitempty"`
	Description string `json:"description,omitempty"`
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
	AgentFailed     bool                   `json:"agentFailed,omitempty"`   // explicit LLM/DeepAgents failure marker
	AgentFailedReason string               `json:"agentFailedReason,omitempty"`
	FinalSummary    string                 `json:"finalSummary"`
	Error           string                 `json:"error,omitempty"`
}

type SceneAgentToolCallVo struct {
	CallID        string                `json:"callId,omitempty"`
	EvidenceID    string                `json:"evidenceId,omitempty"`
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
	CallID        string                `json:"callId,omitempty"`
	EvidenceID    string                `json:"evidenceId,omitempty"`
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
	// InitialState carries a real faulty scene for repair tasks (T19-T24). The agent
	// must actually modify the specified objects; it is never the gold.
	InitialState *SemanticSceneState `json:"initialState,omitempty"`
}

// SemanticSceneState is a minimal, method-independent faulty-scene snapshot that a
// repair task seeds into the builder. Only used for repair evaluation, never scored.
type SemanticSceneState struct {
	Objects  []SemanticSceneObject `json:"objects,omitempty"`
	Bindings []SemanticBindingVO   `json:"bindings,omitempty"`
}

type SemanticSceneObject struct {
	ID               string `json:"id,omitempty"`
	Type             string `json:"type,omitempty"`
	MonitoringTarget string `json:"monitoringTarget,omitempty"`
	BelongsTo        string `json:"belongsTo,omitempty"`
	Observes         string `json:"observes,omitempty"`
	AssetKey         string `json:"assetKey,omitempty"`
	AssetPolicy      string `json:"assetPolicy,omitempty"`
}

type SemanticBindingVO struct {
	Subject string `json:"subject,omitempty"`
	Target  string `json:"target,omitempty"`
	Type    string `json:"type,omitempty"`
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
