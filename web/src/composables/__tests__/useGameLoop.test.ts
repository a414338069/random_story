import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { EventResponse, ChooseResponse, EndGameResponse } from '@/core/types'

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}))

vi.mock('@/api/game', () => ({
  getEvent: vi.fn(),
  chooseOption: vi.fn(),
  endGame: vi.fn(),
}))

vi.mock('@/api/client', () => ({
  FetchError: class FetchError extends Error {
    status: number
    constructor(msg: string, status: number) {
      super(msg)
      this.status = status
    }
  },
}))

const mockGetEvent = vi.mocked(await import('@/api/game')).getEvent
const mockChooseOption = vi.mocked(await import('@/api/game')).chooseOption
const mockEndGame = vi.mocked(await import('@/api/game')).endGame

import { useGameLoop } from '@/composables/useGameLoop'
import { useGameState } from '@/composables/useGameState'

function makeEvent(overrides: Partial<EventResponse> = {}): EventResponse {
  return {
    narrative: '一段修仙叙事',
    options: [{ id: 'opt1', text: '选项一', consequence_preview: null }],
    title: null,
    has_options: true,
    is_breakthrough: false,
    metadata: null,
    ...overrides,
  }
}

function makeChooseResponse(overrides: Partial<ChooseResponse> = {}): ChooseResponse {
  return {
    state: {
      session_id: 'test-session',
      name: '测试角色',
      gender: '男',
      attributes: { root_bone: 3, comprehension: 3, mindset: 2, luck: 2 },
      realm: '炼气',
      realm_progress: 0.5,
      cultivation: 500,
      spirit_stones: 100,
      age: 20,
      lifespan: 150,
      faction: '',
      talent_ids: [],
      techniques: [],
      technique_grades: [],
      inventory: [],
      is_alive: true,
      event_count: 1,
      ascended: false,
    },
    aftermath: {
      cultivation_change: 50,
      age_advance: 2,
      narrative: '修炼有成',
    },
    ...overrides,
  }
}

