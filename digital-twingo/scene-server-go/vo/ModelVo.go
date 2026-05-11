package vo

// ModelVo maps to the model table (model tree).
type ModelVo struct {
	Id        int     `json:"id" db:"id"`
	ParentId  int     `json:"parentid" db:"parentid"`
	Name      string  `json:"name" db:"name"`
	URL       *string `json:"url" db:"url"`
	Leaf      bool    `json:"leaf" db:"leaf"`
	Category  string  `json:"category" db:"category"`
	Tags      string  `json:"tags" db:"tags"`
	Thumbnail string  `json:"thumbnail" db:"thumbnail"`
}
