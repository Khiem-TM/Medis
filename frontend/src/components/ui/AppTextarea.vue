<script setup lang="ts">
defineProps<{
  modelValue?: string
  label?: string
  error?: string
  hint?: string
  placeholder?: string
  disabled?: boolean
  required?: boolean
  rows?: number
  id?: string
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
    <textarea
      :id="id"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :rows="rows ?? 3"
      :class="[
        'w-full rounded-lg border px-3 py-2 text-sm text-on-surface placeholder-outline resize-y transition-colors focus:outline-none focus:ring-2',
        error
          ? 'border-error focus:ring-error/30 focus:border-error'
          : 'border-outline-variant focus:ring-primary/30 focus:border-primary',
        disabled ? 'bg-surface-container-low cursor-not-allowed' : 'bg-card',
      ]"
      @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
    />
    <p v-if="error" class="text-xs text-error">{{ error }}</p>
    <p v-else-if="hint" class="text-xs text-outline">{{ hint }}</p>
  </div>
</template>
