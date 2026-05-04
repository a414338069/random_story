<script setup lang="ts">
import type { EventOption } from '@/core/types'

defineProps<{
  option: EventOption
}>()
</script>

<template>
  <button class="option-card">
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
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  text-align: left;
  transition: all 0.2s;
  font-family: inherit;
  font-size: 1rem;
  min-height: 44px;
}

.option-card:hover {
  border-color: #4a7c7c;
  background: rgba(74, 124, 124, 0.05);
  transform: translateX(4px);
}

.option-card:active {
  transform: translateX(2px);
}

.oc-text {
  color: #2c2c2c;
}

.oc-preview {
  font-size: 0.8rem;
  color: #888;
}
</style>
