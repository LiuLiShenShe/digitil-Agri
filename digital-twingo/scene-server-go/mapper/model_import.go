package mapper

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/jmoiron/sqlx"
)

// categoryMap maps directory names to category IDs and parent categories.
var categoryMap = map[string]struct {
	CategoryID int
	Category   string
}{
	"terrain":     {1001, "terrain"},
	"building":    {2001, "building"},
	"greenhouse":  {3001, "greenhouse"},
	"irrigation":  {4001, "irrigation"},
	"machinery":   {5001, "machinery"},
	"plant":       {6001, "plant"},
	"iot":         {7001, "iot"},
	"decoration":  {8001, "decoration"},
}

func batchImportModels(rootDir, currentDir string, db *sqlx.DB) (int, error) {
	count := 0
	entries, err := os.ReadDir(currentDir)
	if err != nil {
		return 0, err
	}

	for _, entry := range entries {
		fullPath := filepath.Join(currentDir, entry.Name())

		if entry.IsDir() {
			n, err := batchImportModels(rootDir, fullPath, db)
			if err != nil {
				return count, err
			}
			count += n
			continue
		}

		if !strings.HasSuffix(strings.ToLower(entry.Name()), ".glb") {
			continue
		}

		// Determine category from parent directory
		parentDir := filepath.Base(filepath.Dir(fullPath))
		catInfo, ok := categoryMap[parentDir]
		if !ok {
			// Try grandparent
			grandparent := filepath.Base(filepath.Dir(filepath.Dir(fullPath)))
			catInfo, ok = categoryMap[grandparent]
			if !ok {
				fmt.Printf("Skipping %s: unknown category for dir %s\n", entry.Name(), parentDir)
				continue
			}
		}

		// Generate model ID (use a simple increment from DB)
		var maxID int
		db.Get(&maxID, "SELECT COALESCE(MAX(id), 0) FROM model")
		modelID := maxID + 1 + count

		modelName := strings.TrimSuffix(entry.Name(), filepath.Ext(entry.Name()))

		// Move file to models directory
		destDir := "scene-assets/models"
		os.MkdirAll(destDir, 0755)
		destPath := filepath.Join(destDir, entry.Name())
		if err := os.Rename(fullPath, destPath); err != nil {
			// If rename fails (cross-device), copy instead
			data, readErr := os.ReadFile(fullPath)
			if readErr != nil {
				fmt.Printf("Failed to read %s: %v\n", entry.Name(), readErr)
				continue
			}
			if writeErr := os.WriteFile(destPath, data, 0644); writeErr != nil {
				fmt.Printf("Failed to write %s: %v\n", entry.Name(), writeErr)
				continue
			}
		}

		url := "/scene-assets/models/" + entry.Name()

		_, err = db.Exec(
			`INSERT INTO model (id, parentid, name, url, leaf, category, tags, thumbnail)
			 VALUES (?, ?, ?, ?, 1, ?, ?, ?)`,
			modelID, catInfo.CategoryID, modelName, url, catInfo.Category, "", "",
		)
		if err != nil {
			fmt.Printf("DB insert failed for %s: %v\n", entry.Name(), err)
			continue
		}

		fmt.Printf("Imported: %s → category=%s id=%d\n", entry.Name(), catInfo.Category, modelID)
		count++
	}

	return count, nil
}
