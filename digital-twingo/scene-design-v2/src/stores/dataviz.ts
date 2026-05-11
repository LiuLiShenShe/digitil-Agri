/**
 *   三维数字孪生设计平台
 *
 *  @brief Pinia store — 数据可视化状态管理
 *    Phase 3: 管理图表类型、数据源绑定、实时数据缓存、WebSocket状态
 *
 *  @author Sparcle
 *  @version 3.0
 **/

import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'

export interface SensorPoint {
  timestamp: number
  value: number
}

export interface SensorDataSet {
  temperature: SensorPoint[]
  humidity: SensorPoint[]
  soilMoisture: SensorPoint[]
  co2: SensorPoint[]
  lightIntensity: SensorPoint[]
  powerOutput: SensorPoint[]
  windSpeed: SensorPoint[]
  ph: SensorPoint[]
}

export interface DataSource {
  id: string
  name: string
  type: 'solar' | 'wind' | 'greenhouse' | 'field' | 'building' | 'irrigation'
  modelId?: string
  metrics: { key: string; label: string; unit: string; min: number; max: number }[]
}

export type ChartType = 'line' | 'gauge' | 'radar' | 'bar3d' | 'heatmap' | 'pie'

export const useDataVizStore = defineStore('dataviz', () => {
  // Panel state
  const panelVisible = ref(false)
  const activeChart = ref<ChartType>('line')
  const activeDataSourceId = ref<string | null>(null)
  const activeMetric = ref('temperature')

  // Time range (milliseconds)
  const timeRange = ref(5 * 60 * 1000) // default 5 min

  // WebSocket state
  const wsConnected = ref(false)
  const wsReconnecting = ref(false)

  // Real-time data cache (keyed by dataSourceId)
  const realtimeData = reactive<Record<string, SensorDataSet>>({})

  // Historical data cache
  const historicalData = reactive<Record<string, SensorDataSet>>({})

  // Last update timestamp
  const lastUpdate = ref(0)

  // Available data sources
  const dataSources = ref<DataSource[]>([
    {
      id: 'ds-greenhouse-01',
      name: '1号温室传感器组',
      type: 'greenhouse',
      metrics: [
        { key: 'temperature', label: '温度', unit: '°C', min: 10, max: 45 },
        { key: 'humidity', label: '湿度', unit: '%', min: 20, max: 100 },
        { key: 'soilMoisture', label: '土壤湿度', unit: '%', min: 0, max: 100 },
        { key: 'co2', label: 'CO₂浓度', unit: 'ppm', min: 300, max: 2000 },
        { key: 'lightIntensity', label: '光照强度', unit: 'lux', min: 0, max: 100000 },
        { key: 'ph', label: '土壤pH', unit: 'pH', min: 4, max: 9 }
      ]
    },
    {
      id: 'ds-solar-01',
      name: '光伏阵列监测',
      type: 'solar',
      metrics: [
        { key: 'powerOutput', label: '发电功率', unit: 'KW', min: 0, max: 500 },
        { key: 'temperature', label: '面板温度', unit: '°C', min: -10, max: 70 },
        { key: 'lightIntensity', label: '辐照度', unit: 'W/m²', min: 0, max: 1200 }
      ]
    },
    {
      id: 'ds-wind-01',
      name: '风力发电机组',
      type: 'wind',
      metrics: [
        { key: 'powerOutput', label: '发电功率', unit: 'KW', min: 0, max: 800 },
        { key: 'windSpeed', label: '风速', unit: 'm/s', min: 0, max: 30 },
        { key: 'temperature', label: '机舱温度', unit: '°C', min: -20, max: 60 }
      ]
    },
    {
      id: 'ds-field-01',
      name: '智慧示范田传感器',
      type: 'field',
      metrics: [
        { key: 'soilMoisture', label: '土壤湿度', unit: '%', min: 0, max: 100 },
        { key: 'temperature', label: '土壤温度', unit: '°C', min: -5, max: 40 },
        { key: 'ph', label: '土壤pH', unit: 'pH', min: 4, max: 9 },
        { key: 'humidity', label: '空气湿度', unit: '%', min: 20, max: 100 },
        { key: 'lightIntensity', label: '光照强度', unit: 'lux', min: 0, max: 100000 }
      ]
    },
    {
      id: 'ds-irrigation-01',
      name: '智能灌溉系统',
      type: 'irrigation',
      metrics: [
        { key: 'soilMoisture', label: '土壤湿度', unit: '%', min: 0, max: 100 },
        { key: 'temperature', label: '水温', unit: '°C', min: 5, max: 35 },
        { key: 'humidity', label: '空气湿度', unit: '%', min: 20, max: 100 }
      ]
    }
  ])

  // Getters
  const activeDataSource = computed(() =>
    dataSources.value.find(ds => ds.id === activeDataSourceId.value) || null
  )

  const activeMetricConfig = computed(() => {
    const ds = activeDataSource.value
    if (!ds) return null
    return ds.metrics.find(m => m.key === activeMetric.value) || ds.metrics[0] || null
  })

  const currentRealtimeData = computed(() => {
    if (!activeDataSourceId.value) return []
    const ds = realtimeData[activeDataSourceId.value]
    if (!ds) return []
    return (ds as any)[activeMetric.value] || []
  })

  // Actions
  function setPanelVisible(visible: boolean) {
    panelVisible.value = visible
  }

  function togglePanel() {
    panelVisible.value = !panelVisible.value
  }

  function setActiveChart(chart: ChartType) {
    activeChart.value = chart
  }

  function setActiveDataSource(id: string | null) {
    activeDataSourceId.value = id
  }

  function setActiveMetric(metric: string) {
    activeMetric.value = metric
  }

  function setTimeRange(range: number) {
    timeRange.value = range
  }

  function setWsConnected(connected: boolean) {
    wsConnected.value = connected
  }

  function setWsReconnecting(reconnecting: boolean) {
    wsReconnecting.value = reconnecting
  }

  function pushRealtimeData(sourceId: string, metric: string, point: SensorPoint) {
    if (!realtimeData[sourceId]) {
      realtimeData[sourceId] = {
        temperature: [], humidity: [], soilMoisture: [], co2: [],
        lightIntensity: [], powerOutput: [], windSpeed: [], ph: []
      }
    }
    const arr = (realtimeData[sourceId] as any)[metric] as SensorPoint[]
    arr.push(point)
    // Keep only data within time range
    const cutoff = Date.now() - timeRange.value
    while (arr.length > 0 && arr[0].timestamp < cutoff) {
      arr.shift()
    }
    // Cap at 500 points to prevent memory issues
    while (arr.length > 500) {
      arr.shift()
    }
    lastUpdate.value = Date.now()
  }

  function setHistoricalData(sourceId: string, data: SensorDataSet) {
    (historicalData as any)[sourceId] = data
  }

  function bindModelToDataSource(modelId: string, sourceId: string) {
    const ds = dataSources.value.find(d => d.id === sourceId)
    if (ds) {
      ds.modelId = modelId
      activeDataSourceId.value = sourceId
    }
  }

  return {
    panelVisible,
    activeChart,
    activeDataSourceId,
    activeMetric,
    timeRange,
    wsConnected,
    wsReconnecting,
    realtimeData,
    historicalData,
    lastUpdate,
    dataSources,
    activeDataSource,
    activeMetricConfig,
    currentRealtimeData,
    setPanelVisible,
    togglePanel,
    setActiveChart,
    setActiveDataSource,
    setActiveMetric,
    setTimeRange,
    setWsConnected,
    setWsReconnecting,
    pushRealtimeData,
    setHistoricalData,
    bindModelToDataSource
  }
})
