import type { TalentCard } from '@/core/types'

export const talents: TalentCard[] = [
  {
    id: 'f01', name: '粗壮体魄', grade: '凡品', rarity: 0.4, category: '肉身',
    description: '天生骨骼精奇，肉身强健，气血旺盛。',
    effects: { attr_bonuses: { root_bone: 1 }, modifiers: { max_health_bonus: 20 } },
  },
  {
    id: 'f02', name: '耳聪目明', grade: '凡品', rarity: 0.4, category: '感知',
    description: '五感敏锐，过目不忘，学习事半功倍。',
    effects: { attr_bonuses: { comprehension: 1 }, modifiers: { learning_speed: 0.05 } },
  },
  {
    id: 'f03', name: '福星高照', grade: '凡品', rarity: 0.4, category: '气运',
    description: '天生好运，常能逢凶化吉。',
    effects: { attr_bonuses: { luck: 1 }, modifiers: {} },
  },
  {
    id: 'f04', name: '意志坚定', grade: '凡品', rarity: 0.4, category: '心境',
    description: '心志坚韧，不为外物所动。',
    effects: { attr_bonuses: { mindset: 1 }, modifiers: { mental_resist: 0.1 } },
  },
  {
    id: 'f05', name: '灵根初显', grade: '凡品', rarity: 0.4, category: '灵根',
    description: '初步感应天地灵气，踏入修行门槛。',
    effects: { attr_bonuses: {}, modifiers: { qi_recovery: 0.1, max_qi_bonus: 10 } },
  },
  {
    id: 'f06', name: '百折不挠', grade: '凡品', rarity: 0.4, category: '意志',
    description: '愈挫愈勇，屡败屡战，从不轻言放弃。',
    effects: { attr_bonuses: {}, modifiers: { health_recovery: 0.1, resilience: 0.05 } },
  },
  {
    id: 'l01', name: '天生神力', grade: '灵品', rarity: 0.3, category: '肉身',
    description: '力能扛鼎，肉身无双，同阶无敌。',
    effects: { attr_bonuses: { root_bone: 3 }, modifiers: { max_health_bonus: 50, physical_damage_bonus: 0.15 } },
  },
  {
    id: 'l02', name: '过人悟性', grade: '灵品', rarity: 0.3, category: '悟性',
    description: '天资聪颖，举一反三，悟道如饮水。',
    effects: { attr_bonuses: { comprehension: 3 }, modifiers: { learning_speed: 0.15 } },
  },
  {
    id: 'l03', name: '锦鲤命', grade: '灵品', rarity: 0.3, category: '气运',
    description: '气运加身，常遇奇遇机缘。',
    effects: { attr_bonuses: { luck: 3 }, modifiers: { event_luck_bonus: 0.15 } },
  },
  {
    id: 'l04', name: '坚如磐石', grade: '灵品', rarity: 0.3, category: '心境',
    description: '心若磐石，万法不侵，道心稳固。',
    effects: { attr_bonuses: { mindset: 3 }, modifiers: { mental_resist: 0.25 } },
  },
  {
    id: 'l05', name: '灵泉体质', grade: '灵品', rarity: 0.3, category: '灵根',
    description: '体内灵泉涌动，灵力生生不息。',
    effects: { attr_bonuses: {}, modifiers: { max_qi_bonus: 50, qi_recovery: 0.3 } },
  },
  {
    id: 'l06', name: '血祭之契', grade: '灵品', rarity: 0.3, category: '禁忌',
    description: '以血为祭，换取突破机缘。代价沉重。',
    effects: {
      attr_bonuses: {}, modifiers: {},
      positive_effects: { attr_bonuses: {}, modifiers: { breakthrough_pill_chance: 0.25 } },
      negative_effects: { attr_bonuses: {}, modifiers: { breakthrough_health_cost: 0.3 } },
    },
  },
  {
    id: 'x01', name: '天灵根', grade: '玄品', rarity: 0.2, category: '灵根',
    description: '绝世天灵根，修行一日千里，碾压同辈。',
    effects: { attr_bonuses: { root_bone: 5, comprehension: 5 }, modifiers: { max_qi_bonus: 100, cultivation_speed: 0.3 } },
  },
  {
    id: 'x02', name: '不灭道心', grade: '玄品', rarity: 0.2, category: '心境',
    description: '道心不灭，万劫不侵，心魔辟易。',
    effects: { attr_bonuses: { mindset: 5 }, modifiers: { lifespan_bonus: 50, mental_resist: 0.5, demon_resist: 0.3 } },
  },
  {
    id: 'x03', name: '先天道体', grade: '玄品', rarity: 0.2, category: '体质',
    description: '先天道体，与道共鸣，修行顺遂。',
    effects: { attr_bonuses: { root_bone: 2, comprehension: 2, mindset: 2, luck: 2 }, modifiers: { max_qi_bonus: 80, cultivation_speed: 0.2 } },
  },
  {
    id: 'x04', name: '天煞孤星', grade: '玄品', rarity: 0.2, category: '命格',
    description: '天煞入命，克亲妨友，孤苦终生。',
    effects: {
      attr_bonuses: {}, modifiers: {},
      positive_effects: { attr_bonuses: { luck: 3 }, modifiers: { extra_event_option: 1 } },
      negative_effects: { attr_bonuses: {}, modifiers: { romance_blocked: true, npc_relation_penalty: -0.5 } },
    },
  },
  {
    id: 's01', name: '吞噬体质', grade: '仙品', rarity: 0.08, category: '体质',
    description: '万物皆可吞噬化为己用，成长无上限。',
    effects: { attr_bonuses: {}, modifiers: { cultivation_speed: 0.5, devour_effect: 0.5 } },
  },
  {
    id: 's02', name: '不死之身', grade: '仙品', rarity: 0.08, category: '肉身',
    description: '肉身不灭，滴血重生，万劫不灭。',
    effects: { attr_bonuses: {}, modifiers: { max_health_bonus: 200, health_regen: 5, death_resist: 1 } },
  },
  {
    id: 's03', name: '残缺神魂', grade: '仙品', rarity: 0.08, category: '神魂',
    description: '神魂虽残，却蕴含来自上界的异力。',
    effects: {
      attr_bonuses: {}, modifiers: {},
      positive_effects: { attr_bonuses: {}, modifiers: { death_resurrection: 1, soul_power_bonus: 0.3 } },
      negative_effects: { attr_bonuses: { comprehension: -2 }, modifiers: { learning_speed: -0.3 } },
    },
  },
  {
    id: 'd01', name: '逆天改命', grade: '神品', rarity: 0.02, category: '命运',
    description: '跳出三界外，不在五行中。命运由我不由天。',
    effects: { attr_bonuses: { root_bone: 5, comprehension: 5, mindset: 5, luck: 10 }, modifiers: { lifespan_bonus: 100, fate_rewrite: 1 } },
  },
]
