<script setup lang="ts">
import { useRouter } from 'vue-router'
import { NButton } from 'naive-ui'
import { useGameState } from '@/composables/useGameState'

const router = useRouter()
const { gameState, score, ending, grade } = useGameState()

function getGradeColor(g: string): string {
  switch (g) {
    case 'SSS': case 'SS': case 'S': return '#ff8f00'
    case 'A': case 'B': return '#4a7c7c'
    case 'C': return '#666'
    case 'D': return '#999'
    default: return '#999'
  }
}

function playAgain() {
  const { reset } = useGameState()
  reset()
  router.push('/')
}

function showLeaderboard() {
  window.alert('暂无记录')
}
</script>

<template>
  <div class="game-over">
    <div class="go-container">
      <h1 class="go-title">仙途已尽</h1>

      <div class="go-ending">
        <h2 class="go-ending-text">{{ ending || gameState?.endingId || '凡人终老' }}</h2>
      </div>

      <div class="go-score-section">
        <span class="go-grade" :style="{ color: getGradeColor(grade) }">
          {{ grade || '?' }}
        </span>
        <span class="go-score">{{ score }} 分</span>
      </div>

      <div v-if="gameState" class="go-summary">
        <p><strong>{{ gameState.name }}</strong></p>
        <p>境界：{{ gameState.realm || '凡人' }}</p>
        <p>享年：{{ gameState.age }} 岁</p>
        <p>事件：{{ gameState.eventCount }} 次</p>
      </div>

      <div class="go-actions">
        <NButton type="primary" size="large" @click="playAgain">
          再来一局
        </NButton>
        <NButton quaternary size="small" @click="showLeaderboard">
          排行榜
        </NButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.game-over {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f0e8 0%, #e8ddd0 50%, #d4c5b0 100%);
  padding: 20px;
}

.go-container {
  text-align: center;
  max-width: 400px;
}

.go-title {
  font-size: 2.5rem;
  color: #2c2c2c;
  margin-bottom: 32px;
  letter-spacing: 6px;
}

.go-ending {
  margin-bottom: 24px;
}

.go-ending-text {
  font-size: 1.8rem;
  color: #c23a2b;
  margin: 0;
  letter-spacing: 4px;
}

.go-score-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 24px;
}

.go-grade {
  font-size: 3rem;
  font-weight: 900;
}

.go-score {
  font-size: 1.3rem;
  color: #666;
}

.go-summary {
  margin-bottom: 32px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 8px;
}

.go-summary p {
  margin: 6px 0;
  color: #555;
  font-size: 1rem;
}

.go-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
</style>
