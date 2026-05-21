package service

import (
	"crypto/sha1"
	"encoding/hex"
	"fmt"
	"math"
	"sort"
	"strings"

	"scene-server-go/mapper"
	"scene-server-go/vo"
)

type SceneBindingStore interface {
	ListSceneModels(sceneName string) ([]vo.SceneModelVo, error)
	UpdateSceneModelBinding(sceneName string, modelId int, sceneObjectId string, businessObjectId string, assetKey string, isDefaultBinding bool) (int, error)
	ClearSceneModelBinding(sceneName string, modelId int, sceneObjectId string) (int, error)
}

type SceneBusinessBindingService struct {
	sceneStore    SceneBindingStore
	objectService *AgriculturalObjectService
}

func NewSceneBusinessBindingService(sceneStore SceneBindingStore, objectService *AgriculturalObjectService) *SceneBusinessBindingService {
	if sceneStore == nil {
		sceneStore = mapper.NewSceneModelMapper()
	}
	if objectService == nil {
		objectService = NewAgriculturalObjectService()
	}
	return &SceneBusinessBindingService{sceneStore: sceneStore, objectService: objectService}
}

func NewDefaultSceneBusinessBindingService() *SceneBusinessBindingService {
	return NewSceneBusinessBindingService(mapper.NewSceneModelMapper(), NewAgriculturalObjectService())
}

func FallbackSceneObjectID(sceneName string, modelId int) string {
	sum := sha1.Sum([]byte(fmt.Sprintf("%s:%d", sceneName, modelId)))
	return "scene-object-" + hex.EncodeToString(sum[:])[:12]
}

func EnsureSceneObjectID(model *vo.SceneModelVo) string {
	if strings.TrimSpace(model.SceneObjectId) == "" {
		model.SceneObjectId = FallbackSceneObjectID(model.SceneName, model.ModelId)
	}
	return model.SceneObjectId
}

func (s *SceneBusinessBindingService) UpdateBinding(req vo.SceneBindingUpdateRequest) vo.SceneBindingLookupResponse {
	req.SceneName = strings.TrimSpace(req.SceneName)
	req.SceneObjectId = strings.TrimSpace(req.SceneObjectId)
	req.BusinessObjectId = strings.TrimSpace(req.BusinessObjectId)
	req.AssetKey = strings.TrimSpace(req.AssetKey)
	if req.SceneName == "" || req.SceneObjectId == "" {
		return vo.SceneBindingLookupResponse{Code: 400, Error: "sceneName and sceneObjectId are required"}
	}
	model, err := s.findSceneModel(req.SceneName, req.SceneObjectId)
	if err != nil {
		return vo.SceneBindingLookupResponse{Code: 404, Error: err.Error()}
	}
	resolvedSceneName := model.SceneName
	if req.BusinessObjectId != "" {
		lookup := s.objectService.Lookup(vo.ObjectLookupRequest{ObjectID: req.BusinessObjectId})
		if lookup.Code != 200 {
			return vo.SceneBindingLookupResponse{Code: lookup.Code, Error: lookup.Error}
		}
	}
	if req.AssetKey == "" {
		req.AssetKey = model.AssetKey
	}
	_, err = s.sceneStore.UpdateSceneModelBinding(resolvedSceneName, model.ModelId, req.SceneObjectId, req.BusinessObjectId, req.AssetKey, req.IsDefaultBinding)
	if err != nil {
		return vo.SceneBindingLookupResponse{Code: 999, Error: err.Error()}
	}
	return s.LookupBySceneObject(resolvedSceneName, req.SceneObjectId)
}

func (s *SceneBusinessBindingService) ClearBinding(sceneName string, sceneObjectId string) vo.SceneBindingLookupResponse {
	sceneName = strings.TrimSpace(sceneName)
	sceneObjectId = strings.TrimSpace(sceneObjectId)
	if sceneName == "" || sceneObjectId == "" {
		return vo.SceneBindingLookupResponse{Code: 400, Error: "sceneName and sceneObjectId are required"}
	}
	model, err := s.findSceneModel(sceneName, sceneObjectId)
	if err != nil {
		return vo.SceneBindingLookupResponse{Code: 404, Error: err.Error()}
	}
	resolvedSceneName := model.SceneName
	_, err = s.sceneStore.ClearSceneModelBinding(resolvedSceneName, model.ModelId, sceneObjectId)
	if err != nil {
		return vo.SceneBindingLookupResponse{Code: 999, Error: err.Error()}
	}
	return s.LookupBySceneObject(resolvedSceneName, sceneObjectId)
}

func (s *SceneBusinessBindingService) LookupBySceneObject(sceneName string, sceneObjectId string) vo.SceneBindingLookupResponse {
	sceneName = strings.TrimSpace(sceneName)
	sceneObjectId = strings.TrimSpace(sceneObjectId)
	if sceneName == "" || sceneObjectId == "" {
		return vo.SceneBindingLookupResponse{Code: 400, Error: "sceneName and sceneObjectId are required"}
	}
	model, err := s.findSceneModel(sceneName, sceneObjectId)
	if err != nil {
		return vo.SceneBindingLookupResponse{Code: 404, Error: err.Error()}
	}
	binding := bindingFromModel(*model)
	result := vo.SceneBindingLookupResponse{Code: 200, Binding: &binding}
	if binding.BusinessObjectId != "" {
		lookup := s.objectService.Lookup(vo.ObjectLookupRequest{ObjectID: binding.BusinessObjectId})
		if lookup.Code == 200 {
			result.Object = lookup.Object
		}
	}
	return result
}

