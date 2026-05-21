package service

import (
	"database/sql"
	"encoding/json"
	"scene-server-go/mapper"
	"scene-server-go/vo"
	"strings"
)

// SceneService handles scene-related business logic.
type SceneService struct {
	sceneinfoMapper  *mapper.SceneinfoMapper
	sceneModelMapper *mapper.SceneModelMapper
}

func NewSceneService() *SceneService {
	return &SceneService{
		sceneinfoMapper:  mapper.NewSceneinfoMapper(),
		sceneModelMapper: mapper.NewSceneModelMapper(),
	}
}

func (s *SceneService) SceneList() vo.ResultVo {
	list, err := s.sceneinfoMapper.GetSceneList()
	if err != nil {
		return vo.ResultVo{Code: 999, Data: err.Error()}
	}
	return vo.ResultVo{Code: 200, Data: list}
}

func (s *SceneService) insertOrUpdate(sceneinfoVo *vo.SceneinfoVo) vo.ResultVo {
	result, err := s.sceneinfoMapper.InsertOrUpdate(sceneinfoVo)
	if err != nil {
		return vo.ResultVo{Code: 999, Data: err.Error()}
	}
	if result > 0 {
		return vo.ResultVo{Code: 200}
	}
	return vo.ResultVo{Code: 999}
}

func (s *SceneService) LoadScene(sceneName string) vo.ResultVo {
	sceneName = strings.TrimSpace(sceneName)
	sceneVo, resolvedSceneName, err := s.selectSceneInfoByCompatibleName(sceneName)
	if err != nil {
		return vo.ResultVo{Code: 999, Data: err.Error()}
	}

	rtData := make(map[string]interface{})
	rtData["scene"] = sceneVo.ConvertToLoadObj()

	models, err := s.sceneModelMapper.SelectBySceneName(resolvedSceneName)
	if err != nil {
		return vo.ResultVo{Code: 999, Data: err.Error()}
	}

	loadModels := make([]map[string]interface{}, 0)
	for _, model := range models {
		EnsureSceneObjectID(&model)
		loadModels = append(loadModels, model.ConvertToLoadObj())
	}
	rtData["models"] = loadModels

	return vo.ResultVo{Code: 200, Data: rtData}
}

func (s *SceneService) selectSceneInfoByCompatibleName(sceneName string) (*vo.SceneinfoVo, string, error) {
	var firstErr error
	for _, candidate := range compatibleSceneNames(sceneName) {
		sceneVo, err := s.sceneinfoMapper.SelectByPrimaryKey(candidate)
		if err == nil {
			return sceneVo, candidate, nil
		}
		if firstErr == nil || err != sql.ErrNoRows {
			firstErr = err
		}
	}
	return nil, "", firstErr
}

// SaveScene saves a complete scene with its models.
// sceneData is the raw parsed JSON from the request body.
func (s *SceneService) SaveScene(sceneData map[string]interface{}) vo.ResultVo {
	scene, ok := sceneData["scene"].(map[string]interface{})
	if !ok {
		return vo.ResultVo{Code: 999, Data: "scene data missing"}
	}

	sceneName, ok := scene["sceneName"].(string)
	if !ok || sceneName == "" {
		return vo.ResultVo{Code: 999, Data: "保存场景没有名称！"}
	}

	sceneinfoVo := &vo.SceneinfoVo{
		SceneName:        sceneName,
		Background:       toJSONString(scene["background"]),
		AmbientLight:     toJSONString(scene["ambientLight"]),
		DirectionalLight: toJSONString(scene["directionalLight"]),
		SpotLight:        toJSONString(scene["spotLight"]),
		Grid:             toJSONString(scene["grid"]),
		GroundPane:       toJSONString(scene["groundPane"]),
	}

	result := s.insertOrUpdate(sceneinfoVo)
	if result.Code != 200 {
		return result
	}

	// Parse models array
	modelArray, ok := sceneData["models"].([]interface{})
	if !ok {
		return vo.ResultVo{Code: 200}
	}

	modelList := make([]vo.SceneModelVo, 0)
	for idx, obj := range modelArray {
		jsonObj, ok := obj.(map[string]interface{})
		if !ok {
			continue
		}
		options, _ := jsonObj["options"].(map[string]interface{})
		if options == nil {
			continue
		}

		vm := vo.SceneModelVo{}
		vm.SceneName = sceneName
		vm.ModelId = idx
		vm.URL, _ = jsonObj["url"].(string)
		vm.Scale, _ = options["scale"].(float64)
		vm.Angle, _ = toInt(options["angle"])

		if dataId, ok := options["dataId"].(string); ok {
			vm.DataId = dataId
		}
		if sceneObjectId, ok := options["sceneObjectId"].(string); ok {
			vm.SceneObjectId = sceneObjectId
		}
		if vm.SceneObjectId == "" {
			vm.SceneObjectId = FallbackSceneObjectID(sceneName, idx)
		}
		if businessObjectId, ok := options["businessObjectId"].(string); ok {
			vm.BusinessObjectId = businessObjectId
		}
		if assetKey, ok := options["assetKey"].(string); ok {
			vm.AssetKey = assetKey
		}
		if isDefaultBinding, ok := options["isDefaultBinding"].(bool); ok {
			vm.IsDefaultBinding = isDefaultBinding
		}

		if offset, ok := options["offset"].(map[string]interface{}); ok {
			vm.OffsetX, _ = offset["x"].(float64)
			vm.OffsetY, _ = offset["y"].(float64)
			vm.OffsetZ, _ = offset["z"].(float64)
		}

		modelList = append(modelList, vm)
	}

	// Delete existing models for this scene and batch insert
	s.sceneModelMapper.DeleteBySceneName(sceneName)
	s.sceneModelMapper.BatchInsert(modelList)

	return result
}

func toJSONString(v interface{}) string {
	if v == nil {
		return ""
	}
	b, err := json.Marshal(v)
	if err != nil {
		return ""
	}
	return string(b)
}

func toInt(v interface{}) (int, error) {
	switch val := v.(type) {
	case float64:
		return int(val), nil
	case int:
		return val, nil
	case int64:
		return int(val), nil
	case json.Number:
		i, err := val.Int64()
		return int(i), err
	default:
		return 0, nil
	}
}
