<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue'
import { NCollapse, NCollapseItem } from 'naive-ui'
import type { EventLogEntry } from '@/core/types'

const props = defineProps<{
  entries: EventLogEntry[]
  activeDisplayed: string
  isTyping: boolean
  showContinueHint: boolean
}>()

defineEmits<{
  'skip-typewriter': []
  'continue-click': []
}>()

const logContainer = ref<HTMLElement>()

const COLLAPSE_THRESHOLD = 15

interface GroupedEntry {
  groupName: string
  entries: EventLogEntry[]
}

const groupedEntries = computed<GroupedEntry[]>(() => {
  const groups: GroupedEntry[] = []
  const groupMap = new Map<string, EventLogEntry[]>()

  for (const entry of props.entries) {
    const key = entry.realm ?? '早期事件'
    if (!groupMap.has(key)) {
      groupMap.set(key, [])
    }
    groupMap.get(key)!.push(entry)
  }

  for (const [groupName, entries] of groupMap) {
    groups.push({ groupName, entries })
  }

  return groups
})

const shouldCollapse = computed(() => props.entries.length > COLLAPSE_THRESHOLD)

const defaultExpandedNames = computed(() => {
  if (!shouldCollapse.value || groupedEntries.value.length === 0) return []
  return [groupedEntries.value[groupedEntries.value.length - 1].groupName]
})

watch(
  () => props.entries.length,
  async () => {
    await nextTick()
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  }
)
</script>

<template>
  <div ref="logContainer" class="narrative-log">
    <!-- 折叠模式: entries > 15 -->
    <template v-if="shouldCollapse">
      <NCollapse :default-expanded-names="defaultExpandedNames" class="realm-collapse">
        <NCollapseItem
          v-for="group in groupedEntries"
          :key="group.groupName"
          :title="`${group.groupName} — ${group.entries.length} 个事件`"
          :name="group.groupName"
        >
          <div
            v-for="entry in group.entries"
            :key="entry.id"
            class="log-entry"
            :class="{ 'log-entry--active': entry.phase !== 'done' }"
          >
            <div v-if="entry.title" class="log-entry__title">{{ entry.title }}</div>
            <div class="log-entry__narrative">
              <template v-if="entry.phase !== 'done'">
                {{ activeDisplayed }}
                <span v-if="isTyping" class="log-cursor">▍</span>
              </template>
              <template v-else>
                {{ entry.narrative }}
              </template>
            </div>
            <div v-if="entry.chosenOptionId && entry.phase === 'done'" class="log-choice">
              已选择
            </div>
            <div v-if="entry.aftermath && entry.phase === 'done'">
              <div class="log-aftermath">
                <span v-if="entry.aftermath.cultivation_change > 0"
                  >+{{ entry.aftermath.cultivation_change.toFixed(1) }} 修为</span
                >
                <span v-if="entry.aftermath.age_advance > 0">年龄 +{{ entry.aftermath.age_advance }}</span>
              </div>
              <div v-if="entry.aftermath.narrative" class="log-aftermath-narrative">
                {{ entry.aftermath.narrative }}
              </div>
              <div
                v-if="entry.aftermath.breakthrough"
                class="log-breakthrough"
                :class="
                  entry.aftermath.breakthrough.success
                    ? 'log-breakthrough--success'
                    : 'log-breakthrough--fail'
                "
              >
                <span v-if="entry.aftermath.breakthrough.success">✨ 突破成功</span>
                <span v-else-if="entry.aftermath.breakthrough.success === false">💥 突破失败</span>
              </div>
            </div>
          </div>
        </NCollapseItem>
      </NCollapse>
    </template>

    <!-- 平铺模式: entries ≤ 15 -->
    <template v-else>
      <div
        v-for="entry in entries"
        :key="entry.id"
        class="log-entry"
        :class="{ 'log-entry--active': entry.phase !== 'done' }"
      >
        <div v-if="entry.title" class="log-entry__title">{{ entry.title }}</div>
        <div class="log-entry__narrative">
          <template v-if="entry.phase !== 'done'">
            {{ activeDisplayed }}
            <span v-if="isTyping" class="log-cursor">▍</span>
          </template>
          <template v-else>
            {{ entry.narrative }}
          </template>
        </div>
        <div v-if="entry.chosenOptionId && entry.phase === 'done'" class="log-choice">
          已选择
        </div>
        <div v-if="entry.aftermath && entry.phase === 'done'">
          <div class="log-aftermath">
            <span v-if="entry.aftermath.cultivation_change > 0"
              >+{{ entry.aftermath.cultivation_change.toFixed(1) }} 修为</span
            >
            <span v-if="entry.aftermath.age_advance > 0">年龄 +{{ entry.aftermath.age_advance }}</span>
          </div>
          <div v-if="entry.aftermath.narrative" class="log-aftermath-narrative">
            {{ entry.aftermath.narrative }}
          </div>
          <div
            v-if="entry.aftermath.breakthrough"
            class="log-breakthrough"
            :class="
              entry.aftermath.breakthrough.success
                ? 'log-breakthrough--success'
                : 'log-breakthrough--fail'
            "
          >
            <span v-if="entry.aftermath.breakthrough.success">✨ 突破成功</span>
            <span v-else-if="entry.aftermath.breakthrough.success === false">💥 突破失败</span>
          </div>
        </div>
      </div>
    </template>

    <div
      v-if="showContinueHint"
      class="continue-hint"
      @click.stop="$emit('continue-click')"
    >
      <span class="continue-hint__text">点击继续 ▾</span>
    </div>
  </div>
