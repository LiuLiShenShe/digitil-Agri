<!--
 *   三维数字孪生设计平台
 *    热力图组件 — 田块级数据分布
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

const store = useDataVizStore()
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const gridSize = 20
const hours = Array.from({ length: 24 }, (_, i) => `${i.toString().padStart(2, '0')}:00`)
const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

function generateHeatData(): [number, number, number][] {
  const data: [number, number, number][] = []
  const now = new Date()
  const currentHour = now.getHours()
  const currentDay = now.getDay() || 7

  for (let d = 0; d < 7; d++) {
    for (let h = 0; h < 24; h++) {
      // Create realistic daily pattern: peak midday, low at night
      const dayFactor = Math.exp(-Math.pow((h - 14) / 6, 2))
      const baseVal = dayFactor * 0.8 + 0.1
      const noise = (Math.random() - 0.5) * 0.15
      // Highlight current time
      const isCurrent = d === currentDay - 1 && h === currentHour
      const val = Math.min(1, Math.max(0, baseVal + noise + (isCurrent ? 0.1 : 0)))
      data.push([h, d, Math.round(val * 100)])
    }
  }
  return data
}

function buildChart() {
  if (!chartRef.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value, 'dark')
  }

  const metricCfg = store.activeMetricConfig

  chart.setOption({
    tooltip: {
      backgroundColor: 'rgba(12,20,36,0.95)',
      borderColor: 'rgba(0,212,255,0.3)',
      textStyle: { color: '#c8d0da' },
      formatter: (params: any) => {
        if (!params || !params.data) return ''
        const p = params.data
        return `<span style="color:#8899aa">${days[p[1]]} ${hours[p[0]]}</span><br/>
          <span style="color:#00d4ff;font-size:15px;font-weight:600">${p[2]} ${metricCfg?.unit || '%'}</span>`
      }
    },
    grid: { top: 20, left: 70, right: 40, bottom: 30 },
    xAxis: {
      type: 'category',
      data: hours,
      axisLabel: {
        color: '#667788',
        fontSize: 10,
        interval: 3
      },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      splitArea: { show: true, areaStyle: { color: ['rgba(255,255,255,0.02)', 'transparent'] } }
    },
    yAxis: {
      type: 'category',
      data: days,
      axisLabel: { color: '#667788', fontSize: 11 },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      splitArea: { show: true, areaStyle: { color: ['transparent', 'rgba(255,255,255,0.02)'] } }
    },
    visualMap: {
      show: true,
      min: 0,
      max: 100,
      calculable: true,
      orient: 'vertical',
      right: 4,
      top: 'center',
      itemWidth: 8,
      itemHeight: 120,
      textStyle: { color: '#667788', fontSize: 10 },
      inRange: {
        color: ['#0a1628', '#0d3b66', '#0d6ea8', '#00a8d4', '#00d4ff', '#40e8ff']
      }
    },
    series: [{
      type: 'heatmap',
      data: generateHeatData(),
      label: { show: false },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0,212,255,0.5)'
        }
      },
      animationDuration: 1000
    }]
  })
}

watch(() => store.activeMetric, () => {
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
  min-height: 280px;
}
</style>
