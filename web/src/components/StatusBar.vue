<script setup lang="ts">
import { computed } from 'vue'
import { useGameState } from '@/composables/useGameState'
import { useAnimatedNumber } from '@/composables/useAnimatedNumber'

const { gameState } = useGameState()

const cultivationSource = computed(() => gameState.value?.cultivation ?? 0)
const spiritStonesSource = computed(() => gameState.value?.spiritStones ?? 0)

const cultivation = useAnimatedNumber(cultivationSource, 600)
const spiritStones = useAnimatedNumber(spiritStonesSource, 600)
</script>

<template>
  <div v-if="gameState" class="status-bar">
    <span class="sb-item">
      <span class="sb-label">境界</span>
      <span class="sb-value">{{ gameState.realm || '无' }}</span>
    </span>
    <span class="sb-item">
      <span class="sb-label">年龄</span>
      <span class="sb-value">{{ gameState.age }}/{{ gameState.lifespan }}</span>
    </span>
    <span class="sb-item">
      <span class="sb-label">修为</span>
      <span
        class="sb-value"
        :class="{
          'sb-value--up': cultivation.direction.value === 'up',
          'sb-value--down': cultivation.direction.value === 'down',
        }"
      >{{ cultivation.formatted() }}</span>
    </span>
    <span class="sb-item">
      <span class="sb-label">灵石</span>
      <span
        class="sb-value"
        :class="{
          'sb-value--up': spiritStones.direction.value === 'up',
          'sb-value--down': spiritStones.direction.value === 'down',
        }"
      >{{ spiritStones.formatted() }}</span>
    </span>
    <span class="sb-item">
      <span class="sb-label">事件</span>
      <span class="sb-value">{{ gameState.eventCount }}</span>
    </span>
  </div>
</template>

<style scoped>
.status-bar {
  display: flex;
  justify-content: space-around;
  padding: 12px 8px;
  background: rgba(44, 44, 44, 0.95);
  color: #f5f0e8;
  font-size: 0.85rem;
  gap: 4px;
  position: sticky;
  top: 0;
  z-index: 10;
}

.sb-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.sb-label {
  font-size: 0.7rem;
  opacity: 0.7;
  letter-spacing: 1px;
}

.sb-value {
  font-size: 0.95rem;
  font-weight: 700;
  transition: color 0.3s ease, text-shadow 0.3s ease;
}

.sb-value--up {
  color: #4ade80;
  text-shadow: 0 0 6px rgba(74, 222, 128, 0.4);
}

.sb-value--down {
  color: #f87171;
  text-shadow: 0 0 6px rgba(248, 113, 113, 0.4);
}
</style>
