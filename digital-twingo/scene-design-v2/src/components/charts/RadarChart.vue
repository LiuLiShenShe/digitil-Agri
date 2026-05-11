<!--
 *   三维数字孪生设计平台
 *    雷达图组件 — 多维度指标分析
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

const dataSource = computed(() => store.activeDataSource)
const realtimeData = computed(() => {
  if (!store.activeDataSourceId) return null
  return store.realtimeData[store.activeDataSourceId]
})

function buildChart() {
  if (!chartRef.value) return
  const ds = dataSource.value
  const rd = realtimeData.value
  if (!ds || !rd) return

  if (!chart) {
    chart = echarts.init(chartRef.value, 'dark')
  }

  const indicator = ds.metrics.map(m => ({
    name: m.label,
    max: m.max
  }))

  const values = ds.metrics.map(m => {
    const arr = (rd as any)[m.key] as { value: number }[] | undefined
    if (!arr || arr.length === 0) return 0
    return arr[arr.length - 1].value
  })

  chart.setOption({
    radar: {
      center: ['50%', '50%'],
      radius: '65%',
      indicator,
      axisName: { color: '#8899aa', fontSize: 11 },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
      splitArea: {
        areaStyle: {
          color: ['rgba(0,212,255,0.02)', 'rgba(0,212,255,0.04)']
        }
      }
    },
    series: [{
      type: 'radar',
      data: [{
        value: values,
        name: ds.name,
        areaStyle: {
          color: new echarts.graphic.RadialGradient(0.5, 0.5, 1, [
            { offset: 0, color: 'rgba(0,212,255,0.25)' },
            { offset: 1, color: 'rgba(64,144,255,0.08)' }
          ])
        },
        lineStyle: { color: '#00d4ff', width: 2 },
        itemStyle: { color: '#00d4ff' },
        symbol: 'circle',
        symbolSize: 6
      }],
      animationDuration: 800,
      animationEasing: 'cubicOut'
    }]
  })
}

watch(() => store.lastUpdate, () => {
  if (chart && !chart.isDisposed()) {
    buildChart()
  }
})

watch(() => store.activeDataSourceId, () => {
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
  min-height: 300px;
}
</style>
