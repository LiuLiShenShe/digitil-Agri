package service

import (
	"strings"

	"scene-server-go/vo"
)

type AssetFidelityRoutingService struct {
	registry *AssetRegistryService
}

func NewAssetFidelityRoutingService(registry *AssetRegistryService) *AssetFidelityRoutingService {
	if registry == nil {
		registry = NewAssetRegistryService()
	}
	return &AssetFidelityRoutingService{registry: registry}
}

func (s *AssetFidelityRoutingService) Decide(req vo.AssetFidelityRoutingRequest) vo.AssetFidelityRoutingDecisionVo {
	req.AssetKey = strings.TrimSpace(req.AssetKey)
	req.ObjectType = strings.TrimSpace(req.ObjectType)
	decision := vo.AssetFidelityRoutingDecisionVo{
		AssetKey:            req.AssetKey,
		ObjectType:          req.ObjectType,
		PlaceholderAssetKey: "placeholder.device",
	}

	if isKeyPlantRouting(req) {
		decision.Strategy = "F2DMAS"
		decision.SelectedAssetKey = req.AssetKey
		decision.FidelityLevel = "high_fidelity_reconstruction"
		decision.RoutingReason = "关键植株、异常植株或论文样本需要可信几何，优先使用 F2DMAS 或高保真重建路径。"
		return decision
	}

	if isProceduralAsset(req.AssetKey, req.ObjectType) {
		decision.Strategy = "procedural"
		decision.FidelityLevel = "rule_based"
		decision.RoutingReason = "地块、道路、围栏、沟渠或管线属于规则几何，程序化生成可满足当前保真度。"
		return decision
	}

	if meta, ok := s.registry.Get(req.AssetKey); ok && strings.TrimSpace(meta.GLBURL) != "" && meta.MetadataComplete {
		decision.Strategy = "existing_asset"
		decision.SelectedAssetKey = meta.AssetKey
		decision.SelectedURL = meta.GLBURL
		decision.FidelityLevel = meta.FidelityLevel
		decision.RoutingReason = "资产库已有可加载且通过基础元数据验收的 GLB，优先复用已有资产。"
		return decision
	}

	if isEquipmentLike(req.AssetKey, req.ObjectType) {
		decision.Strategy = "TRELLIS.2"
		decision.FidelityLevel = "generated_standard"
		decision.RequiresGenerationTask = true
		decision.GenerationMode = "image_to_3d"
		decision.ReferenceImageRequired = true
		decision.RoutingReason = "普通设备或装饰资产缺失，进入 TRELLIS.2 图片转 3D 生成任务，同时保留占位模型。"
		return decision
	}

	decision.Strategy = "placeholder"
	decision.FidelityLevel = "placeholder"
	decision.RequiresGenerationTask = true
	decision.GenerationMode = "manual_review"
	decision.ReferenceImageRequired = true
	decision.RoutingReason = "资产缺失且暂无明确自动生成策略，使用占位模型保持场景连续并记录补资产任务。"
	return decision
}

func isKeyPlantRouting(req vo.AssetFidelityRoutingRequest) bool {
	objectType := strings.TrimSpace(req.ObjectType)
	value := strings.ToLower(strings.TrimSpace(req.BusinessValue))
	required := strings.ToLower(strings.TrimSpace(req.RequiredFidelity))
	return objectType == string(vo.ObjectTypePlant) &&
		(req.IsKeyPlant ||
			req.IsAbnormalPlant ||
			req.IsResearchSample ||
			strings.Contains(value, "research") ||
			strings.Contains(value, "abnormal") ||
			strings.Contains(required, "trustworthy") ||
			strings.Contains(required, "high"))
}

func isProceduralAsset(assetKey string, objectType string) bool {
	text := strings.ToLower(strings.TrimSpace(assetKey) + " " + strings.TrimSpace(objectType))
	for _, keyword := range []string{"parcel", "road", "fence", "ditch", "pipeline", "管线", "沟渠", "围栏", "道路", "地块"} {
		if strings.Contains(text, keyword) {
			return true
		}
	}
	return false
}

func isEquipmentLike(assetKey string, objectType string) bool {
	text := strings.ToLower(strings.TrimSpace(assetKey) + " " + strings.TrimSpace(objectType))
	for _, keyword := range []string{"camera", "sensor", "device", "equipment", "tractor", "drone", "摄像", "传感", "设备", "农机", "无人机"} {
		if strings.Contains(text, keyword) {
			return true
		}
	}
	return true
}
