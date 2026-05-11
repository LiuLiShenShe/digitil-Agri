package mapper

import (
	"scene-server-go/vo"
)

// GdtextureMapper provides database operations for the gdtexture table.
type GdtextureMapper struct{}

func NewGdtextureMapper() *GdtextureMapper {
	return &GdtextureMapper{}
}

func (m *GdtextureMapper) DeleteByPrimaryKey(name string) (int, error) {
	result, err := db.Exec("DELETE FROM gdtexture WHERE `name` = ?", name)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *GdtextureMapper) Insert(record *vo.GdtextureVo) (int, error) {
	result, err := db.Exec("INSERT INTO gdtexture (pic) VALUES (?)", record.Pic)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *GdtextureMapper) InsertSelective(record *vo.GdtextureVo) (int, error) {
	return m.Insert(record)
}

func (m *GdtextureMapper) SelectByPrimaryKey(name string) (*vo.GdtextureVo, error) {
	var record vo.GdtextureVo
	err := db.Get(&record, "SELECT `name`, pic FROM gdtexture WHERE `name` = ?", name)
	if err != nil {
		return nil, err
	}
	return &record, nil
}

func (m *GdtextureMapper) SelectAll() ([]vo.GdtextureVo, error) {
	var list []vo.GdtextureVo
	err := db.Select(&list, "SELECT `name`, pic FROM gdtexture")
	return list, err
}

func (m *GdtextureMapper) UpdateByPrimaryKeySelective(record *vo.GdtextureVo) (int, error) {
	result, err := db.Exec("UPDATE gdtexture SET pic = ? WHERE `name` = ?", record.Pic, record.Name)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *GdtextureMapper) UpdateByPrimaryKey(record *vo.GdtextureVo) (int, error) {
	return m.UpdateByPrimaryKeySelective(record)
}
