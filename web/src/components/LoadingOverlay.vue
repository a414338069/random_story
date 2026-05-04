<script setup lang="ts">
defineProps<{
  loading?: boolean
}>()
</script>

<template>
  <Teleport to="body">
    <div v-if="loading !== false" class="loading-overlay">
      <div class="lo-content">
        <div class="lo-spinner" />
        <p class="lo-text">天命推演中…</p>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.loading-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

.lo-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.lo-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(245, 240, 232, 0.3);
  border-top-color: #f5f0e8;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.lo-text {
  color: #f5f0e8;
  font-size: 1rem;
  letter-spacing: 2px;
  margin: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
