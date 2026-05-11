<template>
  <div ref="containerRef" class="monitor-scene"></div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import type { MonitorDeviceStatus, MonitorYieldHeat } from '@/services/monitorService'

const props = defineProps<{
  devices: MonitorDeviceStatus[]
  heatmap: MonitorYieldHeat[]
}>()

const containerRef = ref<HTMLElement>()
let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let controls: OrbitControls | null = null
let frameId = 0
let deviceGroup: THREE.Group | null = null
let heatGroup: THREE.Group | null = null

const statusColor: Record<string, number> = {
  online: 0x39d98a,
  offline: 0x667085,
  warning: 0xffb020,
  critical: 0xff4d4f
}

function initScene() {
  const container = containerRef.value
  if (!container) return

  scene = new THREE.Scene()
  scene.fog = new THREE.Fog(0x06101a, 260, 760)

  camera = new THREE.PerspectiveCamera(42, container.clientWidth / container.clientHeight, 0.1, 2000)
  camera.position.set(220, 250, 240)
  camera.lookAt(0, 0, 0)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(container.clientWidth, container.clientHeight)
  renderer.setClearColor(0x06101a, 0)
  container.appendChild(renderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.enablePan = false
  controls.autoRotate = true
  controls.autoRotateSpeed = 0.35
  controls.minDistance = 180
  controls.maxDistance = 560
  controls.target.set(0, 0, 0)

  const ambient = new THREE.AmbientLight(0x9fb8c8, 1.6)
  const sun = new THREE.DirectionalLight(0xffffff, 1.8)
  sun.position.set(120, 240, 90)
  scene.add(ambient, sun)

  buildPark()
  rebuildDynamicLayers()
  animate()
}

function buildPark() {
  if (!scene) return
  const groundMaterial = new THREE.MeshStandardMaterial({
    color: 0x1f4b35,
    roughness: 0.82,
    metalness: 0.05
  })
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(330, 230, 1, 1), groundMaterial)
  ground.rotation.x = -Math.PI / 2
  ground.position.y = -0.2
  scene.add(ground)

  const roadMaterial = new THREE.MeshStandardMaterial({ color: 0x2a3440, roughness: 0.85 })
  const road = new THREE.Mesh(new THREE.BoxGeometry(320, 0.18, 12), roadMaterial)
  road.position.set(0, 0.05, 0)
  scene.add(road)
  const roadCross = new THREE.Mesh(new THREE.BoxGeometry(12, 0.2, 210), roadMaterial)
  roadCross.position.set(-46, 0.06, 0)
  scene.add(roadCross)

  const greenhouseMaterial = new THREE.MeshPhysicalMaterial({
    color: 0xa8e6cf,
    roughness: 0.18,
    metalness: 0.1,
    transparent: true,
    opacity: 0.62
  })
  ;[
    [-100, 0, -62],
    [-36, 0, -62],
    [28, 0, -62],
    [-100, 0, 62],
    [-36, 0, 62],
    [28, 0, 62]
  ].forEach((pos) => {
    const house = new THREE.Group()
    const body = new THREE.Mesh(new THREE.BoxGeometry(46, 18, 28), greenhouseMaterial)
    body.position.y = 9
    const roof = new THREE.Mesh(new THREE.CylinderGeometry(14, 14, 46, 24, 1, true, 0, Math.PI), greenhouseMaterial)
    roof.rotation.z = Math.PI / 2
    roof.position.y = 18
    house.add(body, roof)
    house.position.set(pos[0], pos[1], pos[2])
    scene?.add(house)
  })

  const fieldColors = [0x6baa45, 0x8ab94f, 0xc4a64b, 0x5a9f73]
  for (let i = 0; i < 4; i++) {
    const field = new THREE.Mesh(
      new THREE.BoxGeometry(50, 0.35, 54),
      new THREE.MeshStandardMaterial({ color: fieldColors[i], roughness: 0.9 })
    )
    field.position.set(88 + (i % 2) * 58, 0.08, -34 + Math.floor(i / 2) * 72)
    scene.add(field)
  }

  const tower = new THREE.Mesh(
    new THREE.CylinderGeometry(5, 7, 46, 24),
    new THREE.MeshStandardMaterial({ color: 0x6e7f90, roughness: 0.5, metalness: 0.45 })
  )
  tower.position.set(-150, 23, 68)
  scene.add(tower)

  const waterTop = new THREE.Mesh(
    new THREE.CylinderGeometry(13, 13, 7, 24),
    new THREE.MeshStandardMaterial({ color: 0x4fb4dd, roughness: 0.35, metalness: 0.25 })
  )
  waterTop.position.set(-150, 49, 68)
  scene.add(waterTop)
}

