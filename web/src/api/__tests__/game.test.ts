import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockFetch = vi.fn()

beforeEach(() => {
  vi.clearAllMocks()
  globalThis.fetch = mockFetch
})

describe('startGame', () => {
  it('should call POST /api/v1/game/start and normalize response', async () => {
    const mockResponse = {
      session_id: 'test-session',
      state: {
        id: 'test-session',
        name: 'TestName',
        gender: '男',
        talent_ids: ['f01', 'l02', 'x01'],
        root_bone: 4,
        comprehension: 3,
        mindset: 2,
        luck: 1,
        realm: '凡人',
        realm_progress: 0,
        health: 100,
        qi: 0,
        lifespan: 80,
        faction: '',
        spirit_stones: 0,
        techniques: [],
        inventory: [],
        event_count: 0,
        score: 0,
        ending_id: null,
        is_alive: true,
        last_active_at: null,
        created_at: '2026-01-01T00:00:00',
        updated_at: '2026-01-01T00:00:00',
      },
    }

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    })

    const { startGame } = await import('@/api/game')
    const result = await startGame({
      name: 'TestName',
      gender: '男',
      talent_card_ids: ['f01', 'l02', 'x01'],
      attributes: { root_bone: 4, comprehension: 3, mindset: 2, luck: 1 },
    })

    expect(result.sessionId).toBe('test-session')
    expect(result.state.name).toBe('TestName')
    expect(result.state.realm).toBe('凡人')
  })
})
