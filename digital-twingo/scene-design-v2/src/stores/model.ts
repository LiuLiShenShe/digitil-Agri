/**
 *   三维数字孪生设计平台
 *
 *  @brief Pinia store — 管理当前活动模型（支持多选）
 *
 *  @author Sparcle
 *  @version 2.1
 **/

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Model } from '@/lib/model'

export const useModelStore = defineStore('model', () => {
  const activeModel = ref<Model | null>(null)
  const selectedModels = ref<Model[]>([])
  const offset = ref({ x: 0, y: 0, z: 0 })
  const multiSelectMode = ref(false)

  const activeModelId = computed(() => activeModel.value?.getModelId)
  const selectedCount = computed(() => selectedModels.value.length)
  const hasMultiSelection = computed(() => selectedModels.value.length > 1)

  function updateActiveModel(model: Model | null) {
    activeModel.value = model
    if (model) {
      offset.value.x = model.getOptions.offset.x
      offset.value.y = model.getOptions.offset.y
      offset.value.z = model.getOptions.offset.z
    } else {
      offset.value = { x: 0, y: 0, z: 0 }
    }
  }

  function updateMultiSelection(models: Model[]) {
    selectedModels.value = models
    if (models.length === 1) {
      updateActiveModel(models[0])
    } else if (models.length === 0) {
      updateActiveModel(null)
    }
  }

  function setActiveDataId(data: { model: Model; dataId: string }) {
    if (activeModel.value !== data.model) return
    activeModel.value?.setDataId(data.dataId)
  }

  return {
    activeModel,
    selectedModels,
    offset,
    activeModelId,
    selectedCount,
    hasMultiSelection,
    multiSelectMode,
    updateActiveModel,
    updateMultiSelection,
    setActiveDataId
  }
})
