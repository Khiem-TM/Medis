<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  modelValue: string
  length?: number
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const len = props.length ?? 6
const digits = ref<string[]>(Array(len).fill(''))
const inputs = ref<HTMLInputElement[]>([])

watch(() => props.modelValue, (val) => {
  const chars = (val || '').split('').slice(0, len)
  digits.value = [...chars, ...Array(len - chars.length).fill('')]
})

function onInput(index: number, e: Event) {
  const input = e.target as HTMLInputElement
  const char = input.value.replace(/\D/g, '').slice(-1)
  digits.value[index] = char
  emit('update:modelValue', digits.value.join(''))
  if (char && index < len - 1) {
    inputs.value[index + 1]?.focus()
  }
}

function onKeydown(index: number, e: KeyboardEvent) {
  if (e.key === 'Backspace' && !digits.value[index] && index > 0) {
    digits.value[index - 1] = ''
    emit('update:modelValue', digits.value.join(''))
    inputs.value[index - 1]?.focus()
  }
}

function onPaste(e: ClipboardEvent) {
  e.preventDefault()
  const text = e.clipboardData?.getData('text') || ''
  const nums = text.replace(/\D/g, '').slice(0, len)
  nums.split('').forEach((c, i) => { digits.value[i] = c })
  emit('update:modelValue', digits.value.join(''))
  const nextEmpty = digits.value.findIndex((d) => !d)
  const focusIdx = nextEmpty === -1 ? len - 1 : nextEmpty
  inputs.value[focusIdx]?.focus()
}
</script>

<template>
  <div class="flex gap-3 justify-center">
    <input
      v-for="(_, i) in digits"
      :key="i"
      :ref="(el) => { if (el) inputs[i] = el as HTMLInputElement }"
      type="text"
      inputmode="numeric"
      maxlength="1"
      :value="digits[i]"
      :disabled="disabled"
      :class="[
        'w-12 h-14 text-center text-2xl font-bold border-2 rounded-xl transition-colors focus:outline-none',
        digits[i]
          ? 'border-primary bg-primary-fixed text-primary'
          : 'border-outline-variant bg-card text-on-surface focus:border-primary focus:ring-2 focus:ring-primary/20',
        disabled ? 'opacity-50 cursor-not-allowed' : '',
      ]"
      @input="onInput(i, $event)"
      @keydown="onKeydown(i, $event)"
      @paste="onPaste"
    />
  </div>
</template>
