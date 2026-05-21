package mapper

import "strings"
import "testing"

func TestAgriculturalObjectSelectColumnsEscapesSpatialJSONColumn(t *testing.T) {
	columns := agriculturalObjectSelectColumns()

	if !strings.Contains(columns, "CAST(`spatial` AS CHAR)") {
		t.Fatalf("agricultural object select columns must escape spatial JSON column, got: %s", columns)
	}
	if !strings.Contains(columns, "AS `spatial`") {
		t.Fatalf("agricultural object select columns must escape spatial alias, got: %s", columns)
	}
}

func TestNormalizeDatetimeForMySQLAcceptsRFC3339(t *testing.T) {
	got := normalizeDatetimeForMySQL("2026-05-21T08:00:00Z")

	if got != "2026-05-21 08:00:00" {
		t.Fatalf("normalized datetime = %q, want %q", got, "2026-05-21 08:00:00")
	}
}
