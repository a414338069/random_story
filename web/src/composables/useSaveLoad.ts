import { ref } from 'vue'
import { listSaves, loadSave, deleteSave, getEventHistory } from '@/api/save'
import { useGameState } from './useGameState'
import type { SaveSlotInfo, EventHistoryEntry, EventLogEntry, AftermathData } from '@/core/types'

// localStorage keys
const LS_USER_ID = 'cultivation_user_id'
const LS_ACTIVE_SLOT = 'cultivation_active_slot'

// Module-level singleton refs
const saves = ref<SaveSlotInfo[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

/**
 * Get or create a stable user ID stored in localStorage.
 * Format: UUID v4 (crypto.randomUUID())
 */
export function getOrCreateUserId(): string {
  let id = localStorage.getItem(LS_USER_ID)
  if (!id || !/^[0-9a-f-]{36}$/.test(id)) {
    id = crypto.randomUUID()
    localStorage.setItem(LS_USER_ID, id)
  }
  return id
}

/**
 * Get the currently active save slot number, or null.
 */
export function getActiveSlot(): number | null {
  const raw = localStorage.getItem(LS_ACTIVE_SLOT)
  if (raw === null) return null
  const num = Number(raw)
  return Number.isFinite(num) ? num : null
}

/**
 * Set the active save slot in localStorage.
 */
export function setActiveSlot(slot: number): void {
  localStorage.setItem(LS_ACTIVE_SLOT, String(slot))
}

/**
 * Clear the active save slot from localStorage.
 */
export function clearActiveSlot(): void {
  localStorage.removeItem(LS_ACTIVE_SLOT)
}

export function useSaveLoad() {
  async function listMySaves(): Promise<SaveSlotInfo[]> {
    loading.value = true
    error.value = null
    try {
      const userId = getOrCreateUserId()
      saves.value = await listSaves(userId)
      return saves.value
    } catch (err) {
      const msg = err instanceof Error ? err.message : '获取存档列表失败'
      error.value = msg
      return []
    } finally {
      loading.value = false
    }
  }

  async function loadMySave(slot: number): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const userId = getOrCreateUserId()
      const result = await loadSave(userId, slot)
      const { setSession, update } = useGameState()
      setSession(result.sessionId)
      update(result.state)
      setActiveSlot(slot)
    } catch (err) {
      const msg = err instanceof Error ? err.message : '加载存档失败'
      error.value = msg
      throw err
    } finally {
      loading.value = false
    }
  }

  async function deleteMySave(slot: number): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const userId = getOrCreateUserId()
      await deleteSave(userId, slot)
      saves.value = saves.value.filter((s) => s.slot !== slot)
      if (getActiveSlot() === slot) {
        clearActiveSlot()
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : '删除存档失败'
      error.value = msg
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchEventHistory(sessionId: string): Promise<EventHistoryEntry[]> {
    loading.value = true
    error.value = null
    try {
      return await getEventHistory(sessionId)
    } catch (err) {
      const msg = err instanceof Error ? err.message : '获取事件历史失败'
      error.value = msg
      return []
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch event history from backend and convert to EventLogEntry[] for restoring event log.
   */
  async function restoreEventLog(sessionId: string): Promise<EventLogEntry[]> {
    const history = await fetchEventHistory(sessionId)
    return history.map((e) => {
      // Backend may deserialize options JSON — handle both string and pre-parsed array
      let parsedOptions: EventLogEntry['options'] = []
      if (e.options) {
        if (Array.isArray(e.options)) {
          parsedOptions = e.options
        } else if (typeof e.options === 'string') {
          try {
            parsedOptions = JSON.parse(e.options)
          } catch {
            parsedOptions = []
          }
        }
      }

      let entryAftermath: AftermathData | null = null

      if (e.aftermath) {
        entryAftermath = e.aftermath
      } else if (e.consequences) {
        try {
          // Backend may deserialize consequences — handle both string and pre-parsed object
          const cons = typeof e.consequences === 'string'
            ? JSON.parse(e.consequences)
            : e.consequences
          const cultivationGain = (cons as Record<string, unknown>).cultivation_gain
          entryAftermath = {
            cultivation_change: typeof cultivationGain === 'number' ? cultivationGain : 0,
            age_advance: 0,
          }
        } catch {
          entryAftermath = null
        }
      }

      return {
        id: e.eventIndex,
        narrative: e.narrative,
        displayedText: e.narrative,
        options: parsedOptions,
        chosenOptionId: e.chosenOptionId != null ? String(e.chosenOptionId) : null,
        aftermath: entryAftermath,
        phase: 'done' as const,
        hasOptions: parsedOptions.length > 0,
        title: null,
        realm: e.realm || null,
      }
    })
  }

  return {
    saves,
    loading,
    error,
    listMySaves,
    loadMySave,
    deleteMySave,
    fetchEventHistory,
    restoreEventLog,
  }
}
