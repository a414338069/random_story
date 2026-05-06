export interface Attributes {
  rootBone: number
  comprehension: number
  mindset: number
  luck: number
}

export interface PlayerStatePydantic {
  id: string
  name: string
  gender: string
  talent_ids: string[]
  root_bone: number
  comprehension: number
  mindset: number
  luck: number
  realm: string
  realm_progress: number
  cultivation: number
  age: number
  health: number
  qi: number
  lifespan: number
  faction: string
  spirit_stones: number
  techniques: string[]
  inventory: string[]
  event_count: number
  score: number
  ending_id: string | null
  is_alive: boolean
  last_active_at: string | null
  created_at: string
  updated_at: string
}

export interface GameStateDict {
  session_id: string
  name: string
  gender: string
  attributes: Attributes
  realm: string
  realm_progress: number
  cultivation: number
  spirit_stones: number
  age: number
  lifespan: number
  faction: string
  talent_ids: string[]
  techniques: string[]
  technique_grades: string[]
  inventory: string[]
  is_alive: boolean
  event_count: number
  ascended: boolean
}

export interface NormalizedGameState {
  sessionId: string
  name: string
  gender: string
  talentIds: string[]
  attributes: Attributes
  realm: string
  realmProgress: number
  cultivation: number
  age: number
  lifespan: number
  faction: string
  spiritStones: number
  techniques: string[]
  inventory: string[]
  eventCount: number
  isAlive: boolean
  ascended: boolean
  score: number
  endingId: string | null
}

export interface TalentCard {
  id: string
  name: string
  grade: string
  rarity: number
  category: string
  description: string
}

export interface EventOption {
  id: string
  text: string
  consequence_preview: string | null
}

export interface EventResponse {
  narrative: string
  options: EventOption[]
  title: string | null
  has_options: boolean
  metadata: Record<string, unknown> | null
}

export interface EventLogEntry {
  id: number
  narrative: string
  displayedText: string
  options: EventOption[]
  chosenOptionId: string | null
  aftermath: { cultivation_change: number; age_advance: number; narrative?: string; breakthrough?: BreakthroughInfo } | null
  phase: 'typing' | 'waiting_click' | 'choosing' | 'submitting' | 'aftermath' | 'breakthrough' | 'done'
  hasOptions: boolean
  title: string | null
}

export interface BreakthroughInfo {
  message: string
  new_realm: string | null
  success: boolean | null
  use_pill?: boolean
}

export interface ChooseResponse {
  state: GameStateDict
  aftermath: {
    cultivation_change: number
    age_advance: number
    narrative?: string
    breakthrough?: BreakthroughInfo
  }
}

export interface GameStartRequest {
  name: string
  gender: '男' | '女'
  talent_card_ids: string[]
  attributes: {
    root_bone: number
    comprehension: number
    mindset: number
    luck: number
  }
}

export interface GameStartResponse {
  session_id: string
  state: PlayerStatePydantic
}

export interface EndGameResponse {
  session_id: string
  ending: string
  score: number
  grade: string
}

export interface LeaderboardEntry {
  rank: number
  player_name: string
  score: number
  realm: string
  ending_id: string | null
}

export type LoopPhase = 'idle' | 'fetching' | 'typing' | 'waiting_click' | 'choosing' | 'breakthrough_choosing' | 'submitting' | 'aftermath' | 'gameover'
