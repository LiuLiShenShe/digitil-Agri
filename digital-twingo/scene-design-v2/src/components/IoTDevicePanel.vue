<!--
 *   三维数字孪生设计平台
 *    物联网设备面板 — Phase 4
 *    显示IoT设备列表、实时数据、设备-模型绑定
 *
 *  @author Sparcle
 *  @version 4.0
 -->

<template>
  <transition name="viz-slide">
    <div
      ref="panelRef"
      class="iot-panel glass-panel"
      :class="{ dragging }"
      :style="panelStyle"
      v-show="dialogStore.iotPanel"
      @pointerdown="bringToFront"
    >
      <div class="panel-head" title="拖动移动面板，双击回到默认位置" @pointerdown="startDrag" @dblclick="resetPosition">
        <div class="panel-head-left">
          <span class="panel-dot"></span>
          <span class="panel-title">IoT 设备管理</span>
          <span class="device-count">{{ iotStore.onlineDevices.length }}/{{ iotStore.devices.length }} 在线</span>
        </div>
        <div class="panel-head-right">
          <el-button :icon="Refresh" circle size="small" plain @click="loadDevices" title="刷新" />
          <el-button type="danger" :icon="Close" circle size="small" plain @click="dialogStore.showIotPanel(false)" />
        </div>
      </div>

      <!-- 设备类型统计 -->
      <div class="type-stats">
        <span class="type-chip" v-for="(count, type) in iotStore.deviceCountByType" :key="type">
          <span class="chip-icon" :class="type">{{ typeIcons[type] || '📡' }}</span>
          {{ typeLabels[type] || type }}: {{ count }}
        </span>
      </div>

      <!-- 设备列表 -->
      <div class="device-list" v-loading="iotStore.devicesLoading">
        <div
          v-for="device in iotStore.devices"
          :key="device.deviceId"
          :class="['device-card', { selected: iotStore.selectedDeviceId === device.deviceId }]"
          @click="selectDevice(device.deviceId)"
        >
          <div class="device-header">
            <span class="device-status" :class="device.status"></span>
            <span class="device-name">{{ device.deviceName || device.deviceId }}</span>
            <span class="device-type-tag">{{ typeLabels[device.deviceType] || device.deviceType }}</span>
          </div>
          <div class="device-id">ID: {{ device.deviceId }}</div>

          <!-- 实时指标 -->
          <div class="device-metrics-inline" v-if="iotStore.realtimeMetrics[device.deviceId]">
            <span
              v-for="(val, key) in iotStore.realtimeMetrics[device.deviceId]"
              :key="key"
              class="metric-mini"
            >
              {{ key }}: {{ val.toFixed(1) }}
            </span>
          </div>

          <!-- 绑定信息 -->
          <div class="device-bind" v-if="device.modelId">
            <span class="bind-icon">🔗</span> 已绑定模型 #{{ device.modelId }}
          </div>
        </div>

        <div v-if="iotStore.devices.length === 0 && !iotStore.devicesLoading" class="empty-hint">
          暂无设备，启动模拟器后将自动创建设备
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { Refresh, Close } from '@element-plus/icons-vue'
import { useDialogStore } from '@/stores/dialog'
import { useIotStore } from '@/stores/iot'
import { fetchDevices } from '@/services/iotService'
import { useDraggablePanel } from '@/composables/useDraggablePanel'

const dialogStore = useDialogStore()
const iotStore = useIotStore()
const { panelRef, panelStyle, dragging, startDrag, resetPosition, bringToFront } = useDraggablePanel({
  storageKey: 'scene-design:panel:iot',
  initialTop: 60,
  initialRight: 720,
  width: 340,
  zIndex: 710
})

const typeLabels: Record<string, string> = {
  sensor: '传感器',
  camera: '摄像头',
  controller: '控制器',
  weather_station: '气象站'
}

const typeIcons: Record<string, string> = {
  sensor: '🌡️',
  camera: '📹',
  controller: '🎛️',
  weather_station: '🌤️'
}

function selectDevice(deviceId: string) {
  iotStore.setSelectedDevice(deviceId === iotStore.selectedDeviceId ? null : deviceId)
}

async function loadDevices() {
  iotStore.setLoading(true)
  await fetchDevices()
  iotStore.setLoading(false)
}
</script>

<style scoped>
.iot-panel {
  position: fixed;
  width: 340px;
  max-height: calc(100vh - 80px);
  overflow-y: auto;
  background: rgba(7, 11, 24, 0.92);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 212, 255, 0.15);
  border-radius: 12px;
  padding: 0;
  color: #e8ecf1;
}

.iot-panel.dragging {
  cursor: grabbing;
  opacity: 0.96;
}

.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  cursor: grab;
  touch-action: none;
  user-select: none;
}

.iot-panel.dragging .panel-head {
  cursor: grabbing;
}

.panel-head-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
}

.panel-dot {
  width: 8px;
  height: 8px;
  background: #00d4ff;
  border-radius: 50%;
  box-shadow: 0 0 6px #00d4ff;
}

.device-count {
  font-size: 11px;
  color: #668;
  margin-left: 4px;
}

.panel-head-right {
  display: flex;
  gap: 4px;
}

.type-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 10px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.type-chip {
  font-size: 11px;
  color: #aab;
  background: rgba(255, 255, 255, 0.04);
  padding: 3px 8px;
  border-radius: 10px;
}

.chip-icon { margin-right: 2px; }

.device-list {
  padding: 8px;
}

.device-card {
  padding: 10px 12px;
  margin: 4px 0;
  border-radius: 8px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
  background: rgba(255, 255, 255, 0.02);
}

.device-card:hover {
  background: rgba(0, 212, 255, 0.06);
  border-color: rgba(0, 212, 255, 0.15);
}

.device-card.selected {
  background: rgba(0, 212, 255, 0.08);
  border-color: rgba(0, 212, 255, 0.3);
}

.device-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.device-status {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.device-status.online {
  background: #22dd66;
  box-shadow: 0 0 6px #22dd66;
}

.device-status.offline {
  background: #666;
}

.device-status.warning {
  background: #ffaa00;
  box-shadow: 0 0 6px #ffaa00;
}

.device-status.critical {
  background: #ff4444;
  box-shadow: 0 0 6px #ff4444;
  animation: blink 0.5s infinite;
}

@keyframes blink {
  50% { opacity: 0.3; }
}

.device-name {
  font-size: 13px;
  font-weight: 500;
}

.device-type-tag {
  font-size: 10px;
  color: #889;
  background: rgba(255, 255, 255, 0.06);
  padding: 1px 6px;
  border-radius: 6px;
  margin-left: auto;
}

.device-id {
  font-size: 10px;
  color: #556;
  margin: 4px 0 0 16px;
  font-family: monospace;
}

.device-metrics-inline {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin: 6px 0 0 16px;
}

.metric-mini {
  font-size: 10px;
  color: #aab;
  background: rgba(0, 212, 255, 0.06);
  padding: 2px 6px;
  border-radius: 4px;
}

.device-bind {
  margin: 4px 0 0 16px;
  font-size: 11px;
  color: #00d4ff;
}

.empty-hint {
  text-align: center;
  color: #556;
  font-size: 12px;
  padding: 40px 0;
}
</style>
