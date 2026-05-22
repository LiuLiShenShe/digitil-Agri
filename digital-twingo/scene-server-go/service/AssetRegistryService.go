package service

import (
	"sort"
	"strings"

	"scene-server-go/vo"
)

type AssetRegistryService struct {
	assets map[string]vo.AssetMetadataVo
}

func NewAssetRegistryService() *AssetRegistryService {
	assets := map[string]vo.AssetMetadataVo{}
	for _, item := range semanticAssets() {
		meta := metadataFromSemanticAsset(item)
		assets[meta.AssetKey] = meta
	}
	return &AssetRegistryService{assets: assets}
}

func (s *AssetRegistryService) Get(assetKey string) (vo.AssetMetadataVo, bool) {
	if s == nil {
		return vo.AssetMetadataVo{}, false
	}
	item, ok := s.assets[strings.TrimSpace(assetKey)]
	return item, ok
}

func (s *AssetRegistryService) List() []vo.AssetMetadataVo {
	if s == nil {
		return nil
	}
	result := make([]vo.AssetMetadataVo, 0, len(s.assets))
	for _, item := range s.assets {
		result = append(result, item)
	}
	sort.SliceStable(result, func(i, j int) bool {
		return result[i].AssetKey < result[j].AssetKey
	})
	return result
}

func (s *AssetRegistryService) PlantGeometryVersions(objectID string) []vo.PlantGeometryVersionVo {
	objectID = strings.TrimSpace(objectID)
	if objectID == "" {
		objectID = "plant-tomato-001"
	}
	stages := []struct {
		stage string
		label string
		url   string
	}{
		{stage: "seedling", label: "苗期", url: "/scene-assets/models/Tomato_1.glb"},
		{stage: "vegetative", label: "营养生长期", url: "/scene-assets/models/Tomato_2.glb"},
		{stage: "flowering", label: "开花期", url: "/scene-assets/models/Tomato_3.glb"},
		{stage: "fruiting", label: "结果期", url: "/scene-assets/models/Tomato_4.glb"},
		{stage: "mature", label: "成熟期", url: "/scene-assets/models/Tomato_Crop.glb"},
	}
	result := make([]vo.PlantGeometryVersionVo, 0, len(stages))
	for i, stage := range stages {
		result = append(result, vo.PlantGeometryVersionVo{
			ObjectID:      objectID,
			Stage:         stage.stage,
			StageLabel:    stage.label,
			AssetKey:      "tomato",
			GLBURL:        stage.url,
			ThumbnailURL:  "/scene-assets/thumbs/c0c208ec95e4.jpg",
			FidelityLevel: "milestone_f2dmas",
			Version:       "tomato-stage-v" + string(rune('1'+i)),
			CreatedAt:     "2026-05-22T00:00:00Z",
			PhenotypeBinding: vo.PlantPhenotypeBindingVo{
				ObjectID:  objectID,
				MetricKey: "plantHeight",
				Source:    "farm_memory.observation",
			},
		})
	}
	return result
}

func metadataFromSemanticAsset(item vo.AssetSemantic) vo.AssetMetadataVo {
	url := strings.TrimSpace(item.URL)
	meta := vo.AssetMetadataVo{
		AssetKey:              item.AssetKey,
		Name:                  item.Name,
		Aliases:               append([]string{}, item.Aliases...),
		Category:              item.Category,
		Source:                assetSourceForURL(url),
		License:               assetLicenseForURL(url),
		FidelityLevel:         assetFidelityLevel(item),
		ThumbnailURL:          assetThumbnailURL(item.AssetKey, url),
		GLBURL:                url,
		ApplicableObjectTypes: applicableObjectTypes(item),
		DefaultScale:          item.DefaultScale,
		Footprint:             item.Footprint,
		LayoutRules:           append([]string{}, item.LayoutRules...),
		Version: vo.AssetVersionInfoVo{
			Version:   "v1.0.0",
			Revision:  modelURLStem(url),
			UpdatedAt: "2026-05-22",
		},
	}
	meta.Quality = qualityForAsset(meta)
	meta.MetadataComplete = assetMetadataComplete(meta)
	return meta
}

func assetSourceForURL(url string) string {
	url = strings.TrimSpace(url)
	if url == "" {
		return ""
	}
	if strings.HasPrefix(url, "/scene-assets/") {
		return "scene-assets managed library"
	}
	if strings.HasPrefix(url, "/models/") {
		return "frontend public/models legacy library"
	}
	return "project managed asset"
}

func assetLicenseForURL(url string) string {
	if strings.TrimSpace(url) == "" {
		return ""
	}
	return "project-internal demo asset"
}

func assetFidelityLevel(item vo.AssetSemantic) string {
	switch item.AssetKey {
	case "tomato":
		return "medium_milestone"
	case "road", "fence":
		return "procedural_ready"
	case "camera", "sensor", "tractor", "drone":
		return "needs_generation"
	default:
		if strings.TrimSpace(item.URL) == "" {
			return "needs_generation"
		}
		return "standard_scene_asset"
	}
}

