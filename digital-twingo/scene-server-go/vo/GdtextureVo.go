package vo

// GdtextureVo maps to the gdtexture table.
type GdtextureVo struct {
	Name string `json:"name" db:"name"`
	Pic  string `json:"pic" db:"pic"`
}