func (s *SceneBusinessBindingService) LookupByBusinessObject(sceneName string, businessObjectId string) vo.SceneBindingLookupResponse {
	sceneName = strings.TrimSpace(sceneName)
	businessObjectId = strings.TrimSpace(businessObjectId)
	if sceneName == "" || businessObjectId == "" {
		return vo.SceneBindingLookupResponse{Code: 400, Error: "sceneName and businessObjectId are required"}
	}
	models, err := s.listSceneModelsByCompatibleName(sceneName)
	if err != nil {
		return vo.SceneBindingLookupResponse{Code: 999, Error: err.Error()}
	}
	bindings := make([]vo.SceneBusinessBindingVo, 0)
	for i := range models {
		EnsureSceneObjectID(&models[i])
		if models[i].BusinessObjectId == businessObjectId {
			bindings = append(bindings, bindingFromModel(models[i]))
		}
	}
	sort.SliceStable(bindings, func(i, j int) bool {
		if bindings[i].IsDefaultBinding != bindings[j].IsDefaultBinding {
			return bindings[i].IsDefaultBinding
		}
		return bindings[i].SceneObjectId < bindings[j].SceneObjectId
	})
	result := vo.SceneBindingLookupResponse{Code: 200, Bindings: bindings}
	lookup := s.objectService.Lookup(vo.ObjectLookupRequest{ObjectID: businessObjectId})
	if lookup.Code == 200 {
		result.Object = lookup.Object
	}
	return result
}

func (s *SceneBusinessBindingService) ValidateScene(sceneName string) vo.SceneBindingValidationResponse {
	sceneName = strings.TrimSpace(sceneName)
	if sceneName == "" {
		return vo.SceneBindingValidationResponse{Code: 400, Error: "sceneName is required"}
	}
	models, err := s.listSceneModelsByCompatibleName(sceneName)
	if err != nil {
		return vo.SceneBindingValidationResponse{Code: 999, Error: err.Error()}
	}
	summary := vo.SceneBindingValidationSummaryVo{
		SceneName: sceneName,
		Issues:    []vo.SceneBindingValidationIssueVo{},
	}
	verifiedTypes := map[string]bool{}
	for i := range models {
		EnsureSceneObjectID(&models[i])
		businessObjectId := strings.TrimSpace(models[i].BusinessObjectId)
		assetKey := strings.TrimSpace(models[i].AssetKey)
		summary.TotalSceneObjects++
		var obj *vo.AgriculturalObjectVo
		if businessObjectId != "" {
			summary.BoundSceneObjects++
			lookup := s.objectService.Lookup(vo.ObjectLookupRequest{ObjectID: businessObjectId})
			if lookup.Code == 200 && lookup.Object != nil {
				obj = lookup.Object
				if isCoreBindingType(obj.Type) {
					verifiedTypes[obj.Type] = true
				}
			}
		}
		if obj == nil && isCoreAssetKey(assetKey) {
			summary.Issues = append(summary.Issues, validationIssue("missing_business_binding", models[i], "", "核心可观测场景对象缺少业务对象绑定"))
		}
		if obj != nil && missingDataBinding(*obj) {
			summary.Issues = append(summary.Issues, validationIssue("missing_data_binding", models[i], obj.Type, "业务对象缺少可用数据绑定线索"))
		}
		if assetKey == "" {
			businessType := ""
			if obj != nil {
				businessType = obj.Type
			}
			summary.Issues = append(summary.Issues, validationIssue("missing_asset_metadata", models[i], businessType, "场景对象缺少资产元数据 assetKey"))
		}
	}
	if summary.TotalSceneObjects > 0 {
		summary.BindingRate = math.Round(float64(summary.BoundSceneObjects)/float64(summary.TotalSceneObjects)*10000) / 100
	}
	for _, objectType := range coreBindingObjectTypes {
		if verifiedTypes[objectType] {
			summary.VerifiedObjectTypes = append(summary.VerifiedObjectTypes, objectType)
		} else {
			summary.MissingObjectTypes = append(summary.MissingObjectTypes, objectType)
		}
	}
	return vo.SceneBindingValidationResponse{Code: 200, Summary: summary}
}

func (s *SceneBusinessBindingService) findSceneModel(sceneName string, sceneObjectId string) (*vo.SceneModelVo, error) {
	models, err := s.listSceneModelsByCompatibleName(sceneName)
	if err != nil {
		return nil, err
	}
	for i := range models {
		EnsureSceneObjectID(&models[i])
		if models[i].SceneObjectId == sceneObjectId {
			return &models[i], nil
		}
	}
	return nil, fmt.Errorf("scene object not found: %s", sceneObjectId)
}

