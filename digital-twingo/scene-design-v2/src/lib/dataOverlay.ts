/**
 *   三维数字孪生设计平台
 *
 *  @brief 3D数据叠加层 — 场景中模型上方的浮动数据标签、状态指示器、3D柱状图
 *    Phase 3: 将IoT传感器数据直接渲染到Three.js场景中的模型上
 *
 *  @author Sparcle
 *  @version 3.0
 **/

import * as THREE from 'three'
import type { Model } from '@/lib/model'

export interface OverlayConfig {
  label: string
  value: number
  unit: string
  status: 'normal' | 'warning' | 'critical'
  color?: string
  heightOffset?: number
}

const STATUS_COLORS: Record<string, number> = {
  normal: 0x00d4ff,
  warning: 0xffaa00,
  critical: 0xff4444
}

const STATUS_COLORS_CSS: Record<string, string> = {
  normal: '#00d4ff',
  warning: '#ffaa00',
  critical: '#ff4444'
}

export class DataOverlayManager {
  private scene: THREE.Scene
  private overlays = new Map<string, THREE.Group>()
  private labelSprites = new Map<string, THREE.Sprite>()
  private barMeshes = new Map<string, THREE.Group[]>()
  private pulseRings = new Map<string, THREE.Mesh[]>()

  constructor(scene: THREE.Scene) {
    this.scene = scene
  }

  /** 为模型创建数据叠加层 */
  createOverlay(modelId: string, model: Model, config: OverlayConfig): THREE.Group {
    this.removeOverlay(modelId)

    const group = new THREE.Group()
    group.name = `data-overlay-${modelId}`

    const pos = model.rootObject.position.clone()
    const box = new THREE.Box3().setFromObject(model.rootObject)
    const height = box.max.y - box.min.y
    const offsetY = config.heightOffset || height * 0.6

    // 状态光环
    const ringGeom = new THREE.TorusGeometry(1.2, 0.08, 16, 32)
    const ringMat = new THREE.MeshBasicMaterial({
      color: STATUS_COLORS[config.status] || STATUS_COLORS.normal,
      transparent: true,
      opacity: 0.8
    })
    const ring = new THREE.Mesh(ringGeom, ringMat)
    ring.rotation.x = Math.PI / 2
    ring.position.y = offsetY + 0.3
    group.add(ring)

    // 外圈脉冲环
    const pulseGeom = new THREE.TorusGeometry(1.5, 0.04, 16, 32)
    const pulseMat = new THREE.MeshBasicMaterial({
      color: STATUS_COLORS[config.status] || STATUS_COLORS.normal,
      transparent: true,
      opacity: 0.4
    })
    const pulse = new THREE.Mesh(pulseGeom, pulseMat)
    pulse.rotation.x = Math.PI / 2
    pulse.position.y = offsetY + 0.3
    pulse.userData.pulsePhase = Math.random() * Math.PI * 2
    group.add(pulse)
    this.pulseRings.set(modelId, [ring, pulse])

    // 数据标签 (Sprite)
    const labelSprite = this.createLabelSprite(config)
    labelSprite.position.y = offsetY + 2.0
    labelSprite.scale.set(5, 2, 1)
    group.add(labelSprite)
    this.labelSprites.set(modelId, labelSprite)

    // 3D柱状图 — 在模型旁边显示数值柱
    const barGroup = this.createDataBar(config, offsetY)
    barGroup.position.x = 2.5
    group.add(barGroup)
    this.barMeshes.set(modelId, [barGroup])

    group.position.copy(pos)
    this.scene.add(group)
    this.overlays.set(modelId, group)
    return group
  }

  /** 更新叠加层数据 */
  updateOverlay(modelId: string, config: OverlayConfig): void {
    const group = this.overlays.get(modelId)
    if (!group) return

    // Update sprite label
    const sprite = this.labelSprites.get(modelId)
    if (sprite) {
      const texture = this.createLabelTexture(config)
      sprite.material.map?.dispose()
      sprite.material.map = texture
      sprite.material.needsUpdate = true
    }

    // Update ring colors
    const rings = this.pulseRings.get(modelId)
    if (rings) {
      const color = STATUS_COLORS[config.status] || STATUS_COLORS.normal
      for (const r of rings) {
        ;(r.material as THREE.MeshBasicMaterial).color.set(color)
      }
    }
  }

  /** 移除叠加层 */
  removeOverlay(modelId: string): void {
    const group = this.overlays.get(modelId)
    if (group) {
      this.disposeGroup(group)
      this.scene.remove(group)
      this.overlays.delete(modelId)
    }
    this.labelSprites.delete(modelId)
    this.barMeshes.delete(modelId)
    this.pulseRings.delete(modelId)
  }

  /** 清除所有叠加层 */
  clearAll(): void {
    for (const [id] of this.overlays) {
      this.removeOverlay(id)
    }
  }

  /** 更新动画 (每帧调用) */
  update(deltaTime: number): void {
    for (const [modelId, rings] of this.pulseRings) {
      const [_, pulse] = rings
      if (pulse && pulse.userData.pulsePhase !== undefined) {
        pulse.userData.pulsePhase += deltaTime * 2
        const phase = pulse.userData.pulsePhase
        const scale = 1 + Math.sin(phase) * 0.3
        pulse.scale.setScalar(scale)
        ;(pulse.material as THREE.MeshBasicMaterial).opacity = 0.4 - Math.sin(phase) * 0.2
      }
    }
  }

