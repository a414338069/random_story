import { ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGameState } from './useGameState'
import { useTypewriter } from './useTypewriter'
import { getEvent, chooseOption, endGame } from '@/api/game'
import { FetchError } from '@/api/client'
import type { EventResponse, LoopPhase } from '@/core/types'

export function useGameLoop() {
  const router = useRouter()
  const { sessionId, phase, update, score, ending, grade, gameState } = useGameState()
  const typewriter = useTypewriter()

  const currentEvent = ref<EventResponse | null>(null)
  const aftermath = ref<{ cultivation_change: number; age_advance: number } | null>(null)
  const error = ref<string | null>(null)
  const retryCount = ref(0)
  const loading = ref(false)

  let cancelled = false

  function setPhase(p: LoopPhase) {
    phase.value = p
  }

  async function advanceEvent() {
    if (!sessionId.value || cancelled) return
    setPhase('fetching')
    error.value = null
    aftermath.value = null
    currentEvent.value = null
    loading.value = true

    try {
      const event = await getEvent(sessionId.value)
      if (cancelled) return
      currentEvent.value = event
      retryCount.value = 0
      loading.value = false

      setPhase('typing')
      await typewriter.typeText(event.narrative, 40)

      if (!cancelled) {
        setPhase('choosing')
      }
    } catch (err: unknown) {
      if (cancelled) return
      loading.value = false

      if (err instanceof FetchError) {
        if (err.status === 400) {
          handleGameOver()
          return
        }
        error.value = err.message
      } else {
        error.value = '天机紊乱，连接中断'
      }
      retryCount.value++
      if (retryCount.value >= 3) {
        error.value = '多次推演失败，建议返回标题页重开'
      }
      setPhase('idle')
    }
  }

  async function handleChoose(optionId: string) {
    if (!sessionId.value || cancelled || phase.value !== 'choosing') return
    typewriter.skipToEnd()
    setPhase('submitting')
    error.value = null
    loading.value = true

    try {
      const result = await chooseOption(sessionId.value, optionId)
      if (cancelled) return

      update(result.state)
      aftermath.value = result.aftermath
      loading.value = false
      setPhase('aftermath')

      if (!result.state.isAlive) {
        setTimeout(() => handleGameOver(), 1500)
      } else {
        setTimeout(() => advanceEvent(), 1500)
      }
    } catch (err: unknown) {
      if (cancelled) return
      loading.value = false
      if (err instanceof FetchError) {
        error.value = err.message
      } else {
        error.value = '天机紊乱，连接中断'
      }
      setPhase('idle')
    }
  }

  async function handleGameOver() {
    if (!sessionId.value || cancelled) return
    setPhase('gameover')
    loading.value = true
    try {
      const result = await endGame(sessionId.value)
      score.value = result.score
      ending.value = result.ending
      grade.value = result.grade
      if (gameState.value) {
        gameState.value.score = result.score
        gameState.value.endingId = result.ending
      }
    } catch {
      score.value = 0
      ending.value = '未知'
      grade.value = 'D'
    }
    loading.value = false
    router.push('/gameover')
  }

  function handleRetry() {
    advanceEvent()
  }

  function handleReturnHome() {
    const { reset } = useGameState()
    reset()
    cancelled = true
    typewriter.cancel()
    router.push('/')
  }

  onUnmounted(() => {
    cancelled = true
    typewriter.cancel()
  })

  return {
    currentEvent,
    aftermath,
    error,
    retryCount,
    loading,
    phase,
    typewriter,
    advanceEvent,
    handleChoose,
    handleRetry,
    handleReturnHome,
  }
}
