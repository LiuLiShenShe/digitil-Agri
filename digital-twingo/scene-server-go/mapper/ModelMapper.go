package mapper

import (
	"scene-server-go/vo"
)

// ModelMapper provides database operations for the model table.
type ModelMapper struct{}

func NewModelMapper() *ModelMapper {
	return &ModelMapper{}
}

func (m *ModelMapper) DeleteByPrimaryKey(id int) (int, error) {
	result, err := db.Exec("DELETE FROM model WHERE id = ?", id)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *ModelMapper) Insert(record *vo.ModelVo) (int, error) {
	result, err := db.Exec("INSERT INTO model (parentid, name, url, leaf, category, tags, thumbnail) VALUES (?, ?, ?, ?, ?, ?, ?)",
		record.ParentId, record.Name, record.URL, record.Leaf, record.Category, record.Tags, record.Thumbnail)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *ModelMapper) InsertSelective(record *vo.ModelVo) (int, error) {
	return m.Insert(record)
}

func (m *ModelMapper) SelectByPrimaryKey(id int) (*vo.ModelVo, error) {
	var record vo.ModelVo
	err := db.Get(&record, "SELECT id, parentid, name, url, leaf FROM model WHERE id = ?", id)
	if err != nil {
		return nil, err
	}
	return &record, nil
}

func (m *ModelMapper) SelectAll() ([]vo.ModelVo, error) {
	var list []vo.ModelVo
	err := db.Select(&list, "SELECT id, parentid, name, url, leaf, category, tags, thumbnail FROM model")
	return list, err
}

func (m *ModelMapper) UpdateByPrimaryKeySelective(record *vo.ModelVo) (int, error) {
	result, err := db.Exec("UPDATE model SET parentid = ?, name = ?, url = ?, leaf = ?, category = ?, tags = ?, thumbnail = ? WHERE id = ?",
		record.ParentId, record.Name, record.URL, record.Leaf, record.Category, record.Tags, record.Thumbnail, record.Id)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *ModelMapper) UpdateByPrimaryKey(record *vo.ModelVo) (int, error) {
	return m.UpdateByPrimaryKeySelective(record)
}

// BatchImportModels scans a directory recursively, imports .glb files.
// The directory name is used as category tag, filename (without ext) as model name.
func BatchImportModels(rootDir string) (int, error) {
	return batchImportModels(rootDir, rootDir, db)
}
