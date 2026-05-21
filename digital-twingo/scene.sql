/*
 Navicat Premium Data Transfer

 Source Server         : aa
 Source Server Type    : MySQL
 Source Server Version : 80045
 Source Host           : localhost:3306
 Source Schema         : scene

 Target Server Type    : MySQL
 Target Server Version : 80045
 File Encoding         : 65001

 Date: 06/05/2026 10:14:53
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for dataindex
-- ----------------------------
DROP TABLE IF EXISTS `dataindex`;
CREATE TABLE `dataindex`  (
  `dataId` varchar(16) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `category` varchar(16) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `name` varchar(128) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`dataId`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of dataindex
-- ----------------------------
INSERT INTO `dataindex` VALUES ('c001', 'chemicalInd', '北京榕杉化工科技有限公司');
INSERT INTO `dataindex` VALUES ('p001', 'powerInd', '北京弘喜发电科技有限公司');
INSERT INTO `dataindex` VALUES ('p002', 'powerInd', '北京煜邦电力技术有限公司');

-- ----------------------------
-- Table structure for gdtexture
-- ----------------------------
DROP TABLE IF EXISTS `gdtexture`;
CREATE TABLE `gdtexture`  (
  `name` varchar(64) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `pic` varchar(256) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`name`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of gdtexture
-- ----------------------------
INSERT INTO `gdtexture` VALUES ('大理石', './textures/marble.jpg');
INSERT INTO `gdtexture` VALUES ('混凝土', './textures/concrete.jpg');
INSERT INTO `gdtexture` VALUES ('草地', './textures/grass.jpg');

-- ----------------------------
-- Table structure for model
-- ----------------------------
DROP TABLE IF EXISTS `model`;
CREATE TABLE `model`  (
  `id` int(0) NOT NULL,
  `parentid` int(0) NULL DEFAULT NULL,
  `name` varchar(64) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `url` varchar(256) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `leaf` tinyint(1) NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of model
-- ----------------------------
INSERT INTO `model` VALUES (1, 0, '建筑物', NULL, 0);
INSERT INTO `model` VALUES (2, 0, '发电设备', NULL, 0);
INSERT INTO `model` VALUES (101, 1, '写字楼', NULL, 0);
INSERT INTO `model` VALUES (102, 1, '办公楼', NULL, 0);
INSERT INTO `model` VALUES (103, 1, '厂房', NULL, 0);
INSERT INTO `model` VALUES (104, 1, '住宅', NULL, 0);
INSERT INTO `model` VALUES (201, 2, '风电', NULL, 0);
INSERT INTO `model` VALUES (202, 2, '光伏', NULL, 0);
INSERT INTO `model` VALUES (101001, 101, '三层办公楼', './models/building01.glb', 1);
INSERT INTO `model` VALUES (101002, 101, '灰色二层', './models/building02.glb', 1);
INSERT INTO `model` VALUES (102001, 102, '园顶综合楼', './models/capitol.glb', 1);
INSERT INTO `model` VALUES (103001, 103, '红色平层烟囱', './models/factory.glb', 1);
INSERT INTO `model` VALUES (103002, 103, '煜邦一期厂房', './models/ypfac.glb', 1);
INSERT INTO `model` VALUES (104001, 104, '三层联排别墅', './models/building04.glb', 1);
INSERT INTO `model` VALUES (104002, 104, '塔楼', './models/skyscrapper.glb', 1);
INSERT INTO `model` VALUES (201001, 201, '旋转的风机', './models/wind0.glb', 1);
INSERT INTO `model` VALUES (202001, 202, '光伏板', './models/solar.glb', 1);

-- ----------------------------
-- Table structure for sceneinfo
-- ----------------------------
DROP TABLE IF EXISTS `sceneinfo`;
CREATE TABLE `sceneinfo`  (
  `sceneName` varchar(64) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `background` varchar(512) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `ambientLight` varchar(128) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `directionalLight` varchar(128) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `spotLight` varchar(128) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `grid` varchar(128) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `groundPane` varchar(128) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`sceneName`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sceneinfo
-- ----------------------------
INSERT INTO `sceneinfo` VALUES ('新建场景', '{\"imgs\":[\"posx.jpg\",\"negx.jpg\",\"posy.jpg\",\"negy.jpg\",\"posz.jpg\",\"negz.jpg\"],\"texturePath\":\"/scene/textures/\"}', '{\"color\":\"#ffffff\",\"intensity\":0.6}', '{}', '{}', '', '{}');
INSERT INTO `sceneinfo` VALUES ('煜邦科技园', '{\"texturePath\":\"/textures/\",\"imgs\":[\"posx.jpg\",\"negx.jpg\",\"posy.jpg\",\"negy.jpg\",\"posz.jpg\",\"negz.jpg\"]}', '{\"color\":\"#444444\",\"intensity\":1.2}', '{\"color\":\"#ffffff\",\"intensity\":0.8,\"pos\":{\"x\":20,\"y\":1000,\"z\":200}}', '{\"color\":\"#ffffff\",\"intensity\":0.8,\"angle\":-8,\"hight\":300,\"distance\":500}', '{\"size\":1000,\"division\":10,\"color1\":\"#FF0000\",\"color2\":\"#444444\"}', '{\"color\":\"#88cc88\",\"turnOff\":false,\"texture\":\"/textures/concrete.jpg\"}');
INSERT INTO `sceneinfo` VALUES ('煜邦科技园55', '', '{\"color\":\"#444444\",\"intensity\":1.2}', '{\"color\":\"#ffffff\",\"intensity\":0.8,\"pos\":{\"x\":20,\"y\":500,\"z\":200}}', '{\"angle\":-8,\"color\":\"#ffffff\",\"distance\":500,\"hight\":300,\"intensity\":0.8}', '{\"color1\":\"#FF0000\",\"color2\":\"#444444\",\"division\":10,\"size\":1000}', '');

-- ----------------------------
-- Table structure for scenemodel
-- ----------------------------
DROP TABLE IF EXISTS `scenemodel`;
CREATE TABLE `scenemodel`  (
  `sceneName` varchar(64) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `modelId` int(0) NOT NULL,
  `url` varchar(256) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `scale` double NULL DEFAULT NULL,
  `offsetX` double NULL DEFAULT NULL,
  `offsetY` double NULL DEFAULT NULL,
  `offsetZ` double NULL DEFAULT NULL,
  `angle` int(0) NULL DEFAULT NULL,
  `dataId` varchar(16) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `sceneObjectId` varchar(64) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL DEFAULT '',
  `businessObjectId` varchar(64) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL DEFAULT '',
  `assetKey` varchar(64) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL DEFAULT '',
  `isDefaultBinding` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`sceneName`, `modelId`) USING BTREE,
  KEY `idx_scene_object` (`sceneName`, `sceneObjectId`) USING BTREE,
  KEY `idx_business_object` (`sceneName`, `businessObjectId`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of scenemodel
-- ----------------------------
INSERT INTO `scenemodel` VALUES ('煜邦科技园', 0, './models/factory.glb', 13.914, -147.52921560840915, -5.27, -249.96855821471252, 0, 'p001', 'legacy-yupont-0', '', '', 0);
INSERT INTO `scenemodel` VALUES ('煜邦科技园', 1, './models/building01.glb', 270.42, 230.86249972542015, -0.15010354636238654, -174.33427919824817, 0, 'c001', 'legacy-yupont-1', '', '', 0);
INSERT INTO `scenemodel` VALUES ('煜邦科技园', 2, './models/ypfac.glb', 25.1542, 156.1890044104609, -1.06, 153.23526690639673, 90, 'p002', 'legacy-yupont-2', '', '', 0);
INSERT INTO `scenemodel` VALUES ('煜邦科技园', 3, './models/capitol.glb', 203.47, -47.961000813089896, -0.3827076969435579, -15.429421129378992, 0, 'p005', 'legacy-yupont-3', '', '', 0);
INSERT INTO `scenemodel` VALUES ('煜邦科技园55', 0, './models/factory.glb', 13.914, -147.52921560840915, -5.27, -249.96855821471252, 0, 'p001', 'legacy-yupont55-0', '', '', 0);
INSERT INTO `scenemodel` VALUES ('煜邦科技园55', 1, './models/building01.glb', 270.42, 230.86249972542015, -0.15010354636238654, -174.33427919824817, 0, 'c001', 'legacy-yupont55-1', '', '', 0);
INSERT INTO `scenemodel` VALUES ('煜邦科技园55', 2, './models/ypfac.glb', 10, 489.45804763939316, -1.06, 148.51908246653733, 90, 'p002', 'legacy-yupont55-2', '', '', 0);
INSERT INTO `scenemodel` VALUES ('煜邦科技园55', 3, './models/capitol.glb', 203.47, -47.961000813089896, -0.3827076969435579, -15.429421129378992, 0, 'p005', 'legacy-yupont55-3', '', '', 0);
INSERT INTO `scenemodel` VALUES ('煜邦科技园55', 4, './models/ypfac.glb', 0.83, 0, 0, 0, 0, '', 'legacy-yupont55-4', '', '', 0);
INSERT INTO `scenemodel` VALUES ('煜邦科技园55', 5, './models/ypfac.glb', 0.83, 0, 0, 0, 0, '', 'legacy-yupont55-5', '', '', 0);
INSERT INTO `scenemodel` VALUES ('煜邦科技园55', 6, './models/ypfac.glb', 0.83, 0, 0, 0, 0, '', 'legacy-yupont55-6', '', '', 0);
INSERT INTO `sceneinfo` VALUES ('番茄温室 MVP', '{\"texturePath\":\"/textures/\",\"imgs\":[\"posx.jpg\",\"negx.jpg\",\"posy.jpg\",\"negy.jpg\",\"posz.jpg\",\"negz.jpg\"]}', '{\"color\":\"#ffffff\",\"intensity\":0.72}', '{\"color\":\"#ffffff\",\"intensity\":0.9,\"pos\":{\"x\":120,\"y\":360,\"z\":180}}', '{}', '{\"size\":400,\"division\":20,\"color1\":\"#4da3ff\",\"color2\":\"#314155\"}', '{\"color\":\"#385a3c\",\"turnOff\":false,\"texture\":\"/textures/grass.jpg\"}');
INSERT INTO `scenemodel` VALUES ('番茄温室 MVP', 0, '/scene-assets/models/Silo_House.glb', 0.9, 0, 0, 0, 0, '', 'scene-gh-tomato-001', 'gh-tomato-001', 'greenhouse', 1);
INSERT INTO `scenemodel` VALUES ('番茄温室 MVP', 1, '/scene-assets/models/Grass.glb', 1.0, -6, 0, 0, 0, '', 'scene-parcel-tomato-a', 'parcel-tomato-a', 'parcel', 1);
INSERT INTO `scenemodel` VALUES ('番茄温室 MVP', 2, '/scene-assets/models/Tomato_Crop.glb', 0.8, -10.5, 0, -2, 0, '', 'scene-plant-tomato-001', 'plant-tomato-001', 'tomato', 1);
INSERT INTO `scenemodel` VALUES ('番茄温室 MVP', 3, '/scene-assets/models/TowerWindmill.glb', 0.7, 0, 0, 8, 0, '', 'scene-sensor-greenhouse-001', 'sensor-greenhouse-001', 'sensor', 1);
INSERT INTO `scenemodel` VALUES ('番茄温室 MVP', 4, '/scene-assets/models/Well.glb', 0.8, 8, 0, 3, 0, '', 'scene-device-irrigation-001', 'device-irrigation-001', 'irrigation', 1);
INSERT INTO `scenemodel` VALUES ('番茄温室 MVP', 5, '/scene-assets/models/Windmill.glb', 0.5, 0, 0, -8, 0, '', 'scene-camera-greenhouse-001', 'camera-greenhouse-001', 'camera', 1);

-- ----------------------------
-- Table structure for skybox
-- ----------------------------
DROP TABLE IF EXISTS `skybox`;
CREATE TABLE `skybox`  (
  `alias` varchar(128) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `path` varchar(256) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `left` varchar(128) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `right` varchar(128) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `front` varchar(128) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `back` varchar(128) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `top` varchar(128) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  `bottom` varchar(128) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`alias`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of skybox
-- ----------------------------
INSERT INTO `skybox` VALUES ('乡村黄昏', './textures/', 'r_left.png', 'r_right.png', 'r_front.png', 'r_back.png', 'r_up.png', 'r_down.png');
INSERT INTO `skybox` VALUES ('山间日出', './textures/', 'nn_left.png', 'nn_right.png', 'nn_front.png', 'nn_back.png', 'nn_up.png', 'nn_down.png');
INSERT INTO `skybox` VALUES ('星河夜景', './textures/', 'night3.jpg', 'night1.jpg', 'night2.jpg', 'night4.jpg', 'night5.jpg', 'night6.jpg');
INSERT INTO `skybox` VALUES ('蓝天白云', './textures/', 'negz.jpg', 'posz.jpg', 'posx.jpg', 'negx.jpg', 'posy.jpg', 'negy.jpg');
INSERT INTO `skybox` VALUES ('阴天', './textures/', 'negz_gray.jpg', 'posz_gray.jpg', 'posx_gray.jpg', 'negx_gray.jpg', 'posy_gray.jpg', 'negy_gray.jpg');

-- ----------------------------
-- Table structure for sysconfig
-- ----------------------------
DROP TABLE IF EXISTS `sysconfig`;
CREATE TABLE `sysconfig`  (
  `key` varchar(256) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NOT NULL,
  `value` varchar(256) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`key`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb3 COLLATE = utf8mb3_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of sysconfig
-- ----------------------------
INSERT INTO `sysconfig` VALUES ('defaultScene', '煜邦科技园');

SET FOREIGN_KEY_CHECKS = 1;
