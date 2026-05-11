/**
 *   三维数字孪生设计平台
 *
 *  @brief Pinia store — 告警状态管理
 *    Phase 4: 阈值告警、设备离线告警、告警确认
 *
 *  @author Sparcle
 *  @version 4.0
 **/

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface AlertLog {
  id: number
  deviceId: string
  alertType: 'threshold' | 'offline' | 'anomaly'
  severity: 'info' | 'warning' | 'critical'
  message: string
  acknowledged: boolean
  createdAt: string
}

export const useAlertStore = defineStore('alert', () => {
  const alerts = ref<AlertLog[]>([])
  const panelVisible = ref(false)
  const loading = ref(false)
  const newAlertSound = ref(false)

  const unackedCount = computed(() =>
    alerts.value.filter(a => !a.acknowledged).length
  )

  const criticalCount = computed(() =>
    alerts.value.filter(a => !a.acknowledged && a.severity === 'critical').length
  )

  const recentAlerts = computed(() =>
    alerts.value.slice(0, 20)
  )

  const alertsByDevice = computed(() => {
    const map: Record<string, AlertLog[]> = {}
    for (const a of alerts.value) {
      if (!map[a.deviceId]) map[a.deviceId] = []
      map[a.deviceId].push(a)
    }
    return map
  })

  function setAlerts(list: AlertLog[]) {
    alerts.value = list
  }

  function addAlert(alert: AlertLog) {
    alerts.value.unshift(alert)
    if (alerts.value.length > 500) {
      alerts.value.pop()
    }
    if (alert.severity === 'critical') {
      newAlertSound.value = true
      setTimeout(() => { newAlertSound.value = false }, 3000)
    }
  }

  function acknowledgeAlert(alertId: number) {
    const alert = alerts.value.find(a => a.id === alertId)
    if (alert) {
      alert.acknowledged = true
    }
  }

  function acknowledgeAll() {
    for (const a of alerts.value) {
      a.acknowledged = true
    }
  }

  function setPanelVisible(visible: boolean) {
    panelVisible.value = visible
  }

  function togglePanel() {
    panelVisible.value = !panelVisible.value
  }

  function setLoading(l: boolean) {
    loading.value = l
  }

  return {
    alerts,
    panelVisible,
    loading,
    newAlertSound,
    unackedCount,
    criticalCount,
    recentAlerts,
    alertsByDevice,
    setAlerts,
    addAlert,
    acknowledgeAlert,
    acknowledgeAll,
    setPanelVisible,
    togglePanel,
    setLoading
  }
})
