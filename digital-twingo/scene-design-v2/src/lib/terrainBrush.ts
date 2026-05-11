/**
 * 地形纹理刷 — 在地面上绘制不同纹理（泥土、水泥、草地等）
 */
import * as THREE from 'three'

export interface BrushConfig {
  size: number
  opacity: number
  hardness: number
  texture: string
}

export interface GroundTextureLayer {
  name: string
  texture: THREE.Texture
  maskCanvas: HTMLCanvasElement
  maskCtx: CanvasRenderingContext2D
  maskTexture: THREE.CanvasTexture
}

export class TerrainBrush {
  private groundPlane: THREE.Mesh | null = null
  private layers: GroundTextureLayer[] = []
  private brushConfig: BrushConfig = {
    size: 60,
    opacity: 0.7,
    hardness: 0.5,
    texture: 'grass'
  }
  private uvData: Uint8ClampedArray | null = null
  private compositeCanvas: HTMLCanvasElement
  private compositeCtx: CanvasRenderingContext2D
  private compositeTexture: THREE.CanvasTexture
  private resolution = 1024
  private isPainting = false

  public onLayerChange: (() => void) | null = null

  constructor() {
    this.compositeCanvas = document.createElement('canvas')
    this.compositeCanvas.width = this.resolution
    this.compositeCanvas.height = this.resolution
    this.compositeCtx = this.compositeCanvas.getContext('2d')!
    this.compositeTexture = new THREE.CanvasTexture(this.compositeCanvas)
    this.compositeTexture.wrapS = this.compositeTexture.wrapT = THREE.RepeatWrapping
    this.compositeTexture.repeat.set(4, 4)
    this.compositeTexture.colorSpace = THREE.SRGBColorSpace
  }

  /** 绑定地面平面 */
  bindGround(groundPlane: THREE.Mesh) {
    this.groundPlane = groundPlane
    this.applyCompositeToGround()
  }

  /** 获取画布纹理(用于 UI 预览) */
  getCompositeCanvas(): HTMLCanvasElement {
    return this.compositeCanvas
  }

  /** 获取合成的材质纹理 */
  getTexture(): THREE.CanvasTexture {
    return this.compositeTexture
  }

  /** 添加纹理图层 */
  addLayer(name: string, textureUrl: string, baseOpacity = 1): Promise<GroundTextureLayer> {
    return new Promise((resolve, reject) => {
      const loader = new THREE.TextureLoader()
      loader.load(textureUrl,
        (tex) => {
          tex.wrapS = tex.wrapT = THREE.RepeatWrapping
          tex.repeat.set(4, 4)
          tex.colorSpace = THREE.SRGBColorSpace

          const canvas = document.createElement('canvas')
          canvas.width = this.resolution
          canvas.height = this.resolution
          const ctx = canvas.getContext('2d')!

          if (baseOpacity > 0) {
            ctx.fillStyle = `rgba(255,255,255,${baseOpacity})`
            ctx.fillRect(0, 0, canvas.width, canvas.height)
          }

          const canvasTex = new THREE.CanvasTexture(canvas)
          canvasTex.wrapS = canvasTex.wrapT = THREE.RepeatWrapping

          const layer: GroundTextureLayer = { name, texture: tex, maskCanvas: canvas, maskCtx: ctx, maskTexture: canvasTex }
          this.layers.push(layer)
          this.recomposite()
          this.onLayerChange?.()
          resolve(layer)
        },
        undefined,
        () => reject(new Error(`Failed to load texture: ${textureUrl}`))
      )
    })
  }

  /** 移除图层 */
  removeLayer(name: string) {
    const idx = this.layers.findIndex(l => l.name === name)
    if (idx >= 0) {
      this.layers.splice(idx, 1)
      this.recomposite()
      this.onLayerChange?.()
    }
  }

  /** 设置笔刷配置 */
  setBrushConfig(config: Partial<BrushConfig>) {
    Object.assign(this.brushConfig, config)
  }

  getBrushConfig(): BrushConfig {
    return { ...this.brushConfig }
  }

  /** 开始绘制 */
  beginPaint() {
    this.isPainting = true
  }

  /** 结束绘制 */
  endPaint() {
    this.isPainting = false
    this.applyCompositeToGround()
  }

  /** 在地面上绘制一个笔触 */
  paintStroke(uvX: number, uvY: number, layerName: string) {
    if (!this.isPainting) return
    const layer = this.layers.find(l => l.name === layerName)
    if (!layer) return

    const cx = uvX * this.resolution
    const cy = (1 - uvY) * this.resolution
    const radius = (this.brushConfig.size / 1000) * this.resolution

    const gradient = layer.maskCtx.createRadialGradient(cx, cy, 0, cx, cy, radius)
    const alpha = this.brushConfig.opacity
    gradient.addColorStop(0, `rgba(255,255,255,${alpha})`)
    gradient.addColorStop(this.brushConfig.hardness, `rgba(255,255,255,${alpha * 0.5})`)
    gradient.addColorStop(1, 'rgba(255,255,255,0)')

    layer.maskCtx.globalCompositeOperation = 'source-over'
    layer.maskCtx.fillStyle = gradient
    layer.maskCtx.beginPath()
    layer.maskCtx.arc(cx, cy, radius, 0, Math.PI * 2)
    layer.maskCtx.fill()

    layer.maskTexture.needsUpdate = true
    this.recomposite()
  }

