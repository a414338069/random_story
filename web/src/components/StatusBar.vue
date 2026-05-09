<script setup lang="ts">
import { computed } from 'vue'
import { NButton, NIcon } from 'naive-ui'
import { PersonOutline } from '@vicons/ionicons5'
import { useGameState } from '@/composables/useGameState'
import { useAnimatedNumber } from '@/composables/useAnimatedNumber'

const emit = defineEmits<{
  togglePanel: []
}>()

const { gameState } = useGameState()

const cultivationSource = computed(() => gameState.value?.cultivation ?? 0)
const spiritStonesSource = computed(() => gameState.value?.spiritStones ?? 0)

const cultivation = useAnimatedNumber(cultivationSource, 600)
const spiritStones = useAnimatedNumber(spiritStonesSource, 600)
</script>

<template>
  <div v-if="gameState" class="status-bar">
    <div class="sb-group">
      <span class="sb-item">
        <span class="sb-label">境界</span>
        <span class="sb-value">{{ gameState.realm || '无' }}</span>
      </span>
      <span class="sb-divider">·</span>
      <span class="sb-item">
        <span class="sb-label">年龄</span>
        <span class="sb-value">{{ gameState.age }}/{{ gameState.lifespan }}</span>
      </span>
      <span class="sb-divider">·</span>
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
      <span class="sb-divider">·</span>
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
    </div>
    <NButton quaternary size="small" class="sb-character-btn" @click="emit('togglePanel')">
      <template #icon>
        <NIcon><PersonOutline /></NIcon>
      </template>
      人物
    </NButton>
  </div>
</template>

<style scoped>
.status-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: var(--paper-white, #f6f3ed);
  border-bottom: 1px solid var(--border-color, #e8e2d9);
  position: sticky;
  top: 0;
  z-index: 10;
  gap: 16px;
}

.sb-group {
  display: flex;
  align-items: center;
  gap: 20px;
}

.sb-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  min-width: 48px;
}

.sb-label {
  font-size: 0.75rem;
  color: var(--text-muted, #8a857d);
  letter-spacing: 0.5px;
  font-weight: 400;
}

.sb-value {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--ink-black, #1a1814);
  transition: color 0.3s ease;
  font-family: var(--font-display, 'Noto Serif SC', Georgia, serif);
}

.sb-value--up {
  color: #7da87d;
}

.sb-value--down {
  color: #c06050;
}

.sb-divider {
  color: var(--accent, #b8b3a8);
  font-size: 1rem;
  line-height: 1;
  margin-top: 12px;
  align-self: flex-start;
}

.sb-character-btn {
  flex-shrink: 0;
}

/* Mobile responsive */
@media (max-width: 480px) {
  .status-bar {
    padding: 10px 12px;
    gap: 12px;
  }

  .sb-group {
    gap: 12px;
  }

  .sb-item {
    min-width: 40px;
  }

  .sb-label {
    font-size: 0.7rem;
  }

  .sb-value {
    font-size: 0.85rem;
  }

  .sb-divider {
    font-size: 0.85rem;
  }
}
</style>
