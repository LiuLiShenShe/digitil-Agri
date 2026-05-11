/**
 * 图层管理器 — 场景模型分组/图层管理
 */
import * as THREE from 'three'
import type { Model } from './model'

export interface LayerInfo {
  id: string
  name: string
  visible: boolean
  locked: boolean
  color: string
  modelIds: Set<string>
}

export class LayerManager {
  private layers = new Map<string, LayerInfo>()
  private defaultLayerId: string
  private modelLayerMap = new Map<string, string>() // modelId → layerId

  constructor() {
    this.defaultLayerId = 'default'
    this.layers.set('default', {
      id: 'default',
      name: '默认图层',
      visible: true,
      locked: false,
      color: '#ffffff',
      modelIds: new Set()
    })
  }

  createLayer(name: string, color = '#ffffff'): LayerInfo {
    const id = 'layer_' + Math.random().toString(36).slice(2, 10)
    const layer: LayerInfo = { id, name, visible: true, locked: false, color, modelIds: new Set() }
    this.layers.set(id, layer)
    return layer
  }

  deleteLayer(layerId: string): boolean {
    if (layerId === this.defaultLayerId) return false
    const layer = this.layers.get(layerId)
    if (!layer) return false
    for (const modelId of layer.modelIds) {
      this.modelLayerMap.delete(modelId)
    }
    this.layers.delete(layerId)
    return true
  }

  addModelToLayer(modelId: string, layerId?: string) {
    const targetLayerId = layerId || this.defaultLayerId
    const prevLayerId = this.modelLayerMap.get(modelId)
    if (prevLayerId) {
      this.layers.get(prevLayerId)?.modelIds.delete(modelId)
    }
    this.modelLayerMap.set(modelId, targetLayerId)
    this.layers.get(targetLayerId)?.modelIds.add(modelId)
  }

  removeModel(modelId: string) {
    const layerId = this.modelLayerMap.get(modelId)
    if (layerId) {
      this.layers.get(layerId)?.modelIds.delete(modelId)
    }
    this.modelLayerMap.delete(modelId)
  }

  getModelLayer(modelId: string): string | undefined {
    return this.modelLayerMap.get(modelId)
  }

  getLayer(layerId: string): LayerInfo | undefined {
    return this.layers.get(layerId)
  }

  getAllLayers(): LayerInfo[] {
    return Array.from(this.layers.values())
  }

  setLayerVisible(layerId: string, visible: boolean, scene: THREE.Scene, sceneModels: Record<string, Model>) {
    const layer = this.layers.get(layerId)
    if (!layer) return
    layer.visible = visible
    layer.modelIds.forEach(modelId => {
      const model = sceneModels[modelId]
      if (model) {
        model.rootObject.visible = visible
      }
    })
  }

  setLayerLocked(layerId: string, locked: boolean) {
    const layer = this.layers.get(layerId)
    if (layer) layer.locked = locked
  }

  renameLayer(layerId: string, name: string) {
    const layer = this.layers.get(layerId)
    if (layer) layer.name = name
  }

  getModelIdsInLayer(layerId: string): string[] {
    return Array.from(this.layers.get(layerId)?.modelIds || [])
  }

  getLayerModelCount(layerId: string): number {
    return this.layers.get(layerId)?.modelIds.size || 0
  }

  isModelLocked(modelId: string): boolean {
    const layerId = this.modelLayerMap.get(modelId)
    if (!layerId) return false
    return this.layers.get(layerId)?.locked || false
  }

  toJSON() {
    const layers: any[] = []
    this.layers.forEach(l => {
      layers.push({
        id: l.id,
        name: l.name,
        visible: l.visible,
        locked: l.locked,
        color: l.color,
        modelIds: Array.from(l.modelIds)
      })
    })
    return layers
  }

  fromJSON(data: any[]) {
    this.layers.clear()
    this.modelLayerMap.clear()
    for (const l of data) {
      this.layers.set(l.id, {
        id: l.id,
        name: l.name,
        visible: l.visible,
        locked: l.locked,
        color: l.color || '#ffffff',
        modelIds: new Set(l.modelIds || [])
      })
      for (const mid of l.modelIds || []) {
        this.modelLayerMap.set(mid, l.id)
      }
    }
    if (!this.layers.has('default')) {
      this.layers.set('default', {
        id: 'default',
        name: '默认图层',
        visible: true,
        locked: false,
        color: '#ffffff',
        modelIds: new Set()
      })
    }
  }
}
