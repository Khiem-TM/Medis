<script setup lang="ts">
defineProps<{
  modelValue?: string | number
  label?: string
  error?: string
  hint?: string
  placeholder?: string
  disabled?: boolean
  required?: boolean
  id?: string
  options: Array<{ label: string; value: string | number }>
}>()

defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<template>
  <div class="flex flex-col gap-1">
    <label v-if="label" :for="id" class="text-sm font-medium text-on-surface-variant">
      {{ label }}
      <span v-if="required" class="text-error ml-0.5">*</span>
    </label>
    <select
      :id="id"
      :value="modelValue"
      :disabled="disabled"
      :class="[
        'w-full rounded-lg border px-3 py-2 text-sm text-on-surface transition-colors focus:outline-none focus:ring-2 appearance-none bg-card',
        error
          ? 'border-error focus:ring-error/30'
          : 'border-outline-variant focus:ring-primary/30 focus:border-primary',
        disabled ? 'bg-surface-container-low cursor-not-allowed' : '',
      ]"
      @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
    >
      <option v-if="placeholder" value="">{{ placeholder }}</option>
      <option v-for="opt in options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
    </select>
    <p v-if="error" class="text-xs text-error">{{ error }}</p>
    <p v-else-if="hint" class="text-xs text-outline">{{ hint }}</p>
  </div>
</template>
