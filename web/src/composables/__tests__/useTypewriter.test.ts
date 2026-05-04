import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

describe('useTypewriter', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should be importable', async () => {
    const mod = await import('@/composables/useTypewriter')
    expect(mod.useTypewriter).toBeDefined()
  })

  it('should have correct initial state', async () => {
    const { useTypewriter } = await import('@/composables/useTypewriter')
    const tw = useTypewriter()
    expect(tw.displayed.value).toBe('')
    expect(tw.isTyping.value).toBe(false)
    expect(tw.isComplete.value).toBe(false)
  })

  it('should support skipToEnd after not starting', async () => {
    const { useTypewriter } = await import('@/composables/useTypewriter')
    const tw = useTypewriter()
    tw.skipToEnd()
    expect(tw.displayed.value).toBe('')
  })
})
