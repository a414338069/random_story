<script setup lang="ts">
defineProps<{
  text: string
  displayed: string
  isTyping: boolean
}>()
</script>

<template>
  <div class="narrative-box" :class="{ clickable: isTyping }">
    <p class="nb-text">{{ displayed }}</p>
    <span v-if="isTyping" class="nb-cursor">▍</span>
    <p v-if="isTyping" class="nb-hint">点击跳过</p>
  </div>
</template>

<style scoped>
.narrative-box {
  flex: 1;
  padding: 24px 16px;
  cursor: default;
  position: relative;
  min-height: 200px;
  background: #ffffff;
  border: 1px solid #e8e2d9;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(26,24,20,0.05);
  margin-bottom: 16px;
}

.narrative-box.clickable {
  cursor: pointer;
}

.nb-text {
  font-size: 1rem;
  line-height: 1.8;
  color: #3d3a34;
  margin: 0;
  white-space: pre-wrap;
}

.nb-cursor {
  animation: blink 0.8s step-end infinite;
  color: #b8b3a8;
}

.nb-hint {
  position: absolute;
  bottom: 8px;
  right: 16px;
  font-size: 0.72rem;
  color: var(--text-muted, #8a857d);
  margin: 0;
}

@keyframes blink {
  50% { opacity: 0; }
}
</style>
