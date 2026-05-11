package vo

// SceneModelVo maps to the scenemodel table.
// Extends SceneModelVoKey by embedding.
type SceneModelVo struct {
	SceneModelVoKey
	URL     string  `json:"url" db:"url"`
	Scale   float64 `json:"scale" db:"scale"`
	OffsetX float64 `json:"offsetx" db:"offsetX"`
	OffsetY float64 `json:"offsety" db:"offsetY"`
	OffsetZ float64 `json:"offsetz" db:"offsetZ"`
	Angle   int     `json:"angle" db:"angle"`
	DataId  string  `json:"dataid" db:"dataId"`
}

// ConvertToLoadObj converts the scene model into a load-suitable map,
// matching Java SceneModelVo.convertToLoadObj().
func (s *SceneModelVo) ConvertToLoadObj() map[string]interface{} {
	loadObj := make(map[string]interface{})
	loadObj["url"] = s.URL

	options := make(map[string]interface{})
	options["scale"] = s.Scale
	options["angle"] = s.Angle
	options["dataId"] = s.DataId

	offset := make(map[string]interface{})
	offset["x"] = s.OffsetX
	offset["y"] = s.OffsetY
	offset["z"] = s.OffsetZ
	options["offset"] = offset

	loadObj["options"] = options
	return loadObj
}
