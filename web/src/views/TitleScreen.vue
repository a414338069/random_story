<script setup lang="ts">
import { useRouter } from 'vue-router'
import { NButton, NSpace } from 'naive-ui'

const router = useRouter()

function startGame() {
  router.push('/select')
}

function showLeaderboard() {
  window.alert('暂无记录')
}
</script>

<template>
  <div class="title-screen">
    <div class="title-content">
      <h1 class="title-main">重生模拟器</h1>
      <p class="title-sub">AI修仙人生手帐</p>
      <NSpace vertical :size="20" class="title-actions">
        <NButton type="primary" size="large" @click="startGame" class="start-btn">
          开始修仙
        </NButton>
        <NButton quaternary size="small" @click="showLeaderboard">
          排行榜
        </NButton>
      </NSpace>
    </div>
  </div>
</template>

<style scoped>
.title-screen {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--paper-white, #f6f3ed);
  padding: 20px;
}

.title-content {
  text-align: center;
}

.title-main {
  font-family: var(--font-display);
  font-size: 2.8rem;
  font-weight: 700;
  color: var(--ink-black, #1a1814);
  margin: 0 0 8px 0;
  letter-spacing: 4px;
}

.title-sub {
  font-size: 1.1rem;
  color: var(--text-muted, #8a857d);
  margin: 0 0 48px 0;
  letter-spacing: 2px;
  font-weight: 400;
}

.title-actions {
  align-items: center;
}

.start-btn {
  min-width: 200px;
  font-size: 1.05rem;
  padding: 12px 48px;
  border-radius: 6px;
}
</style>
