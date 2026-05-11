/**
 *   三维数字孪生设计平台
 *
 *  @brief IoT 设备 API 服务
 *    Phase 4: 设备CRUD、数据查询、告警查询、WebSocket连接
 *
 *  @author Sparcle
 *  @version 4.0
 **/

import axios from 'axios'
import { useIotStore } from '@/stores/iot'
import { useAlertStore } from '@/stores/alert'
import type { IotDevice, IotDataPoint, SimulatedDevice } from '@/stores/iot'
import type { AlertLog } from '@/stores/alert'

let wsConnection: WebSocket | null = null
let wsReconnectTimer: ReturnType<typeof setTimeout> | null = null
let wsReconnectAttempts = 0
const WS_MAX_RECONNECT_MS = 30000
const WS_BASE_RECONNECT_MS = 2000

function defaultWsBase(): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/sceneApi`
}

export async function fetchDevices(): Promise<IotDevice[]> {
  const res = await axios.get('/iot/devices')
  if (res.data.code === 200) {
    useIotStore().setDevices(res.data.data || [])
    return res.data.data
  }
  return []
}

export async function fetchDevice(deviceId: string): Promise<IotDevice | null> {
  const res = await axios.get(`/iot/devices/${deviceId}`)
  if (res.data.code === 200) {
    return res.data.data
  }
  return null
}

export async function createDevice(device: Partial<IotDevice>): Promise<IotDevice | null> {
  const res = await axios.post('/iot/devices', device)
  if (res.data.code === 200) {
    useIotStore().addDevice(res.data.data)
    return res.data.data
  }
  return null
}

export async function updateDevice(deviceId: string, updates: Partial<IotDevice>): Promise<boolean> {
  const res = await axios.put(`/iot/devices/${deviceId}`, updates)
  if (res.data.code === 200) {
    useIotStore().updateDevice(deviceId, updates)
    return true
  }
  return false
}

export async function deleteDevice(deviceId: string): Promise<boolean> {
  const res = await axios.delete(`/iot/devices/${deviceId}`)
  if (res.data.code === 200) {
    useIotStore().removeDevice(deviceId)
    return true
  }
  return false
}

export async function bindDeviceModel(deviceId: string, modelId: number): Promise<boolean> {
  const res = await axios.post(`/iot/devices/${deviceId}/bind/${modelId}`)
  if (res.data.code === 200) {
    useIotStore().bindModel(deviceId, modelId)
    return true
  }
  return false
}

export async function fetchDeviceData(deviceId: string, limit = 100): Promise<IotDataPoint[]> {
  const res = await axios.get(`/iot/devices/${deviceId}/data`, { params: { limit } })
  if (res.data.code === 200) {
    return res.data.data || []
  }
  return []
}

export async function fetchDeviceMetricData(deviceId: string, metricKey: string, limit = 100): Promise<IotDataPoint[]> {
  const res = await axios.get(`/iot/devices/${deviceId}/metrics/${metricKey}`, { params: { limit } })
  if (res.data.code === 200) {
    return res.data.data || []
  }
  return []
}

export async function fetchAlerts(limit = 50): Promise<AlertLog[]> {
  const res = await axios.get('/iot/alerts', { params: { limit } })
  if (res.data.code === 200) {
    useAlertStore().setAlerts(res.data.data || [])
    return res.data.data
  }
  return []
}

export async function fetchUnackedCount(): Promise<number> {
  const res = await axios.get('/iot/alerts/unacked-count')
  if (res.data.code === 200) {
    return res.data.data?.count || 0
  }
  return 0
}

export async function acknowledgeAlert(alertId: number): Promise<boolean> {
  const res = await axios.put(`/iot/alerts/${alertId}/acknowledge`)
  if (res.data.code === 200) {
    useAlertStore().acknowledgeAlert(alertId)
    return true
  }
  return false
}

export async function fetchSimulatorDevices(): Promise<SimulatedDevice[]> {
  const res = await axios.get('/iot/simulator/devices')
  if (res.data.code === 200) {
    return res.data.data || []
  }
  return []
}

export function connectIoTWebSocket(): void {
  const wsUrl = (import.meta.env.VITE_WS_URL as string) || defaultWsBase()
  const fullUrl = `${wsUrl}/iot/ws`

  if (wsConnection && wsConnection.readyState === WebSocket.OPEN) return

  try {
    wsConnection = new WebSocket(fullUrl)
    wsConnection.onopen = () => {
      wsReconnectAttempts = 0
      console.log('IoT WebSocket connected')
    }
    wsConnection.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        if (msg.type === 'iotData') {
          useIotStore().updateRealtimeMetrics(msg.deviceId, msg.metrics)
        } else if (msg.type === 'alert') {
          useAlertStore().addAlert(msg as AlertLog)
        }
      } catch { /* ignore */ }
    }
    wsConnection.onclose = () => {
      scheduleIoTReconnect()
    }
    wsConnection.onerror = () => {
      wsConnection?.close()
    }
  } catch {
    scheduleIoTReconnect()
  }
}

function scheduleIoTReconnect(): void {
  if (wsReconnectTimer) return
  const delay = Math.min(WS_MAX_RECONNECT_MS, WS_BASE_RECONNECT_MS * Math.pow(1.5, wsReconnectAttempts))
  wsReconnectAttempts++
  wsReconnectTimer = setTimeout(() => {
    wsReconnectTimer = null
    connectIoTWebSocket()
  }, delay)
}

export function disconnectIoTWebSocket(): void {
  if (wsReconnectTimer) {
    clearTimeout(wsReconnectTimer)
    wsReconnectTimer = null
  }
  if (wsConnection) {
    wsConnection.onclose = null
    wsConnection.close()
    wsConnection = null
  }
}
