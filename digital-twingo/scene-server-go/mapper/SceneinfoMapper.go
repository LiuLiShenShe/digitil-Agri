package mapper

import (
	"github.com/jmoiron/sqlx"
	"scene-server-go/vo"
)

var db *sqlx.DB

// SetDB sets the global database handle.
func SetDB(database *sqlx.DB) {
	db = database
}

// SceneinfoMapper provides database operations for the sceneinfo table.
type SceneinfoMapper struct{}

func NewSceneinfoMapper() *SceneinfoMapper {
	return &SceneinfoMapper{}
}

func (m *SceneinfoMapper) DeleteByPrimaryKey(sceneName string) (int, error) {
	result, err := db.Exec("DELETE FROM sceneinfo WHERE sceneName = ?", sceneName)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *SceneinfoMapper) Insert(record *vo.SceneinfoVo) (int, error) {
	result, err := db.Exec(`INSERT INTO sceneinfo (sceneName, background, ambientLight, directionalLight, spotLight, grid, groundPane)
		VALUES (?, ?, ?, ?, ?, ?, ?)`,
		record.SceneName, record.Background, record.AmbientLight, record.DirectionalLight,
		record.SpotLight, record.Grid, record.GroundPane)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *SceneinfoMapper) InsertSelective(record *vo.SceneinfoVo) (int, error) {
	return m.Insert(record)
}

// InsertOrUpdate inserts a new record or updates on duplicate key.
func (m *SceneinfoMapper) InsertOrUpdate(record *vo.SceneinfoVo) (int, error) {
	result, err := db.Exec(`INSERT INTO sceneinfo (sceneName, background, ambientLight, directionalLight, spotLight, grid, groundPane)
		VALUES (?, ?, ?, ?, ?, ?, ?)
		ON DUPLICATE KEY UPDATE
			background = VALUES(background),
			ambientLight = VALUES(ambientLight),
			directionalLight = VALUES(directionalLight),
			spotLight = VALUES(spotLight),
			grid = VALUES(grid),
			groundPane = VALUES(groundPane)`,
		record.SceneName, record.Background, record.AmbientLight, record.DirectionalLight,
		record.SpotLight, record.Grid, record.GroundPane)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *SceneinfoMapper) GetSceneList() ([]string, error) {
	var list []string
	err := db.Select(&list, "SELECT sceneName FROM sceneinfo")
	return list, err
}

func (m *SceneinfoMapper) SelectByPrimaryKey(sceneName string) (*vo.SceneinfoVo, error) {
	var record vo.SceneinfoVo
	err := db.Get(&record, `SELECT sceneName, background, ambientLight, directionalLight, spotLight, grid, groundPane
		FROM sceneinfo WHERE sceneName = ?`, sceneName)
	if err != nil {
		return nil, err
	}
	return &record, nil
}

func (m *SceneinfoMapper) UpdateByPrimaryKeySelective(record *vo.SceneinfoVo) (int, error) {
	result, err := db.Exec(`UPDATE sceneinfo SET
		background = COALESCE(NULLIF(?, ''), background),
		ambientLight = COALESCE(NULLIF(?, ''), ambientLight),
		directionalLight = COALESCE(NULLIF(?, ''), directionalLight),
		spotLight = COALESCE(NULLIF(?, ''), spotLight),
		grid = COALESCE(NULLIF(?, ''), grid),
		groundPane = COALESCE(NULLIF(?, ''), groundPane)
		WHERE sceneName = ?`,
		record.Background, record.AmbientLight, record.DirectionalLight,
		record.SpotLight, record.Grid, record.GroundPane, record.SceneName)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *SceneinfoMapper) UpdateByPrimaryKey(record *vo.SceneinfoVo) (int, error) {
	result, err := db.Exec(`UPDATE sceneinfo SET
		sceneName = ?, background = ?, ambientLight = ?, directionalLight = ?, spotLight = ?, grid = ?, groundPane = ?
		WHERE sceneName = ?`,
		record.SceneName, record.Background, record.AmbientLight, record.DirectionalLight,
		record.SpotLight, record.Grid, record.GroundPane, record.SceneName)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}
