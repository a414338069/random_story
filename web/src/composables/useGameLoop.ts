import { ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGameState } from './useGameState'
import { useTypewriter } from './useTypewriter'
import { getEvent, chooseOption, endGame } from '@/api/game'
import { FetchError } from '@/api/client'
import type { EventLogEntry, LoopPhase } from '@/core/types'

export function useGameLoop() {
  const router = useRouter()
  const { sessionId, phase, update, score, ending, grade, gameState } = useGameState()
  const typewriter = useTypewriter()

  const eventLog = ref<EventLogEntry[]>([])
  const currentEntry = computed(() =>
    eventLog.value.length > 0 ? eventLog.value[eventLog.value.length - 1] : null
  )
  // backward compat: currentEvent is an alias for currentEntry (used by views that haven't migrated)
  const currentEvent = computed(() => currentEntry.value)

  const aftermath = ref<{
    cultivation_change: number
    age_advance: number
    narrative?: string
    breakthrough?: { message: string; new_realm: string | null; success: boolean | null }
  } | null>(null)
  const error = ref<string | null>(null)
  const retryCount = ref(0)
  const loading = ref(false)
  const eventId = ref(0)

  let cancelled = false

  function setPhase(p: LoopPhase) {
    phase.value = p
  }

  async function advanceEvent() {
    if (!sessionId.value || cancelled) return
    setPhase('fetching')
    error.value = null
    aftermath.value = null
    loading.value = true

    try {
      const event = await getEvent(sessionId.value)
      if (cancelled) return

      eventId.value++
      const entry: EventLogEntry = {
        id: eventId.value,
        narrative: event.narrative,
        displayedText: '',
        options: event.options,
        chosenOptionId: null,
        aftermath: null,
        phase: 'typing',
        hasOptions: event.has_options,
        title: event.title,
      }
      eventLog.value.push(entry)

      retryCount.value = 0
      loading.value = false

      setPhase('typing')
      await typewriter.typeText(event.narrative, 40)

      if (cancelled) return

      // After typewriter finishes, decide next phase based on has_options
      if (event.has_options) {
        setPhase('choosing')
        entry.phase = 'choosing'
      } else {
        setPhase('waiting_click')
        entry.phase = 'waiting_click'
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

  async function handleChoose(optionId: string | null) {
    if (!sessionId.value || cancelled) return

    const isChoosing = phase.value === 'choosing'
    const isWaitingClick = phase.value === 'waiting_click'

    if (!isChoosing && !isWaitingClick) return

    typewriter.skipToEnd()
    setPhase('submitting')
    error.value = null
    loading.value = true

    const entry = currentEntry.value
    if (entry) {
      entry.phase = 'submitting'
      entry.chosenOptionId = optionId
    }

    try {
      const result = await chooseOption(sessionId.value, optionId)
      if (cancelled) return

      update(result.state)
      aftermath.value = result.aftermath
      if (entry) {
        entry.aftermath = result.aftermath
      }
      loading.value = false
      setPhase('aftermath')
      if (entry) {
        entry.phase = 'aftermath'
      }

      if (!result.state.isAlive) {
        setTimeout(() => handleGameOver(), 2500)
      } else if (result.aftermath?.breakthrough) {
        // 有突破时：不自动advance，显示突破信息等待用户确认
        if (entry) {
          entry.phase = 'breakthrough'
        }
        setPhase('waiting_click') // 允许点击继续
      } else {
        // 正常：2.5秒后自动推进
        setTimeout(() => {
          if (entry) {
            entry.phase = 'done'
          }
          advanceEvent()
        }, 2500)
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

  function handleContinueClick() {
    if (phase.value !== 'waiting_click') return
    const entry = currentEntry.value
    if (entry && entry.phase === 'breakthrough') {
      entry.phase = 'done'
      advanceEvent()
      return
    }
    handleChoose(null)
  }

  function skipTypewriter() {
    if (typewriter.isTyping.value) {
      typewriter.skipToEnd()
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
    eventLog,
    currentEntry,
    aftermath,
    error,
    retryCount,
    loading,
    phase,
    typewriter,
    advanceEvent,
    handleChoose,
    handleContinueClick,
    skipTypewriter,
    handleRetry,
    handleReturnHome,
  }
}
