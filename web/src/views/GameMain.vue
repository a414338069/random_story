<script setup lang="ts">
import { ref, onMounted } from 'vue'
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

// 选项点击反馈状态
const selectedOptionId = ref<string | null>(null)
const optionsDisabled = ref(false)

function onOptionClick(optionId: string) {
  if (optionsDisabled.value || selectedOptionId.value) return
  selectedOptionId.value = optionId
  optionsDisabled.value = true
  // 200ms 延迟提交，增加触感反馈
  setTimeout(() => {
    handleChoose(optionId)
    // 提交后不清除状态，保持禁用直到下次事件
  }, 200)
}

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
        <div class="gm-ink-drop" />
        <p class="gm-loading-text">天命推演中...</p>
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
            :disabled="optionsDisabled"
            :pressed="selectedOptionId === opt.id"
            @click="onOptionClick(opt.id)"
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
  gap: 24px;
}

.gm-ink-drop {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  animation: inkDrop 1.6s ease-out infinite;
  background: radial-gradient(
    circle at 40% 40%,
    rgba(44, 44, 44, 0.9) 0%,
    rgba(44, 44, 44, 0.4) 30%,
    rgba(74, 124, 124, 0.3) 60%,
    transparent 70%
  );
  filter: blur(0.5px);
}

.gm-loading-text {
  font-family: var(--font-family);
  font-size: 1.05rem;
  color: var(--ink-black);
  letter-spacing: 3px;
  opacity: 0;
  animation: textFadeIn 0.6s ease 0.5s forwards;
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

@keyframes inkDrop {
  0% {
    transform: scale(0);
    opacity: 0;
    box-shadow: 0 0 0 0 rgba(74, 124, 124, 0.4);
  }
  20% {
    transform: scale(0.3);
    opacity: 1;
  }
  50% {
    transform: scale(1);
    opacity: 0.9;
    box-shadow: 0 0 20px 8px rgba(74, 124, 124, 0.15);
  }
  70% {
    transform: scale(1.1);
    opacity: 0.6;
    box-shadow: 0 0 40px 16px rgba(74, 124, 124, 0.05);
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
