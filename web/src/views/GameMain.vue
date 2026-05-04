<script setup lang="ts">
import { onMounted } from 'vue'
import { NButton } from 'naive-ui'
import StatusBar from '@/components/StatusBar.vue'
import NarrativeBox from '@/components/NarrativeBox.vue'
import OptionCard from '@/components/OptionCard.vue'
import LoadingOverlay from '@/components/LoadingOverlay.vue'
import { useGameLoop } from '@/composables/useGameLoop'

const {
  currentEvent,
  aftermath,
  error,
  loading,
  phase,
  typewriter,
  advanceEvent,
  handleChoose,
  handleRetry,
  handleReturnHome,
} = useGameLoop()

onMounted(() => {
  advanceEvent()
})

function skipTypewriter() {
  if (typewriter.isTyping.value) {
    typewriter.skipToEnd()
  }
}
</script>

<template>
  <div class="game-main">
    <StatusBar />

    <div class="gm-content">
      <div v-if="phase === 'fetching' || (loading && phase === 'typing')" class="gm-loading">
        天命推演中…
      </div>

      <div v-else-if="error" class="gm-error">
        <p class="gm-error-text">{{ error }}</p>
        <div class="gm-error-actions">
          <NButton @click="handleRetry">重试</NButton>
          <NButton quaternary @click="handleReturnHome">返回标题</NButton>
        </div>
      </div>

      <template v-else-if="currentEvent">
        <NarrativeBox
          :text="currentEvent.narrative"
          :displayed="typewriter.displayed.value"
          :is-typing="typewriter.isTyping.value"
          @click="skipTypewriter"
        />

        <div v-if="phase === 'aftermath' && aftermath" class="gm-aftermath">
          <p v-if="aftermath.cultivation_change > 0">
            +{{ aftermath.cultivation_change.toFixed(1) }} 修为
          </p>
          <p v-if="aftermath.age_advance > 0">
            年龄增长 {{ aftermath.age_advance }} 岁
          </p>
        </div>

        <div v-if="phase === 'choosing'" class="gm-options">
          <OptionCard
            v-for="opt in currentEvent.options"
            :key="opt.id"
            :option="opt"
            @click="handleChoose(opt.id)"
          />
        </div>
      </template>

      <LoadingOverlay v-if="loading && phase !== 'fetching'" />
    </div>
  </div>
</template>

<style scoped>
.game-main {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: #f5f0e8;
}

.gm-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
  overflow-y: auto;
  position: relative;
}

.gm-loading,
.gm-error {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.gm-error-text {
  color: #c23a2b;
  font-size: 1.1rem;
  text-align: center;
}

.gm-error-actions {
  display: flex;
  gap: 12px;
}

.gm-aftermath {
  text-align: center;
  padding: 16px;
  margin-top: 12px;
  border-top: 1px dashed #ccc;
  animation: fadeIn 0.3s ease;
}

.gm-aftermath p {
  margin: 4px 0;
  color: #4a7c7c;
  font-size: 1rem;
}

.gm-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: auto;
  padding-top: 20px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
