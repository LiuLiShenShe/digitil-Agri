<!--
 *   三维数字孪生设计平台
 *    饼图/环形图组件 — 数据分布展示
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

const dataSources = computed(() => store.dataSources)

function buildChart() {
  if (!chartRef.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value, 'dark')
  }

  const dss = dataSources.value
  const metric = store.activeMetricConfig

  const pieData = dss.map((ds, i) => {
    const rd = store.realtimeData[ds.id]
    const arr = rd ? (rd as any)[store.activeMetric] as { value: number }[] : []
    const val = arr && arr.length > 0 ? arr[arr.length - 1].value : Math.round(Math.random() * 60 + 20)
    return {
      value: val,
      name: ds.name,
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
          { offset: 0, color: i % 2 === 0 ? '#4090ff' : '#00b8d4' },
          { offset: 1, color: i % 2 === 0 ? '#00d4ff' : '#40e8ff' }
        ])
      }
    }
  })

  const total = pieData.reduce((sum, d) => sum + d.value, 0)

  chart.setOption({
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(12,20,36,0.95)',
      borderColor: 'rgba(0,212,255,0.3)',
      textStyle: { color: '#c8d0da' },
      formatter: (params: any) => {
        if (!params) return ''
        const pct = params.percent ? params.percent.toFixed(1) : '0.0'
        return `<span style="color:#8899aa">${params.name}</span><br/>
          <span style="color:#00d4ff;font-size:16px;font-weight:600">${params.value} ${metric?.unit || ''}</span>
          <span style="color:#667788"> (${pct}%)</span>`
      }
    },
    graphic: total > 0 ? [{
      type: 'text',
      left: 'center',
      top: '42%',
      style: {
        text: total.toFixed(0),
        textAlign: 'center',
        fill: '#e8ecf1',
        fontSize: 28,
        fontWeight: 700
      }
    }, {
      type: 'text',
      left: 'center',
      top: '54%',
      style: {
        text: metric?.unit || '',
        textAlign: 'center',
        fill: '#667788',
        fontSize: 12
      }
    }] : [],
    series: [{
      type: 'pie',
      radius: ['55%', '78%'],
      center: ['50%', '48%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 6,
        borderColor: 'rgba(12,20,36,0.9)',
        borderWidth: 3
      },
      label: {
        show: true,
        position: 'outside',
        color: '#8899aa',
        fontSize: 11,
        formatter: '{b}\n{d}%'
      },
      labelLine: {
        length: 20,
        length2: 24,
        lineStyle: { color: 'rgba(255,255,255,0.15)' }
      },
      emphasis: {
        label: { fontSize: 15, fontWeight: 'bold' },
        scaleSize: 8,
        itemStyle: { shadowBlur: 20, shadowColor: 'rgba(0,212,255,0.4)' }
      },
      data: pieData,
      animationDuration: 1000,
      animationEasing: 'cubicOut'
    }]
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
