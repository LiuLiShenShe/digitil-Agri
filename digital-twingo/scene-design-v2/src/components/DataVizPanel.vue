<!--
 *   三维数字孪生设计平台
 *    数据可视化面板 — Phase 3 核心组件
 *    集成折线图、仪表盘、雷达图、3D柱状图、热力图、饼图
 *
 *  @author Sparcle
 *  @version 3.0
 -->

<template>
  <transition name="viz-slide">
    <div
      ref="panelRef"
      class="dataviz"
      :class="{ dragging }"
      :style="panelStyle"
      v-show="dialogStore.dataVizPanel"
      @pointerdown="bringToFront"
    >
      <!-- 面板头部 -->
      <div class="viz-head" title="拖动移动面板，双击回到默认位置" @pointerdown="startDrag" @dblclick="resetPosition">
        <div class="viz-head-left">
          <span class="viz-dot"></span>
          <span class="viz-title">数据可视化</span>
          <span class="viz-badge" v-if="store.wsConnected" title="实时数据已连接">
            <span class="badge-dot live"></span>实时
          </span>
          <span class="viz-badge" v-else title="模拟数据模式">
            <span class="badge-dot mock"></span>模拟
          </span>
        </div>
        <div class="viz-head-right">
          <el-button :icon="Refresh" circle size="small" plain @click="refreshData" title="刷新数据" />
          <el-button type="danger" :icon="Close" circle size="small" plain @click="dialogStore.showDataVizPanel(false)" />
        </div>
      </div>

      <!-- 数据源选择器 -->
      <div class="viz-selector">
        <el-select
          v-model="store.activeDataSourceId"
          placeholder="选择数据源"
          size="small"
          class="viz-select"
          @change="onSourceChange"
        >
          <el-option
            v-for="ds in store.dataSources"
            :key="ds.id"
            :label="ds.name"
            :value="ds.id"
          >
            <span class="ds-option">
              <span class="ds-icon" :class="ds.type">{{ typeIcons[ds.type] }}</span>
              {{ ds.name }}
            </span>
          </el-option>
        </el-select>
        <el-select
          v-model="store.activeMetric"
          placeholder="选择指标"
          size="small"
          class="viz-select viz-metric"
          v-if="store.activeDataSource"
        >
          <el-option
            v-for="m in store.activeDataSource.metrics"
            :key="m.key"
            :label="`${m.label} (${m.unit})`"
            :value="m.key"
          />
        </el-select>
      </div>

      <!-- 图表类型标签 -->
      <div class="viz-tabs">
        <button
          v-for="tab in chartTabs"
          :key="tab.key"
          :class="['viz-tab', { active: store.activeChart === tab.key }]"
          @click="store.setActiveChart(tab.key)"
          :title="tab.label"
        >
          <span class="tab-icon" v-html="tab.icon"></span>
          <span class="tab-label">{{ tab.label }}</span>
        </button>
      </div>

      <!-- 图表区域 -->
      <div class="viz-content">
        <div class="viz-chart-container" :key="store.activeChart">
          <RealtimeLineChart v-if="store.activeChart === 'line'" />
          <GaugeChart v-else-if="store.activeChart === 'gauge'" />
          <RadarChart v-else-if="store.activeChart === 'radar'" />
          <BarChart3D v-else-if="store.activeChart === 'bar3d'" />
          <HeatmapChart v-else-if="store.activeChart === 'heatmap'" />
          <PieChart v-else-if="store.activeChart === 'pie'" />
        </div>
      </div>

      <!-- 底部状态栏 -->
      <div class="viz-footer">
        <div class="viz-footer-left">
          <span class="footer-metric">{{ store.activeMetricConfig?.label || '--' }}</span>
          <span class="footer-value" :class="statusClass">{{ latestValue }}</span>
          <span class="footer-unit">{{ store.activeMetricConfig?.unit || '' }}</span>
        </div>
        <div class="viz-footer-right">
          <span class="footer-time">{{ lastUpdateText }}</span>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Close, Refresh } from '@element-plus/icons-vue'
import { useDataVizStore } from '@/stores/dataviz'
import { useDialogStore } from '@/stores/dialog'
import { getRealtimeService } from '@/services/websocket'
import { generateHistoricalData } from '@/services/dataService'
import { useDraggablePanel } from '@/composables/useDraggablePanel'

