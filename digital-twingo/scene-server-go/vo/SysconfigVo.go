package vo

// SysconfigVo maps to the sysconfig table.
type SysconfigVo struct {
	Key   string `json:"key" db:"key"`
	Value string `json:"value" db:"value"`
}
