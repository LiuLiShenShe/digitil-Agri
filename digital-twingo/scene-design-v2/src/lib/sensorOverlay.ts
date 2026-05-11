/**
 *   三维数字孪生设计平台
 *
 *  @brief 传感器3D可视化 — 浮空数据标签、传感器节点模型、热力指示器
 *    Phase 4: IoT传感器数据在场景中的可视化
 *
 *  @author Sparcle
 *  @version 4.0
 **/

import * as THREE from 'three'
import type { Scene } from '@/lib/scene'

export interface SensorVisualConfig {
  position: THREE.Vector3
  label: string
  metrics: { key: string; label: string; value: number; unit: string; status: 'normal' | 'warning' | 'critical' }[]
  radius?: number
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

export class SensorOverlayManager {
  private scene: THREE.Scene
  private sensorNodes = new Map<string, THREE.Group>()
  private disposed = false

  constructor(scene: THREE.Scene) {
    this.scene = scene
  }

  /** 创建传感器可视化节点 */
  createSensorNode(id: string, config: SensorVisualConfig): THREE.Group {
    this.removeSensorNode(id)

    const group = new THREE.Group()
    group.name = `sensor-${id}`
    group.position.copy(config.position)

    const radius = config.radius || 0.5

    // 基座 — 圆柱体
    const baseGeom = new THREE.CylinderGeometry(radius * 0.6, radius * 0.8, 0.3, 16)
    const baseMat = new THREE.MeshStandardMaterial({
      color: 0x334455,
      roughness: 0.5,
      metalness: 0.7
    })
    const base = new THREE.Mesh(baseGeom, baseMat)
    base.position.y = 0.15
    group.add(base)

    // 主体球
    const sphereGeom = new THREE.SphereGeometry(radius, 24, 24)
    const sphereMat = new THREE.MeshStandardMaterial({
      color: STATUS_COLORS.normal,
      roughness: 0.3,
      metalness: 0.3,
      emissive: STATUS_COLORS.normal,
      emissiveIntensity: 0.4
    })
    const sphere = new THREE.Mesh(sphereGeom, sphereMat)
    sphere.position.y = 0.7
    sphere.name = 'sensor-sphere'
    group.add(sphere)

    // 光环
    const ringGeom = new THREE.TorusGeometry(radius * 1.3, 0.05, 16, 32)
    const ringMat = new THREE.MeshBasicMaterial({
      color: STATUS_COLORS.normal,
      transparent: true,
      opacity: 0.7
    })
    const ring = new THREE.Mesh(ringGeom, ringMat)
    ring.rotation.x = Math.PI / 2
    ring.position.y = 0.7
    ring.name = 'sensor-ring'
    group.add(ring)

    // 浮空标签
    const labelSprite = this.createSensorLabel(config)
    labelSprite.position.y = 2.0
    labelSprite.scale.set(4, 1.5, 1)
    group.add(labelSprite)
    group.userData.labelSprite = labelSprite

    this.scene.add(group)
    this.sensorNodes.set(id, group)
    return group
  }

  /** 更新传感器数据 */
  updateSensorData(id: string, metrics: SensorVisualConfig['metrics']): void {
    const group = this.sensorNodes.get(id)
    if (!group) return

    // 更新球体颜色（取最严重的状态）
    let worstStatus: 'normal' | 'warning' | 'critical' = 'normal'
    for (const m of metrics) {
      if (m.status === 'critical') { worstStatus = 'critical'; break }
      if (m.status === 'warning') worstStatus = 'warning'
    }

    const sphere = group.getObjectByName('sensor-sphere') as THREE.Mesh
    if (sphere) {
      const color = STATUS_COLORS[worstStatus]
      ;(sphere.material as THREE.MeshStandardMaterial).color.set(color)
      ;(sphere.material as THREE.MeshStandardMaterial).emissive.set(color)
    }

    const ring = group.getObjectByName('sensor-ring') as THREE.Mesh
    if (ring) {
      ;(ring.material as THREE.MeshBasicMaterial).color.set(STATUS_COLORS[worstStatus])
    }

    // 更新标签
    const oldSprite = group.userData.labelSprite as THREE.Sprite
    if (oldSprite) {
      group.remove(oldSprite)
      oldSprite.material.map?.dispose()
      oldSprite.material.dispose()
    }

    const config: SensorVisualConfig = {
      position: group.position,
      label: '',
      metrics
    }
    const newSprite = this.createSensorLabel(config)
    newSprite.position.y = 2.0
    newSprite.scale.set(4, 1.5, 1)
    group.add(newSprite)
    group.userData.labelSprite = newSprite
  }

