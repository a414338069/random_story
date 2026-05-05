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
    case '凡品': return '#8a8a8a'
    case '灵品': return '#5b8fbf'
    case '玄品': return '#7c5ba5'
    case '仙品': return '#c9a76e'
    case '神品': return '#c23a2b'
    default: return '#8a8a8a'
  }
}

export function getGradeBgColor(grade: string): string {
  switch (grade) {
    case '凡品': return 'rgba(138,138,138,0.06)'
    case '灵品': return 'rgba(91,143,191,0.08)'
    case '玄品': return 'rgba(124,91,165,0.08)'
    case '仙品': return 'rgba(201,167,110,0.10)'
    case '神品': return 'rgba(194,58,43,0.08)'
    default: return 'rgba(138,138,138,0.06)'
  }
}

export function getGradeClass(grade: string): string {
  switch (grade) {
    case '凡品': return 'grade-common'
    case '灵品': return 'grade-uncommon'
    case '玄品': return 'grade-rare'
    case '仙品': return 'grade-legendary'
    case '神品': return 'grade-mythic'
    default: return 'grade-common'
  }
}

export const MAX_REDRAW = 4

export function canReDraw(redrawCount: number): boolean {
  return redrawCount < MAX_REDRAW
}
