<script setup lang="ts">
defineProps<{
  loading?: boolean
}>()
</script>

<template>
  <Teleport to="body">
    <div v-if="loading !== false" class="loading-overlay">
      <div class="lo-ink-drop" />
      <p class="lo-text">天命推演中...</p>
    </div>
  </Teleport>
</template>

<style scoped>
.loading-overlay {
  position: fixed;
  inset: 0;
  background: rgba(246, 243, 237, 0.85);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  z-index: 1000;
}

.lo-ink-drop {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 3px solid #e8e2d9;
  border-top-color: #b8b3a8;
  animation: spin 0.8s linear infinite;
}

.lo-text {
  color: var(--text-muted, #8a857d);
  font-family: var(--font-family);
  font-size: 0.95rem;
  letter-spacing: 2px;
  margin: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
