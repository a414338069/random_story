<script setup lang="ts">
const props = defineProps<{
  modelValue: { rootBone: number; comprehension: number; mindset: number; luck: number }
}>()

const emit = defineEmits<{
  'update:modelValue': [value: typeof props.modelValue]
}>()

const labels: Record<string, string> = {
  rootBone: '根骨',
  comprehension: '悟性',
  mindset: '心境',
  luck: '气运',
}

function change(key: keyof typeof props.modelValue, delta: number) {
  const next = props.modelValue[key] + delta
  if (next < 0 || next > 10) return
  const total = Object.values(props.modelValue).reduce((a, b) => a + b, 0)
  if (delta > 0 && total >= 10) return
  emit('update:modelValue', {
    ...props.modelValue,
    [key]: next,
  })
}

function setValue(key: keyof typeof props.modelValue, val: number) {
  const clamped = Math.max(0, Math.min(10, val))
  const otherKeys = Object.keys(props.modelValue).filter(k => k !== key) as (keyof typeof props.modelValue)[]
  const otherSum = otherKeys.reduce((sum, k) => sum + props.modelValue[k], 0)
  const maxAllowed = 10 - otherSum
  emit('update:modelValue', {
    ...props.modelValue,
    [key]: Math.min(clamped, maxAllowed),
  })
}
</script>

<template>
  <div class="attr-allocator">
    <div
      v-for="(label, key) in labels"
      :key="key"
      class="attr-row"
    >
      <span class="attr-label">{{ label }}</span>
      <button class="attr-btn" @click="change(key as any, -1)">−</button>
      <input
        class="attr-input"
        type="number"
        :value="modelValue[key as keyof typeof modelValue]"
        min="0"
        max="10"
        @input="setValue(key as any, Number(($event.target as HTMLInputElement).value))"
      />
      <button class="attr-btn" @click="change(key as any, 1)">+</button>
    </div>
  </div>
</template>

<style scoped>
.attr-allocator {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px 0;
}

.attr-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.attr-label {
  width: 60px;
  font-size: 1rem;
  color: #2c2c2c;
}

.attr-btn {
  width: 36px;
  height: 36px;
  border: 1px solid #ccc;
  border-radius: 4px;
  background: #fff;
  font-size: 1.2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.attr-btn:hover {
  background: #f0f0f0;
}

.attr-input {
  width: 60px;
  height: 36px;
  text-align: center;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1rem;
}
</style>