  /** 移除传感器节点 */
  removeSensorNode(id: string): void {
    const group = this.sensorNodes.get(id)
    if (group) {
      this.disposeGroup(group)
      this.scene.remove(group)
      this.sensorNodes.delete(id)
    }
  }

  /** 清除所有 */
  clearAll(): void {
    for (const [id] of this.sensorNodes) {
      this.removeSensorNode(id)
    }
  }

  /** 每帧更新 */
  update(deltaTime: number): void {
    for (const [_, group] of this.sensorNodes) {
      const ring = group.getObjectByName('sensor-ring') as THREE.Mesh
      if (ring) {
        ring.rotation.z += deltaTime * 0.5
      }
      const sphere = group.getObjectByName('sensor-sphere') as THREE.Mesh
      if (sphere) {
        const mat = sphere.material as THREE.MeshStandardMaterial
        mat.emissiveIntensity = 0.3 + Math.sin(Date.now() * 0.003) * 0.15
      }
    }
  }

  dispose(): void {
    this.clearAll()
    this.disposed = true
  }

  private createSensorLabel(config: SensorVisualConfig): THREE.Sprite {
    const canvas = document.createElement('canvas')
    canvas.width = 512
    canvas.height = 32 + config.metrics.length * 24

    const ctx = canvas.getContext('2d')!

    // Background
    ctx.fillStyle = 'rgba(7, 11, 24, 0.88)'
    ctx.beginPath()
    ctx.roundRect(4, 4, canvas.width - 8, canvas.height - 8, 10)
    ctx.fill()

    ctx.strokeStyle = '#00d4ff44'
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.roundRect(4, 4, canvas.width - 8, canvas.height - 8, 10)
    ctx.stroke()

    let y = 22
    for (const m of config.metrics) {
      const color = STATUS_COLORS_CSS[m.status] || '#e8ecf1'
      ctx.fillStyle = '#8899aa'
      ctx.font = '12px "PingFang SC", "Microsoft YaHei", sans-serif'
      ctx.textAlign = 'left'
      ctx.fillText(`${m.label}:`, 16, y)

      ctx.fillStyle = color
      ctx.font = 'bold 13px "PingFang SC", "Microsoft YaHei", sans-serif'
      ctx.textAlign = 'right'
      ctx.fillText(`${m.value.toFixed(1)} ${m.unit}`, canvas.width - 16, y)

      y += 22
    }

    const texture = new THREE.CanvasTexture(canvas)
    texture.minFilter = THREE.LinearFilter
    texture.magFilter = THREE.LinearFilter
    texture.needsUpdate = true

    const material = new THREE.SpriteMaterial({
      map: texture,
      transparent: true,
      depthTest: false,
      depthWrite: false
    })
    return new THREE.Sprite(material)
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

let sensorManagerInstance: SensorOverlayManager | null = null

export function getSensorOverlayManager(scene?: THREE.Scene): SensorOverlayManager {
  if (scene && !sensorManagerInstance) {
    sensorManagerInstance = new SensorOverlayManager(scene)
  }
  if (!sensorManagerInstance) {
    throw new Error('SensorOverlayManager not initialized')
  }
  return sensorManagerInstance
}

export function disposeSensorOverlayManager(): void {
  if (sensorManagerInstance) {
    sensorManagerInstance.dispose()
    sensorManagerInstance = null
  }
}
