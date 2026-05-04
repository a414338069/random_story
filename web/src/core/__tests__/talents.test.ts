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
    expect(getGradeColor('凡品')).toBe('#9e9e9e')
    expect(getGradeColor('灵品')).toBe('#4caf50')
    expect(getGradeColor('玄品')).toBe('#3f51b5')
    expect(getGradeColor('仙品')).toBe('#9c27b0')
    expect(getGradeColor('神品')).toBe('#ff8f00')
    expect(getGradeColor('未知')).toBe('#9e9e9e')
  })
})

describe('getGradeBgColor', () => {
  it('should return correct background color for each grade', () => {
    expect(getGradeBgColor('凡品')).toBe('rgba(158,158,158,0.1)')
    expect(getGradeBgColor('神品')).toBe('rgba(255,143,0,0.1)')
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
