<script setup lang="ts">
import { onMounted } from 'vue'
import { NButton } from 'naive-ui'
import StatusBar from '@/components/StatusBar.vue'
import NarrativeLog from '@/components/NarrativeLog.vue'
import OptionCard from '@/components/OptionCard.vue'
import LoadingOverlay from '@/components/LoadingOverlay.vue'
import { useGameLoop } from '@/composables/useGameLoop'

const {
  eventLog,
  currentEntry,
  aftermath,
  error,
  loading,
  phase,
  typewriter,
  advanceEvent,
  handleChoose,
  handleContinueClick,
  handleRetry,
  handleReturnHome,
} = useGameLoop()

onMounted(() => {
  advanceEvent()
})

function onGlobalClick() {
  if (phase.value === 'waiting_click') {
    handleContinueClick()
  } else if (typewriter.isTyping.value) {
    typewriter.skipToEnd()
  }
}

function onOptionClick(optionId: string) {
  handleChoose(optionId)
}
</script>

<template>
  <div class="game-main" @click="onGlobalClick">
    <StatusBar />

    <div class="gm-content">
      <div v-if="phase === 'fetching' && eventLog.length === 0" class="gm-loading">
        <div class="gm-spinner" />
        <p class="gm-loading-text">命运书写中...</p>
      </div>

      <div v-else-if="error" class="gm-error">
        <p class="gm-error-text">{{ error }}</p>
        <div class="gm-error-actions">
          <NButton @click="handleRetry">重试</NButton>
          <NButton quaternary @click="handleReturnHome">返回标题</NButton>
        </div>
      </div>

      <template v-else>
        <NarrativeLog
          :entries="eventLog"
          :active-displayed="typewriter.displayed.value"
          :is-typing="typewriter.isTyping.value"
          :show-continue-hint="phase === 'waiting_click'"
          @skip-typewriter="typewriter.skipToEnd()"
          @continue-click="handleContinueClick"
        />

        <div v-if="(phase === 'aftermath' || phase === 'waiting_click') && currentEntry?.phase === 'breakthrough' && aftermath" class="gm-aftermath">
          <p v-if="aftermath.narrative" class="gm-aftermath-narrative">
            {{ aftermath.narrative }}
          </p>
          <div v-if="aftermath.breakthrough" class="gm-breakthrough gm-breakthrough--active">
            <p class="gm-breakthrough-msg">{{ aftermath.breakthrough.message }}</p>
            <p class="gm-breakthrough-hint">
              点击继续你的修行之路
            </p>
          </div>
          <p v-if="aftermath.cultivation_change > 0" class="gm-aftermath-stat">
            +{{ aftermath.cultivation_change.toFixed(1) }} 修为
          </p>
          <p v-if="aftermath.age_advance > 0" class="gm-aftermath-stat">
            年龄增长 {{ aftermath.age_advance }} 岁
          </p>
        </div>
        <div v-else-if="phase === 'aftermath' && aftermath" class="gm-aftermath">
          <p v-if="aftermath.narrative" class="gm-aftermath-narrative">
            {{ aftermath.narrative }}
          </p>
          <div v-if="aftermath.breakthrough" class="gm-breakthrough">
            <p class="gm-breakthrough-msg">{{ aftermath.breakthrough.message }}</p>
          </div>
          <p v-if="aftermath.cultivation_change > 0" class="gm-aftermath-stat">
            +{{ aftermath.cultivation_change.toFixed(1) }} 修为
          </p>
          <p v-if="aftermath.age_advance > 0" class="gm-aftermath-stat">
            年龄增长 {{ aftermath.age_advance }} 岁
          </p>
        </div>

        <div v-if="phase === 'choosing' && currentEntry" class="gm-options">
          <OptionCard
            v-for="opt in currentEntry.options"
            :key="opt.id"
            :option="opt"
            @click="onOptionClick(opt.id)"
          />
        </div>
      </template>

      <LoadingOverlay v-if="loading && phase === 'submitting'" />
    </div>
  </div>
</template>

<style scoped>
.game-main {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--paper-white, #f6f3ed);
}

.gm-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0 16px 16px;
  overflow: hidden;
  position: relative;
}

.gm-loading,
.gm-error {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;
}

.gm-spinner {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 3px solid #e8e2d9;
  border-top-color: #b8b3a8;
  animation: spin 0.8s linear infinite;
}

.gm-loading-text {
  font-size: 0.9rem;
  color: var(--text-muted, #8a857d);
  letter-spacing: 2px;
}

.gm-error-text {
  color: #c06050;
  font-size: 1rem;
  text-align: center;
}

.gm-error-actions {
  display: flex;
  gap: 12px;
}

.gm-aftermath {
  text-align: center;
  padding: 12px;
  animation: fadeIn 0.3s ease;
}

.gm-aftermath p {
  margin: 2px 0;
  color: #b8b3a8;
  font-size: 0.9rem;
}

.gm-aftermath-narrative {
  color: #8a857d;
  font-size: 0.95rem;
  line-height: 1.6;
  margin-bottom: 8px;
}

.gm-breakthrough {
  background: linear-gradient(135deg, #fff8e7, #fef3d0);
  border: 1px solid #e8d9a0;
  border-radius: 8px;
  padding: 10px 16px;
  margin: 8px 0;
  animation: fadeIn 0.5s ease;
}

.gm-breakthrough--active {
  animation: breakthroughPulse 2s ease-in-out infinite;
  box-shadow: 0 0 20px rgba(212, 175, 55, 0.4);
  border-color: #d4af37;
}

.gm-breakthrough-msg {
  color: #8b6914;
  font-weight: 600;
  font-size: 0.95rem;
  margin: 0;
}

.gm-breakthrough-hint {
  color: #b8860b;
  font-size: 0.8rem;
  margin: 8px 0 0;
  animation: fadeInOut 2s ease-in-out infinite;
}

.gm-aftermath-stat {
  margin: 2px 0;
  color: #b8b3a8;
  font-size: 0.9rem;
}

.gm-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px 0;
  padding-top: 12px;
  border-top: 1px solid #f0ece5;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes breakthroughPulse {
  0%, 100% { box-shadow: 0 0 10px rgba(212, 175, 55, 0.3); }
  50% { box-shadow: 0 0 25px rgba(212, 175, 55, 0.6); }
}

@keyframes fadeInOut {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
