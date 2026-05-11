<script setup lang="ts">
import { computed } from 'vue'
import type { TalentCard } from '@/core/types'
import {
  getGradeColor,
  getGradeBgColor,
  getGradeClass,
  formatModifierValue,
  getModifierLabel,
} from '@/core/talents'

const props = defineProps<{ card: TalentCard }>()

const attrNameMap: Record<string, string> = {
  root_bone: '根骨',
  comprehension: '悟性',
  mindset: '心境',
  luck: '气运',
}

interface EffectItem {
  label: string
  value: string
  positive: boolean
}

function collectAttrs(
  source: Record<string, number> | undefined,
  items: EffectItem[],
) {
  if (!source) return
  for (const [key, val] of Object.entries(source)) {
    if (val === 0) continue
    const name = attrNameMap[key] ?? key
    const sign = val > 0 ? '+' : ''
    items.push({ label: name, value: `${sign}${val}`, positive: val > 0 })
  }
}

function collectMods(
  source: Record<string, number | boolean> | undefined,
  items: EffectItem[],
  defaultPositive: boolean,
) {
  if (!source) return
  for (const [key, val] of Object.entries(source)) {
    if (val === 0 || val === false) continue
    const label = getModifierLabel(key)
    const formatted = formatModifierValue(val)
    const positive = typeof val === 'boolean' ? defaultPositive : val > 0
    items.push({ label, value: formatted, positive })
  }
}

const displayEffects = computed<EffectItem[]>(() => {
  const items: EffectItem[] = []
  const { effects } = props.card

  collectAttrs(effects.attr_bonuses, items)
  collectAttrs(effects.positive_effects?.attr_bonuses, items)
  collectAttrs(effects.negative_effects?.attr_bonuses, items)

  collectMods(effects.modifiers, items, true)
  collectMods(effects.positive_effects?.modifiers, items, true)
  collectMods(effects.negative_effects?.modifiers, items, false)

  return items
})

const hasEffects = computed(() => displayEffects.value.length > 0)
</script>

<template>
  <div
    class="talent-card"
    :class="getGradeClass(card.grade)"
    :style="{
      borderColor: getGradeColor(card.grade),
      background: getGradeBgColor(card.grade),
    }"
  >
    <span class="tc-grade" :style="{ color: getGradeColor(card.grade) }">
      {{ card.grade }}
    </span>
    <h4 class="tc-name">{{ card.name }}</h4>
    <span class="tc-category">{{ card.category }}</span>
    <p class="tc-desc">{{ card.description }}</p>
    <div v-if="hasEffects" class="tc-effects">
      <span
        v-for="(item, i) in displayEffects"
        :key="i"
        class="effect-tag"
        :class="item.positive ? 'effect-pos' : 'effect-neg'"
      >{{ item.label }}{{ item.value }}</span>
    </div>
  </div>
</template>

<style scoped>
.talent-card {
  background: #ffffff;
  border: 1px solid #e8e2d9;
  border-radius: 8px;
  padding: 16px;
  width: 140px;
  min-width: 140px;
  max-width: 140px;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  text-align: center;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  box-shadow: 0 1px 3px rgba(26,24,20,0.05);
  position: relative;
  overflow: hidden;
  box-sizing: border-box;
}

.talent-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(26,24,20,0.08);
}

/* Grade indicator via left border accent */
.grade-common {
  border-left: 3px solid #b8b3a8;
}

.grade-uncommon {
  border-left: 3px solid #7da8b5;
}

.grade-rare {
  border-left: 3px solid #9b7db5;
}

.grade-legendary {
  border-left: 3px solid #c9a76e;
}

.grade-mythic {
  border-left: 3px solid #c06050;
}

.tc-grade {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 1px;
  color: var(--text-muted, #8a857d);
}

.tc-name {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #1a1814;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
}

.tc-category {
  font-size: 0.75rem;
  color: var(--text-muted, #8a857d);
  flex-shrink: 0;
}

.tc-desc {
  margin: 0;
  font-size: 0.78rem;
  color: #8a857d;
  line-height: 1.4;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.tc-effects {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
  justify-content: center;
  flex-shrink: 0;
  max-height: 80px;
  overflow-y: auto;
}

.effect-tag {
  font-size: 0.68rem;
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.effect-pos {
  color: #52c41a;
  background: rgba(82, 196, 26, 0.1);
}

.effect-neg {
  color: #ff4d4f;
  background: rgba(255, 77, 79, 0.1);
}
</style>
