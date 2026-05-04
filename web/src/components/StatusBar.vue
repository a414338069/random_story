<script setup lang="ts">
import { useGameState } from '@/composables/useGameState'

const { gameState } = useGameState()
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
      <span class="sb-value">{{ gameState.cultivation.toFixed(0) }}</span>
    </span>
    <span class="sb-item">
      <span class="sb-label">灵石</span>
      <span class="sb-value">{{ gameState.spiritStones }}</span>
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
}
</style>
