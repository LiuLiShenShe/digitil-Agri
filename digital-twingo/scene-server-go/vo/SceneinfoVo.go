package vo

import "encoding/json"

// SceneinfoVo maps to the sceneinfo table.
type SceneinfoVo struct {
	SceneName       string `json:"sceneName" db:"sceneName"`
	Background      string `json:"background" db:"background"`
	AmbientLight    string `json:"ambientLight" db:"ambientLight"`
	DirectionalLight string `json:"directionalLight" db:"directionalLight"`
	SpotLight       string `json:"spotLight" db:"spotLight"`
	Grid            string `json:"grid" db:"grid"`
	GroundPane      string `json:"groundPane" db:"groundPane"`
}

// ConvertToLoadObj converts the scene info into a load-suitable map,
// parsing JSON string fields back to objects, matching Java convertToLoadObj().
func (s *SceneinfoVo) ConvertToLoadObj() map[string]interface{} {
	result := make(map[string]interface{})
	result["sceneName"] = s.SceneName
	result["background"] = parseJSON(s.Background)
	result["ambientLight"] = parseJSON(s.AmbientLight)
	result["directionalLight"] = parseJSON(s.DirectionalLight)
	result["spotLight"] = parseJSON(s.SpotLight)
	result["grid"] = parseJSON(s.Grid)
	result["groundPane"] = parseJSON(s.GroundPane)
	return result
}

func parseJSON(s string) interface{} {
	if s == "" {
		return nil
	}
	var v interface{}
	if err := json.Unmarshal([]byte(s), &v); err != nil {
		return nil
	}
	return v
}
