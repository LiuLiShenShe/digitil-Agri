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
	result, err := db.Exec(`INSERT INTO scenemodel (sceneName, modelId, url, scale, offsetX, offsetY, offsetZ, angle, dataId)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		record.SceneName, record.ModelId, record.URL, record.Scale,
		record.OffsetX, record.OffsetY, record.OffsetZ, record.Angle, record.DataId)
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

	query := `INSERT INTO scenemodel (sceneName, modelId, url, scale, offsetX, offsetY, offsetZ, angle, dataId) VALUES`
	values := make([]interface{}, 0)

	for i, model := range modelList {
		if i > 0 {
			query += ","
		}
		query += "(?, ?, ?, ?, ?, ?, ?, ?, ?)"
		values = append(values, model.SceneName, model.ModelId, model.URL, model.Scale,
			model.OffsetX, model.OffsetY, model.OffsetZ, model.Angle, model.DataId)
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
	err := db.Select(&models, `SELECT sceneName, modelId, url, scale, offsetX, offsetY, offsetZ, angle, dataId
		FROM scenemodel WHERE sceneName = ?`, sceneName)
	return models, err
}

func (m *SceneModelMapper) SelectByPrimaryKey(key *vo.SceneModelVoKey) (*vo.SceneModelVo, error) {
	var record vo.SceneModelVo
	err := db.Get(&record, `SELECT sceneName, modelId, url, scale, offsetX, offsetY, offsetZ, angle, dataId
		FROM scenemodel WHERE sceneName = ? AND modelId = ?`, key.SceneName, key.ModelId)
	if err != nil {
		return nil, err
	}
	return &record, nil
}

func (m *SceneModelMapper) UpdateByPrimaryKeySelective(record *vo.SceneModelVo) (int, error) {
	result, err := db.Exec(`UPDATE scenemodel SET
		url = ?, scale = ?, offsetX = ?, offsetY = ?, offsetZ = ?, angle = ?, dataId = ?
		WHERE sceneName = ? AND modelId = ?`,
		record.URL, record.Scale, record.OffsetX, record.OffsetY, record.OffsetZ,
		record.Angle, record.DataId, record.SceneName, record.ModelId)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *SceneModelMapper) UpdateByPrimaryKey(record *vo.SceneModelVo) (int, error) {
	return m.UpdateByPrimaryKeySelective(record)
}

