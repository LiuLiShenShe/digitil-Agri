package service

import (
	"testing"

	"scene-server-go/mapper"
)

func TestCompletedGeneratedAssetIsAutoApproved(t *testing.T) {
	if got := finalGeneratedAssetStatus("completed"); got != "approved" {
		t.Fatalf("finalGeneratedAssetStatus(completed) = %q, want approved", got)
	}
}

func TestGeneratedAssetModelNamePrefersAssetName(t *testing.T) {
	job := &mapper.AssetJobRecord{JobID: "job-001", AssetName: "番茄AI模型"}

	if got := generatedAssetModelName(job); got != "番茄AI模型" {
		t.Fatalf("generatedAssetModelName() = %q, want 番茄AI模型", got)
	}
}

func TestGeneratedAssetModelNameFallsBackToJobID(t *testing.T) {
	job := &mapper.AssetJobRecord{JobID: "job-001"}

	if got := generatedAssetModelName(job); got != "job-001" {
		t.Fatalf("generatedAssetModelName() = %q, want job-001", got)
	}
}
