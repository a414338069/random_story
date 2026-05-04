import { ref, computed } from 'vue'
import type { NormalizedGameState, LoopPhase } from '@/core/types'

const gameState = ref<NormalizedGameState | null>(null)
const sessionId = ref<string | null>(null)
const phase = ref<LoopPhase>('idle')
const score = ref<number>(0)
const ending = ref<string>('')
const grade = ref<string>('')

export function useGameState() {
  const isAlive = computed(() => {
    return gameState.value?.isAlive ?? false
  })

  function update(state: NormalizedGameState) {
    gameState.value = { ...state }
  }

  function setSession(id: string) {
    sessionId.value = id
    sessionStorage.setItem('gameSessionId', id)
  }

  function setPhase(p: LoopPhase) {
    phase.value = p
  }

  function reset() {
    gameState.value = null
    sessionId.value = null
    phase.value = 'idle'
    score.value = 0
    ending.value = ''
    grade.value = ''
    sessionStorage.removeItem('gameSessionId')
  }

  return {
    gameState,
    sessionId,
    phase,
    score,
    ending,
    grade,
    isAlive,
    update,
    setSession,
    setPhase,
    reset,
  }
}
