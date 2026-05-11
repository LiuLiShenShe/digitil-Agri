/**
 * 监控中心大屏 API 服务
 */

import axios from 'axios'

const BASE = (import.meta.env.VITE_BASEURL as string) || ''

export interface MonitorDashboard {
  updatedAt: string
  overview: MonitorOverview
  keyMetrics: MonitorMetricCard[]
  deviceStatus: MonitorDeviceStatus[]
  energy: MonitorEnergy
  yieldAnalysis: MonitorYield
  environment: MonitorEnvironment
  recentAlerts: MonitorAlert[]
  realtimeMetrics: MonitorRealtimeMetric[]
}

export interface MonitorOverview {
  parkName: string
  deviceTotal: number
  onlineCount: number
  offlineCount: number
  warningCount: number
  criticalCount: number
  onlineRate: number
  unackedAlerts: number
  environmentScore: number
}

export interface MonitorMetricCard {
  key: string
  label: string
  value: number
  unit: string
  delta: number
  status: 'normal' | 'warning' | 'critical'
  updatedAt?: string
}

export interface MonitorDeviceStatus {
  deviceId: string
  deviceName: string
  deviceType: string
  status: 'online' | 'offline' | 'warning' | 'critical'
  lastDataTime: string
  metrics: Record<string, number>
}

export interface MonitorEnergy {
  todayTotal: number
  waterTotal: number
  electricityTotal: number
  gasTotal: number
  bars: MonitorEnergyBar[]
  trend: MonitorTrendPoint[]
}

export interface MonitorEnergyBar {
  name: string
  water: number
  electricity: number
  gas: number
}

export interface MonitorTrendPoint {
  time: string
  value: number
}

export interface MonitorYield {
  total: number
  unit: string
  areas: MonitorYieldArea[]
  heatmap: MonitorYieldHeat[]
}

export interface MonitorYieldArea {
  name: string
  yield: number
  target: number
  rate: number
}

export interface MonitorYieldHeat {
  x: number
  y: number
  value: number
  area: string
}

export interface MonitorEnvironment {
  score: number
  level: string
  summary: string
  items: MonitorMetricCard[]
  hourly: MonitorTrendPoint[]
  recommendations: string[]
}

export interface MonitorAlert {
  id: number
  deviceId: string
  severity: 'info' | 'warning' | 'critical'
  alertType: string
  message: string
  acknowledged: boolean
  createdAt: string
}

export interface MonitorRealtimeMetric {
  deviceId: string
  timestamp: string
  metrics: Record<string, number>
}

export async function fetchMonitorDashboard(): Promise<MonitorDashboard | null> {
  const res = await axios.get(`${BASE}/monitor/dashboard`)
  if (res.data?.code === 200) {
    return res.data.data as MonitorDashboard
  }
  return null
}
