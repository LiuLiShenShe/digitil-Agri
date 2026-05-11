package vo

// ResultVo is a generic response wrapper, equivalent to Java ResultVo<T>.
type ResultVo struct {
	Code int         `json:"code"`
	Data interface{} `json:"data"`
}
