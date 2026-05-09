<script setup lang="ts">
import { computed } from 'vue'
import {
  NDrawer,
  NDrawerContent,
  NTag,
  NProgress,
  NDivider,
  NSpace,
  NText,
} from 'naive-ui'
import type { NormalizedGameState, TalentCard } from '@/core/types'
import { talents } from '@/data/talents'

const props = defineProps<{
  visible: boolean
  gameState: NormalizedGameState
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  close: []
}>()

const localVisible = computed({
  get: () => props.visible,
  set: (val: boolean) => emit('update:visible', val),
})

function handleClose() {
  emit('update:visible', false)
  emit('close')
}

// ── realm tag colors ──

const realmColorType: Record<string, 'default' | 'info' | 'success' | 'warning' | 'error'> = {
  '凡人': 'default',
  '炼气': 'success',
  '筑基': 'info',
  '金丹': 'warning',
  '元婴': 'warning',
  '化神': 'error',
  '合体': 'error',
  '大乘': 'error',
  '渡劫飞升': 'warning',
}

function getRealmColor(realm: string): string {
  return realmColorType[realm] ?? 'default'
}

// ── attribute progress color ──

function getAttrProgressColor(value: number): string {
  if (value >= 8) return '#52c41a'
  if (value >= 5) return '#faad14'
  return '#ff4d4f'
}

// ── matched talents ──

const matchedTalents = computed<TalentCard[]>(() => {
  const ids = props.gameState?.talentIds ?? []
  return ids
    .map((id: string) => talents.find(t => t.id === id))
    .filter((t): t is TalentCard => t !== undefined)
})

// ── talent effects summary ──

const attrNameMap: Record<string, string> = {
  root_bone: '根骨',
  comprehension: '悟性',
  mindset: '心境',
  luck: '气运',
}

function getTalentEffectsSummary(talent: TalentCard): string {
  const bonuses = talent.effects.attr_bonuses
  const parts: string[] = []
  for (const [key, val] of Object.entries(bonuses)) {
    if (val === 0) continue
    const name = attrNameMap[key] ?? key
    const sign = val > 0 ? '+' : ''
    parts.push(`${name}${sign}${val}`)
  }
  return parts.length > 0 ? parts.join(' ') : '特殊效果'
}

function getTalentGradeType(grade: string): 'default' | 'info' | 'warning' | 'success' | 'error' {
  switch (grade) {
    case '凡品': return 'default'
    case '灵品': return 'info'
    case '玄品': return 'success'
    case '仙品': return 'warning'
    case '神品': return 'error'
    default: return 'default'
  }
}
</script>

