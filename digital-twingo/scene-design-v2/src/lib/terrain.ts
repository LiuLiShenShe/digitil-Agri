/**
 * 地形导入工具 — 支持高度图、GeoJSON、DEM 高程数据生成地形 Mesh
 */
import * as THREE from 'three'

export type TerrainSource = 'heightmap' | 'geojson' | 'dem'

export interface TerrainOptions {
  width?: number
  depth?: number
  segments?: number
  heightScale?: number
  colorLow?: string
  colorHigh?: string
  texture?: string
  wireframe?: boolean
}

const defaultOptions: TerrainOptions = {
  width: 1000,
  depth: 1000,
  segments: 128,
  heightScale: 80,
  colorLow: '#336633',
  colorHigh: '#88cc44',
  wireframe: false
}

export class TerrainImporter {
  private options: TerrainOptions
  public mesh: THREE.Mesh | null = null
  private textureLoader = new THREE.TextureLoader()

  constructor(options: TerrainOptions = {}) {
    this.options = { ...defaultOptions, ...options }
  }

  /** 从高度图图片生成地形 */
  async loadHeightmap(imageUrl: string, onProgress?: (pct: number) => void): Promise<THREE.Mesh> {
    const width = this.options.width ?? 1000
    const depth = this.options.depth ?? 1000
    const segments = this.options.segments ?? 128
    const heightScale = this.options.heightScale ?? 80
    const colorLow = this.options.colorLow ?? '#336633'
    const colorHigh = this.options.colorHigh ?? '#88cc44'
    const texture = this.options.texture
    const wireframe = this.options.wireframe ?? false

    const heightData = await this.loadImageData(imageUrl, onProgress)
    const geometry = new THREE.PlaneGeometry(width, depth, segments, segments)
    geometry.rotateX(-Math.PI / 2)

    const positions = geometry.attributes.position
    for (let i = 0; i < positions.count; i++) {
      const x = i % (segments + 1)
      const y = Math.floor(i / (segments + 1))
      const px = Math.floor((x / segments) * (heightData.length - 1))
      const py = Math.floor((y / segments) * (heightData.length - 1))
      const h = heightData[px] !== undefined ? heightData[px][py] * heightScale : 0
      positions.setY(i, h)
    }
    geometry.computeVertexNormals()

    let material: THREE.Material
    if (texture) {
      const tex = this.textureLoader.load(texture)
      tex.wrapS = tex.wrapT = THREE.RepeatWrapping
      tex.repeat.set(4, 4)
      material = new THREE.MeshStandardMaterial({ map: tex, wireframe })
    } else {
      this.applyVertexColors(geometry, colorLow, colorHigh, heightScale)
      material = new THREE.MeshStandardMaterial({ vertexColors: true, wireframe, flatShading: false })
    }

    this.mesh = new THREE.Mesh(geometry, material)
    this.mesh.receiveShadow = true
    this.mesh.userData.type = 'terrain'
    this.mesh.userData.terrainSource = 'heightmap'
    return this.mesh
  }

  /** 从 GeoJSON 生成地形（含等高线解析） */
  async loadGeoJSON(geojsonUrl: string, onProgress?: (pct: number) => void): Promise<THREE.Mesh> {
    const response = await fetch(geojsonUrl)
    const geojson = await response.json()
    onProgress?.(100)
    return this.buildFromGeoJSON(geojson)
  }

