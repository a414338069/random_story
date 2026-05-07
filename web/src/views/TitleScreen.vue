<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NCard, NSpace, NText, NSpin, useMessage, useDialog } from 'naive-ui'
import { useSaveLoad } from '@/composables/useSaveLoad'
import { getOrCreateUserId } from '@/composables/useSaveLoad'

const router = useRouter()
const message = useMessage()
const dialog = useDialog()
const { saves, loading, listMySaves, loadMySave, deleteMySave } = useSaveLoad()

const TOTAL_SLOTS = 3

const hasSaves = computed(() => saves.value.length > 0)

function getSaveForSlot(slot: number) {
  return saves.value.find((s) => s.slot === slot)
}

onMounted(async () => {
  await listMySaves()
})

function startNewGame(slot: number) {
  router.push({ path: '/select', query: { slot: String(slot) } })
}

async function continueGame(slot: number) {
  try {
    await loadMySave(slot)
    router.push('/game')
  } catch {
    message.error('加载存档失败')
  }
}

function confirmDelete(slot: number, name: string) {
  dialog.warning({
    title: '删除存档',
    content: `确定要删除「${name}」的存档吗？此操作不可撤销。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await deleteMySave(slot)
        message.success('存档已删除')
        await listMySaves()
      } catch {
        message.error('删除存档失败')
      }
    },
  })
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

      <NSpin :show="loading" size="small">
        <!-- 有存档：显示3个档位 -->
        <div v-if="hasSaves" class="save-slots">
          <div
            v-for="slot in TOTAL_SLOTS"
            :key="slot"
            class="save-slot-wrapper"
          >
            <NCard
              size="small"
              :class="['save-card', getSaveForSlot(slot) ? 'save-card--occupied' : 'save-card--empty']"
              :bordered="true"
              @click="getSaveForSlot(slot) && continueGame(slot)"
              :style="{ cursor: getSaveForSlot(slot) ? 'pointer' : 'default' }"
            >
              <template v-if="getSaveForSlot(slot)">
                <div class="save-info">
                  <div class="save-name">
                    <NText depth="1" class="save-char-name">{{ getSaveForSlot(slot)!.name }}</NText>
                    <NText depth="3" class="save-realm">{{ getSaveForSlot(slot)!.realm }}</NText>
                  </div>
                  <div class="save-detail">
                    <span>{{ getSaveForSlot(slot)!.age }}岁</span>
                    <span class="save-sep">·</span>
                    <span>事件 {{ getSaveForSlot(slot)!.eventCount }}</span>
                  </div>
                  <NSpace :size="8" class="save-actions">
                    <NButton
                      size="small"
                      type="primary"
                      @click="continueGame(slot)"
                    >
                      继续
                    </NButton>
                    <NButton
                      size="small"
                      quaternary
                      type="error"
                      @click.stop="confirmDelete(slot, getSaveForSlot(slot)!.name)"
                    >
                      删除
                    </NButton>
                  </NSpace>
                </div>
              </template>
              <template v-else>
                <div class="save-empty">
                  <NText depth="3" class="save-empty-text">空档位</NText>
                  <NButton
                    size="small"
                    quaternary
                    type="primary"
                    @click="startNewGame(slot)"
                  >
                    开始新游戏
                  </NButton>
                </div>
              </template>
            </NCard>
          </div>
        </div>

        <!-- 无存档：显示原始单按钮 -->
        <NSpace v-else vertical :size="20" class="title-actions">
          <NButton
            type="primary"
            size="large"
            @click="startNewGame(1)"
            class="start-btn"
          >
            开始修仙
          </NButton>
        </NSpace>
      </NSpin>

      <NButton quaternary size="small" @click="showLeaderboard" class="leaderboard-btn">
        排行榜
      </NButton>
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
  width: 100%;
  max-width: 400px;
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
  margin: 0 0 40px 0;
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
  border-radius: var(--border-radius-sm);
}

.leaderboard-btn {
  margin-top: 24px;
}

/* Save slots grid */
.save-slots {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 8px;
}

.save-slot-wrapper {
  width: 100%;
}

.save-card {
  transition: box-shadow var(--transition-fast), border-color var(--transition-fast);
}

.save-card--occupied {
  border-color: var(--accent, #b8b3a8);
}

.save-card--occupied:hover {
  border-color: var(--accent-hover, #a8a398);
  box-shadow: var(--card-shadow-hover);
}

.save-card--empty {
  border-style: dashed;
  border-color: var(--border-color, #e8e2d9);
}

.save-card--empty:hover {
  border-color: var(--accent, #b8b3a8);
  box-shadow: var(--card-shadow);
}

/* Occupied save info */
.save-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  text-align: left;
}

.save-name {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.save-char-name {
  font-family: var(--font-display);
  font-size: 1.05rem;
  font-weight: 600;
}

.save-realm {
  font-size: 0.85rem;
}

.save-detail {
  font-size: 0.82rem;
  color: var(--text-muted, #8a857d);
}

.save-sep {
  margin: 0 2px;
}

.save-actions {
  margin-top: 4px;
}

/* Empty slot */
.save-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

.save-empty-text {
  font-size: 0.9rem;
  letter-spacing: 1px;
}
</style>