import RealtimeLineChart from '@/components/charts/RealtimeLineChart.vue'
import GaugeChart from '@/components/charts/GaugeChart.vue'
import RadarChart from '@/components/charts/RadarChart.vue'
import BarChart3D from '@/components/charts/BarChart3D.vue'
import HeatmapChart from '@/components/charts/HeatmapChart.vue'
import PieChart from '@/components/charts/PieChart.vue'

const store = useDataVizStore()
const dialogStore = useDialogStore()
const wsService = getRealtimeService()
const { panelRef, panelStyle, dragging, startDrag, resetPosition, bringToFront } = useDraggablePanel({
  storageKey: 'scene-design:panel:dataviz',
  initialTop: 80,
  initialRight: 372,
  width: 420,
  zIndex: 730
})

const typeIcons: Record<string, string> = {
  greenhouse: '🏠',
  solar: '☀️',
  wind: '🌬️',
  field: '🌾',
  building: '🏢',
  irrigation: '💧'
}

const chartTabs = [
  { key: 'line' as const, label: '实时曲线', icon: '<svg width="16" height="16" viewBox="0 0 16 16"><polyline points="1,13 4,7 7,9 10,3 13,6 15,1" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>' },
  { key: 'gauge' as const, label: '仪表盘', icon: '<svg width="16" height="16" viewBox="0 0 16 16"><circle cx="8" cy="10" r="5" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M3 10 A5 5 0 0 1 13 10" fill="none" stroke="currentColor" stroke-width="1.5"/></svg>' },
  { key: 'radar' as const, label: '雷达图', icon: '<svg width="16" height="16" viewBox="0 0 16 16"><polygon points="8,1 14,5 13,12 3,12 2,5" fill="none" stroke="currentColor" stroke-width="1.2"/></svg>' },
  { key: 'bar3d' as const, label: '3D对比', icon: '<svg width="16" height="16" viewBox="0 0 16 16"><rect x="1" y="9" width="3" height="5" fill="currentColor" opacity="0.7"/><rect x="5" y="4" width="3" height="10" fill="currentColor" opacity="0.8"/><rect x="9" y="6" width="3" height="8" fill="currentColor" opacity="0.9"/></svg>' },
  { key: 'heatmap' as const, label: '热力图', icon: '<svg width="16" height="16" viewBox="0 0 16 16"><rect x="1" y="1" width="4" height="4" rx="1" fill="currentColor" opacity="0.4"/><rect x="6" y="1" width="4" height="4" rx="1" fill="currentColor" opacity="0.6"/><rect x="11" y="1" width="4" height="4" rx="1" fill="currentColor" opacity="0.9"/></svg>' },
  { key: 'pie' as const, label: '分布图', icon: '<svg width="16" height="16" viewBox="0 0 16 16"><circle cx="8" cy="8" r="7" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M8 1 A7 7 0 0 1 15 8 L8 8 Z" fill="currentColor" opacity="0.4"/></svg>' }
]

const latestValue = computed(() => {
  const data = store.currentRealtimeData as { value: number }[]
  if (!data || data.length === 0) return '--'
  return data[data.length - 1].value.toFixed(1)
})

const lastUpdateText = computed(() => {
  if (store.lastUpdate === 0) return '等待数据...'
  return '更新于 ' + new Date(store.lastUpdate).toLocaleTimeString('zh-CN')
})

const statusClass = computed(() => {
  const cfg = store.activeMetricConfig
  if (!cfg) return ''
  const val = parseFloat(latestValue.value)
  if (isNaN(val)) return ''
  const range = cfg.max - cfg.min
  const pct = (val - cfg.min) / range
  if (pct > 0.85) return 'critical'
  if (pct > 0.7) return 'warning'
  return 'normal'
})

function onSourceChange(id: string) {
  if (!id) return
  // Subscribe WebSocket
  wsService.subscribe(id)
  // Generate historical data
  const histData = generateHistoricalData(id)
  store.setHistoricalData(id, histData)
}

function refreshData() {
  if (!store.activeDataSourceId) return
  const histData = generateHistoricalData(store.activeDataSourceId)
  store.setHistoricalData(store.activeDataSourceId, histData)
  wsService.subscribe(store.activeDataSourceId)
}

