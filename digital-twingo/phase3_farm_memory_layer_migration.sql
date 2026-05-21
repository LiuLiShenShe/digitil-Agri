-- Phase 3 farm memory layer migration
-- 执行方式: docker exec gofast-mysql mysql -u root -proot scene < phase3_farm_memory_layer_migration.sql

CREATE TABLE IF NOT EXISTS `farm_event_memory` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `eventId` varchar(96) NOT NULL,
  `objectId` varchar(64) NOT NULL,
  `relatedObjectId` varchar(64) DEFAULT '',
  `eventType` varchar(32) NOT NULL,
  `severity` varchar(16) DEFAULT 'info',
  `summary` text,
  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `dataQuality` varchar(16) NOT NULL DEFAULT 'simulated',
  `metadata` json DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_event_id` (`eventId`),
  KEY `idx_object_time` (`objectId`, `timestamp`),
  KEY `idx_related_time` (`relatedObjectId`, `timestamp`),
  KEY `idx_event_type` (`eventType`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `farm_daily_archive` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `objectId` varchar(64) NOT NULL,
  `archiveDate` date NOT NULL,
  `metricSummaries` json DEFAULT NULL,
  `eventCounts` json DEFAULT NULL,
  `dataQuality` varchar(16) NOT NULL DEFAULT 'simulated',
  `createdAt` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_object_date` (`objectId`, `archiveDate`),
  KEY `idx_archive_date` (`archiveDate`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP PROCEDURE IF EXISTS add_phase3_iot_data_metric_index;
DELIMITER //
CREATE PROCEDURE add_phase3_iot_data_metric_index()
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'iot_data'
      AND INDEX_NAME = 'idx_iot_data_device_metric_time'
  ) THEN
    ALTER TABLE `iot_data`
      ADD INDEX `idx_iot_data_device_metric_time` (`deviceId`, `metricKey`, `timestamp`);
  END IF;
END //
DELIMITER ;
CALL add_phase3_iot_data_metric_index();
DROP PROCEDURE add_phase3_iot_data_metric_index;
