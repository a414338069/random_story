<script setup lang="ts">
import type { TalentCard } from '@/core/types'
import { getGradeColor, getGradeBgColor } from '@/core/talents'

const props = defineProps<{ card: TalentCard }>()
</script>

<template>
  <div
    class="talent-card"
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
  border: 2px solid;
  border-radius: 8px;
  padding: 16px;
  width: 140px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
  transition: transform 0.2s;
}

.talent-card:hover {
  transform: translateY(-4px);
}

.tc-grade {
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 2px;
}

.tc-name {
  margin: 0;
  font-size: 1.1rem;
  color: #2c2c2c;
}

.tc-category {
  font-size: 0.8rem;
  color: #888;
}

.tc-desc {
  margin: 0;
  font-size: 0.8rem;
  color: #666;
  line-height: 1.4;
}
</style>
