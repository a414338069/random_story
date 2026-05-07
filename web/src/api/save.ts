import { apiRequest } from './client'
import { normalizeFromPydantic } from '@/core/normalize'
import type { NormalizedGameState, PlayerStatePydantic, SaveSlotInfo, EventHistoryEntry } from '@/core/types'

interface SaveListResponse {
  saves: Array<{
    slot: number
    session_id: string
    name: string
    realm: string
    age: number
    event_count: number
    last_active_at: string | null
    is_alive: boolean
  }>
}

interface LoadSaveResponse {
  session_id: string
  state: PlayerStatePydantic
}

interface EventHistoryRawItem {
  player_id: string
  event_index: number
  event_type: string
  narrative: string
  realm: string | null
  options: unknown  // backend deserializes JSON → may be array or string
  chosen_option_id: number | null
  consequences: unknown  // backend deserializes JSON → may be object or string
  aftermath: string | null
}

export async function listSaves(userId: string): Promise<SaveSlotInfo[]> {
  const res: SaveListResponse = await apiRequest(`/api/v1/game/saves?user_id=${encodeURIComponent(userId)}`)
  return res.saves.map((s) => ({
    slot: s.slot,
    sessionId: s.session_id,
    name: s.name,
    realm: s.realm,
    age: s.age,
    eventCount: s.event_count,
    lastActiveAt: s.last_active_at,
    isAlive: s.is_alive,
  }))
}

export async function loadSave(
  userId: string,
  saveSlot: number,
): Promise<{ sessionId: string; state: NormalizedGameState }> {
  const res: LoadSaveResponse = await apiRequest('/api/v1/game/save/load', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, save_slot: saveSlot }),
  })
  return {
    sessionId: res.session_id,
    state: normalizeFromPydantic(res.state),
  }
}

export async function deleteSave(userId: string, saveSlot: number): Promise<{ success: boolean }> {
  return await apiRequest(`/api/v1/game/save/${encodeURIComponent(userId)}/${saveSlot}`, {
    method: 'DELETE',
  })
}

export async function getEventHistory(sessionId: string): Promise<EventHistoryEntry[]> {
  const res: EventHistoryRawItem[] = await apiRequest(`/api/v1/game/events/${encodeURIComponent(sessionId)}`)
  return res.map((e) => {
    let parsedAftermath: EventHistoryEntry['aftermath'] = null
    if (e.aftermath) {
      try {
        parsedAftermath = typeof e.aftermath === 'string'
          ? JSON.parse(e.aftermath)
          : e.aftermath
      } catch {
        parsedAftermath = null
      }
    }
    return {
      eventIndex: e.event_index,
      eventType: e.event_type,
      narrative: e.narrative,
      realm: e.realm,
      options: e.options,
      chosenOptionId: e.chosen_option_id,
      consequences: e.consequences,
      aftermath: parsedAftermath,
    }
  })
}
