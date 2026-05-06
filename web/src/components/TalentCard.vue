<script setup lang="ts">
import type { TalentCard } from '@/core/types'
import { getGradeColor, getGradeBgColor, getGradeClass } from '@/core/talents'

const props = defineProps<{ card: TalentCard }>()
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
  </div>
</template>

<style scoped>
.talent-card {
  background: #ffffff;
  border: 1px solid #e8e2d9;
  border-radius: 8px;
  padding: 16px;
  width: 140px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  box-shadow: 0 1px 3px rgba(26,24,20,0.05);
  position: relative;
  overflow: hidden;
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
}

.tc-category {
  font-size: 0.75rem;
  color: var(--text-muted, #8a857d);
}

.tc-desc {
  margin: 0;
  font-size: 0.78rem;
  color: #8a857d;
  line-height: 1.4;
}
</style>
