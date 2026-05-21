package service

import (
	"fmt"
	"strings"

	"scene-server-go/vo"
)

const (
	missingReferenceStatusMissing  = "missing"
	missingReferenceStatusResolved = "resolved"
	missingReferenceStatusUploaded = "uploaded"
	missingGenerationStatusWaiting = "waiting_image"
	missingGenerationStatusQueued  = "queued"
	missingGenerationStatusRunning = "running"
	missingGenerationStatusDone    = "completed"
	missingGenerationStatusFailed  = "failed"
)

type ReferenceImageResolver struct {
	presets map[string][]vo.ReferenceImageCandidateVo
}

func NewReferenceImageResolver() *ReferenceImageResolver {
	return &ReferenceImageResolver{presets: presetReferenceImages()}
}

func (r *ReferenceImageResolver) Resolve(asset vo.MissingAssetVo) vo.MissingAssetReferenceImageVo {
	candidates := append([]vo.ReferenceImageCandidateVo{}, r.presets[strings.TrimSpace(asset.AssetKey)]...)
	if len(candidates) == 0 {
		return vo.MissingAssetReferenceImageVo{
			Status: missingReferenceStatusMissing,
		}
	}
	best := candidates[0]
	return vo.MissingAssetReferenceImageVo{
		Status:     missingReferenceStatusResolved,
		Source:     best.Source,
		URL:        best.URL,
		Candidates: candidates,
	}
}

func presetReferenceImages() map[string][]vo.ReferenceImageCandidateVo {
	return map[string][]vo.ReferenceImageCandidateVo{
		"irrigation": {
			{ID: "preset_irrigation_machine", Source: "preset", URL: "/scene-assets/reference/irrigation-machine.png", Score: 0.88},
		},
		"greenhouse": {
			{ID: "preset_greenhouse_photo", Source: "preset", URL: "/scene-assets/reference/greenhouse.jpg", Score: 0.86},
		},
	}
}

func buildMissingAssetPrompt(asset vo.MissingAssetVo) string {
	name := strings.TrimSpace(asset.Name)
	if name == "" {
		name = strings.TrimSpace(asset.AssetKey)
	}
	category := strings.TrimSpace(asset.Category)
	if category == "" {
		category = "asset"
	}
	return fmt.Sprintf("智慧农业数字孪生场景中的%s，类别为%s，单体清晰，适合生成低多边形 GLB 模型", name, category)
}
