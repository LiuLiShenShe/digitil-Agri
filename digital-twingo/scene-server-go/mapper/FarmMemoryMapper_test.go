package mapper

import (
	"strings"
	"testing"
)

func TestBuildLatestMetricPointsQueryUsesDatabaseSideLatestSelection(t *testing.T) {
	args := []interface{}{}
	query := buildLatestMetricPointsQuery(
		[]string{"iot-greenhouse-01", "iot-irrigation-01"},
		[]string{"temperature", "waterFlow"},
		&args,
	)

	if !strings.Contains(query, "MAX(timestamp)") || !strings.Contains(query, "GROUP BY deviceId, metricKey") {
		t.Fatalf("latest metric query should select newest rows in SQL, got: %s", query)
	}
	if strings.Contains(query, "ORDER BY timestamp ASC") {
		t.Fatalf("latest metric query should not scan all history ordered ascending: %s", query)
	}
	if len(args) != 8 {
		t.Fatalf("latest metric query args = %d, want 8: %#v", len(args), args)
	}
}
