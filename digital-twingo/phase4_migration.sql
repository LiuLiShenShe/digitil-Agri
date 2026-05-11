-- Phase 4: IoT 与监控接入 — 数据库迁移
-- 执行方式: docker exec gofast-mysql mysql -u root -proot scene < phase4_migration.sql

-- IoT 设备表
CREATE TABLE IF NOT EXISTS `iot_device` (
  `deviceId` varchar(64) NOT NULL,
  `deviceName` varchar(128) DEFAULT '',
  `deviceType` varchar(32) DEFAULT 'sensor',
  `modelId` int DEFAULT NULL,
  `position` json DEFAULT NULL,
  `mqttTopic` varchar(256) DEFAULT '',
  `status` varchar(16) DEFAULT 'offline',
  `lastDataTime` datetime DEFAULT NULL,
  `config` json DEFAULT NULL,
  `createdAt` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`deviceId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- IoT 数据时序表
CREATE TABLE IF NOT EXISTS `iot_data` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `deviceId` varchar(64) NOT NULL,
  `metricKey` varchar(64) NOT NULL,
  `metricValue` double DEFAULT NULL,
  `unit` varchar(16) DEFAULT '',
  `timestamp` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_device_time` (`deviceId`, `timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 告警记录表
CREATE TABLE IF NOT EXISTS `alert_log` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `deviceId` varchar(64) DEFAULT '',
  `alertType` varchar(32) DEFAULT 'threshold',
  `severity` varchar(16) DEFAULT 'warning',
  `message` text,
  `acknowledged` tinyint(1) DEFAULT 0,
  `createdAt` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_device` (`deviceId`),
  INDEX `idx_created` (`createdAt`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