  /** 获取当前叠加层数量 */
  get overlayCount(): number {
    return this.overlays.size
  }

  /** 显示/隐藏指定模型的叠加层 */
  setVisible(modelId: string, visible: boolean): void {
    const group = this.overlays.get(modelId)
    if (group) {
      group.visible = visible
    }
  }

  /** 创建Canvas纹理标签 */
  private createLabelTexture(config: OverlayConfig): THREE.CanvasTexture {
    const canvas = document.createElement('canvas')
    canvas.width = 256
    canvas.height = 96
    const ctx = canvas.getContext('2d')!

    // 半透明背景
    ctx.fillStyle = 'rgba(7, 11, 24, 0.85)'
    ctx.beginPath()
    ctx.roundRect(8, 4, 240, 88, 12)
    ctx.fill()

    // 边框
    const borderColor = STATUS_COLORS_CSS[config.status] || STATUS_COLORS_CSS.normal
    ctx.strokeStyle = borderColor
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.roundRect(8, 4, 240, 88, 12)
    ctx.stroke()

    // 标签名
    ctx.fillStyle = '#8899aa'
    ctx.font = 'bold 14px "PingFang SC", "Microsoft YaHei", sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText(config.label, 128, 32)

    // 数值
    ctx.fillStyle = '#e8ecf1'
    ctx.font = 'bold 28px "PingFang SC", "Microsoft YaHei", sans-serif'
    ctx.fillText(`${config.value.toFixed(1)}`, 128, 64)

    // 单位
    ctx.fillStyle = '#667788'
    ctx.font = '13px "PingFang SC", "Microsoft YaHei", sans-serif'
    ctx.fillText(config.unit, 128 + 40, 64)

    const texture = new THREE.CanvasTexture(canvas)
    texture.minFilter = THREE.LinearFilter
    texture.magFilter = THREE.LinearFilter
    texture.needsUpdate = true
    return texture
  }

  private createLabelSprite(config: OverlayConfig): THREE.Sprite {
    const texture = this.createLabelTexture(config)
    const material = new THREE.SpriteMaterial({
      map: texture,
      transparent: true,
      depthTest: false,
      depthWrite: false
    })
    return new THREE.Sprite(material)
  }

  /** 创建3D数据柱 */
  private createDataBar(config: OverlayConfig, maxHeight: number): THREE.Group {
    const group = new THREE.Group()

    // 根据值的比例计算柱高 (max 5 units)
    const barHeight = Math.max(0.3, Math.min(5, (config.value / 100) * 5))
    const barColor = STATUS_COLORS[config.status] || STATUS_COLORS.normal

    // 底座
    const baseGeom = new THREE.CylinderGeometry(0.3, 0.35, 0.15, 16)
    const baseMat = new THREE.MeshStandardMaterial({
      color: barColor,
      emissive: barColor,
      emissiveIntensity: 0.3,
      roughness: 0.4,
      metalness: 0.6
    })
    const base = new THREE.Mesh(baseGeom, baseMat)
    base.position.y = 0.075
    group.add(base)

    // 柱子
    const barGeom = new THREE.CylinderGeometry(0.2, 0.25, barHeight, 16)
    const barMat = new THREE.MeshStandardMaterial({
      color: barColor,
      emissive: barColor,
      emissiveIntensity: 0.5,
      roughness: 0.3,
      metalness: 0.4,
      transparent: true,
      opacity: 0.85
    })
    const bar = new THREE.Mesh(barGeom, barMat)
    bar.position.y = barHeight / 2 + 0.1
    group.add(bar)

    // 顶部发光球
    const topGeom = new THREE.SphereGeometry(0.25, 16, 16)
    const topMat = new THREE.MeshStandardMaterial({
      color: barColor,
      emissive: barColor,
      emissiveIntensity: 0.8,
      roughness: 0.2,
      metalness: 0.2
    })
    const top = new THREE.Mesh(topGeom, topMat)
    top.position.y = barHeight + 0.15
    group.add(top)

    return group
  }

  private disposeGroup(group: THREE.Group): void {
    group.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        child.geometry.dispose()
        if (Array.isArray(child.material)) {
          child.material.forEach(m => m.dispose())
        } else {
          child.material.dispose()
        }
      }
      if (child instanceof THREE.Sprite) {
        child.material.map?.dispose()
        child.material.dispose()
      }
    })
  }
}

/** 全局单例 (绑定到主场景) */
let managerInstance: DataOverlayManager | null = null

export function getDataOverlayManager(scene?: THREE.Scene): DataOverlayManager {
  if (scene && !managerInstance) {
    managerInstance = new DataOverlayManager(scene)
  }
  if (!managerInstance) {
    throw new Error('DataOverlayManager not initialized. Call getDataOverlayManager(scene) first.')
  }
  return managerInstance
}

export function disposeDataOverlayManager(): void {
  if (managerInstance) {
    managerInstance.clearAll()
    managerInstance = null
  }
}
