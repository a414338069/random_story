import { apiRequest } from './client'
import { normalizeFromPydantic, normalizeFromDict } from '@/core/normalize'
import type {
  GameStartRequest,
  GameStartResponse,
  NormalizedGameState,
  GameStateDict,
  EventResponse,
  ChooseResponse,
  EndGameResponse,
  LeaderboardEntry,
  BreakthroughInfo,
} from '@/core/types'

const BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export async function startGame(
  req: GameStartRequest,
): Promise<{ sessionId: string; state: NormalizedGameState }> {
  const res: GameStartResponse = await apiRequest('/api/v1/game/start', {
    method: 'POST',
    body: JSON.stringify(req),
  })
  return {
    sessionId: res.session_id,
    state: normalizeFromPydantic(res.state),
  }
}

export async function getEvent(sessionId: string): Promise<EventResponse & { normalizedState?: NormalizedGameState }> {
  const res: EventResponse = await apiRequest('/api/v1/game/event', {
    method: 'POST',
    body: JSON.stringify({ player_id: sessionId }),
  })
  if (res.state) {
    return { ...res, normalizedState: normalizeFromDict(res.state) }
  }
  return res
}

export async function chooseOption(
  sessionId: string,
  optionId: string | null,
): Promise<{ state: NormalizedGameState; aftermath: { cultivation_change: number; age_advance: number; narrative?: string; breakthrough?: BreakthroughInfo } }> {
  const res: ChooseResponse = await apiRequest('/api/v1/game/event/choose', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, option_id: optionId }),
  })
  return {
    state: normalizeFromDict(res.state),
    aftermath: res.aftermath,
  }
}

export async function getState(sessionId: string): Promise<NormalizedGameState> {
  const res = await apiRequest<GameStateDict>(`/api/v1/game/state/${sessionId}`)
  return normalizeFromDict(res)
}

export async function endGame(sessionId: string): Promise<EndGameResponse> {
  return await apiRequest('/api/v1/game/end', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId }),
  })
}

export async function getLeaderboard(): Promise<LeaderboardEntry[]> {
  return await apiRequest('/api/v1/game/leaderboard')
}


