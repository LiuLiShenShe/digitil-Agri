/**
 *   三维数字孪生设计平台
 *
 *    拖拽控件  改写自 three/examples/js/control/DragControls
 *             增加高度控制(y轴方向，lockHeight方法)，以保持在同一水平面上移动
 *             简化了拖拽对象(单一Group)
 *    Phase 2: 增加网格吸附、模型间对齐吸附、多对象拖拽支持
 *
 *  @author Sparcle
 *  @version 2.1
 **/

import * as THREE from 'three'
import { EventDispatcher } from 'three'
import { Model } from '@/lib/model'
import type { SnapConfig } from '@/lib/scene'

export class DragControl extends EventDispatcher<any> {
  private _plane = new THREE.Plane()
  private _raycaster = new THREE.Raycaster()
  private _pointer = new THREE.Vector2()
  private _offset = new THREE.Vector3()
  private _intersection = new THREE.Vector3()
  private _worldPosition = new THREE.Vector3()
  private _inverseMatrix = new THREE.Matrix4()

  private _domElement: any
  private _camera: any
  private _snapConfig: SnapConfig
  private _scene: any
  private _snapIndicator: THREE.Mesh | null = null

  public _model: Model | undefined | null
  public _models: Model[] = []  // multi-drag
  private _selected: any
  private _hovered: any
  private _lockHeight = true

  enabled = true

  constructor(_camera: any, _domElement: any, snapConfig?: SnapConfig, scene?: any) {
    super()
    this._domElement = _domElement
    this._domElement.style.touchAction = 'none'
    this._domElement.dragControl = this
    this._camera = _camera
    this._snapConfig = snapConfig || { gridSize: 10, enabled: false }
    this._scene = scene
    this._selected = undefined
    this._hovered = undefined
    this.activate()
    this.enabled = true
  }

  public lockHeight(lock: boolean) {
    this._lockHeight = lock
  }

  public setSnapConfig(config: SnapConfig) {
    this._snapConfig = config
  }

  public setMultiModels(models: Model[]) {
    this._models = models
    if (models.length > 0) {
      this._model = models[0]
    }
  }

  public clearMultiModels() {
    this._models = []
  }

  public dispose() {
    this.deatctivate()
    this.hideSnapIndicator()
  }

  private activate() {
    this._domElement.addEventListener('pointermove', onPointerMove)
    this._domElement.addEventListener('pointerdown', onPointerDown)
    this._domElement.addEventListener('pointerup', onPointerCancel)
    this._domElement.addEventListener('pointerleave', onPointerCancel)
  }

  private deatctivate() {
    this._domElement.removeEventListener('pointermove', onPointerMove)
    this._domElement.removeEventListener('pointerdown', onPointerDown)
    this._domElement.removeEventListener('pointerup', onPointerCancel)
    this._domElement.removeEventListener('pointerleave', onPointerCancel)
    this._domElement.style.cursor = ''
  }

  private snapPosition(pos: THREE.Vector3): THREE.Vector3 {
    if (!this._snapConfig.enabled) return pos

    const gs = this._snapConfig.gridSize
    const snapped = new THREE.Vector3(
      Math.round(pos.x / gs) * gs,
      pos.y,
      Math.round(pos.z / gs) * gs
    )

    // 模型间对齐吸附
    if (this._scene && this._model) {
      const alignPoint = this.findAlignmentSnap(snapped, this._model.getModelId)
      if (alignPoint) return alignPoint
    }

    return snapped
  }

  /** 查找与场景中其他模型的边缘对齐点 */
  private findAlignmentSnap(pos: THREE.Vector3, excludeModelId: string): THREE.Vector3 | null {
    const threshold = 15
    let bestSnap: THREE.Vector3 | null = null
    let bestDist = Infinity

    for (const child of this._scene.children) {
      if (!child.userData || child.userData.modelId === excludeModelId) continue
      if (child.userData.type !== 'targetObj') continue

      const box3 = new THREE.Box3().setFromObject(child)
      const size = new THREE.Vector3()
      box3.getSize(size)
      const center = child.position.clone()
      const halfW = size.x / 2
      const halfD = size.z / 2

      const edges = [
        new THREE.Vector3(center.x + halfW, center.y, center.z),
        new THREE.Vector3(center.x - halfW, center.y, center.z),
        new THREE.Vector3(center.x, center.y, center.z + halfD),
        new THREE.Vector3(center.x, center.y, center.z - halfD)
      ]

      for (const edge of edges) {
        const dist2d = new THREE.Vector2(pos.x - edge.x, pos.z - edge.z).length()
        if (dist2d < threshold && dist2d < bestDist) {
          bestDist = dist2d
          bestSnap = new THREE.Vector3(edge.x, pos.y, edge.z)
        }
      }

      // 中心对齐
      const centerDist2d = new THREE.Vector2(pos.x - center.x, pos.z - center.z).length()
      if (centerDist2d < threshold && centerDist2d < bestDist) {
        bestDist = centerDist2d
        bestSnap = new THREE.Vector3(center.x, pos.y, center.z)
      }
    }

    return bestSnap
  }

