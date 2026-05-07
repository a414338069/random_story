<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NButton, NInput, NRadio, NRadioGroup, NSpace, useMessage } from 'naive-ui'
import TalentCardComp from '@/components/TalentCard.vue'
import AttributeAllocator from '@/components/AttributeAllocator.vue'
import { drawCards, canReDraw } from '@/core/talents'
import { useGameState } from '@/composables/useGameState'
import { getOrCreateUserId } from '@/composables/useSaveLoad'
import { startGame } from '@/api/game'
import type { TalentCard } from '@/core/types'

const router = useRouter()
const route = useRoute()
const message = useMessage()
const { setSession, update } = useGameState()

const step = ref(1)
const name = ref('')
const gender = ref<'男' | '女'>('男')
const currentCards = ref<TalentCard[]>([])
const redrawCount = ref(0)
const attributes = ref({ rootBone: 3, comprehension: 3, mindset: 2, luck: 2 })
const loading = ref(false)

const attrSum = computed(() => {
  const a = attributes.value
  return a.rootBone + a.comprehension + a.mindset + a.luck
})

const canConfirm = computed(() => {
  return attrSum.value === 10 && !loading.value
})

function startDraw() {
  currentCards.value = drawCards(3)
  step.value = 2
}

function handleRedraw() {
  if (!canReDraw(redrawCount.value)) {
    message.warning('已达到最大重抽次数')
    return
  }
  currentCards.value = drawCards(3)
  redrawCount.value++
}

async function handleConfirm() {
  if (!canConfirm.value) return
  loading.value = true
  try {
    const userId = getOrCreateUserId()
    const saveSlot = route.query.slot ? Number(route.query.slot) : undefined
    const result = await startGame({
      name: name.value || '无名散修',
      gender: gender.value,
      talent_card_ids: currentCards.value.map(c => c.id),
      attributes: {
        root_bone: Math.round(attributes.value.rootBone),
        comprehension: Math.round(attributes.value.comprehension),
        mindset: Math.round(attributes.value.mindset),
        luck: Math.round(attributes.value.luck),
      },
      user_id: userId,
      save_slot: saveSlot,
    })
    setSession(result.sessionId)
    update(result.state)
    router.push('/game')
  } catch (err: any) {
    message.error(err?.message || '创建角色失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="talent-select">
    <div class="ts-container">
      <h2 class="ts-title">创建角色</h2>

      <div v-if="step === 1" class="ts-step">
        <div class="ts-field">
          <label>角色名</label>
          <NInput v-model:value="name" placeholder="输入你的道号" maxlength="10" />
        </div>
        <div class="ts-field">
          <label>性别</label>
          <NRadioGroup v-model:value="gender">
            <NRadio value="男">男</NRadio>
            <NRadio value="女">女</NRadio>
          </NRadioGroup>
        </div>
        <NButton type="primary" size="large" @click="startDraw" class="ts-next-btn">
          抽取天赋
        </NButton>
      </div>

      <div v-if="step === 2" class="ts-step">
        <h3>选择天赋</h3>
        <div class="ts-cards">
          <TalentCardComp
            v-for="card in currentCards"
            :key="card.id"
            :card="card"
          />
        </div>
        <NSpace justify="center" :size="16">
          <NButton
            v-if="canReDraw(redrawCount)"
            quaternary
            @click="handleRedraw"
          >
            重新抽取 ({{ 4 - redrawCount }}次)
          </NButton>
          <NButton type="primary" @click="step = 3">
            确认天赋，分配属性
          </NButton>
        </NSpace>
      </div>

      <div v-if="step === 3" class="ts-step">
        <h3>分配属性（共10点）</h3>
        <AttributeAllocator v-model="attributes" />
        <p class="ts-sum">
          剩余点数：{{ 10 - attrSum }}
        </p>
        <NButton
          type="primary"
          size="large"
          :disabled="!canConfirm"
          :loading="loading"
          @click="handleConfirm"
          class="ts-confirm-btn"
        >
          开始修仙
        </NButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.talent-select {
  min-height: 100vh;
  background: var(--paper-white, #f6f3ed);
  padding: 40px 20px;
}

.ts-container {
  max-width: 480px;
  margin: 0 auto;
}

.ts-title {
  text-align: center;
  font-family: var(--font-display);
  font-size: 1.6rem;
  color: var(--ink-black, #1a1814);
  margin-bottom: 32px;
  letter-spacing: 2px;
}

.ts-step {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.ts-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ts-field label {
  font-size: 0.9rem;
  color: var(--text-muted, #8a857d);
}

.ts-next-btn,
.ts-confirm-btn {
  width: 100%;
  margin-top: 12px;
}

.ts-cards {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

.ts-sum {
  text-align: center;
  font-size: 0.95rem;
  color: var(--text-muted, #8a857d);
}
</style>
