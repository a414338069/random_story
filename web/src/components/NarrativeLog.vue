<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import type { EventLogEntry } from '@/core/types'

const props = defineProps<{
  entries: EventLogEntry[]
  activeDisplayed: string
  isTyping: boolean
  showContinueHint: boolean
}>()

defineEmits<{
  'skip-typewriter': []
  'continue-click': []
}>()

const logContainer = ref<HTMLElement>()

watch(
  () => props.entries.length,
  async () => {
    await nextTick()
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  }
)
</script>

<template>
  <div ref="logContainer" class="narrative-log">
    <div
      v-for="entry in entries"
      :key="entry.id"
      class="log-entry"
      :class="{ 'log-entry--active': entry === entries[entries.length - 1] }"
    >
      <div v-if="entry.title" class="log-entry__title">{{ entry.title }}</div>
      <div class="log-entry__narrative">
        <template v-if="entry === entries[entries.length - 1]">
          {{ activeDisplayed }}
          <span v-if="isTyping" class="log-cursor">▍</span>
        </template>
        <template v-else>
          {{ entry.narrative }}
        </template>
      </div>
      <div v-if="entry.chosenOptionId && entry.phase === 'done'" class="log-choice">
        已选择
      </div>
      <div v-if="entry.aftermath && entry.phase === 'done'" class="log-aftermath">
        <span v-if="entry.aftermath.cultivation_change > 0"
          >+{{ entry.aftermath.cultivation_change.toFixed(1) }} 修为</span
        >
        <span v-if="entry.aftermath.age_advance > 0">年龄 +{{ entry.aftermath.age_advance }}</span>
      </div>
    </div>
    <div
      v-if="showContinueHint"
      class="continue-hint"
      @click.stop="$emit('continue-click')"
    >
      <span class="continue-hint__text">点击继续 ▾</span>
    </div>
  </div>
</template>

<style scoped>
.narrative-log {
  flex: 1;
  overflow-y: auto;
  scroll-behavior: smooth;
  padding: 16px;
}

.log-entry {
  padding: 12px 0;
  border-bottom: 1px solid #f0ece5;
  animation: fadeSlideIn 0.3s ease;
}

.log-entry:last-child {
  border-bottom: none;
}

.log-entry__title {
  font-family: var(--font-display, 'Noto Serif SC', Georgia, serif);
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--ink-black, #1a1814);
  margin-bottom: 6px;
}

.log-entry__narrative {
  font-size: 0.95rem;
  line-height: 1.8;
  color: #3d3a34;
  white-space: pre-wrap;
}

.log-cursor {
  animation: blink 0.8s step-end infinite;
  color: #b8b3a8;
}

.log-choice {
  font-size: 0.8rem;
  color: #b8b3a8;
  margin-top: 4px;
}

.log-aftermath {
  display: flex;
  gap: 12px;
  font-size: 0.8rem;
  color: #b8b3a8;
  margin-top: 4px;
}

.continue-hint {
  text-align: center;
  padding: 16px;
  cursor: pointer;
}

.continue-hint__text {
  color: var(--text-muted, #8a857d);
  font-size: 0.85rem;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes fadeSlideIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes blink {
  50% {
    opacity: 0;
  }
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}
</style>