// Auto-select first data source
watch(() => dialogStore.dataVizPanel, (visible) => {
  if (visible && !store.activeDataSourceId) {
    store.setActiveDataSource(store.dataSources[0]?.id || null)
    if (store.activeDataSourceId) {
      wsService.subscribe(store.activeDataSourceId)
      const histData = generateHistoricalData(store.activeDataSourceId)
      store.setHistoricalData(store.activeDataSourceId, histData)
    }
  }
})

onMounted(() => {
  wsService.connect()
})

onUnmounted(() => {
  // Don't disconnect WS — it may be used by other components
})
</script>

<style scoped>
.dataviz {
  display: flex;
  flex-direction: column;
  position: fixed;
  width: 420px;
  max-height: calc(100vh - 100px);
  background: rgba(12, 20, 36, 0.92);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  color: #c8d0da;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), 0 0 1px rgba(0, 212, 255, 0.1);
}

.dataviz.dragging {
  cursor: grabbing;
  opacity: 0.96;
}

.viz-slide-enter-active { transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1); }
.viz-slide-leave-active { transition: all 0.25s cubic-bezier(0.4, 0, 0.6, 1); }
.viz-slide-enter-from { transform: translateX(30px); opacity: 0; }
.viz-slide-leave-to { transform: translateX(30px); opacity: 0; }

/* 头部 */
.viz-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
  cursor: grab;
  touch-action: none;
  user-select: none;
}

.dataviz.dragging .viz-head {
  cursor: grabbing;
}

.viz-head-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.viz-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #00d4ff;
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
}

.viz-title {
  color: #e8ecf1;
  font-size: 15px;
  font-weight: 600;
}

.viz-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #8899aa;
  background: rgba(255, 255, 255, 0.05);
  padding: 2px 8px;
  border-radius: 10px;
}

.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.badge-dot.live {
  background: #00d4ff;
  box-shadow: 0 0 4px rgba(0, 212, 255, 0.6);
  animation: pulse-dot 2s ease-in-out infinite;
}

.badge-dot.mock {
  background: #ffaa00;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.viz-head-right {
  display: flex;
  gap: 6px;
}

.viz-head-right :deep(.el-button) {
  --el-button-bg-color: rgba(255,255,255,0.05);
  --el-button-border-color: rgba(255,255,255,0.1);
  --el-button-hover-bg-color: rgba(0,212,255,0.1);
}

/* 选择器 */
.viz-selector {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  flex-shrink: 0;
}

.viz-select {
  flex: 1;
}

.viz-metric {
  flex: 0 0 160px;
}

.ds-option {
  display: flex;
  align-items: center;
  gap: 6px;
}

.ds-icon {
  font-size: 14px;
}

/* 图表类型标签 */
.viz-tabs {
  display: flex;
  gap: 4px;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  overflow-x: auto;
  flex-shrink: 0;
}

.viz-tab {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  background: transparent;
  color: #667788;
  cursor: pointer;
  font-size: 12px;
  white-space: nowrap;
  transition: all 0.2s;
  font-family: inherit;
}

.viz-tab:hover {
  color: #8899aa;
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.12);
}

.viz-tab.active {
  color: #00d4ff;
  background: rgba(0, 212, 255, 0.1);
  border-color: rgba(0, 212, 255, 0.3);
  box-shadow: 0 0 12px rgba(0, 212, 255, 0.1);
}

.tab-icon {
  display: flex;
  align-items: center;
  color: currentColor;
}

.tab-label {
  font-size: 11px;
}

/* 图表内容区 */
.viz-content {
  flex: 1;
  overflow: hidden;
  min-height: 260px;
}

.viz-chart-container {
  width: 100%;
  height: 100%;
  padding: 8px 4px;
}

/* 底部状态栏 */
.viz-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
  background: rgba(0, 0, 0, 0.2);
}

.viz-footer-left {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.footer-metric {
  font-size: 12px;
  color: #667788;
}

.footer-value {
  font-size: 22px;
  font-weight: 700;
  color: #e8ecf1;
  letter-spacing: -0.5px;
}

.footer-value.normal { color: #00d4ff; }
.footer-value.warning { color: #ffaa00; }
.footer-value.critical { color: #ff4444; }

.footer-unit {
  font-size: 12px;
  color: #667788;
}

.viz-footer-right {
  display: flex;
  align-items: center;
}

.footer-time {
  font-size: 11px;
  color: #667788;
  font-variant-numeric: tabular-nums;
}
</style>
