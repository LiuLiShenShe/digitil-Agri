<!--
 *   三维数字孪生设计平台
 *    3D柱状图组件 — 多模型数据对比
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
import 'echarts-gl'
import { useDataVizStore } from '@/stores/dataviz'

const store = useDataVizStore()
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const dataSources = computed(() => store.dataSources)

function buildChart() {
  if (!chartRef.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value, 'dark')
  }

  const dss = dataSources.value
  const metric = store.activeMetricConfig

  // Build comparison data — one bar per data source
  const categories = dss.map(ds => ds.name.length > 6 ? ds.name.slice(0, 6) + '...' : ds.name)
  const seriesData = dss.map((ds, i) => {
    const rd = store.realtimeData[ds.id]
    const arr = rd ? (rd as any)[store.activeMetric] as { value: number }[] : []
    const val = arr && arr.length > 0 ? arr[arr.length - 1].value : Math.random() * 50 + 20
    return {
      value: [i, val, val * 1.2],
      name: ds.name
    }
  })

  chart.setOption({
    grid: { top: 20, left: 60, right: 30, bottom: 60 },
    tooltip: {
      backgroundColor: 'rgba(12,20,36,0.95)',
      borderColor: 'rgba(0,212,255,0.3)',
      textStyle: { color: '#c8d0da' },
      formatter: (params: any) => {
        if (!params || !params.name) return ''
        return `<span style="color:#8899aa">${params.name}</span><br/>
          <span style="color:#00d4ff;font-size:16px;font-weight:600">${params.value[1]} ${store.activeMetricConfig?.unit || ''}</span>`
      }
    },
    xAxis3D: {
      type: 'category',
      data: categories,
      name: '',
      axisLabel: { color: '#667788', fontSize: 10 },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.15)' } }
    },
    yAxis3D: {
      type: 'value',
      name: metric?.unit || '',
      nameTextStyle: { color: '#667788', fontSize: 11 },
      axisLabel: { color: '#667788', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } }
    },
    zAxis3D: {
      type: 'value',
      name: '',
      axisLabel: { show: false },
      splitLine: { show: false }
    },
    visualMap: {
      show: false,
      dimension: 1,
      min: 0,
      max: metric?.max || 100,
      inRange: {
        color: ['#1a3a5c', '#0d6ea8', '#00a8d4', '#00d4ff', '#40e8ff']
      }
    },
    series: [{
      type: 'bar3D',
      data: seriesData,
      shading: 'lambert',
      barSize: 0.4,
      label: {
        show: true,
        formatter: (p: any) => p.value[1].toFixed(1),
        textStyle: { color: '#e8ecf1', fontSize: 11 }
      },
      itemStyle: { opacity: 0.9 },
      emphasis: {
        label: { textStyle: { fontSize: 14, fontWeight: 'bold' } },
        itemStyle: { color: '#00d4ff' }
      }
    }],
    animationDuration: 1200,
    animationEasing: 'elasticOut'
  })
}

watch(() => store.lastUpdate, () => {
  if (chart && !chart.isDisposed()) {
    buildChart()
  }
})

watch([() => store.activeMetric, () => store.dataSources], () => {
  if (chart) {
    chart.dispose()
    chart = null
  }
  buildChart()
})

onMounted(() => {
  setTimeout(buildChart, 150)
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
  min-height: 320px;
}
</style>
