package vo

// SceneModelVoKey is the composite primary key for scenemodel table.
type SceneModelVoKey struct {
	SceneName string `json:"scenename" db:"sceneName"`
	ModelId   int    `json:"modelid" db:"modelId"`
}