  /** 擦除某个图层的笔触 */
  eraseStroke(uvX: number, uvY: number, layerName: string) {
    const layer = this.layers.find(l => l.name === layerName)
    if (!layer) return

    const cx = uvX * this.resolution
    const cy = (1 - uvY) * this.resolution
    const radius = (this.brushConfig.size / 1000) * this.resolution

    layer.maskCtx.globalCompositeOperation = 'destination-out'
    layer.maskCtx.fillStyle = 'rgba(0,0,0,1)'
    layer.maskCtx.beginPath()
    layer.maskCtx.arc(cx, cy, radius, 0, Math.PI * 2)
    layer.maskCtx.fill()

    layer.maskTexture.needsUpdate = true
    this.recomposite()
  }

  /** 从 UV 坐标获取地面上的世界坐标 */
  uvToWorldPosition(uvX: number, uvY: number): THREE.Vector3 | null {
    if (!this.groundPlane) return null
    const w = (this.groundPlane.geometry as THREE.PlaneGeometry).parameters.width || 1000
    const d = (this.groundPlane.geometry as THREE.PlaneGeometry).parameters.height || 1000
    return new THREE.Vector3((uvX - 0.5) * w, 0, (uvY - 0.5) * d)
  }

  /** 将世界坐标转换为 UV */
  worldToUV(worldX: number, worldZ: number): { u: number; v: number } | null {
    if (!this.groundPlane) return null
    const w = (this.groundPlane.geometry as THREE.PlaneGeometry).parameters.width || 1000
    const d = (this.groundPlane.geometry as THREE.PlaneGeometry).parameters.height || 1000
    return {
      u: worldX / w + 0.5,
      v: worldZ / d + 0.5
    }
  }

  /** 重新合成所有图层 */
  private recomposite() {
    const ctx = this.compositeCtx
    ctx.clearRect(0, 0, this.resolution, this.resolution)

    // 画基底色
    ctx.fillStyle = '#886644'
    ctx.fillRect(0, 0, this.resolution, this.resolution)

    for (const layer of this.layers) {
      ctx.save()
      ctx.globalAlpha = 1
      // 先绘制纹理
      const pattern = ctx.createPattern(layer.maskTexture.image as any, 'repeat')
      if (pattern) {
        ctx.fillStyle = pattern
        ctx.fillRect(0, 0, this.resolution, this.resolution)
      }
      // 使用遮罩
      ctx.globalCompositeOperation = 'destination-in'
      ctx.drawImage(layer.maskCanvas, 0, 0)
      ctx.restore()

      // 合并到结果
      ctx.save()
      ctx.globalAlpha = 1
      ctx.globalCompositeOperation = 'source-over'
      ctx.drawImage(layer.maskCanvas, 0, 0)
      ctx.restore()
    }

    this.compositeTexture.needsUpdate = true
  }

  /** 将合成纹理应用到地面 Plane */
  private applyCompositeToGround() {
    if (!this.groundPlane) return
    const mat = this.groundPlane.material as THREE.MeshStandardMaterial
    mat.map = this.compositeTexture
    mat.color.set('#ffffff')
    mat.needsUpdate = true
  }

  /** 保存所有图层数据为 JSON */
  saveLayersData(): any[] {
    return this.layers.map(l => ({
      name: l.name,
      maskDataUrl: l.maskCanvas.toDataURL()
    }))
  }

  /** 从 JSON 恢复图层 */
  async restoreLayersData(data: any[]): Promise<void> {
    this.layers = []
    for (const d of data) {
      const canvas = document.createElement('canvas')
      canvas.width = this.resolution
      canvas.height = this.resolution
      const ctx = canvas.getContext('2d')!

      await new Promise<void>((resolve) => {
        const img = new Image()
        img.onload = () => {
          ctx.drawImage(img, 0, 0)
          resolve()
        }
        img.src = d.maskDataUrl
      })

      const canvasTex = new THREE.CanvasTexture(canvas)
      canvasTex.wrapS = canvasTex.wrapT = THREE.RepeatWrapping

      this.layers.push({
        name: d.name,
        texture: new THREE.Texture(),
        maskCanvas: canvas,
        maskCtx: ctx,
        maskTexture: canvasTex
      })
    }
    this.recomposite()
    this.applyCompositeToGround()
  }

  dispose() {
    this.layers.forEach(l => {
      l.texture.dispose()
      l.maskTexture.dispose()
    })
    this.layers = []
    this.compositeTexture.dispose()
  }
}