describe('useGameLoop', () => {
  beforeEach(() => {
    const { reset, setSession } = useGameState()
    reset()
    setSession('test-session')
    vi.clearAllMocks()
  })

  it('should be importable and return expected interface', () => {
    const loop = useGameLoop()
    expect(loop.advanceEvent).toBeTypeOf('function')
    expect(loop.handleChoose).toBeTypeOf('function')
    expect(loop.handleContinueClick).toBeTypeOf('function')
    expect(loop.skipTypewriter).toBeTypeOf('function')
    expect(loop.handleRetry).toBeTypeOf('function')
    expect(loop.handleReturnHome).toBeTypeOf('function')
    expect(loop.eventLog.value).toEqual([])
    expect(loop.currentEntry.value).toBeNull()
    expect(loop.aftermath.value).toBeNull()
    expect(loop.error.value).toBeNull()
    expect(loop.loading.value).toBe(false)
  })

  it('should fetch event and push to eventLog', async () => {
    const event = makeEvent()
    mockGetEvent.mockResolvedValueOnce(event)

    const loop = useGameLoop()
    await loop.advanceEvent()

    expect(mockGetEvent).toHaveBeenCalledWith('test-session')
    expect(loop.eventLog.value).toHaveLength(1)
    expect(loop.eventLog.value[0].narrative).toBe('一段修仙叙事')
    expect(loop.eventLog.value[0].hasOptions).toBe(true)
    expect(loop.loading.value).toBe(false)
  })

  it('should set phase to choosing for normal event with options', async () => {
    const { phase } = useGameState()
    mockGetEvent.mockResolvedValueOnce(makeEvent())

    const loop = useGameLoop()
    await loop.advanceEvent()

    expect(phase.value).toBe('choosing')
  })

  it('should set phase to waiting_click for narrative-only event', async () => {
    const { phase } = useGameState()
    mockGetEvent.mockResolvedValueOnce(makeEvent({ has_options: false, options: [] }))

    const loop = useGameLoop()
    await loop.advanceEvent()

    expect(phase.value).toBe('waiting_click')
  })

  it('should set phase to breakthrough_choosing for breakthrough event', async () => {
    const { phase } = useGameState()
    mockGetEvent.mockResolvedValueOnce(
      makeEvent({
        is_breakthrough: true,
        options: [
          { id: 'use_pill', text: '服用丹药', consequence_preview: null },
          { id: 'direct', text: '直接突破', consequence_preview: null },
        ],
      })
    )

    const loop = useGameLoop()
    await loop.advanceEvent()

    expect(phase.value).toBe('breakthrough_choosing')
  })

  it('should handle choose option and set aftermath', async () => {
    const { phase } = useGameState()
    mockGetEvent.mockResolvedValueOnce(makeEvent())
    const chooseResp = makeChooseResponse()
    mockChooseOption.mockResolvedValueOnce(chooseResp)

    const loop = useGameLoop()
    await loop.advanceEvent()
    expect(phase.value).toBe('choosing')

    await loop.handleChoose('opt1')

    expect(mockChooseOption).toHaveBeenCalledWith('test-session', 'opt1')
    expect(loop.aftermath.value).toEqual(chooseResp.aftermath)
    expect(loop.eventLog.value[0].chosenOptionId).toBe('opt1')
    expect(loop.eventLog.value[0].aftermath).toEqual(chooseResp.aftermath)
  })

  it('should handle breakthrough choice (use_pill)', async () => {
    const { phase } = useGameState()
    mockGetEvent.mockResolvedValueOnce(
      makeEvent({
        is_breakthrough: true,
        options: [
          { id: 'use_pill', text: '服用丹药', consequence_preview: null },
          { id: 'direct', text: '直接突破', consequence_preview: null },
        ],
      })
    )
    const btResp = makeChooseResponse({
      aftermath: {
        cultivation_change: -200,
        age_advance: 0,
        narrative: '突破成功！晋升至筑基！',
        breakthrough: { message: '突破成功！晋升至筑基！', new_realm: '筑基', success: true, use_pill: true },
      },
    })
    mockChooseOption.mockResolvedValueOnce(btResp)

    const loop = useGameLoop()
    await loop.advanceEvent()
    expect(phase.value).toBe('breakthrough_choosing')

    await loop.handleChoose('use_pill')

    expect(mockChooseOption).toHaveBeenCalledWith('test-session', 'use_pill')
    expect(loop.aftermath.value?.breakthrough?.success).toBe(true)
  })

  it('should ignore choose when not in correct phase', async () => {
    const { phase } = useGameState()
    phase.value = 'idle'

    const loop = useGameLoop()
    await loop.handleChoose('opt1')

    expect(mockChooseOption).not.toHaveBeenCalled()
  })

  it('should handle continue click and advance to next event', async () => {
    const { phase } = useGameState()
    mockGetEvent.mockResolvedValueOnce(makeEvent({ has_options: false, options: [] }))
    mockGetEvent.mockResolvedValueOnce(makeEvent({ narrative: '第二个事件' }))

    const loop = useGameLoop()
    await loop.advanceEvent()
    expect(phase.value).toBe('waiting_click')

    loop.handleContinueClick()

    expect(loop.eventLog.value[0].phase).toBe('done')
  })

  it('should ignore continue click when not in waiting_click phase', () => {
    const { phase } = useGameState()
    phase.value = 'choosing'

    const loop = useGameLoop()
    loop.handleContinueClick()

    expect(mockGetEvent).not.toHaveBeenCalled()
  })

  it('should handle API error with retry', async () => {
    const { FetchError } = await import('@/api/client')
    mockGetEvent.mockRejectedValueOnce(new FetchError('服务器错误', 500))

    const loop = useGameLoop()
    await loop.advanceEvent()

    expect(loop.error.value).toBe('服务器错误')
    expect(loop.retryCount.value).toBe(1)
  })

  it('should trigger game over on 400 error', async () => {
    const { FetchError } = await import('@/api/client')
    const { phase } = useGameState()
    mockGetEvent.mockRejectedValueOnce(new FetchError('游戏结束', 400))
    mockEndGame.mockResolvedValueOnce({
      session_id: 'test-session',
      ending: '寿终正寝',
      score: 500,
      grade: 'B',
    })

    const loop = useGameLoop()
    await loop.advanceEvent()

    expect(phase.value).toBe('gameover')
  })

  it('should handle retry via handleRetry', async () => {
    mockGetEvent.mockResolvedValueOnce(makeEvent())

    const loop = useGameLoop()
    loop.handleRetry()

    expect(mockGetEvent).toHaveBeenCalled()
  })

  it('should not advance when no session', async () => {
    const { reset } = useGameState()
    reset()

    const loop = useGameLoop()
    await loop.advanceEvent()

    expect(mockGetEvent).not.toHaveBeenCalled()
  })
})