function rebuildDynamicLayers() {
  if (!scene) return
  if (deviceGroup) {
    scene.remove(deviceGroup)
    disposeGroup(deviceGroup)
  }
  if (heatGroup) {
    scene.remove(heatGroup)
    disposeGroup(heatGroup)
  }
  deviceGroup = new THREE.Group()
  heatGroup = new THREE.Group()

  const positions = [
    [-116, 22, -82],
    [18, 22, -82],
    [-154, 58, 68],
    [-42, 14, 10],
    [134, 14, -62],
    [146, 14, 76],
    [-130, 22, 0],
    [68, 22, 88]
  ]

  props.devices.forEach((device, index) => {
    const color = statusColor[device.status] ?? statusColor.offline
    const node = new THREE.Group()
    const beacon = new THREE.Mesh(
      new THREE.SphereGeometry(3.4, 24, 24),
      new THREE.MeshStandardMaterial({
        color,
        emissive: color,
        emissiveIntensity: 0.65,
        roughness: 0.25
      })
    )
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(7, 0.36, 12, 36),
      new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.72 })
    )
    ring.rotation.x = Math.PI / 2
    ring.userData.spin = 0.01 + index * 0.001
    node.add(beacon, ring)
    const pos = positions[index % positions.length]
    node.position.set(pos[0], pos[1], pos[2])
    deviceGroup?.add(node)
  })

  props.heatmap.forEach((item) => {
    const normalized = Math.max(0, Math.min(1, item.value / 100))
    const color = new THREE.Color().setHSL(0.36 - normalized * 0.2, 0.62, 0.42)
    const cell = new THREE.Mesh(
      new THREE.BoxGeometry(13, 0.5 + normalized * 7, 13),
      new THREE.MeshStandardMaterial({
        color,
        emissive: color,
        emissiveIntensity: 0.16,
        transparent: true,
        opacity: 0.82
      })
    )
    cell.position.set(72 + item.x * 15, 0.3 + normalized * 3.5, -82 + item.y * 15)
    heatGroup?.add(cell)
  })

  scene.add(heatGroup, deviceGroup)
}

function animate() {
  if (!renderer || !scene || !camera) return
  controls?.update()
  deviceGroup?.children.forEach((node) => {
    node.children.forEach((child) => {
      if (child instanceof THREE.Mesh && child.geometry instanceof THREE.TorusGeometry) {
        child.rotation.z += child.userData.spin || 0.01
      }
    })
  })
  renderer.render(scene, camera)
  frameId = requestAnimationFrame(animate)
}

function resize() {
  const container = containerRef.value
  if (!container || !renderer || !camera) return
  camera.aspect = container.clientWidth / container.clientHeight
  camera.updateProjectionMatrix()
  renderer.setSize(container.clientWidth, container.clientHeight)
}

function disposeGroup(group: THREE.Group) {
  group.traverse((child) => {
    if (child instanceof THREE.Mesh) {
      child.geometry.dispose()
      if (Array.isArray(child.material)) {
        child.material.forEach((material) => material.dispose())
      } else {
        child.material.dispose()
      }
    }
  })
}

watch(() => [props.devices, props.heatmap], rebuildDynamicLayers, { deep: true })

onMounted(() => {
  initScene()
  window.addEventListener('resize', resize)
})

onUnmounted(() => {
  cancelAnimationFrame(frameId)
  window.removeEventListener('resize', resize)
  controls?.dispose()
  if (scene) {
    scene.traverse((child) => {
      if (child instanceof THREE.Mesh) {
        child.geometry.dispose()
        if (Array.isArray(child.material)) {
          child.material.forEach((material) => material.dispose())
        } else {
          child.material.dispose()
        }
      }
    })
  }
  renderer?.dispose()
  renderer?.domElement.parentElement?.removeChild(renderer.domElement)
})
</script>

<style scoped>
.monitor-scene {
  width: 100%;
  height: 100%;
  min-height: 300px;
  background:
    radial-gradient(circle at 50% 42%, rgba(57, 217, 138, 0.16), transparent 32%),
    linear-gradient(180deg, rgba(8, 22, 32, 0.98), rgba(4, 10, 18, 0.98));
  overflow: hidden;
}
</style>
