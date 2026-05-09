import { describe, it, expect } from 'vitest'
import { talents } from '@/data/talents'

describe('talent effects sync', () => {
  it('all 20 talents have effects field', () => {
    expect(talents).toHaveLength(20)
    for (const card of talents) {
      expect(card.effects).toBeDefined()
    }
  })

  it('each effect has attr_bonuses and modifiers of correct type', () => {
    for (const card of talents) {
      const { effects } = card
      expect(typeof effects.attr_bonuses).toBe('object')
      expect(typeof effects.modifiers).toBe('object')
      for (const val of Object.values(effects.attr_bonuses)) {
        expect(typeof val).toBe('number')
      }
      for (const val of Object.values(effects.modifiers)) {
        expect(typeof val === 'number' || typeof val === 'boolean').toBe(true)
      }
    }
  })

  it('cards without positive/negative effects have undefined for those fields', () => {
    const cardsWithSubEffects = new Set(['l06', 'x04', 's03'])
    for (const card of talents) {
      if (cardsWithSubEffects.has(card.id)) {
        expect(card.effects.positive_effects).toBeDefined()
        expect(card.effects.negative_effects).toBeDefined()
      } else {
        expect(card.effects.positive_effects).toBeUndefined()
        expect(card.effects.negative_effects).toBeUndefined()
      }
    }
  })

  it('f01 粗壮体魄 has root_bone bonus and max_health_bonus', () => {
    const card = talents.find(c => c.id === 'f01')!
    expect(card.effects.attr_bonuses.root_bone).toBe(1)
    expect(card.effects.modifiers.max_health_bonus).toBe(20)
  })

  it('d01 逆天改命 has all four attribute bonuses', () => {
    const card = talents.find(c => c.id === 'd01')!
    expect(card.effects.attr_bonuses.root_bone).toBe(5)
    expect(card.effects.attr_bonuses.comprehension).toBe(5)
    expect(card.effects.attr_bonuses.mindset).toBe(5)
    expect(card.effects.attr_bonuses.luck).toBe(10)
    expect(card.effects.modifiers.lifespan_bonus).toBe(100)
    expect(card.effects.modifiers.fate_rewrite).toBe(1)
  })

  it('l06 血祭之契 has correct positive/negative effects', () => {
    const card = talents.find(c => c.id === 'l06')!
    expect(card.effects.positive_effects!.modifiers.breakthrough_pill_chance).toBe(0.25)
    expect(card.effects.negative_effects!.modifiers.breakthrough_health_cost).toBe(0.3)
  })

  it('x04 天煞孤星 has correct positive/negative effects', () => {
    const card = talents.find(c => c.id === 'x04')!
    expect(card.effects.positive_effects!.attr_bonuses.luck).toBe(3)
    expect(card.effects.positive_effects!.modifiers.extra_event_option).toBe(1)
    expect(card.effects.negative_effects!.modifiers.romance_blocked).toBe(true)
    expect(card.effects.negative_effects!.modifiers.npc_relation_penalty).toBe(-0.5)
  })

  it('s03 残缺神魂 has correct positive/negative effects', () => {
    const card = talents.find(c => c.id === 's03')!
    expect(card.effects.positive_effects!.modifiers.death_resurrection).toBe(1)
    expect(card.effects.positive_effects!.modifiers.soul_power_bonus).toBe(0.3)
    expect(card.effects.negative_effects!.attr_bonuses.comprehension).toBe(-2)
    expect(card.effects.negative_effects!.modifiers.learning_speed).toBe(-0.3)
  })
})
