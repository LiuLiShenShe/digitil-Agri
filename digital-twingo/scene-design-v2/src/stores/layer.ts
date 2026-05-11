/**
 * Pinia store — 图层管理状态
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { LayerInfo } from '@/lib/layerManager'

export const useLayerStore = defineStore('layer', () => {
  const layers = ref<LayerInfo[]>([])
  const selectedLayerId = ref<string>('default')
  const panelVisible = ref(false)

  const selectedLayer = computed(() =>
    layers.value.find(l => l.id === selectedLayerId.value)
  )

  function setLayers(newLayers: LayerInfo[]) {
    layers.value = newLayers
  }

  function selectLayer(layerId: string) {
    selectedLayerId.value = layerId
  }

  function showPanel(show: boolean) {
    panelVisible.value = show
  }

  function togglePanel() {
    panelVisible.value = !panelVisible.value
  }

  return {
    layers,
    selectedLayerId,
    panelVisible,
    selectedLayer,
    setLayers,
    selectLayer,
    showPanel,
    togglePanel
  }
})
