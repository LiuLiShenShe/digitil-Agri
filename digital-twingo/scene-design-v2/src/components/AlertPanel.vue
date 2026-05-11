<!--
 *   三维数字孪生设计平台
 *    告警面板 — Phase 4
 *    显示阈值告警、设备离线告警，支持确认
 *
 *  @author Sparcle
 *  @version 4.0
 -->

<template>
  <transition name="viz-slide">
    <div class="alert-panel glass-panel" v-show="dialogStore.alertPanel">
      <div class="panel-head">
        <div class="panel-head-left">
          <span class="panel-dot" :class="{ critical: alertStore.criticalCount > 0 }"></span>
          <span class="panel-title">告警中心</span>
          <span class="alert-badge critical" v-if="alertStore.criticalCount > 0">
            {{ alertStore.criticalCount }} 严重
          </span>
          <span class="alert-badge warning" v-if="alertStore.unackedCount > 0">
            {{ alertStore.unackedCount }} 未确认
          </span>
        </div>
        <div class="panel-head-right">
          <el-button size="small" plain @click="alertStore.acknowledgeAll(); acknowledgeAllServer()" v-if="alertStore.unackedCount > 0">
            全部确认
          </el-button>
          <el-button type="danger" :icon="Close" circle size="small" plain @click="dialogStore.showAlertPanel(false)" />
        </div>
      </div>

      <!-- 告警列表 -->
      <div class="alert-list" v-loading="alertStore.loading">
        <div
          v-for="alert in alertStore.recentAlerts"
          :key="alert.id"
          :class="['alert-card', alert.severity, { acknowledged: alert.acknowledged }]"
        >
          <div class="alert-severity-bar" :class="alert.severity"></div>
          <div class="alert-body">
            <div class="alert-meta">
              <span class="alert-type">{{ typeLabels[alert.alertType] || alert.alertType }}</span>
              <span class="alert-device">{{ alert.deviceId }}</span>
              <span class="alert-time">{{ formatTime(alert.createdAt) }}</span>
            </div>
            <div class="alert-msg">{{ alert.message }}</div>
          </div>
          <button
            v-if="!alert.acknowledged"
            class="ack-btn"
            @click="ackAlert(alert.id)"
            title="确认告警"
          >
            确认
          </button>
          <span v-else class="ack-done">✓</span>
        </div>

        <div v-if="alertStore.alerts.length === 0" class="empty-hint">
          暂无告警记录
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { Close } from '@element-plus/icons-vue'
import { useDialogStore } from '@/stores/dialog'
import { useAlertStore } from '@/stores/alert'
import { fetchAlerts, acknowledgeAlert } from '@/services/iotService'

const dialogStore = useDialogStore()
const alertStore = useAlertStore()

const typeLabels: Record<string, string> = {
  threshold: '阈值告警',
  offline: '设备离线',
  anomaly: '异常检测'
}

function formatTime(ts: string): string {
  const d = new Date(ts)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

async function ackAlert(alertId: number) {
  await acknowledgeAlert(alertId)
}

async function acknowledgeAllServer() {
  for (const a of alertStore.recentAlerts) {
    if (!a.acknowledged) {
      await acknowledgeAlert(a.id)
    }
  }
}
</script>

<style scoped>
.alert-panel {
  position: fixed;
  right: 720px;
  top: 60px;
  width: 360px;
  max-height: calc(100vh - 80px);
  overflow-y: auto;
  z-index: 101;
  background: rgba(7, 11, 24, 0.92);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 68, 68, 0.2);
  border-radius: 12px;
  padding: 0;
  color: #e8ecf1;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.panel-head-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-dot {
  width: 8px;
  height: 8px;
  background: #ffaa00;
  border-radius: 50%;
  box-shadow: 0 0 6px #ffaa00;
}

.panel-dot.critical {
  background: #ff4444;
  box-shadow: 0 0 8px #ff4444;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  50% { transform: scale(1.5); opacity: 0.5; }
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
}

.alert-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 6px;
}

.alert-badge.critical {
  background: rgba(255, 68, 68, 0.2);
  color: #ff6666;
}

.alert-badge.warning {
  background: rgba(255, 170, 0, 0.2);
  color: #ffaa00;
}

.panel-head-right {
  display: flex;
  gap: 4px;
  align-items: center;
}

.alert-list {
  padding: 8px;
}

.alert-card {
  display: flex;
  margin: 4px 0;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.04);
  transition: background 0.2s;
}

.alert-card:hover {
  background: rgba(255, 255, 255, 0.04);
}

.alert-card.acknowledged {
  opacity: 0.5;
}

.alert-severity-bar {
  width: 4px;
  flex-shrink: 0;
}

.alert-severity-bar.info { background: #4488cc; }
.alert-severity-bar.warning { background: #ffaa00; }
.alert-severity-bar.critical { background: #ff4444; }

.alert-body {
  flex: 1;
  padding: 10px 12px;
  min-width: 0;
}

.alert-meta {
  display: flex;
  gap: 8px;
  font-size: 10px;
  color: #778;
  margin-bottom: 4px;
}

.alert-type {
  color: #00d4ff;
}

.alert-msg {
  font-size: 12px;
  color: #ccd;
}

.ack-btn {
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid rgba(0, 212, 255, 0.2);
  color: #00d4ff;
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 6px;
  cursor: pointer;
  margin: 8px;
  flex-shrink: 0;
  align-self: center;
}

.ack-btn:hover {
  background: rgba(0, 212, 255, 0.2);
}

.ack-done {
  padding: 8px 12px;
  color: #22dd66;
  font-size: 14px;
  flex-shrink: 0;
  align-self: center;
}

.empty-hint {
  text-align: center;
  color: #556;
  padding: 40px 0;
  font-size: 12px;
}
</style>