func assetThumbnailURL(assetKey string, url string) string {
	if strings.TrimSpace(url) == "" {
		return ""
	}
	thumbs := map[string]string{
		"greenhouse":      "/scene-assets/thumbs/b31242a80a54.jpg",
		"corn":            "/scene-assets/thumbs/c0c208ec95e4.jpg",
		"wheat":           "/scene-assets/thumbs/5d22775ae535.jpg",
		"rice":            "/scene-assets/thumbs/27345ae0538a.jpg",
		"tomato":          "/scene-assets/thumbs/c39d702fb821.jpg",
		"lettuce":         "/scene-assets/thumbs/84f853ef3a53.jpg",
		"pumpkin":         "/scene-assets/thumbs/0b00beeaf813.jpg",
		"weather_station": "/scene-assets/thumbs/b31242a80a54.jpg",
		"irrigation":      "/scene-assets/thumbs/5d22775ae535.jpg",
		"water_tower":     "/scene-assets/thumbs/27345ae0538a.jpg",
		"warehouse":       "/scene-assets/thumbs/c39d702fb821.jpg",
		"admin_building":  "/scene-assets/thumbs/84f853ef3a53.jpg",
		"road":            "/scene-assets/thumbs/0b00beeaf813.jpg",
		"fence":           "/scene-assets/thumbs/c0c208ec95e4.jpg",
		"windmill":        "/scene-assets/thumbs/b31242a80a54.jpg",
		"solar":           "/scene-assets/thumbs/27345ae0538a.jpg",
	}
	return thumbs[assetKey]
}

func applicableObjectTypes(item vo.AssetSemantic) []string {
	switch item.AssetKey {
	case "greenhouse":
		return []string{string(vo.ObjectTypeGreenhouse)}
	case "tomato", "corn", "wheat", "rice", "lettuce", "pumpkin":
		return []string{string(vo.ObjectTypePlant), string(vo.ObjectTypeCropRow), string(vo.ObjectTypeCropBatch), string(vo.ObjectTypeParcel)}
	case "weather_station", "sensor":
		return []string{string(vo.ObjectTypeSensor), string(vo.ObjectTypeDevice)}
	case "irrigation", "water_tower":
		return []string{string(vo.ObjectTypeDevice)}
	case "camera":
		return []string{string(vo.ObjectTypeCamera)}
	case "road", "fence":
		return []string{string(vo.ObjectTypeParcel), "Infrastructure"}
	default:
		return []string{"SceneObject"}
	}
}

func qualityForAsset(meta vo.AssetMetadataVo) vo.AssetQualityInfoVo {
	quality := vo.AssetQualityInfoVo{
		Loadable:      strings.TrimSpace(meta.GLBURL) != "",
		Axis:          "Y-up",
		UnitScale:     1,
		Center:        vo.OffsetVo{X: 0, Y: 0, Z: 0},
		PolygonCount:  estimatedPolygonCount(meta.AssetKey),
		TextureCount:  estimatedTextureCount(meta.AssetKey),
		VolumeM3:      estimatedVolume(meta.AssetKey),
		HasThumbnail:  strings.TrimSpace(meta.ThumbnailURL) != "",
		HasSource:     strings.TrimSpace(meta.Source) != "",
		HasLicense:    strings.TrimSpace(meta.License) != "",
		LOD:           "lod0",
		QualityStatus: "accepted",
	}
	if !quality.Loadable {
		quality.QualityStatus = ""
		quality.Axis = ""
		quality.UnitScale = 0
		quality.PolygonCount = 0
		quality.TextureCount = 0
		quality.VolumeM3 = 0
		quality.LOD = ""
		quality.Issues = append(quality.Issues, "missing_glb")
	}
	if !quality.HasThumbnail {
		quality.Issues = append(quality.Issues, "missing_thumbnail")
	}
	if !quality.HasSource {
		quality.Issues = append(quality.Issues, "missing_source")
	}
	if !quality.HasLicense {
		quality.Issues = append(quality.Issues, "missing_license")
	}
	if len(quality.Issues) > 0 && quality.QualityStatus == "accepted" {
		quality.QualityStatus = "flagged"
	}
	return quality
}

func assetMetadataComplete(meta vo.AssetMetadataVo) bool {
	return strings.TrimSpace(meta.AssetKey) != "" &&
		strings.TrimSpace(meta.Category) != "" &&
		strings.TrimSpace(meta.Source) != "" &&
		strings.TrimSpace(meta.License) != "" &&
		strings.TrimSpace(meta.FidelityLevel) != "" &&
		strings.TrimSpace(meta.ThumbnailURL) != "" &&
		strings.TrimSpace(meta.GLBURL) != "" &&
		len(meta.ApplicableObjectTypes) > 0 &&
		meta.Quality.Loadable &&
		meta.Quality.PolygonCount > 0 &&
		meta.Quality.TextureCount >= 0 &&
		meta.Quality.VolumeM3 > 0 &&
		strings.TrimSpace(meta.Version.Version) != ""
}

func estimatedPolygonCount(assetKey string) int {
	switch assetKey {
	case "greenhouse":
		return 18000
	case "road", "fence":
		return 800
	case "tomato", "corn", "wheat", "rice", "lettuce", "pumpkin":
		return 4500
	default:
		return 6000
	}
}

func estimatedTextureCount(assetKey string) int {
	switch assetKey {
	case "road", "fence":
		return 1
	default:
		return 2
	}
}

func estimatedVolume(assetKey string) float64 {
	switch assetKey {
	case "greenhouse":
		return 920
	case "road":
		return 12
	case "fence":
		return 8
	case "tomato", "corn", "wheat", "rice", "lettuce", "pumpkin":
		return 2.5
	default:
		return 25
	}
}
