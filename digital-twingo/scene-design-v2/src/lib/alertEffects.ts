/**
 *   三维数字孪生设计平台
 *
 *  @brief 告警视觉效果 — 模型颜色闪烁、高亮边框、告警脉冲
 *    Phase 4: 告警触发时的3D视觉效果
 *
 *  @author Sparcle
 *  @version 4.0
 **/

import * as THREE from 'three'
import type { Scene } from '@/lib/scene'
import type { Model } from '@/lib/model'

export type AlertStatus = 'none' | 'info' | 'warning' | 'critical'

interface AlertEffectEntry {
  modelId: string
  model: Model
  status: AlertStatus
  originalMaterials: Map<THREE.Mesh, THREE.Material | THREE.Material[]>
  startedAt: number
}

const ALERT_COLORS: Record<string, number> = {
  info: 0x4488cc,
  warning: 0xffaa00,
  critical: 0xff2222
}

const ALERT_EMISSIVE: Record<string, number> = {
  info: 0x224466,
  warning: 0x443300,
  critical: 0x440000
}

export class AlertEffectManager {
  private scene: Scene
  private effects = new Map<string, AlertEffectEntry>()
  private disposed = false

  constructor(scene: Scene) {
    this.scene = scene
  }

  /** 对模型应用告警效果 */
  applyAlert(modelId: string, model: Model, status: AlertStatus): void {
    // 如果已存在，先清除
    if (this.effects.has(modelId)) {
      this.clearAlert(modelId)
    }

    if (status === 'none') return

    const entry: AlertEffectEntry = {
      modelId,
      model,
      status,
      originalMaterials: new Map(),
      startedAt: Date.now()
    }

    // 替换所有mesh材质为告警材质
    model.rootObject.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        entry.originalMaterials.set(child, child.material)

        const color = ALERT_COLORS[status] || ALERT_COLORS.warning
        const emissive = ALERT_EMISSIVE[status] || ALERT_EMISSIVE.warning

        if (Array.isArray(child.material)) {
          child.material = child.material.map(m => {
            const clone = (m as THREE.MeshStandardMaterial).clone()
            clone.color.set(color)
            clone.emissive.set(emissive)
            clone.emissiveIntensity = 0.6
            return clone
          })
        } else {
          const clone = (child.material as THREE.MeshStandardMaterial).clone()
          clone.color.set(color)
          clone.emissive.set(emissive)
          clone.emissiveIntensity = 0.6
          child.material = clone
        }
      }
    })

    this.effects.set(modelId, entry)
  }

  /** 清除模型的告警效果 */
  clearAlert(modelId: string): void {
    const entry = this.effects.get(modelId)
    if (!entry) return

    entry.model.rootObject.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        const original = entry.originalMaterials.get(child)
        if (original) {
          // Dispose cloned materials
          if (Array.isArray(child.material)) {
            child.material.forEach(m => m.dispose())
          } else {
            child.material.dispose()
          }
          child.material = original
        }
      }
    })

    this.effects.delete(modelId)
  }

  /** 清除所有告警效果 */
  clearAll(): void {
    for (const [id] of this.effects) {
      this.clearAlert(id)
    }
  }

  /** 每帧更新 — 闪烁和脉冲动画 */
  update(deltaTime: number): void {
    const now = Date.now()
    for (const [_, entry] of this.effects) {
      const elapsed = (now - entry.startedAt) / 1000

      // 闪烁频率随严重程度变化
      let blinkFreq = 2
      if (entry.status === 'critical') blinkFreq = 4
      else if (entry.status === 'warning') blinkFreq = 2.5

      const blink = Math.sin(elapsed * blinkFreq * Math.PI) * 0.5 + 0.5
      const intensity = 0.3 + blink * 0.7

      entry.model.rootObject.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          this.setEmissiveIntensity(child, intensity)
        }
      })
    }
  }

  private setEmissiveIntensity(mesh: THREE.Mesh, intensity: number): void {
    if (Array.isArray(mesh.material)) {
      for (const m of mesh.material) {
        if ((m as any).emissiveIntensity !== undefined) {
          ;(m as THREE.MeshStandardMaterial).emissiveIntensity = intensity
        }
      }
    } else {
      if ((mesh.material as any).emissiveIntensity !== undefined) {
        ;(mesh.material as THREE.MeshStandardMaterial).emissiveIntensity = intensity
      }
    }
  }

  dispose(): void {
    this.clearAll()
    this.disposed = true
  }
}

let alertEffectInstance: AlertEffectManager | null = null

export function getAlertEffectManager(scene?: Scene): AlertEffectManager {
  if (scene && !alertEffectInstance) {
    alertEffectInstance = new AlertEffectManager(scene)
  }
  if (!alertEffectInstance) {
    throw new Error('AlertEffectManager not initialized')
  }
  return alertEffectInstance
}

export function disposeAlertEffectManager(): void {
  if (alertEffectInstance) {
    alertEffectInstance.dispose()
    alertEffectInstance = null
  }
}