  private showSnapIndicator(pos: THREE.Vector3) {
    if (!this._scene) return
    if (!this._snapIndicator) {
      const geo = new THREE.RingGeometry(8, 10, 32)
      const mat = new THREE.MeshBasicMaterial({ color: 0x00d4ff, side: THREE.DoubleSide, depthTest: false })
      this._snapIndicator = new THREE.Mesh(geo, mat)
      this._snapIndicator.rotation.x = -Math.PI / 2
      this._snapIndicator.renderOrder = 999
      this._scene.add(this._snapIndicator)
    }
    this._snapIndicator.position.copy(pos)
    this._snapIndicator.position.y += 0.5
    this._snapIndicator.visible = true
  }

  private hideSnapIndicator() {
    if (this._snapIndicator) {
      this._snapIndicator.visible = false
    }
  }

  public onPointerMove(event: PointerEvent) {
    if (this.enabled === false || !this._model) return
    this.updatePointer(event)
    this._raycaster.setFromCamera(this._pointer, this._camera)

    if (this._selected) {
      if (this._raycaster.ray.intersectPlane(this._plane, this._intersection)) {
        if (this._models.length > 1) {
          const currentModel = this._model!
          const oldPos = currentModel.rootObject.position.clone()
          const newPos = this._intersection.clone().sub(this._offset).applyMatrix4(this._inverseMatrix)
          if (this._lockHeight) newPos.y = oldPos.y

          const snapped = this.snapPosition(newPos)
          if (this._snapConfig.enabled) {
            this.showSnapIndicator(snapped)
          }

          const delta = new THREE.Vector3().subVectors(snapped, oldPos)
          this._models.forEach(m => {
            if (m.getModelId === currentModel.getModelId) {
              m.rootObject.position.copy(snapped)
            } else {
              m.rootObject.position.x += delta.x
              m.rootObject.position.z += delta.z
            }
          })
        } else {
          const oldY = this._model.rootObject.position.y
          let newPos = this._intersection.clone().sub(this._offset).applyMatrix4(this._inverseMatrix)
          newPos = this.snapPosition(newPos)
          if (this._lockHeight) newPos.y = oldY

          this._model.rootObject.position.copy(newPos)
          if (this._snapConfig.enabled) {
            this.showSnapIndicator(newPos)
          }
        }
      }
      this.dispatchEvent({ type: 'drag', object: this._model })
    }

    if (event.pointerType === 'mouse' || event.pointerType === 'pen') {
      const _intersections = [] as any
      this._raycaster.setFromCamera(this._pointer, this._camera)
      this._raycaster.intersectObjects([this._model.rootObject], true, _intersections)
      if (_intersections.length > 0) {
        const object = _intersections[0].object
        this._plane.setFromNormalAndCoplanarPoint(
          this._camera.getWorldDirection(this._plane.normal),
          this._worldPosition.setFromMatrixPosition(object.matrixWorld)
        )
        if (this._hovered && this._hovered !== object) {
          this.dispatchEvent({ type: 'hoveroff', object: this._hovered })
          this._domElement.style.cursor = 'auto'
          this._hovered = undefined
        }
        if (this._hovered !== object) {
          this.dispatchEvent({ type: 'hoveron', object: object })
          this._domElement.style.cursor = 'pointer'
          this._hovered = object
        }
      } else {
        if (this._hovered) {
          this.dispatchEvent({ type: 'hoveroff', object: this._hovered })
          this._domElement.style.cursor = 'auto'
          this._hovered = undefined
        }
      }
    }
  }

  public onPointerDown(event: PointerEvent) {
    if (this.enabled === false || !this._model) return
    this.updatePointer(event)

    const _intersections = [] as any
    this._raycaster.setFromCamera(this._pointer, this._camera)
    this._raycaster.intersectObjects([this._model.rootObject], true, _intersections)
    if (_intersections.length > 0) {
      this._selected = true
      this._plane.setFromNormalAndCoplanarPoint(
        this._camera.getWorldDirection(this._plane.normal),
        this._worldPosition.setFromMatrixPosition(this._model.rootObject.matrixWorld)
      )
      if (this._raycaster.ray.intersectPlane(this._plane, this._intersection)) {
        this._inverseMatrix.copy(this._model.rootObject.parent!.matrixWorld).invert()
        this._offset.copy(this._intersection).sub(
          this._worldPosition.setFromMatrixPosition(this._model.rootObject.matrixWorld)
        )
      }
      this._domElement.style.cursor = 'move'
      this.dispatchEvent({ type: 'dragstart', object: this._model })
    }
  }

  public onPointerCancel() {
    if (this.enabled === false || !this._model) return
    if (this._selected) {
      this.dispatchEvent({ type: 'dragend', object: this._model })
      this._selected = false
      this.hideSnapIndicator()
    }
    this._domElement.style.cursor = this._hovered ? 'pointer' : 'auto'
  }

  public updatePointer(event: PointerEvent) {
    const rect = this._domElement.getBoundingClientRect()
    this._pointer.x = (event.clientX - rect.left) / rect.width * 2 - 1
    this._pointer.y = -(event.clientY - rect.top) / rect.height * 2 + 1
  }
}

function onPointerMove(event: PointerEvent) {
  const el = event.target as any
  if (el && el.dragControl) {
    el.dragControl.onPointerMove(event)
  }
}

function onPointerDown(event: PointerEvent) {
  const el = event.target as any
  if (el && el.dragControl) {
    el.dragControl.onPointerDown(event)
  }
}

function onPointerCancel(event: PointerEvent) {
  const el = event.target as any
  if (el && el.dragControl) {
    el.dragControl.onPointerCancel()
  }
}
