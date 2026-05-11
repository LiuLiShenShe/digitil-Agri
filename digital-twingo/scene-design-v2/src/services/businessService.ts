import axios from 'axios'

export interface BusinessOverview {
  updatedAt: string
  parkName: string
  summary: BusinessSummary
  subsystems: BusinessSubsystem[]
}

export interface BusinessSummary {
  systemTotal: number
  demoReadyCount: number
  partialCount: number
  missingCount: number
  warningAlerts: number
  criticalAlerts: number
  unackedAlerts: number
  overallScore: number
  completionRate: number
}

export interface BusinessSubsystem {
  key: string
  name: string
  objective: string
  status: 'normal' | 'warning' | 'critical'
  implementationLevel: 'ready' | 'partial' | 'missing'
  completionRate: number
  primaryDeviceIds: string[]
  metrics: BusinessMetric[]
  workflows: BusinessWorkflow[]
  alerts: BusinessAlert[]
  gaps: string[]
}

export interface BusinessMetric {
  key: string
  label: string
  value: number
  unit: string
  status: 'normal' | 'warning' | 'critical' | 'missing'
}

export interface BusinessWorkflow {
  name: string
  state: 'ready' | 'partial' | 'missing'
  description: string
}

export interface BusinessAlert {
  id: number
  deviceId: string
  severity: 'info' | 'warning' | 'critical'
  alertType: string
  message: string
  acknowledged: boolean
  createdAt: string
}

export async function fetchBusinessOverview(): Promise<BusinessOverview | null> {
  const res = await axios.get('/business/overview')
  if (res.data?.code === 200) {
    return res.data.data as BusinessOverview
  }
  return null
}
