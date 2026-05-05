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
  background: rgba(44, 44, 44, 0.7);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;
  z-index: 1000;
}

.lo-ink-drop {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  animation: inkDrop 1.6s ease-out infinite;
  background: radial-gradient(
    circle at 40% 40%,
    rgba(245, 240, 232, 0.9) 0%,
    rgba(245, 240, 232, 0.4) 30%,
    rgba(194, 58, 43, 0.3) 60%,
    transparent 70%
  );
  filter: blur(0.5px);
}

.lo-text {
  color: #f5f0e8;
  font-family: var(--font-family);
  font-size: 1.05rem;
  letter-spacing: 3px;
  margin: 0;
  opacity: 0;
  animation: textFadeIn 0.6s ease 0.5s forwards;
}

@keyframes inkDrop {
  0% {
    transform: scale(0);
    opacity: 0;
    box-shadow: 0 0 0 0 rgba(194, 58, 43, 0.4);
  }
  20% {
    transform: scale(0.3);
    opacity: 1;
  }
  50% {
    transform: scale(1);
    opacity: 0.9;
    box-shadow: 0 0 20px 8px rgba(194, 58, 43, 0.15);
  }
  70% {
    transform: scale(1.1);
    opacity: 0.6;
    box-shadow: 0 0 40px 16px rgba(194, 58, 43, 0.05);
  }
  100% {
    transform: scale(1.3);
    opacity: 0;
    box-shadow: 0 0 60px 24px transparent;
  }
}

@keyframes textFadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
