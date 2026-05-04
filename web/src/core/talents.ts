import { talents } from '@/data/talents'
import type { TalentCard } from '@/core/types'

export function drawCards(count: number): TalentCard[] {
  const pool = [...talents]
  const results: TalentCard[] = []

  for (let i = 0; i < count; i++) {
    const totalWeight = pool.reduce((sum, t) => sum + t.rarity, 0)
    let rand = Math.random() * totalWeight
    let picked = 0
    for (let j = 0; j < pool.length; j++) {
      rand -= pool[j].rarity
      if (rand <= 0) {
        picked = j
        break
      }
    }
    results.push(pool[picked])
    pool.splice(picked, 1)
  }

  return results
}

export function getGradeColor(grade: string): string {
  switch (grade) {
    case '凡品': return '#9e9e9e'
    case '灵品': return '#4caf50'
    case '玄品': return '#3f51b5'
    case '仙品': return '#9c27b0'
    case '神品': return '#ff8f00'
    default: return '#9e9e9e'
  }
}

export function getGradeBgColor(grade: string): string {
  switch (grade) {
    case '凡品': return 'rgba(158,158,158,0.1)'
    case '灵品': return 'rgba(76,175,80,0.1)'
    case '玄品': return 'rgba(63,81,181,0.1)'
    case '仙品': return 'rgba(156,39,176,0.1)'
    case '神品': return 'rgba(255,143,0,0.1)'
    default: return 'rgba(158,158,158,0.1)'
  }
}

export const MAX_REDRAW = 4

export function canReDraw(redrawCount: number): boolean {
  return redrawCount < MAX_REDRAW
}