</template>

<style scoped>
.narrative-log {
  flex: 1;
  overflow-y: auto;
  scroll-behavior: smooth;
  padding: 16px;
}

.log-entry {
  padding: 12px 0;
  border-bottom: 1px solid #f0ece5;
  animation: fadeSlideIn 0.3s ease;
}

.log-entry:last-child {
  border-bottom: none;
}

.log-entry__title {
  font-family: var(--font-display, 'Noto Serif SC', Georgia, serif);
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--ink-black, #1a1814);
  margin-bottom: 6px;
}

.log-entry__narrative {
  font-size: 0.95rem;
  line-height: 1.8;
  color: #3d3a34;
  white-space: pre-wrap;
}

.log-cursor {
  animation: blink 0.8s step-end infinite;
  color: #b8b3a8;
}

.log-choice {
  font-size: 0.8rem;
  color: #b8b3a8;
  margin-top: 4px;
}

.log-aftermath {
  display: flex;
  gap: 12px;
  font-size: 0.8rem;
  color: #b8b3a8;
  margin-top: 4px;
}

.log-aftermath-narrative {
  font-size: 0.8rem;
  color: #b8b3a8;
  margin-top: 6px;
  line-height: 1.5;
}

.log-breakthrough {
  margin-top: 6px;
  font-size: 0.85rem;
  font-weight: 600;
}

.log-breakthrough--success {
  color: #b8860b;
}

.log-breakthrough--fail {
  color: #dc3545;
}

.continue-hint {
  text-align: center;
  padding: 16px;
  cursor: pointer;
}

.continue-hint__text {
  color: var(--text-muted, #8a857d);
  font-size: 0.85rem;
  animation: pulse 2s ease-in-out infinite;
}

.realm-collapse {
  --n-text-color: var(--text-secondary, #3d3a34);
}

.realm-collapse :deep(.n-collapse-item__header-main) {
  font-family: var(--font-display, 'Noto Serif SC', Georgia, serif);
  font-size: 0.85rem;
  color: var(--text-muted, #8a857d);
  padding: 4px 0;
}

.realm-collapse :deep(.n-collapse-item) {
  margin-bottom: 0;
}

.realm-collapse :deep(.n-collapse-item__content-wrapper) {
  padding: 0;
}

@keyframes fadeSlideIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes blink {
  50% {
    opacity: 0;
  }
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.5;
  }
  50% {
    opacity: 1;
  }
}
</style>
