-- Phase 2: 3D 场景业务绑定 — 数据库迁移
-- 执行方式: docker exec gofast-mysql mysql -u root -proot scene < phase2_scene_business_binding_migration.sql

SET @sql := (
  SELECT IF(COUNT(*) = 0,
    'ALTER TABLE `scenemodel` ADD COLUMN `sceneObjectId` varchar(64) NOT NULL DEFAULT '''' AFTER `dataId`',
    'SELECT 1')
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'scenemodel' AND COLUMN_NAME = 'sceneObjectId'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(COUNT(*) = 0,
    'ALTER TABLE `scenemodel` ADD COLUMN `businessObjectId` varchar(64) NOT NULL DEFAULT '''' AFTER `sceneObjectId`',
    'SELECT 1')
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'scenemodel' AND COLUMN_NAME = 'businessObjectId'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(COUNT(*) = 0,
    'ALTER TABLE `scenemodel` ADD COLUMN `assetKey` varchar(64) NOT NULL DEFAULT '''' AFTER `businessObjectId`',
    'SELECT 1')
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'scenemodel' AND COLUMN_NAME = 'assetKey'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(COUNT(*) = 0,
    'ALTER TABLE `scenemodel` ADD COLUMN `isDefaultBinding` tinyint(1) NOT NULL DEFAULT 0 AFTER `assetKey`',
    'SELECT 1')
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'scenemodel' AND COLUMN_NAME = 'isDefaultBinding'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(COUNT(*) = 0,
    'CREATE INDEX `idx_scene_object` ON `scenemodel` (`sceneName`, `sceneObjectId`)',
    'SELECT 1')
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'scenemodel' AND INDEX_NAME = 'idx_scene_object'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @sql := (
  SELECT IF(COUNT(*) = 0,
    'CREATE INDEX `idx_business_object` ON `scenemodel` (`sceneName`, `businessObjectId`)',
    'SELECT 1')
  FROM INFORMATION_SCHEMA.STATISTICS
  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'scenemodel' AND INDEX_NAME = 'idx_business_object'
);
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

UPDATE `scenemodel`
SET `sceneObjectId` = CONCAT('legacy-', MD5(CONCAT(`sceneName`, ':', `modelId`)))
WHERE `sceneObjectId` = '';

INSERT INTO `sceneinfo` VALUES (
  '番茄温室 MVP',
  '{"texturePath":"/textures/","imgs":["posx.jpg","negx.jpg","posy.jpg","negy.jpg","posz.jpg","negz.jpg"]}',
  '{"color":"#ffffff","intensity":0.72}',
  '{"color":"#ffffff","intensity":0.9,"pos":{"x":120,"y":360,"z":180}}',
  '{}',
  '{"size":400,"division":20,"color1":"#4da3ff","color2":"#314155"}',
  '{"color":"#385a3c","turnOff":false,"texture":"/textures/grass.jpg"}'
) ON DUPLICATE KEY UPDATE `sceneName` = VALUES(`sceneName`);

INSERT INTO `scenemodel`
  (`sceneName`, `modelId`, `url`, `scale`, `offsetX`, `offsetY`, `offsetZ`, `angle`, `dataId`, `sceneObjectId`, `businessObjectId`, `assetKey`, `isDefaultBinding`)
VALUES
  ('番茄温室 MVP', 0, '/scene-assets/models/Silo_House.glb', 0.9, 0, 0, 0, 0, '', 'scene-gh-tomato-001', 'gh-tomato-001', 'greenhouse', 1),
  ('番茄温室 MVP', 1, '/scene-assets/models/Grass.glb', 1.0, -6, 0, 0, 0, '', 'scene-parcel-tomato-a', 'parcel-tomato-a', 'parcel', 1),
  ('番茄温室 MVP', 2, '/scene-assets/models/Tomato_Crop.glb', 0.8, -10.5, 0, -2, 0, '', 'scene-plant-tomato-001', 'plant-tomato-001', 'tomato', 1),
  ('番茄温室 MVP', 3, '/scene-assets/models/TowerWindmill.glb', 0.7, 0, 0, 8, 0, '', 'scene-sensor-greenhouse-001', 'sensor-greenhouse-001', 'sensor', 1),
  ('番茄温室 MVP', 4, '/scene-assets/models/Well.glb', 0.8, 8, 0, 3, 0, '', 'scene-device-irrigation-001', 'device-irrigation-001', 'irrigation', 1),
  ('番茄温室 MVP', 5, '/scene-assets/models/Windmill.glb', 0.5, 0, 0, -8, 0, '', 'scene-camera-greenhouse-001', 'camera-greenhouse-001', 'camera', 1)
ON DUPLICATE KEY UPDATE
  `url` = VALUES(`url`),
  `scale` = VALUES(`scale`),
  `offsetX` = VALUES(`offsetX`),
  `offsetY` = VALUES(`offsetY`),
  `offsetZ` = VALUES(`offsetZ`),
  `angle` = VALUES(`angle`),
  `sceneObjectId` = VALUES(`sceneObjectId`),
  `businessObjectId` = VALUES(`businessObjectId`),
  `assetKey` = VALUES(`assetKey`),
  `isDefaultBinding` = VALUES(`isDefaultBinding`);
