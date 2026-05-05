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
  border: 2px solid;
  border-radius: 8px;
  padding: 16px;
  width: 140px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  text-align: center;
  transition: transform 0.2s, box-shadow 0.3s;
  position: relative;
  overflow: hidden;
}

.talent-card:hover {
  transform: translateY(-4px);
}

/* 凡品 Common — plain, understated */
.grade-common {
  border-style: solid;
  border-color: #8a8a8a;
  box-shadow: none;
}

/* 灵品 Uncommon — soft blue glow */
.grade-uncommon {
  box-shadow:
    0 0 8px rgba(91, 143, 191, 0.3),
    0 0 16px rgba(91, 143, 191, 0.1);
}

/* 玄品 Rare — purple gradient border via pseudo-element */
.grade-rare {
  border-color: transparent;
  background-clip: padding-box;
}

.grade-rare::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 8px;
  padding: 2px;
  background: linear-gradient(135deg, #7c5ba5, #a87ccf, #5b3d8a);
  mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  mask-composite: exclude;
  -webkit-mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  pointer-events: none;
  box-shadow: 0 0 12px rgba(124, 91, 165, 0.25);
}

/* 仙品 Legendary — gold shimmer + animation */
.grade-legendary {
  border-color: transparent;
  animation: goldShimmer 3s ease-in-out infinite;
}

.grade-legendary::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 8px;
  padding: 2px;
  background: linear-gradient(
    135deg,
    #c9a76e,
    #e8d5a8,
    #c9a76e,
    #a08040,
    #c9a76e
  );
  background-size: 200% 200%;
  animation: goldBorderShift 4s linear infinite;
  mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  mask-composite: exclude;
  -webkit-mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  pointer-events: none;
}

@keyframes goldShimmer {
  0%, 100% { box-shadow: 0 0 10px rgba(201, 167, 110, 0.3), 0 0 20px rgba(201, 167, 110, 0.1); }
  50% { box-shadow: 0 0 16px rgba(201, 167, 110, 0.5), 0 0 30px rgba(201, 167, 110, 0.2); }
}

@keyframes goldBorderShift {
  0% { background-position: 0% 50%; }
  100% { background-position: 200% 50%; }
}

/* 神品 Mythic — vermilion pulse */
.grade-mythic {
  border-color: transparent;
  animation: mythicPulse 2.5s ease-in-out infinite;
}

.grade-mythic::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 8px;
  padding: 2px;
  background: linear-gradient(135deg, #c23a2b, #e85545, #a02020, #c23a2b);
  background-size: 200% 200%;
  animation: goldBorderShift 3s linear infinite;
  mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  mask-composite: exclude;
  -webkit-mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  pointer-events: none;
}

@keyframes mythicPulse {
  0%, 100% { box-shadow: 0 0 12px rgba(194, 58, 43, 0.3), 0 0 24px rgba(194, 58, 43, 0.1); }
  50% { box-shadow: 0 0 20px rgba(194, 58, 43, 0.5), 0 0 36px rgba(194, 58, 43, 0.2); }
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
