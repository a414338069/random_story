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
      <span class="sb-label">修为进度</span>
      <span class="sb-value">{{ gameState.realmProgress != null ? (gameState.realmProgress * 100).toFixed(0) + '%' : '—' }}</span>
    </span>
  </div>
</template>

<style scoped>
.status-bar {
  display: flex;
  justify-content: space-around;
  padding: 10px 12px;
  background: #ffffff;
  border-bottom: 1px solid #e8e2d9;
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
  color: var(--text-muted, #8a857d);
  letter-spacing: 1px;
}

.sb-value {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--ink-black, #1a1814);
  transition: color 0.3s ease;
}

.sb-value--up {
  color: #7da87d;
}

.sb-value--down {
  color: #c06050;
}
</style>
