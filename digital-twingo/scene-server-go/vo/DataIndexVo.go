package vo

// DataIndexVo maps to the dataindex table.
type DataIndexVo struct {
	DataId   string `json:"dataid" db:"dataId"`
	Category string `json:"category" db:"category"`
	Name     string `json:"name" db:"name"`
}
