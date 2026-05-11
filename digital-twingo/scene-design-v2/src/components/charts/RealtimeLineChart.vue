<!--
 *   三维数字孪生设计平台
 *    实时数据折线图
 *
 *  @author Sparcle
 *  @version 3.0
 -->

<template>
  <div class="chart-wrapper">
    <div ref="chartRef" class="chart-canvas"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import * as echarts from 'echarts'
import { useDataVizStore } from '@/stores/dataviz'
import type { SensorPoint } from '@/stores/dataviz'

const store = useDataVizStore()
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const chartData = computed(() => store.currentRealtimeData as SensorPoint[])
const metricCfg = computed(() => store.activeMetricConfig)

function buildChart() {
  if (!chartRef.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value, 'dark')
  }

  const data = chartData.value
  const cfg = metricCfg.value
  const now = Date.now()
  const range = store.timeRange

  chart.setOption({
    grid: { top: 50, left: 55, right: 25, bottom: 40 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(12,20,36,0.95)',
      borderColor: 'rgba(0,212,255,0.3)',
      textStyle: { color: '#c8d0da', fontSize: 12 },
      formatter: (params: any) => {
        const p = params[0]
        if (!p) return ''
        const t = new Date(p.data[0]).toLocaleTimeString('zh-CN')
        return `<span style="color:#8899aa">${t}</span><br/>
          <span style="color:#00d4ff;font-size:16px;font-weight:600">${p.data[1]} ${cfg?.unit || ''}</span>`
      }
    },
    xAxis: {
      type: 'time',
      min: now - range,
      max: now,
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      axisLabel: {
        color: '#667788',
        fontSize: 10,
        formatter: (val: number) => {
          const d = new Date(val)
          return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
        }
      },
      splitLine: { show: false }
    },
    yAxis: {
      type: 'value',
      name: cfg?.unit || '',
      nameTextStyle: { color: '#667788', fontSize: 11 },
      axisLine: { show: false },
      axisLabel: { color: '#667788', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)', type: 'dashed' } }
    },
    series: [{
      type: 'line',
      data: data.map(p => [p.timestamp, p.value]),
      smooth: true,
      symbol: 'none',
      lineStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#4090ff' },
          { offset: 1, color: '#00d4ff' }
        ]),
        width: 2
      },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(0,212,255,0.25)' },
          { offset: 1, color: 'rgba(0,212,255,0.02)' }
        ])
      }
    }]
  })
}

watch(() => store.lastUpdate, () => {
  if (chart && !chart.isDisposed()) {
    buildChart()
  }
})

watch([() => store.activeDataSourceId, () => store.activeMetric], () => {
  if (chart) {
    chart.dispose()
    chart = null
  }
  buildChart()
})

onMounted(() => {
  setTimeout(buildChart, 100)
})

onUnmounted(() => {
  if (chart && !chart.isDisposed()) {
    chart.dispose()
    chart = null
  }
})
</script>

<style scoped>
.chart-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
}

.chart-canvas {
  width: 100%;
  height: 100%;
  min-height: 240px;
}
</style>
