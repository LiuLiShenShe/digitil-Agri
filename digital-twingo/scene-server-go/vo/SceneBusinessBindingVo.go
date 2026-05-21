package vo

type SceneBindingUpdateRequest struct {
	SceneName        string `json:"sceneName"`
	SceneObjectId    string `json:"sceneObjectId"`
	BusinessObjectId string `json:"businessObjectId"`
	AssetKey         string `json:"assetKey"`
	IsDefaultBinding bool   `json:"isDefaultBinding"`
}

type SceneBusinessBindingVo struct {
	SceneName        string `json:"sceneName"`
	ModelId          int    `json:"modelId"`
	SceneObjectId    string `json:"sceneObjectId"`
	BusinessObjectId string `json:"businessObjectId"`
	AssetKey         string `json:"assetKey"`
	IsDefaultBinding bool   `json:"isDefaultBinding"`
	URL              string `json:"url"`
}

type SceneBindingLookupResponse struct {
	Code     int                      `json:"code"`
	Error    string                   `json:"error,omitempty"`
	Binding  *SceneBusinessBindingVo  `json:"binding,omitempty"`
	Bindings []SceneBusinessBindingVo `json:"bindings,omitempty"`
	Object   *AgriculturalObjectVo    `json:"object,omitempty"`
}

type SceneBindingValidationIssueVo struct {
	Category         string `json:"category"`
	SceneName        string `json:"sceneName"`
	SceneObjectId    string `json:"sceneObjectId"`
	ModelId          int    `json:"modelId"`
	BusinessObjectId string `json:"businessObjectId,omitempty"`
	BusinessType     string `json:"businessType,omitempty"`
	Message          string `json:"message"`
}

type SceneBindingValidationSummaryVo struct {
	SceneName           string                          `json:"sceneName"`
	TotalSceneObjects   int                             `json:"totalSceneObjects"`
	BoundSceneObjects   int                             `json:"boundSceneObjects"`
	BindingRate         float64                         `json:"bindingRate"`
	VerifiedObjectTypes []string                        `json:"verifiedObjectTypes"`
	MissingObjectTypes  []string                        `json:"missingObjectTypes"`
	Issues              []SceneBindingValidationIssueVo `json:"issues"`
}

type SceneBindingValidationResponse struct {
	Code    int                             `json:"code"`
	Error   string                          `json:"error,omitempty"`
	Summary SceneBindingValidationSummaryVo `json:"summary"`
}
