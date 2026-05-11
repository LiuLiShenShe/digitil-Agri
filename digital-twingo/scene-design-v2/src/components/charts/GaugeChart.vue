<!--
 *   三维数字孪生设计平台
 *    仪表盘组件 — 单指标实时展示
 *
 *  @author Sparcle
 *  @version 3.0
 -->

<template>
  <div class="chart-wrapper">
    <div ref="chartRef" class="chart-canvas"></div>
    <div class="gauge-value">{{ displayValue }}<span class="gauge-unit">{{ metricCfg?.unit }}</span></div>
    <div class="gauge-label">{{ metricCfg?.label || '--' }}</div>
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

const displayValue = computed(() => {
  const data = chartData.value
  if (!data || data.length === 0) return '--'
  return data[data.length - 1].value.toFixed(1)
})

function buildChart() {
  if (!chartRef.value) return
  if (!chart) {
    chart = echarts.init(chartRef.value, 'dark')
  }

  const cfg = metricCfg.value
  if (!cfg) return

  const currentVal = chartData.value.length > 0
    ? chartData.value[chartData.value.length - 1].value
    : 0
  const pct = Math.round(((currentVal - cfg.min) / (cfg.max - cfg.min)) * 100)

  chart.setOption({
    series: [{
      type: 'gauge',
      startAngle: 210,
      endAngle: -30,
      center: ['50%', '58%'],
      radius: '85%',
      min: cfg.min,
      max: cfg.max,
      splitNumber: 10,
      axisLine: {
        show: true,
        lineStyle: {
          width: 18,
          color: [
            [0.3, '#4090ff'],
            [0.7, '#00d4ff'],
            [1, '#ff6b6b']
          ]
        }
      },
      pointer: {
        icon: 'path://M12.8,0.7l12,40.1H0.7L12.8,0.7z',
        length: '72%',
        width: 6,
        offsetCenter: [0, '-6%'],
        itemStyle: {
          color: '#c8d0da'
        }
      },
      axisTick: {
        length: 10,
        lineStyle: { color: 'auto', width: 2 }
      },
      splitLine: {
        length: 22,
        lineStyle: { color: 'auto', width: 4 }
      },
      axisLabel: {
        color: '#667788',
        fontSize: 10,
        distance: 25,
        formatter: (val: number) => val.toFixed(0)
      },
      title: { show: false },
      detail: { show: false },
      data: [{ value: currentVal, name: cfg.label }],
      animationDuration: 600,
      animationEasing: 'cubicOut'
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
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.chart-canvas {
  width: 100%;
  height: 240px;
}

.gauge-value {
  font-size: 36px;
  font-weight: 700;
  color: #e8ecf1;
  margin-top: -16px;
  letter-spacing: -1px;
}

.gauge-unit {
  font-size: 14px;
  font-weight: 400;
  color: #667788;
  margin-left: 4px;
}

.gauge-label {
  font-size: 13px;
  color: #8899aa;
  margin-top: 2px;
}
</style>
