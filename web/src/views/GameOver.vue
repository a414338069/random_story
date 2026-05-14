<script setup lang="ts">
import { useRouter } from 'vue-router'
import { NButton, ref } from 'naive-ui'
import { useGameState } from '@/composables/useGameState'
import LeaderboardModal from '@/components/LeaderboardModal.vue'

const router = useRouter()
const { gameState, score, ending, grade } = useGameState()
const showLeaderboardModal = ref(false)

function getGradeColor(g: string): string {
  switch (g) {
    case 'SSS': case 'SS': case 'S': return '#1a1814'
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
  showLeaderboardModal.value = true
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

  <LeaderboardModal v-model:show="showLeaderboardModal" />
</template>

<style scoped>
.game-over {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--paper-white, #f6f3ed);
  padding: 20px;
}

.go-container {
  text-align: center;
  max-width: 400px;
}

.go-title {
  font-family: var(--font-display);
  font-size: 2.2rem;
  color: var(--ink-black, #1a1814);
  margin-bottom: 32px;
  letter-spacing: 4px;
}

.go-ending {
  margin-bottom: 24px;
}

.go-ending-text {
  font-family: var(--font-display);
  font-size: 1.6rem;
  color: #b8b3a8;
  margin: 0;
  letter-spacing: 2px;
}

.go-score-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 24px;
}

.go-grade {
  font-size: 2.8rem;
  font-weight: 900;
}

.go-score {
  font-size: 1.1rem;
  color: var(--text-muted, #8a857d);
}

.go-summary {
  margin-bottom: 32px;
  padding: 20px;
  background: #ffffff;
  border: 1px solid #e8e2d9;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(26,24,20,0.05);
}

.go-summary p {
  margin: 6px 0;
  color: #3d3a34;
  font-size: 0.95rem;
}

.go-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
</style>
