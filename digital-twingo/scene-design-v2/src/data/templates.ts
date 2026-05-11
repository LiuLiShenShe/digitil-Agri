/**
 * 场景模板定义 — 预设场景模板配置
 */
import type { TerrainOptions } from '@/lib/terrain'

export interface SceneTemplateModel {
  url: string
  offset: { x: number; y: number; z: number }
  scale: number
  angle: number
}

export interface SceneTemplate {
  id: string
  name: string
  category: string
  description: string
  thumbnail?: string
  config: {
    sceneName: string
    ambientLight: { color: string; intensity: number }
    directionalLight: { color: string; intensity: number; pos: { x: number; y: number; z: number } }
    groundPane: { color: string; width: number; height: number }
    grid: { size: number; division: number }
    terrain?: TerrainOptions
    models: SceneTemplateModel[]
  }
}

export const sceneTemplates: SceneTemplate[] = [
  // ========== 模板 1: 标准温室 ==========
  {
    id: 'template_greenhouse',
    name: '标准温室大棚',
    category: 'greenhouse',
    description: '预制标准玻璃温室场景，包含 2 个大棚、灌溉设备与传感器',
    config: {
      sceneName: '标准温室大棚',
      ambientLight: { color: '#ffffff', intensity: 0.7 },
      directionalLight: { color: '#ffeebb', intensity: 1.0, pos: { x: 200, y: 400, z: 300 } },
      groundPane: { color: '#88aa66', width: 800, height: 800 },
      grid: { size: 800, division: 20 },
      terrain: { width: 800, depth: 800, segments: 64, heightScale: 20, colorLow: '#556633', colorHigh: '#99bb55' },
      models: [
        { url: '/models/greenhouse.glb', offset: { x: -80, y: 0, z: 0 }, scale: 1, angle: 0 },
        { url: '/models/greenhouse.glb', offset: { x: 80, y: 0, z: 0 }, scale: 1, angle: 0 },
        { url: '/models/sensor.glb', offset: { x: -80, y: 0, z: 50 }, scale: 0.3, angle: 0 },
        { url: '/models/sensor.glb', offset: { x: 80, y: 0, z: 50 }, scale: 0.3, angle: 0 },
        { url: '/models/irrigation.glb', offset: { x: 0, y: 0, z: 30 }, scale: 0.8, angle: 90 }
      ]
    }
  },

  // ========== 模板 2: 示范田 ==========
  {
    id: 'template_demo_field',
    name: '智慧示范田',
    category: 'farmland',
    description: '标准示范田场景，包含作物种植区、气象站和无人机巡检',
    config: {
      sceneName: '智慧示范田',
      ambientLight: { color: '#ffffff', intensity: 0.8 },
      directionalLight: { color: '#ffffff', intensity: 1.2, pos: { x: 100, y: 500, z: 200 } },
      groundPane: { color: '#887744', width: 1000, height: 1000 },
      grid: { size: 1000, division: 25 },
      terrain: { width: 1000, depth: 1000, segments: 128, heightScale: 30, colorLow: '#776633', colorHigh: '#aacc66' },
      models: [
        { url: '/models/wheat.glb', offset: { x: -120, y: 0, z: -120 }, scale: 0.5, angle: 0 },
        { url: '/models/wheat.glb', offset: { x: 0, y: 0, z: -120 }, scale: 0.5, angle: 0 },
        { url: '/models/wheat.glb', offset: { x: 120, y: 0, z: -120 }, scale: 0.5, angle: 0 },
        { url: '/models/corn.glb', offset: { x: -120, y: 0, z: 120 }, scale: 0.4, angle: 0 },
        { url: '/models/corn.glb', offset: { x: 0, y: 0, z: 120 }, scale: 0.4, angle: 0 },
        { url: '/models/corn.glb', offset: { x: 120, y: 0, z: 120 }, scale: 0.4, angle: 0 },
        { url: '/models/weather_station.glb', offset: { x: 0, y: 0, z: 0 }, scale: 0.6, angle: 0 },
        { url: '/models/drone.glb', offset: { x: 50, y: 40, z: -50 }, scale: 0.3, angle: 45 }
      ]
    }
  },

  // ========== 模板 3: 综合园区 ==========
  {
    id: 'template_park',
    name: '综合农业园区',
    category: 'park',
    description: '完整的智慧农业园区，包含管理楼、仓库、温室、农田、灌溉系统',
    config: {
      sceneName: '综合农业园区',
      ambientLight: { color: '#ffffff', intensity: 0.6 },
      directionalLight: { color: '#ffeedd', intensity: 1.0, pos: { x: 300, y: 600, z: 400 } },
      groundPane: { color: '#889966', width: 1500, height: 1500 },
      grid: { size: 1500, division: 30 },
      terrain: { width: 1500, depth: 1500, segments: 128, heightScale: 40, colorLow: '#556644', colorHigh: '#99bb77' },
      models: [
        { url: '/models/building_admin.glb', offset: { x: -300, y: 0, z: -300 }, scale: 1, angle: 180 },
        { url: '/models/warehouse.glb', offset: { x: -200, y: 0, z: -300 }, scale: 0.9, angle: 180 },
        { url: '/models/greenhouse.glb', offset: { x: 300, y: 0, z: -200 }, scale: 1, angle: 0 },
        { url: '/models/greenhouse.glb', offset: { x: 300, y: 0, z: 0 }, scale: 1, angle: 0 },
        { url: '/models/greenhouse.glb', offset: { x: 300, y: 0, z: 200 }, scale: 1, angle: 0 },
        { url: '/models/wheat.glb', offset: { x: -100, y: 0, z: 200 }, scale: 0.5, angle: 0 },
        { url: '/models/corn.glb', offset: { x: 100, y: 0, z: 200 }, scale: 0.5, angle: 0 },
        { url: '/models/tractor.glb', offset: { x: 0, y: 0, z: 0 }, scale: 0.7, angle: 90 },
        { url: '/models/irrigation.glb', offset: { x: -100, y: 0, z: -100 }, scale: 0.6, angle: 0 },
        { url: '/models/water_tower.glb', offset: { x: 200, y: 0, z: -300 }, scale: 0.8, angle: 0 },
        { url: '/models/camera_pole.glb', offset: { x: 0, y: 0, z: -200 }, scale: 0.4, angle: 0 },
        { url: '/models/camera_pole.glb', offset: { x: 0, y: 0, z: 200 }, scale: 0.4, angle: 180 },
        { url: '/models/weather_station.glb', offset: { x: 200, y: 0, z: 300 }, scale: 0.5, angle: 0 }
      ]
    }
  }
]

export function getTemplateById(id: string): SceneTemplate | undefined {
  return sceneTemplates.find(t => t.id === id)
}

export function getTemplatesByCategory(category: string): SceneTemplate[] {
  return sceneTemplates.filter(t => t.category === category)
}
