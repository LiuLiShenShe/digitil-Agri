package vo

// CurveData represents a time-value data point for simulated curves.
type CurveData struct {
	Time  string  `json:"time"`
	Value float64 `json:"value"`
}
