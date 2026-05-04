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
}

.narrative-box.clickable {
  cursor: pointer;
}

.nb-text {
  font-size: 1.05rem;
  line-height: 1.8;
  color: #2c2c2c;
  margin: 0;
  white-space: pre-wrap;
}

.nb-cursor {
  animation: blink 0.8s step-end infinite;
  color: #4a7c7c;
}

.nb-hint {
  position: absolute;
  bottom: 8px;
  right: 16px;
  font-size: 0.75rem;
  color: #999;
  margin: 0;
}

@keyframes blink {
  50% { opacity: 0; }
}
</style>
