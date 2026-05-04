import { ref } from 'vue'

export function useTypewriter() {
  const displayed = ref('')
  const isTyping = ref(false)
  const isComplete = ref(false)

  let rafId: number | null = null
  let startTime = 0
  let fullText = ''
  let charsPerMs = 0
  let resolvePromise: (() => void) | null = null

  function typeText(text: string, charsPerSec: number = 30): Promise<void> {
    return new Promise((resolve) => {
      cancel()
      fullText = text
      displayed.value = ''
      isTyping.value = true
      isComplete.value = false
      charsPerMs = charsPerSec / 1000
      startTime = performance.now()
      resolvePromise = resolve

      rafId = requestAnimationFrame(tick)
    })
  }

  function tick(now: number) {
    if (!isTyping.value) return

    const elapsed = now - startTime
    const charsToShow = Math.floor(elapsed * charsPerMs)

    if (charsToShow >= fullText.length) {
      displayed.value = fullText
      isTyping.value = false
      isComplete.value = true
      rafId = null
      resolvePromise?.()
      resolvePromise = null
      return
    }

    displayed.value = fullText.slice(0, charsToShow)
    rafId = requestAnimationFrame(tick)
  }

  function skipToEnd() {
    if (!isTyping.value) return
    displayed.value = fullText
    isTyping.value = false
    isComplete.value = true
    if (rafId !== null) {
      cancelAnimationFrame(rafId)
      rafId = null
    }
    resolvePromise?.()
    resolvePromise = null
  }

  function cancel() {
    if (rafId !== null) {
      cancelAnimationFrame(rafId)
      rafId = null
    }
    isTyping.value = false
    resolvePromise = null
  }

  return {
    displayed,
    isTyping,
    isComplete,
    typeText,
    skipToEnd,
    cancel,
  }
}
