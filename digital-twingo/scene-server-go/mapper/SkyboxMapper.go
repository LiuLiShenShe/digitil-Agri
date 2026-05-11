package mapper

import (
	"scene-server-go/vo"
)

// SkyboxMapper provides database operations for the skybox table.
type SkyboxMapper struct{}

func NewSkyboxMapper() *SkyboxMapper {
	return &SkyboxMapper{}
}

func (m *SkyboxMapper) DeleteByPrimaryKey(alias string) (int, error) {
	result, err := db.Exec("DELETE FROM skybox WHERE `alias` = ?", alias)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *SkyboxMapper) Insert(record *vo.SkyboxVo) (int, error) {
	result, err := db.Exec(`INSERT INTO skybox (path, left, right, front, back, top, bottom)
		VALUES (?, ?, ?, ?, ?, ?, ?)`,
		record.Path, record.Left, record.Right, record.Front, record.Back, record.Top, record.Bottom)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *SkyboxMapper) InsertSelective(record *vo.SkyboxVo) (int, error) {
	return m.Insert(record)
}

func (m *SkyboxMapper) SelectByPrimaryKey(alias string) (*vo.SkyboxVo, error) {
	var record vo.SkyboxVo
	err := db.Get(&record, "SELECT `alias`, `path`, `left`, `right`, front, back, `top`, bottom FROM skybox WHERE `alias` = ?", alias)
	if err != nil {
		return nil, err
	}
	return &record, nil
}

func (m *SkyboxMapper) SelectAll() ([]vo.SkyboxVo, error) {
	var list []vo.SkyboxVo
	err := db.Select(&list, "SELECT `alias`, `path`, `left`, `right`, front, back, `top`, bottom FROM skybox")
	return list, err
}

func (m *SkyboxMapper) UpdateByPrimaryKeySelective(record *vo.SkyboxVo) (int, error) {
	result, err := db.Exec(`UPDATE skybox SET
		path = ?, left = ?, right = ?, front = ?, back = ?, top = ?, bottom = ?
		WHERE alias = ?`,
		record.Path, record.Left, record.Right, record.Front, record.Back, record.Top, record.Bottom, record.Alias)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *SkyboxMapper) UpdateByPrimaryKey(record *vo.SkyboxVo) (int, error) {
	return m.UpdateByPrimaryKeySelective(record)
}
