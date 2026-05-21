package mapper

import (
	"scene-server-go/vo"
)

// SceneModelMapper provides database operations for the scenemodel table.
type SceneModelMapper struct{}

func NewSceneModelMapper() *SceneModelMapper {
	return &SceneModelMapper{}
}

func (m *SceneModelMapper) DeleteByPrimaryKey(key *vo.SceneModelVoKey) (int, error) {
	result, err := db.Exec("DELETE FROM scenemodel WHERE sceneName = ? AND modelId = ?", key.SceneName, key.ModelId)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *SceneModelMapper) DeleteBySceneName(sceneName string) (int, error) {
	result, err := db.Exec("DELETE FROM scenemodel WHERE sceneName = ?", sceneName)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *SceneModelMapper) Insert(record *vo.SceneModelVo) (int, error) {
	result, err := db.Exec(`INSERT INTO scenemodel (sceneName, modelId, url, scale, offsetX, offsetY, offsetZ, angle, dataId, sceneObjectId, businessObjectId, assetKey, isDefaultBinding)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		record.SceneName, record.ModelId, record.URL, record.Scale,
		record.OffsetX, record.OffsetY, record.OffsetZ, record.Angle, record.DataId,
		record.SceneObjectId, record.BusinessObjectId, record.AssetKey, record.IsDefaultBinding)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *SceneModelMapper) BatchInsert(modelList []vo.SceneModelVo) (int, error) {
	if len(modelList) == 0 {
		return 0, nil
	}

	query := `INSERT INTO scenemodel (sceneName, modelId, url, scale, offsetX, offsetY, offsetZ, angle, dataId, sceneObjectId, businessObjectId, assetKey, isDefaultBinding) VALUES`
	values := make([]interface{}, 0)

	for i, model := range modelList {
		if i > 0 {
			query += ","
		}
		query += "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
		values = append(values, model.SceneName, model.ModelId, model.URL, model.Scale,
			model.OffsetX, model.OffsetY, model.OffsetZ, model.Angle, model.DataId,
			model.SceneObjectId, model.BusinessObjectId, model.AssetKey, model.IsDefaultBinding)
	}

	result, err := db.Exec(query, values...)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *SceneModelMapper) InsertSelective(record *vo.SceneModelVo) (int, error) {
	return m.Insert(record)
}

func (m *SceneModelMapper) SelectBySceneName(sceneName string) ([]vo.SceneModelVo, error) {
	var models []vo.SceneModelVo
	err := db.Select(&models, `SELECT sceneName, modelId, url, scale, offsetX, offsetY, offsetZ, angle, dataId,
		COALESCE(sceneObjectId, '') AS sceneObjectId,
		COALESCE(businessObjectId, '') AS businessObjectId,
		COALESCE(assetKey, '') AS assetKey,
		COALESCE(isDefaultBinding, 0) AS isDefaultBinding
		FROM scenemodel WHERE sceneName = ?`, sceneName)
	return models, err
}

func (m *SceneModelMapper) ListSceneModels(sceneName string) ([]vo.SceneModelVo, error) {
	return m.SelectBySceneName(sceneName)
}

func (m *SceneModelMapper) SelectByPrimaryKey(key *vo.SceneModelVoKey) (*vo.SceneModelVo, error) {
	var record vo.SceneModelVo
	err := db.Get(&record, `SELECT sceneName, modelId, url, scale, offsetX, offsetY, offsetZ, angle, dataId,
		COALESCE(sceneObjectId, '') AS sceneObjectId,
		COALESCE(businessObjectId, '') AS businessObjectId,
		COALESCE(assetKey, '') AS assetKey,
		COALESCE(isDefaultBinding, 0) AS isDefaultBinding
		FROM scenemodel WHERE sceneName = ? AND modelId = ?`, key.SceneName, key.ModelId)
	if err != nil {
		return nil, err
	}
	return &record, nil
}

func (m *SceneModelMapper) UpdateByPrimaryKeySelective(record *vo.SceneModelVo) (int, error) {
	result, err := db.Exec(`UPDATE scenemodel SET
		url = ?, scale = ?, offsetX = ?, offsetY = ?, offsetZ = ?, angle = ?, dataId = ?,
		sceneObjectId = ?, businessObjectId = ?, assetKey = ?, isDefaultBinding = ?
		WHERE sceneName = ? AND modelId = ?`,
		record.URL, record.Scale, record.OffsetX, record.OffsetY, record.OffsetZ,
		record.Angle, record.DataId, record.SceneObjectId, record.BusinessObjectId,
		record.AssetKey, record.IsDefaultBinding, record.SceneName, record.ModelId)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *SceneModelMapper) UpdateByPrimaryKey(record *vo.SceneModelVo) (int, error) {
	return m.UpdateByPrimaryKeySelective(record)
}

func (m *SceneModelMapper) UpdateSceneModelBinding(sceneName string, modelId int, sceneObjectId string, businessObjectId string, assetKey string, isDefaultBinding bool) (int, error) {
	result, err := db.Exec(`UPDATE scenemodel SET sceneObjectId = ?, businessObjectId = ?, assetKey = ?, isDefaultBinding = ?
		WHERE sceneName = ? AND modelId = ?`,
		sceneObjectId, businessObjectId, assetKey, isDefaultBinding, sceneName, modelId)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *SceneModelMapper) ClearSceneModelBinding(sceneName string, modelId int, sceneObjectId string) (int, error) {
	result, err := db.Exec(`UPDATE scenemodel SET sceneObjectId = ?, businessObjectId = '', isDefaultBinding = 0
		WHERE sceneName = ? AND modelId = ?`,
		sceneObjectId, sceneName, modelId)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}
