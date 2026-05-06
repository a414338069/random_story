import { describe, it, expect } from 'vitest'
import { drawCards, getGradeColor, getGradeBgColor, canReDraw, MAX_REDRAW } from '@/core/talents'

describe('drawCards', () => {
  it('should return the requested number of cards', () => {
    const cards = drawCards(3)
    expect(cards).toHaveLength(3)
  })

  it('each card should have required fields', () => {
    const cards = drawCards(3)
    for (const card of cards) {
      expect(card.id).toBeTruthy()
      expect(card.name).toBeTruthy()
      expect(card.grade).toBeTruthy()
      expect(card.category).toBeTruthy()
      expect(card.description).toBeTruthy()
    }
  })

  it('cards should be unique (no duplicates per draw)', () => {
    const cards = drawCards(3)
    const ids = cards.map(c => c.id)
    expect(new Set(ids).size).toBe(3)
  })
})

describe('getGradeColor', () => {
  it('should return correct color for each grade', () => {
    expect(getGradeColor('凡品')).toBe('#8a8a8a')
    expect(getGradeColor('灵品')).toBe('#5b8fbf')
    expect(getGradeColor('玄品')).toBe('#7c5ba5')
    expect(getGradeColor('仙品')).toBe('#c9a76e')
    expect(getGradeColor('神品')).toBe('#c23a2b')
    expect(getGradeColor('未知')).toBe('#8a8a8a')
  })
})

describe('getGradeBgColor', () => {
  it('should return correct background color for each grade', () => {
    expect(getGradeBgColor('凡品')).toBe('rgba(138,138,138,0.06)')
    expect(getGradeBgColor('灵品')).toBe('rgba(91,143,191,0.08)')
    expect(getGradeBgColor('神品')).toBe('rgba(194,58,43,0.08)')
    expect(getGradeBgColor('未知')).toBe('rgba(138,138,138,0.06)')
  })
})

describe('canReDraw', () => {
  it('should allow redraw when below max', () => {
    expect(canReDraw(0)).toBe(true)
    expect(canReDraw(3)).toBe(true)
  })

  it('should deny redraw at max', () => {
    expect(canReDraw(MAX_REDRAW)).toBe(false)
    expect(canReDraw(5)).toBe(false)
  })
})
