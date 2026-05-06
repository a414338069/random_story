import { ref, watch, onUnmounted, type Ref, type ComputedRef } from 'vue'

type MaybeRef<T> = Ref<T> | ComputedRef<T> | (() => T)

function toGetter<T>(source: MaybeRef<T>): () => T {
  if (typeof source === 'function') return source
  return () => (source as Ref<T>).value
}

export function useAnimatedNumber(
  source: MaybeRef<number>,
  duration = 600,
  formatter?: (n: number) => string,
) {
  const get = toGetter(source)
  const displayValue = ref(get())
  const direction = ref<'up' | 'down' | 'none'>('none')
  let rafId: number | null = null
  let startTime: number | null = null
  let fromValue = get()

  function animate() {
    if (rafId !== null) {
      cancelAnimationFrame(rafId)
    }

    const toValue = get()
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

  watch(() => get(), animate)

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
