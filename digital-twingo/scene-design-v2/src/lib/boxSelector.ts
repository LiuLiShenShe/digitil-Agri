/**
 * 框选工具 — 支持场景中框选多个模型进行批量操作
 */
import * as THREE from 'three'
import type { Model } from './model'

export interface BoxSelection {
  startX: number
  startY: number
  endX: number
  endY: number
}

export class BoxSelector {
  private scene: THREE.Scene
  private camera: THREE.Camera
  private domElement: HTMLElement
  private selectionBox: HTMLDivElement | null = null
  private enabled = false
  private startPos = new THREE.Vector2()
  private endPos = new THREE.Vector2()

  public onSelectionComplete: ((selectedIds: string[]) => void) | null = null

  constructor(scene: THREE.Scene, camera: THREE.Camera, domElement: HTMLElement) {
    this.scene = scene
    this.camera = camera
    this.domElement = domElement
  }

  enable() {
    if (this.enabled) return
    this.enabled = true
    this.createSelectionBox()
    this.domElement.addEventListener('pointerdown', this.onPointerDown)
    this.domElement.addEventListener('pointermove', this.onPointerMove)
    this.domElement.addEventListener('pointerup', this.onPointerUp)
    this.domElement.style.cursor = 'crosshair'
  }

  disable() {
    this.enabled = false
    this.domElement.removeEventListener('pointerdown', this.onPointerDown)
    this.domElement.removeEventListener('pointermove', this.onPointerMove)
    this.domElement.removeEventListener('pointerup', this.onPointerUp)
    if (this.selectionBox) {
      this.selectionBox.remove()
      this.selectionBox = null
    }
    this.domElement.style.cursor = ''
  }

  toggle(): boolean {
    if (this.enabled) {
      this.disable()
    } else {
      this.enable()
    }
    return this.enabled
  }

  get isEnabled(): boolean {
    return this.enabled
  }

  private createSelectionBox() {
    this.selectionBox = document.createElement('div')
    this.selectionBox.style.position = 'absolute'
    this.selectionBox.style.border = '2px dashed #00d4ff'
    this.selectionBox.style.background = 'rgba(0, 212, 255, 0.08)'
    this.selectionBox.style.pointerEvents = 'none'
    this.selectionBox.style.display = 'none'
    this.selectionBox.style.zIndex = '9999'
    this.domElement.parentElement?.appendChild(this.selectionBox)
  }

  private getCanvasRelativePos(event: PointerEvent): { x: number; y: number } {
    const rect = this.domElement.getBoundingClientRect()
    return { x: event.clientX - rect.left, y: event.clientY - rect.top }
  }

  private onPointerDown = (event: PointerEvent) => {
    if (!this.selectionBox) return
    const pos = this.getCanvasRelativePos(event)
    this.startPos.set(pos.x, pos.y)
    this.selectionBox.style.display = 'block'
    this.selectionBox.style.left = pos.x + 'px'
    this.selectionBox.style.top = pos.y + 'px'
    this.selectionBox.style.width = '0px'
    this.selectionBox.style.height = '0px'
  }

  private onPointerMove = (event: PointerEvent) => {
    if (!this.selectionBox || this.selectionBox.style.display === 'none') return
    const pos = this.getCanvasRelativePos(event)
    this.endPos.set(pos.x, pos.y)
    const left = Math.min(this.startPos.x, this.endPos.x)
    const top = Math.min(this.startPos.y, this.endPos.y)
    const width = Math.abs(this.endPos.x - this.startPos.x)
    const height = Math.abs(this.endPos.y - this.startPos.y)
    this.selectionBox.style.left = left + 'px'
    this.selectionBox.style.top = top + 'px'
    this.selectionBox.style.width = width + 'px'
    this.selectionBox.style.height = height + 'px'
  }

  private onPointerUp = () => {
    if (!this.selectionBox) return
    this.selectionBox.style.display = 'none'

    const minX = Math.min(this.startPos.x, this.endPos.x)
    const maxX = Math.max(this.startPos.x, this.endPos.x)
    const minY = Math.min(this.startPos.y, this.endPos.y)
    const maxY = Math.max(this.startPos.y, this.endPos.y)
    const area = (maxX - minX) * (maxY - minY)
    if (area < 4) return

    const selectedIds = this.getModelsInRect(minX, minY, maxX, maxY)
    this.onSelectionComplete?.(selectedIds)
  }

  private getModelsInRect(minX: number, minY: number, maxX: number, maxY: number): string[] {
    const selectedIds: string[] = []
    this.scene.children.forEach(child => {
      if (child.userData.type === 'targetObj' && child.userData.modelId) {
        const projected = this.worldToScreen(child.position)
        if (projected && projected.x >= minX && projected.x <= maxX && projected.y >= minY && projected.y <= maxY) {
          selectedIds.push(child.userData.modelId)
        }
      }
    })
    return selectedIds
  }

  private worldToScreen(worldPos: THREE.Vector3): { x: number; y: number } | null {
    const vector = worldPos.clone().project(this.camera)
    const rect = this.domElement.getBoundingClientRect()
    return {
      x: (vector.x * 0.5 + 0.5) * rect.width,
      y: (-vector.y * 0.5 + 0.5) * rect.height
    }
  }

  dispose() {
    this.disable()
  }
}
