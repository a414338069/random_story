import { describe, it, expect } from 'vitest'
import {
  MODIFIER_NAME_MAP,
  formatModifierValue,
  getModifierLabel,
} from '../talents'

describe('MODIFIER_NAME_MAP', () => {
  it('has all expected keys', () => {
    const expectedKeys = [
      'max_health_bonus',
      'breakthrough_rate_bonus',
      'learning_speed',
      'mental_resist',
      'qi_recovery',
      'max_qi_bonus',
      'health_recovery',
      'resilience',
      'physical_damage_bonus',
      'event_luck_bonus',
      'breakthrough_pill_chance',
      'breakthrough_health_cost',
      'cultivation_speed',
      'lifespan_bonus',
      'demon_resist',
      'extra_event_option',
      'romance_blocked',
      'npc_relation_penalty',
      'devour_effect',
      'health_regen',
      'death_resist',
      'death_resurrection',
      'soul_power_bonus',
      'fate_rewrite',
    ]
    for (const key of expectedKeys) {
      expect(MODIFIER_NAME_MAP).toHaveProperty(key)
    }
    expect(Object.keys(MODIFIER_NAME_MAP)).toHaveLength(24)
  })
})

describe('formatModifierValue', () => {
  it('returns 30% for 0.3', () => {
    expect(formatModifierValue(0.3)).toBe('30%')
  })

  it('returns 50 for 50', () => {
    expect(formatModifierValue(50)).toBe('50')
  })

  it('returns 生效 for true', () => {
    expect(formatModifierValue(true)).toBe('生效')
  })

  it('returns 失效 for false', () => {
    expect(formatModifierValue(false)).toBe('失效')
  })
})

describe('getModifierLabel', () => {
  it('returns 修为获取 for cultivation_speed', () => {
    expect(getModifierLabel('cultivation_speed')).toBe('修为获取')
  })

  it('returns original key for unknown modifier', () => {
    expect(getModifierLabel('unknown_modifier')).toBe('unknown_modifier')
  })
})