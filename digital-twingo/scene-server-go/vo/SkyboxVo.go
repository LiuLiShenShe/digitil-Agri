package vo

// SkyboxVo maps to the skybox table.
type SkyboxVo struct {
	Alias  string `json:"alias" db:"alias"`
	Path   string `json:"path" db:"path"`
	Left   string `json:"left" db:"left"`
	Right  string `json:"right" db:"right"`
	Front  string `json:"front" db:"front"`
	Back   string `json:"back" db:"back"`
	Top    string `json:"top" db:"top"`
	Bottom string `json:"bottom" db:"bottom"`
}
