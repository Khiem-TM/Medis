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
    <label v-if="label" :for="id" class="text-sm font-medium text-[#374151]">
      {{ label }}
      <span v-if="required" class="text-[#EF4444] ml-0.5">*</span>
    </label>
    <select
      :id="id"
      :value="modelValue"
      :disabled="disabled"
      :class="[
        'w-full rounded-lg border px-3 py-2 text-sm text-[#111827] transition-colors focus:outline-none focus:ring-2 appearance-none bg-white',
        error
          ? 'border-[#EF4444] focus:ring-[#EF4444]/30'
          : 'border-[#E5E7EB] focus:ring-[#10B981]/30 focus:border-[#10B981]',
        disabled ? 'bg-[#F9FAFB] cursor-not-allowed' : '',
      ]"
      @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
    >
      <option v-if="placeholder" value="">{{ placeholder }}</option>
      <option v-for="opt in options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
    </select>
    <p v-if="error" class="text-xs text-[#EF4444]">{{ error }}</p>
    <p v-else-if="hint" class="text-xs text-[#6B7280]">{{ hint }}</p>
  </div>
</template>
