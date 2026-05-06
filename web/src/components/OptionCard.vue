<script setup lang="ts">
import type { EventOption } from '@/core/types'

defineProps<{
  option: EventOption
  disabled?: boolean
  pressed?: boolean
}>()

defineEmits<{
  click: []
}>()
</script>

<template>
  <button
    class="option-card"
    :class="{ 'option-card--pressed': pressed, 'option-card--disabled': disabled }"
    :disabled="disabled"
    @click.stop="$emit('click')"
  >
    <span class="oc-text">{{ option.text }}</span>
    <span v-if="option.consequence_preview" class="oc-preview">
      {{ option.consequence_preview }}
    </span>
  </button>
</template>

<style scoped>
.option-card {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 14px 20px;
  background: #ffffff;
  border: 1px solid #e8e2d9;
  border-radius: 8px;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s ease;
  font-family: inherit;
  font-size: 0.95rem;
  min-height: 44px;
  box-shadow: 0 1px 3px rgba(26,24,20,0.05);
}

.option-card:hover:not(.option-card--disabled) {
  border-color: #b8b3a8;
  box-shadow: 0 4px 12px rgba(26,24,20,0.08);
  transform: translateX(4px);
}

.option-card--pressed {
  transform: scale(0.97);
  background: #faf8f4;
  border-color: #b8b3a8;
}

.option-card--disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

.oc-text {
  color: #3d3a34;
}

.oc-preview {
  font-size: 0.78rem;
  color: var(--text-muted, #8a857d);
}
</style>
