/**
 *   三维数字孪生设计平台
 *
 *  @brief Pinia store — IoT 设备状态管理
 *    Phase 4: IoT设备列表、实时数据、设备-模型绑定
 *
 *  @author Sparcle
 *  @version 4.0
 **/

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface IotDevice {
  deviceId: string
  deviceName: string
  deviceType: 'sensor' | 'camera' | 'controller' | 'weather_station'
  modelId: number | null
  position: any
  mqttTopic: string
  status: 'online' | 'offline' | 'warning' | 'critical'
  lastDataTime: string | null
  config: any
  createdAt: string
}

export interface IotDataPoint {
  id: number
  deviceId: string
  metricKey: string
  metricValue: number
  unit: string
  timestamp: string
}

export interface IotMetricDef {
  key: string
  label: string
  unit: string
  min: number
  max: number
}

export interface SimulatedDevice {
  deviceId: string
  deviceType: string
  metrics: SimulatedMetric[]
}

export interface SimulatedMetric {
  key: string
  unit: string
  base: number
  amp: number
  min: number
  max: number
}

export const useIotStore = defineStore('iot', () => {
  const devices = ref<IotDevice[]>([])
  const selectedDeviceId = ref<string | null>(null)
  const devicesLoading = ref(false)
  const realtimeMetrics = ref<Record<string, Record<string, number>>>({})
  const lastUpdate = ref(0)

  const selectedDevice = computed(() =>
    devices.value.find(d => d.deviceId === selectedDeviceId.value) || null
  )

  const onlineDevices = computed(() =>
    devices.value.filter(d => d.status === 'online')
  )

  const deviceCountByType = computed(() => {
    const counts: Record<string, number> = {}
    for (const d of devices.value) {
      counts[d.deviceType] = (counts[d.deviceType] || 0) + 1
    }
    return counts
  })

  function setDevices(list: IotDevice[]) {
    devices.value = list
  }

  function addDevice(device: IotDevice) {
    devices.value.push(device)
  }

  function updateDevice(deviceId: string, updates: Partial<IotDevice>) {
    const idx = devices.value.findIndex(d => d.deviceId === deviceId)
    if (idx >= 0) {
      Object.assign(devices.value[idx], updates)
    }
  }

  function removeDevice(deviceId: string) {
    const idx = devices.value.findIndex(d => d.deviceId === deviceId)
    if (idx >= 0) {
      devices.value.splice(idx, 1)
    }
    if (selectedDeviceId.value === deviceId) {
      selectedDeviceId.value = null
    }
  }

  function setSelectedDevice(deviceId: string | null) {
    selectedDeviceId.value = deviceId
  }

  function setLoading(loading: boolean) {
    devicesLoading.value = loading
  }

  function updateRealtimeMetrics(deviceId: string, metrics: Record<string, number>) {
    realtimeMetrics.value[deviceId] = { ...(realtimeMetrics.value[deviceId] || {}), ...metrics }
    lastUpdate.value = Date.now()
    updateDevice(deviceId, { status: 'online', lastDataTime: new Date().toISOString() })
  }

  function getDeviceMetrics(deviceId: string): Record<string, number> {
    return realtimeMetrics.value[deviceId] || {}
  }

  function bindModel(deviceId: string, modelId: number) {
    updateDevice(deviceId, { modelId })
  }

  return {
    devices,
    selectedDeviceId,
    selectedDevice,
    devicesLoading,
    realtimeMetrics,
    lastUpdate,
    onlineDevices,
    deviceCountByType,
    setDevices,
    addDevice,
    updateDevice,
    removeDevice,
    setSelectedDevice,
    setLoading,
    updateRealtimeMetrics,
    getDeviceMetrics,
    bindModel
  }
})
