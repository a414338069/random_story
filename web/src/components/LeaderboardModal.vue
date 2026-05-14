<script setup lang="ts">
import { ref, watch } from 'vue'
import { NModal, NDataTable, NSpin, NEmpty, NButton, NTag } from 'naive-ui'
import { getLeaderboard } from '@/api/game'
import type { LeaderboardEntry } from '@/core/types'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
}>()

const loading = ref(false)
const leaderboardData = ref<LeaderboardEntry[]>([])
const errorMsg = ref<string | null>(null)

watch(() => props.show, (newShow) => {
  if (newShow) {
    loadLeaderboard()
  }
})

async function loadLeaderboard() {
  loading.value = true
  errorMsg.value = null
  leaderboardData.value = []
  try {
    leaderboardData.value = await getLeaderboard()
  } catch (e) {
    errorMsg.value = '加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function handleClose(show: boolean) {
  emit('update:show', show)
}

function getRankTagType(rank: number): 'warning' | 'info' | 'default' {
  if (rank === 1) return 'warning'
  if (rank === 2) return 'info'
  if (rank === 3) return 'default'
  return 'default'
}

function getRankTagEffect(rank: number): 'filled' | 'plain' {
  return rank <= 3 ? 'filled' : 'plain'
}

const columns = [
  {
    title: '排名',
    key: 'rank',
    width: 70,
    render: (row: LeaderboardEntry) => {
      return h(NTag, {
        type: getRankTagType(row.rank),
        effect: getRankTagEffect(row.rank),
        size: 'small',
        round: true,
      }, { default: () => `#${row.rank}` })
    },
  },
  {
    title: '角色名',
    key: 'player_name',
  },
  {
    title: '评分',
    key: 'score',
    width: 80,
    render: (row: LeaderboardEntry) => row.score.toLocaleString(),
  },
  {
    title: '境界',
    key: 'realm',
    width: 90,
  },
  {
    title: '结局',
    key: 'ending_id',
    ellipsis: { tooltip: true },
  },
]

import { h } from 'vue'
</script>

<template>
  <NModal
    :show="show"
    preset="card"
    title="排行榜"
    :style="{ width: '520px' }"
    :mask-closable="true"
    @update:show="handleClose"
  >
    <NSpin :show="loading">
      <div v-if="errorMsg" class="lb-error">
        <p class="lb-error-text">{{ errorMsg }}</p>
        <NButton size="small" @click="loadLeaderboard">重试</NButton>
      </div>

      <NEmpty v-else-if="leaderboardData.length === 0 && !loading" description="暂无记录" />

      <NDataTable
        v-else
        :columns="columns"
        :data="leaderboardData"
        :bordered="false"
        :single-line="false"
        size="small"
        :row-class-name="(row: LeaderboardEntry) => row.rank <= 3 ? `rank-top-${row.rank}` : ''"
      />
    </NSpin>
  </NModal>
</template>

<style scoped>
.lb-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px 0;
}
.lb-error-text {
  color: var(--text-muted, #8a857d);
  margin: 0;
}
:deep(.n-data-table) {
  --n-td-color: transparent;
  --n-th-color: transparent;
}
:deep(.n-data-table-tr) {
  transition: background var(--transition-fast);
}
:deep(.rank-top-1) {
  background: rgba(212, 175, 55, 0.08) !important;
}
:deep(.rank-top-2) {
  background: rgba(192, 192, 192, 0.08) !important;
}
:deep(.rank-top-3) {
  background: rgba(205, 127, 50, 0.06) !important;
}
</style>