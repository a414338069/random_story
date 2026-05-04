import { describe, it, expect } from 'vitest'
import { normalizeFromPydantic, normalizeFromDict } from '@/core/normalize'
import type { PlayerStatePydantic, GameStateDict } from '@/core/types'

const mockPydantic: PlayerStatePydantic = {
  id: 'test123',
  name: '测试仙人',
  gender: '男',
  talent_ids: ['f01', 'l01', 'x01'],
  root_bone: 5,
  comprehension: 3,
  mindset: 1,
  luck: 1,
  realm: '练气',
  realm_progress: 0.5,
  health: 100,
  qi: 0,
  lifespan: 80,
  faction: '散修',
  spirit_stones: 10,
  techniques: [],
  inventory: [],
  event_count: 0,
  score: 0,
  ending_id: null,
  is_alive: true,
  last_active_at: null,
  created_at: '2026-01-01T00:00:00',
  updated_at: '2026-01-01T00:00:00',
}

const mockDict: GameStateDict = {
  session_id: 'test123',
  name: '测试仙人',
  gender: '男',
  attributes: { rootBone: 5, comprehension: 3, mindset: 1, luck: 1 },
  realm: '练气',
  realm_progress: 0.5,
  cultivation: 100,
  spirit_stones: 10,
  age: 25,
  lifespan: 80,
  faction: '散修',
  talent_ids: ['f01', 'l01', 'x01'],
  techniques: [],
  technique_grades: [],
  inventory: [],
  is_alive: true,
  event_count: 5,
  ascended: false,
}

describe('normalizeFromPydantic', () => {
  it('should normalize PlayerStatePydantic to NormalizedGameState', () => {
    const result = normalizeFromPydantic(mockPydantic)

    expect(result.sessionId).toBe('test123')
    expect(result.name).toBe('测试仙人')
    expect(result.attributes.rootBone).toBe(5)
    expect(result.attributes.comprehension).toBe(3)
    expect(result.realm).toBe('练气')
    expect(result.realmProgress).toBe(0.5)
    expect(result.cultivation).toBe(0)
    expect(result.age).toBe(0)
    expect(result.score).toBe(0)
    expect(result.isAlive).toBe(true)
    expect(result.ascended).toBe(false)
  })
})

describe('normalizeFromDict', () => {
  it('should normalize GameStateDict to NormalizedGameState', () => {
    const result = normalizeFromDict(mockDict)

    expect(result.sessionId).toBe('test123')
    expect(result.name).toBe('测试仙人')
    expect(result.attributes.rootBone).toBe(5)
    expect(result.realm).toBe('练气')
    expect(result.cultivation).toBe(100)
    expect(result.age).toBe(25)
    expect(result.score).toBe(0)
    expect(result.isAlive).toBe(true)
    expect(result.ascended).toBe(false)
    expect(result.eventCount).toBe(5)
  })
})
