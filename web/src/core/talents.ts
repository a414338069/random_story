import { talents } from '@/data/talents'
import type { TalentCard } from '@/core/types'

export const MODIFIER_NAME_MAP: Record<string, string> = {
  max_health_bonus: '生命上限',
  breakthrough_rate_bonus: '突破概率',
  learning_speed: '修炼速度',
  mental_resist: '心魔抗性',
  qi_recovery: '灵气恢复',
  max_qi_bonus: '灵气上限',
  health_recovery: '生命恢复',
  resilience: '韧性',
  physical_damage_bonus: '伤害加成',
  event_luck_bonus: '事件运气',
  breakthrough_pill_chance: '丹药突破概率',
  breakthrough_health_cost: '突破生命代价',
  cultivation_speed: '修为获取',
  lifespan_bonus: '寿元',
  demon_resist: '心魔抵抗',
  extra_event_option: '额外选项',
  romance_blocked: '禁绝情缘',
  npc_relation_penalty: '关系惩罚',
  devour_effect: '吞噬效果',
  health_regen: '生命回复',
  death_resist: '免死',
  death_resurrection: '死后复活',
  soul_power_bonus: '神魂加成',
  fate_rewrite: '命运改写',
}

export function formatModifierValue(val: number | boolean): string {
  if (typeof val === 'boolean') return val ? '生效' : '失效'
  if (val < 1 && val > -1) return `${(val * 100).toFixed(0)}%`
  return String(val)
}

export function getModifierLabel(key: string): string {
  return MODIFIER_NAME_MAP[key] ?? key
}

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
