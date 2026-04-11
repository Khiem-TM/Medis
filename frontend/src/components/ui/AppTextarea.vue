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
    <label v-if="label" :for="id" class="text-sm font-medium text-[#374151]">
      {{ label }}
      <span v-if="required" class="text-[#EF4444] ml-0.5">*</span>
    </label>
    <textarea
      :id="id"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :rows="rows ?? 3"
      :class="[
        'w-full rounded-lg border px-3 py-2 text-sm text-[#111827] placeholder-[#9CA3AF] resize-y transition-colors focus:outline-none focus:ring-2',
        error
          ? 'border-[#EF4444] focus:ring-[#EF4444]/30 focus:border-[#EF4444]'
          : 'border-[#E5E7EB] focus:ring-[#10B981]/30 focus:border-[#10B981]',
        disabled ? 'bg-[#F9FAFB] cursor-not-allowed' : 'bg-white',
      ]"
      @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
    />
    <p v-if="error" class="text-xs text-[#EF4444]">{{ error }}</p>
    <p v-else-if="hint" class="text-xs text-[#6B7280]">{{ hint }}</p>
  </div>
</template>
