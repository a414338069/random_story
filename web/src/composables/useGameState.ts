import { ref, computed } from 'vue'
import type { NormalizedGameState, LoopPhase } from '@/core/types'
import { setActiveSlot, clearActiveSlot } from './useSaveLoad'

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

  function setSession(id: string, slot?: number) {
    sessionId.value = id
    sessionStorage.setItem('gameSessionId', id)
    if (slot !== undefined) {
      setActiveSlot(slot)
    }
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
    clearActiveSlot()
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
