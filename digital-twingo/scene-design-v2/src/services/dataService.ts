/**
 *   三维数字孪生设计平台
 *
 *  @brief 数据服务 — HTTP API + Mock数据生成器
 *    Phase 3: 农业IoT传感器数据模拟
 *
 *  @author Sparcle
 *  @version 3.0
 **/

import axios from 'axios'
import type { SensorDataSet, SensorPoint } from '@/stores/dataviz'

/** 生成带噪声的模拟传感器数据 */
function noise(base: number, amplitude: number, prev?: number): number {
  const walk = prev !== undefined ? (prev - base) * 0.7 : 0
  const random = (Math.random() - 0.5) * 2 * amplitude
  return Math.round((base + walk + random) * 100) / 100
}

/** 为指定数据源生成历史数据 */
export function generateHistoricalData(
  sourceId: string,
  durationMs: number = 24 * 60 * 60 * 1000, // 24h
  intervalMs: number = 60 * 1000 // 1 point per minute
): SensorDataSet {
  const now = Date.now()
  const points = Math.floor(durationMs / intervalMs)
  const data: SensorDataSet = {
    temperature: [],
    humidity: [],
    soilMoisture: [],
    co2: [],
    lightIntensity: [],
    powerOutput: [],
    windSpeed: [],
    ph: []
  }

  // Different base values per data source type
  const configs: Record<string, { base: Record<string, number>; amp: Record<string, number> }> = {
    'ds-greenhouse-01': {
      base: { temperature: 26, humidity: 65, soilMoisture: 55, co2: 800, lightIntensity: 40000, ph: 6.5 },
      amp: { temperature: 4, humidity: 10, soilMoisture: 8, co2: 150, lightIntensity: 20000, ph: 0.5 }
    },
    'ds-solar-01': {
      base: { temperature: 35, lightIntensity: 600, powerOutput: 250 },
      amp: { temperature: 10, lightIntensity: 400, powerOutput: 180 }
    },
    'ds-wind-01': {
      base: { temperature: 28, windSpeed: 8, powerOutput: 300 },
      amp: { temperature: 5, windSpeed: 6, powerOutput: 250 }
    },
    'ds-field-01': {
      base: { temperature: 22, humidity: 60, soilMoisture: 45, ph: 6.8, lightIntensity: 35000 },
      amp: { temperature: 6, humidity: 12, soilMoisture: 10, ph: 0.4, lightIntensity: 25000 }
    },
    'ds-irrigation-01': {
      base: { temperature: 20, humidity: 55, soilMoisture: 50 },
      amp: { temperature: 3, humidity: 8, soilMoisture: 15 }
    }
  }

  const cfg = configs[sourceId] || configs['ds-greenhouse-01']
  const prev: Record<string, number> = {}

  for (let i = 0; i < points; i++) {
    const ts = now - durationMs + i * intervalMs
    for (const key of Object.keys(cfg.base)) {
      const b = cfg.base[key]
      const a = cfg.amp[key]
      const val = noise(b, a, prev[key])
      prev[key] = val
      const metricKey = key as keyof SensorDataSet
      if (data[metricKey]) {
        ;(data[metricKey] as SensorPoint[]).push({ timestamp: ts, value: val })
      }
    }
  }

  return data
}

/** 从API获取场景数据 */
export async function fetchSceneData(sceneName: string): Promise<any> {
  try {
    const res = await axios.get('/scene/loadScene', { params: { scene: sceneName } })
    return res.data
  } catch {
    return null
  }
}

/** 获取模型关联的数据 */
export async function fetchModelData(dataId: string): Promise<any> {
  try {
    const res = await axios.get('/datasvr/dataIndex', { params: { dataId } })
    return res.data
  } catch {
    return null
  }
}

/** 获取数据索引列表 */
export async function fetchDataIndexList(): Promise<any[]> {
  try {
    const res = await axios.get('/datasvr/list')
    return res.data?.data || []
  } catch {
    return []
  }
}

/** 日间模式调整器 - 给数据添加昼夜节律 */
export function applyDayNightCycle(data: SensorDataSet, now: number): SensorDataSet {
  const hour = new Date(now).getHours()
  // 0=midnight, 1=full daylight
  const dayFactor = Math.max(0, Math.min(1, Math.sin((hour - 6) * Math.PI / 12)))

  const result: SensorDataSet = { ...data }
  const lightSensitive = ['temperature', 'lightIntensity', 'powerOutput']
  for (const key of lightSensitive) {
    const arr = result[key as keyof SensorDataSet] as SensorPoint[]
    if (arr && arr.length > 0) {
      // Adjust last point by day factor
      const last = arr[arr.length - 1]
      if (last) {
        const base = last.value / (0.3 + 0.7 * dayFactor)
        last.value = Math.round(base * (0.3 + 0.7 * dayFactor) * 100) / 100
      }
    }
  }
  return result
}
