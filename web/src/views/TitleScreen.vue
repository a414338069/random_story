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
      <p class="title-sub">AI修仙人生模拟器</p>
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
  background: linear-gradient(135deg, #f5f0e8 0%, #e8ddd0 50%, #d4c5b0 100%);
  padding: 20px;
}

.title-content {
  text-align: center;
}

.title-main {
  font-size: 3rem;
  font-weight: 900;
  color: #2c2c2c;
  margin: 0 0 12px 0;
  letter-spacing: 8px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
}

.title-sub {
  font-size: 1.2rem;
  color: #666;
  margin: 0 0 48px 0;
  letter-spacing: 4px;
}

.title-actions {
  align-items: center;
}

.start-btn {
  min-width: 200px;
  font-size: 1.1rem;
  padding: 12px 48px;
  border-radius: 4px;
}
</style>
