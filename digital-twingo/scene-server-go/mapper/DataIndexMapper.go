package mapper

import (
	"scene-server-go/vo"
)

// DataIndexMapper provides database operations for the dataindex table.
type DataIndexMapper struct{}

func NewDataIndexMapper() *DataIndexMapper {
	return &DataIndexMapper{}
}

func (m *DataIndexMapper) DeleteByPrimaryKey(dataId string) (int, error) {
	result, err := db.Exec("DELETE FROM dataindex WHERE dataId = ?", dataId)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *DataIndexMapper) Insert(record *vo.DataIndexVo) (int, error) {
	result, err := db.Exec("INSERT INTO dataindex (category, name) VALUES (?, ?)", record.Category, record.Name)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *DataIndexMapper) InsertSelective(record *vo.DataIndexVo) (int, error) {
	return m.Insert(record)
}

func (m *DataIndexMapper) SelectByPrimaryKey(dataId string) (*vo.DataIndexVo, error) {
	var record vo.DataIndexVo
	err := db.Get(&record, "SELECT dataId, category, name FROM dataindex WHERE dataId = ?", dataId)
	if err != nil {
		return nil, err
	}
	return &record, nil
}

func (m *DataIndexMapper) UpdateByPrimaryKeySelective(record *vo.DataIndexVo) (int, error) {
	result, err := db.Exec("UPDATE dataindex SET category = ?, name = ? WHERE dataId = ?",
		record.Category, record.Name, record.DataId)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *DataIndexMapper) UpdateByPrimaryKey(record *vo.DataIndexVo) (int, error) {
	return m.UpdateByPrimaryKeySelective(record)
}
