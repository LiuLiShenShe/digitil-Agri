package mapper

import (
	"scene-server-go/vo"
)

// SysconfigMapper provides database operations for the sysconfig table.
type SysconfigMapper struct{}

func NewSysconfigMapper() *SysconfigMapper {
	return &SysconfigMapper{}
}

func (m *SysconfigMapper) DeleteByPrimaryKey(key string) (int, error) {
	result, err := db.Exec("DELETE FROM sysconfig WHERE `key` = ?", key)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *SysconfigMapper) Insert(record *vo.SysconfigVo) (int, error) {
	result, err := db.Exec("INSERT INTO sysconfig (`key`, `value`) VALUES (?, ?)", record.Key, record.Value)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *SysconfigMapper) InsertSelective(record *vo.SysconfigVo) (int, error) {
	return m.Insert(record)
}

func (m *SysconfigMapper) SelectByPrimaryKey(key string) (*vo.SysconfigVo, error) {
	var record vo.SysconfigVo
	err := db.Get(&record, "SELECT `key`, `value` FROM sysconfig WHERE `key` = ?", key)
	if err != nil {
		return nil, err
	}
	return &record, nil
}

func (m *SysconfigMapper) UpdateByPrimaryKeySelective(record *vo.SysconfigVo) (int, error) {
	result, err := db.Exec("UPDATE sysconfig SET `value` = ? WHERE `key` = ?", record.Value, record.Key)
	if err != nil {
		return 0, err
	}
	n, _ := result.RowsAffected()
	return int(n), nil
}

func (m *SysconfigMapper) UpdateByPrimaryKey(record *vo.SysconfigVo) (int, error) {
	return m.UpdateByPrimaryKeySelective(record)
}