  /** 从内存中的 GeoJSON 对象生成地形 */
  buildFromGeoJSON(geojson: any): THREE.Mesh {
    const width = this.options.width ?? 1000
    const depth = this.options.depth ?? 1000
    const segments = this.options.segments ?? 128
    const heightScale = this.options.heightScale ?? 80
    const colorLow = this.options.colorLow ?? '#336633'
    const colorHigh = this.options.colorHigh ?? '#88cc44'
    const wireframe = this.options.wireframe ?? false
    const geometry = new THREE.PlaneGeometry(width, depth, segments, segments)
    geometry.rotateX(-Math.PI / 2)

    const points: { x: number; z: number; elevation: number }[] = []
    const extractPoints = (obj: any) => {
      if (!obj) return
      if (obj.type === 'FeatureCollection' && Array.isArray(obj.features)) {
        obj.features.forEach((f: any) => extractPoints(f))
      } else if (obj.type === 'Feature' && obj.geometry) {
        extractPoints(obj.geometry)
      } else if (obj.type === 'Point' && obj.coordinates) {
        points.push({ x: obj.coordinates[0], z: obj.coordinates[1], elevation: obj.coordinates[2] || 0 })
      } else if (obj.type === 'LineString' && obj.coordinates) {
        obj.coordinates.forEach((c: number[]) => {
          points.push({ x: c[0], z: c[1], elevation: c[2] || 0 })
        })
      } else if (obj.type === 'MultiPoint' && obj.coordinates) {
        obj.coordinates.forEach((c: number[]) => {
          points.push({ x: c[0], z: c[1], elevation: c[2] || 0 })
        })
      }
    }
    extractPoints(geojson)

    const positions = geometry.attributes.position
    for (let i = 0; i < positions.count; i++) {
      const px = positions.getX(i)
      const pz = positions.getZ(i)
      let h = 0
      if (points.length > 0) {
        h = this.interpolateElevation(px, pz, points) * heightScale
      }
      positions.setY(i, h)
    }
    geometry.computeVertexNormals()

    this.applyVertexColors(geometry, colorLow, colorHigh, heightScale)
    const material = new THREE.MeshStandardMaterial({ vertexColors: true, wireframe })
    this.mesh = new THREE.Mesh(geometry, material)
    this.mesh.receiveShadow = true
    this.mesh.userData.type = 'terrain'
    this.mesh.userData.terrainSource = 'geojson'
    return this.mesh
  }

  private loadImageData(url: string, onProgress?: (pct: number) => void): Promise<number[][]> {
    return new Promise((resolve, reject) => {
      const img = new Image()
      img.crossOrigin = 'anonymous'
      img.onload = () => {
        const canvas = document.createElement('canvas')
        canvas.width = img.width
        canvas.height = img.height
        const ctx = canvas.getContext('2d')!
        ctx.drawImage(img, 0, 0)
        const imageData = ctx.getImageData(0, 0, img.width, img.height)
        const data: number[][] = []
        for (let y = 0; y < img.height; y++) {
          data[y] = []
          for (let x = 0; x < img.width; x++) {
            const idx = (y * img.width + x) * 4
            const r = imageData.data[idx]
            const g = imageData.data[idx + 1]
            const b = imageData.data[idx + 2]
            data[y][x] = (r * 0.299 + g * 0.587 + b * 0.114) / 255
          }
        }
        onProgress?.(100)
        resolve(data)
      }
      img.onerror = () => reject(new Error(`Failed to load heightmap: ${url}`))
      img.onprogress = (e: any) => {
        if (e.lengthComputable) onProgress?.(Math.round((e.loaded / e.total) * 100))
      }
      img.src = url
    })
  }

  private interpolateElevation(px: number, pz: number, points: { x: number; z: number; elevation: number }[], radius = 100): number {
    let totalWeight = 0
    let weightedSum = 0
    for (const p of points) {
      const dx = px - p.x
      const dz = pz - p.z
      const dist = Math.sqrt(dx * dx + dz * dz)
      if (dist < 1) return p.elevation
      const weight = 1 / (dist * dist)
      weightedSum += p.elevation * weight
      totalWeight += weight
    }
    return totalWeight > 0 ? weightedSum / totalWeight : 0
  }

  private applyVertexColors(geometry: THREE.PlaneGeometry, lowColor: string, highColor: string, heightScale: number): void {
    const low = new THREE.Color(lowColor)
    const high = new THREE.Color(highColor)
    const positions = geometry.attributes.position
    const colors = new Float32Array(positions.count * 3)
    for (let i = 0; i < positions.count; i++) {
      const y = positions.getY(i)
      const t = Math.max(0, Math.min(1, y / heightScale))
      const c = new THREE.Color().copy(low).lerp(high, t)
      colors[i * 3] = c.r
      colors[i * 3 + 1] = c.g
      colors[i * 3 + 2] = c.b
    }
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
  }

  dispose() {
    if (this.mesh) {
      this.mesh.geometry.dispose()
      if (Array.isArray(this.mesh.material)) {
        this.mesh.material.forEach(m => m.dispose())
      } else {
        this.mesh.material.dispose()
      }
      this.mesh = null
    }
  }
}