func (s *SceneBusinessBindingService) listSceneModelsByCompatibleName(sceneName string) ([]vo.SceneModelVo, error) {
	var firstErr error
	var empty []vo.SceneModelVo
	for _, candidate := range compatibleSceneNames(sceneName) {
		models, err := s.sceneStore.ListSceneModels(candidate)
		if err != nil {
			if firstErr == nil {
				firstErr = err
			}
			continue
		}
		if len(models) > 0 {
			return models, nil
		}
		if candidate == sceneName {
			empty = models
		}
	}
	if firstErr != nil {
		return nil, firstErr
	}
	if empty != nil {
		return empty, nil
	}
	return []vo.SceneModelVo{}, nil
}

func compatibleSceneNames(sceneName string) []string {
	sceneName = strings.TrimSpace(sceneName)
	names := []string{sceneName}
	if legacy := utf8BytesAsWindows1252Text(sceneName); legacy != "" && legacy != sceneName {
		names = append(names, legacy)
	}
	if legacy := utf8BytesAsLatin1Text(sceneName); legacy != "" && legacy != sceneName && legacy != names[len(names)-1] {
		names = append(names, legacy)
	}
	return names
}

func utf8BytesAsWindows1252Text(value string) string {
	runes := make([]rune, 0, len(value))
	for _, b := range []byte(value) {
		if mapped, ok := windows1252ControlRunes[b]; ok {
			runes = append(runes, mapped)
		} else {
			runes = append(runes, rune(b))
		}
	}
	return string(runes)
}

func utf8BytesAsLatin1Text(value string) string {
	runes := make([]rune, 0, len(value))
	for _, b := range []byte(value) {
		runes = append(runes, rune(b))
	}
	return string(runes)
}

var windows1252ControlRunes = map[byte]rune{
	0x80: '€',
	0x82: '‚',
	0x83: 'ƒ',
	0x84: '„',
	0x85: '…',
	0x86: '†',
	0x87: '‡',
	0x88: 'ˆ',
	0x89: '‰',
	0x8A: 'Š',
	0x8B: '‹',
	0x8C: 'Œ',
	0x8E: 'Ž',
	0x91: '‘',
	0x92: '’',
	0x93: '“',
	0x94: '”',
	0x95: '•',
	0x96: '–',
	0x97: '—',
	0x98: '˜',
	0x99: '™',
	0x9A: 'š',
	0x9B: '›',
	0x9C: 'œ',
	0x9E: 'ž',
	0x9F: 'Ÿ',
}

func bindingFromModel(model vo.SceneModelVo) vo.SceneBusinessBindingVo {
	EnsureSceneObjectID(&model)
	return vo.SceneBusinessBindingVo{
		SceneName:        model.SceneName,
		ModelId:          model.ModelId,
		SceneObjectId:    model.SceneObjectId,
		BusinessObjectId: model.BusinessObjectId,
		AssetKey:         model.AssetKey,
		IsDefaultBinding: model.IsDefaultBinding,
		URL:              model.URL,
	}
}

func validationIssue(category string, model vo.SceneModelVo, businessType string, message string) vo.SceneBindingValidationIssueVo {
	return vo.SceneBindingValidationIssueVo{
		Category:         category,
		SceneName:        model.SceneName,
		SceneObjectId:    model.SceneObjectId,
		ModelId:          model.ModelId,
		BusinessObjectId: model.BusinessObjectId,
		BusinessType:     businessType,
		Message:          message,
	}
}

func missingDataBinding(obj vo.AgriculturalObjectVo) bool {
	if obj.DataQuality == string(vo.DataQualityMissing) {
		return true
	}
	if obj.Type == string(vo.ObjectTypeSensor) {
		return len(asStringSlice(obj.Metadata["metrics"])) == 0
	}
	if obj.Type == string(vo.ObjectTypeGreenhouse) {
		return false
	}
	return false
}

func asStringSlice(value interface{}) []string {
	switch items := value.(type) {
	case []string:
		return items
	case []interface{}:
		result := make([]string, 0, len(items))
		for _, item := range items {
			if text, ok := item.(string); ok && text != "" {
				result = append(result, text)
			}
		}
		return result
	default:
		return nil
	}
}

func isCoreBindingType(objectType string) bool {
	for _, item := range coreBindingObjectTypes {
		if item == objectType {
			return true
		}
	}
	return false
}

func isCoreAssetKey(assetKey string) bool {
	assetKey = strings.TrimSpace(strings.ToLower(assetKey))
	if assetKey == "" {
		return false
	}
	switch assetKey {
	case "greenhouse", "parcel", "tomato", "plant", "sensor", "device", "irrigation", "camera":
		return true
	default:
		return false
	}
}

var coreBindingObjectTypes = []string{
	string(vo.ObjectTypeGreenhouse),
	string(vo.ObjectTypeParcel),
	string(vo.ObjectTypePlant),
	string(vo.ObjectTypeSensor),
	string(vo.ObjectTypeDevice),
	string(vo.ObjectTypeCamera),
}
