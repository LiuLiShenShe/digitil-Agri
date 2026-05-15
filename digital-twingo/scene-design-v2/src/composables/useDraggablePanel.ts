import { computed, onBeforeUnmount, onMounted, reactive, ref, type CSSProperties } from 'vue'

interface DraggablePanelOptions {
  storageKey: string
  initialTop: number
  initialLeft?: number
  initialRight?: number
  width?: number
  margin?: number
  zIndex?: number
}

interface PanelPosition {
  x: number
  y: number
}

let panelLayerSeed = 700

function getStoredPosition(storageKey: string): PanelPosition | null {
  if (typeof window === 'undefined') return null

  try {
    const raw = window.localStorage.getItem(storageKey)
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<PanelPosition>
    if (typeof parsed.x !== 'number' || typeof parsed.y !== 'number') return null
    return { x: parsed.x, y: parsed.y }
  } catch {
    return null
  }
}

function isInteractiveTarget(target: EventTarget | null) {
  return target instanceof Element && Boolean(target.closest(
    'button, [role="button"], input, textarea, select, a, .el-button, .el-select, .el-input, .el-dropdown, .el-switch'
  ))
}

export function useDraggablePanel(options: DraggablePanelOptions) {
  const margin = options.margin ?? 12
  const panelRef = ref<HTMLElement | null>(null)
  const dragging = ref(false)
  const zIndex = ref(options.zIndex ?? panelLayerSeed)
  const dragOffset = reactive({ x: 0, y: 0 })
  let previousUserSelect = ''

  const getDefaultPosition = (): PanelPosition => {
    if (typeof window === 'undefined') {
      return { x: options.initialLeft ?? margin, y: options.initialTop }
    }

    const panelWidth = options.width ?? 360
    const x = options.initialLeft ?? window.innerWidth - (options.initialRight ?? margin) - panelWidth
    return clampPosition(x, options.initialTop, panelWidth, 240)
  }

  const clampPosition = (
    x: number,
    y: number,
    panelWidth = panelRef.value?.getBoundingClientRect().width ?? options.width ?? 360,
    panelHeight = panelRef.value?.getBoundingClientRect().height ?? 240
  ): PanelPosition => {
    if (typeof window === 'undefined') return { x, y }

    const maxX = Math.max(margin, window.innerWidth - panelWidth - margin)
    const maxY = Math.max(margin, window.innerHeight - panelHeight - margin)
    return {
      x: Math.min(Math.max(margin, x), maxX),
      y: Math.min(Math.max(margin, y), maxY)
    }
  }

  const position = reactive<PanelPosition>(getStoredPosition(options.storageKey) ?? getDefaultPosition())

  const panelStyle = computed<CSSProperties>(() => ({
    left: `${position.x}px`,
    top: `${position.y}px`,
    zIndex: zIndex.value
  }))

  function persistPosition() {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(options.storageKey, JSON.stringify(position))
  }

  function bringToFront() {
    panelLayerSeed += 1
    zIndex.value = panelLayerSeed
  }

  function onPointerMove(event: PointerEvent) {
    if (!dragging.value) return
    const next = clampPosition(event.clientX - dragOffset.x, event.clientY - dragOffset.y)
    position.x = next.x
    position.y = next.y
  }

  function stopDrag() {
    if (!dragging.value) return
    dragging.value = false
    if (typeof document !== 'undefined') {
      document.body.style.userSelect = previousUserSelect
    }
    window.removeEventListener('pointermove', onPointerMove)
    persistPosition()
  }

  function startDrag(event: PointerEvent) {
    if ((event.pointerType === 'mouse' && event.button !== 0) || isInteractiveTarget(event.target)) return

    const rect = panelRef.value?.getBoundingClientRect()
    const current = clampPosition(position.x, position.y, rect?.width, rect?.height)
    position.x = current.x
    position.y = current.y
    dragOffset.x = event.clientX - position.x
    dragOffset.y = event.clientY - position.y
    dragging.value = true
    bringToFront()

    if (typeof document !== 'undefined') {
      previousUserSelect = document.body.style.userSelect
      document.body.style.userSelect = 'none'
    }

    event.preventDefault()
    window.addEventListener('pointermove', onPointerMove)
    window.addEventListener('pointerup', stopDrag, { once: true })
    window.addEventListener('pointercancel', stopDrag, { once: true })
  }

  function resetPosition(event?: MouseEvent) {
    if (event && isInteractiveTarget(event.target)) return
    const next = getDefaultPosition()
    position.x = next.x
    position.y = next.y
    bringToFront()
    persistPosition()
  }

  function clampToViewport() {
    const rect = panelRef.value?.getBoundingClientRect()
    const next = clampPosition(position.x, position.y, rect?.width, rect?.height)
    position.x = next.x
    position.y = next.y
    persistPosition()
  }

  onMounted(() => {
    clampToViewport()
    window.addEventListener('resize', clampToViewport)
  })

  onBeforeUnmount(() => {
    window.removeEventListener('resize', clampToViewport)
    window.removeEventListener('pointermove', onPointerMove)
    window.removeEventListener('pointerup', stopDrag)
    window.removeEventListener('pointercancel', stopDrag)
  })

  return {
    panelRef,
    panelStyle,
    dragging,
    startDrag,
    resetPosition,
    bringToFront
  }
}