<template>
  <n-drawer
    v-model:show="localVisible"
    :width="360"
    placement="right"
    @close="handleClose"
  >
    <n-drawer-content title="角色状态" closable>
      <div class="panel-root">
        <!-- ═══ Section 1: 基本信息 ═══ -->
        <div class="panel-section">
          <div class="section-title">基本信息</div>
          <n-space vertical :size="8">
            <div class="info-row">
              <span class="info-label">姓名</span>
              <span class="info-value">{{ gameState.name }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">性别</span>
              <span class="info-value">{{ gameState.gender }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">境界</span>
              <n-tag :type="getRealmColor(gameState.realm)" size="small" :bordered="false">
                {{ gameState.realm || '无' }}
              </n-tag>
            </div>
            <div class="info-row">
              <span class="info-label">门派</span>
              <span class="info-value">{{ gameState.faction || '散修' }}</span>
            </div>
          </n-space>
        </div>

        <n-divider />

        <!-- ═══ Section 2: 四维属性 ═══ -->
        <div class="panel-section">
          <div class="section-title">四维属性</div>
          <n-space vertical :size="10">
            <div v-for="attr in [
              { key: 'rootBone' as const, label: '根骨', value: gameState.attributes.rootBone },
              { key: 'comprehension' as const, label: '悟性', value: gameState.attributes.comprehension },
              { key: 'mindset' as const, label: '心境', value: gameState.attributes.mindset },
              { key: 'luck' as const, label: '气运', value: gameState.attributes.luck },
            ]" :key="attr.key" class="attr-row">
              <div class="attr-header">
                <span class="attr-label">{{ attr.label }}</span>
                <span class="attr-value" :style="{ color: getAttrProgressColor(attr.value) }">
                  {{ attr.value }} / 10
                </span>
              </div>
              <n-progress
                type="line"
                :percentage="Math.min(100, (attr.value / 10) * 100)"
                :color="getAttrProgressColor(attr.value)"
                :height="6"
                :border-radius="3"
                :show-indicator="false"
                processing
              />
            </div>
          </n-space>
        </div>

        <n-divider />

        <!-- ═══ Section 3: 天赋 ═══ -->
        <div class="panel-section">
          <div class="section-title">天赋</div>
          <div v-if="matchedTalents.length === 0" class="empty-hint">
            无天赋
          </div>
          <n-space v-else vertical :size="10">
            <div v-for="talent in matchedTalents" :key="talent.id" class="talent-row">
              <div class="talent-header">
                <span class="talent-name">{{ talent.name }}</span>
                <n-tag
                  :type="getTalentGradeType(talent.grade)"
                  size="tiny"
                  :bordered="false"
                >
                  {{ talent.grade }}
                </n-tag>
              </div>
              <n-text depth="3" class="talent-effects">
                {{ getTalentEffectsSummary(talent) }}
              </n-text>
            </div>
          </n-space>
        </div>

        <n-divider />

        <!-- ═══ Section 4: 物品与资源 ═══ -->
        <div class="panel-section">
          <div class="section-title">物品与资源</div>
          <n-space vertical :size="8">
            <div class="info-row">
              <span class="info-label">灵石</span>
              <span class="info-value resource-number">{{ gameState.spiritStones.toLocaleString() }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">背包</span>
              <span class="info-value">{{ gameState.inventory.length }} 件物品</span>
            </div>
            <div class="info-row">
              <span class="info-label">功法</span>
              <span class="info-value">{{ gameState.techniques.length }} 种</span>
            </div>
          </n-space>
        </div>

        <n-divider />

        <!-- ═══ Section 5: 状态 ═══ -->
        <div class="panel-section">
          <div class="section-title">状态</div>
          <n-space vertical :size="10">
            <div class="info-row">
              <span class="info-label">年龄 / 寿元</span>
              <span class="info-value">
                {{ gameState.age }} / {{ gameState.lifespan }}
              </span>
            </div>
            <div class="info-row">
              <span class="info-label">修为</span>
              <span class="info-value resource-number">{{ gameState.cultivation.toLocaleString() }}</span>
            </div>
            <div class="status-progress-row">
              <div class="attr-header">
                <span class="attr-label">境界进度</span>
                <span class="attr-value" :style="{ color: '#c9a76e' }">
                  {{ (gameState.realmProgress * 100).toFixed(0) }}%
                </span>
              </div>
              <n-progress
                type="line"
                :percentage="Math.min(100, gameState.realmProgress * 100)"
                color="#c9a76e"
                :height="8"
                :border-radius="4"
                :show-indicator="false"
                processing
              />
            </div>
          </n-space>
        </div>
      </div>
    </n-drawer-content>
  </n-drawer>
</template>

<style scoped>
.panel-root {
  padding: 4px 0 20px;
  color: #d4cfc6;
}

.panel-section {
  padding: 0 4px;
}

.section-title {
  font-size: 0.78rem;
  font-weight: 600;
  color: #c9a76e;
  text-transform: uppercase;
  letter-spacing: 2px;
  margin-bottom: 10px;
  padding-bottom: 4px;
  border-bottom: 1px solid rgba(201, 167, 110, 0.18);
}

/* ── info rows ── */
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2px 0;
}

.info-label {
  font-size: 0.82rem;
  color: #8a857d;
}

.info-value {
  font-size: 0.85rem;
  font-weight: 500;
  color: #e8e2d9;
}

.resource-number {
  font-family: 'Courier New', monospace;
  color: #f0c040;
}

/* ── attribute rows ── */
.attr-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.attr-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.attr-label {
  font-size: 0.82rem;
  color: #8a857d;
}

.attr-value {
  font-size: 0.82rem;
  font-weight: 600;
}

.status-progress-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-top: 2px;
}

/* ── talent rows ── */
.talent-row {
  padding: 8px 10px;
  background: rgba(201, 167, 110, 0.06);
  border-radius: 6px;
  border: 1px solid rgba(201, 167, 110, 0.1);
}

.talent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.talent-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: #e8e2d9;
}

.talent-effects {
  font-size: 0.75rem;
  line-height: 1.4;
}

/* ── empty hint ── */
.empty-hint {
  font-size: 0.82rem;
  color: #6b6560;
  font-style: italic;
  padding: 6px 0;
}
</style>
