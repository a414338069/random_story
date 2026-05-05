import { ref, watch, onUnmounted } from 'vue'

/**
 * 数值动画 composable
 * 当源值变化时，在 600ms 内平滑过渡显示值
 * 返回当前显示值和变化方向（正/负/无）
 */
export function useAnimatedNumber(
  source: () => number,
  duration = 600,
  formatter?: (n: number) => string,
) {
  const displayValue = ref(source())
  const direction = ref<'up' | 'down' | 'none'>('none')
  let rafId: number | null = null
  let startTime: number | null = null
  let fromValue = source()

  function animate() {
    if (rafId !== null) {
      cancelAnimationFrame(rafId)
    }

    const toValue = source()
    fromValue = displayValue.value

    if (fromValue === toValue) {
      direction.value = 'none'
      return
    }

    direction.value = toValue > fromValue ? 'up' : 'down'
    startTime = performance.now()

    function step(now: number) {
      if (startTime === null) return
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)
      // easeOutCubic 缓动
      const eased = 1 - Math.pow(1 - progress, 3)
      displayValue.value = fromValue + (toValue - fromValue) * eased

      if (progress < 1) {
        rafId = requestAnimationFrame(step)
      } else {
        displayValue.value = toValue
        rafId = null
        setTimeout(() => {
          if (direction.value !== 'none') {
            direction.value = 'none'
          }
        }, 400)
      }
    }

    rafId = requestAnimationFrame(step)
  }

  watch(source, animate)

  onUnmounted(() => {
    if (rafId !== null) {
      cancelAnimationFrame(rafId)
    }
  })

  function formatted(): string {
    const val = displayValue.value
    if (formatter) return formatter(val)
    return Number.isInteger(val) ? val.toString() : val.toFixed(0)
  }

  return {
    displayValue,
    direction,
    formatted,
  }
}
