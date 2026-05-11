/**
 *   三维数字孪生设计平台
 *
 *  @brief WebSocket 实时数据服务
 *    Phase 3: 管理WebSocket连接、自动重连、Mock实时数据模拟
 *
 *  @author Sparcle
 *  @version 3.0
 **/

import { useDataVizStore } from '@/stores/dataviz'
import type { SensorDataSet, SensorPoint } from '@/stores/dataviz'

type DataCallback = (sourceId: string, metric: string, point: SensorPoint) => void

const WS_URL = import.meta.env.VITE_DATA_WS_URL as string | undefined

const RECONNECT_BASE_MS = 2000
const RECONNECT_MAX_MS = 30000
const MOCK_INTERVAL_MS = 2000

/** Mock 数据发生器配置 — 不同数据源的基础值和振幅 */
const MOCK_CONFIGS: Record<string, Record<string, { base: number; amp: number }>> = {
  'ds-greenhouse-01': {
    temperature: { base: 26, amp: 3 },
    humidity: { base: 65, amp: 5 },
    soilMoisture: { base: 55, amp: 3 },
    co2: { base: 800, amp: 80 },
    lightIntensity: { base: 40000, amp: 8000 },
    ph: { base: 6.5, amp: 0.2 }
  },
  'ds-solar-01': {
    temperature: { base: 35, amp: 5 },
    lightIntensity: { base: 600, amp: 200 },
    powerOutput: { base: 250, amp: 100 }
  },
  'ds-wind-01': {
    temperature: { base: 28, amp: 3 },
    windSpeed: { base: 8, amp: 4 },
    powerOutput: { base: 300, amp: 150 }
  },
  'ds-field-01': {
    temperature: { base: 22, amp: 3 },
    humidity: { base: 60, amp: 5 },
    soilMoisture: { base: 45, amp: 4 },
    ph: { base: 6.8, amp: 0.2 },
    lightIntensity: { base: 35000, amp: 10000 }
  },
  'ds-irrigation-01': {
    temperature: { base: 20, amp: 2 },
    humidity: { base: 55, amp: 4 },
    soilMoisture: { base: 50, amp: 6 }
  }
}

export class RealtimeDataService {
  private ws: WebSocket | null = null
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private mockTimer: ReturnType<typeof setInterval> | null = null
  private reconnectAttempts = 0
  private subscribedSources = new Set<string>()
  private callbacks: DataCallback[] = []
  private mockPrevValues: Record<string, Record<string, number>> = {}
  private destroyed = false

  /** 连接WebSocket */
  connect(): void {
    if (this.destroyed) return
    const store = useDataVizStore()

    if (!WS_URL) {
      store.setWsConnected(false)
      this.startMockStream()
      return
    }

    // Try real WebSocket
    try {
      this.ws = new WebSocket(WS_URL)
      this.ws.onopen = () => {
        store.setWsConnected(true)
        store.setWsReconnecting(false)
        this.reconnectAttempts = 0
        this.resubscribe()
      }
      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data)
          if (msg.type === 'data' && msg.sourceId && msg.metric && msg.point) {
            this.handleData(msg.sourceId, msg.metric, msg.point)
          }
        } catch { /* ignore parse errors */ }
      }
      this.ws.onclose = () => {
        store.setWsConnected(false)
        if (!this.destroyed) this.scheduleReconnect()
      }
      this.ws.onerror = () => {
        this.ws?.close()
      }
    } catch {
      // WebSocket unavailable — use mock mode
      store.setWsConnected(false)
      this.startMockStream()
    }
  }

  /** 断开WebSocket */
  disconnect(): void {
    this.destroyed = true
    this.stopMockStream()
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.onclose = null
      this.ws.close()
      this.ws = null
    }
    const store = useDataVizStore()
    store.setWsConnected(false)
    store.setWsReconnecting(false)
  }

  /** 订阅数据源 */
  subscribe(sourceId: string): void {
    this.subscribedSources.add(sourceId)
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'subscribe', sourceId }))
    }
    // Start mock for this source
    this.ensureMockForSource(sourceId)
  }

  /** 取消订阅 */
  unsubscribe(sourceId: string): void {
    this.subscribedSources.delete(sourceId)
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'unsubscribe', sourceId }))
    }
  }

  /** 注册数据回调 */
  onData(cb: DataCallback): () => void {
    this.callbacks.push(cb)
    return () => {
      const idx = this.callbacks.indexOf(cb)
      if (idx >= 0) this.callbacks.splice(idx, 1)
    }
  }

  private resubscribe(): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return
    for (const id of this.subscribedSources) {
      this.ws.send(JSON.stringify({ type: 'subscribe', sourceId: id }))
    }
  }

  private handleData(sourceId: string, metric: string, point: SensorPoint): void {
    const store = useDataVizStore()
    store.pushRealtimeData(sourceId, metric, point)
    for (const cb of this.callbacks) {
      cb(sourceId, metric, point)
    }
  }

  private scheduleReconnect(): void {
    if (this.destroyed) return
    const store = useDataVizStore()
    store.setWsReconnecting(true)
    const delay = Math.min(RECONNECT_MAX_MS, RECONNECT_BASE_MS * Math.pow(1.5, this.reconnectAttempts))
    this.reconnectAttempts++
    this.reconnectTimer = setTimeout(() => {
      if (!this.destroyed) this.connect()
    }, delay)
  }

  // ===== Mock Data Engine =====

  private ensureMockForSource(sourceId: string): void {
    if (!this.mockTimer && this.subscribedSources.size > 0) {
      this.startMockStream()
    }
  }

  private startMockStream(): void {
    if (this.mockTimer || this.destroyed) return
    this.mockTimer = setInterval(() => {
      if (this.destroyed) {
        this.stopMockStream()
        return
      }
      // Only generate mock if WS is not connected
      const store = useDataVizStore()
      if (store.wsConnected) return

      for (const sourceId of this.subscribedSources) {
        const cfg = MOCK_CONFIGS[sourceId]
        if (!cfg) continue
        if (!this.mockPrevValues[sourceId]) {
          this.mockPrevValues[sourceId] = {}
        }
        const prev = this.mockPrevValues[sourceId]
        for (const metric of Object.keys(cfg)) {
          const { base, amp } = cfg[metric]
          const pv = prev[metric]
          const walk = pv !== undefined ? (pv - base) * 0.85 : 0
          const random = (Math.random() - 0.5) * 2 * amp
          const value = Math.round((base + walk + random) * 100) / 100
          prev[metric] = value
          const point: SensorPoint = { timestamp: Date.now(), value }
          store.pushRealtimeData(sourceId, metric, point)
          for (const cb of this.callbacks) {
            cb(sourceId, metric, point)
          }
        }
      }
    }, MOCK_INTERVAL_MS)
  }

  private stopMockStream(): void {
    if (this.mockTimer) {
      clearInterval(this.mockTimer)
      this.mockTimer = null
    }
  }
}

/** 全局单例 */
let instance: RealtimeDataService | null = null

export function getRealtimeService(): RealtimeDataService {
  if (!instance) {
    instance = new RealtimeDataService()
  }
  return instance
}

export function disposeRealtimeService(): void {
  if (instance) {
    instance.disconnect()
    instance = null
  }
}
