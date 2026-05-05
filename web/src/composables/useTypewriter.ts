import { ref } from 'vue'

/** Punctuation pause durations (ms) */
const PUNCT_PAUSE: Record<string, number> = {
  '。': 160,
  '！': 200,
  '？': 200,
  '，': 80,
  '；': 120,
  '：': 120,
  '…': 100,
  '—': 80,
  '.': 160,
  '!': 200,
  '?': 200,
  ',': 80,
  ';': 120,
  ':': 120,
}

export function useTypewriter() {
  const displayed = ref('')
  const isTyping = ref(false)
  const isComplete = ref(false)

  let timerId: ReturnType<typeof setTimeout> | null = null
  let fullText = ''
  let currentIndex = 0
  let baseInterval = 0
  let resolvePromise: (() => void) | null = null

  function typeText(text: string, charsPerSec: number = 30): Promise<void> {
    return new Promise((resolve) => {
      cancel()
      fullText = text
      currentIndex = 0
      displayed.value = ''
      isTyping.value = true
      isComplete.value = false
      baseInterval = 1000 / charsPerSec
      resolvePromise = resolve

      scheduleNext()
    })
  }

  function scheduleNext() {
    if (!isTyping.value) return

    const char = fullText[currentIndex]
    const pause = PUNCT_PAUSE[char] ?? baseInterval

    timerId = setTimeout(() => {
      currentIndex++
      displayed.value = fullText.slice(0, currentIndex)

      if (currentIndex >= fullText.length) {
        isTyping.value = false
        isComplete.value = true
        timerId = null
        resolvePromise?.()
        resolvePromise = null
        return
      }

      scheduleNext()
    }, pause)
  }

  function skipToEnd() {
    if (!isTyping.value) return
    displayed.value = fullText
    isTyping.value = false
    isComplete.value = true
    if (timerId !== null) {
      clearTimeout(timerId)
      timerId = null
    }
    resolvePromise?.()
    resolvePromise = null
  }

  function cancel() {
    if (timerId !== null) {
      clearTimeout(timerId)
      timerId = null
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
