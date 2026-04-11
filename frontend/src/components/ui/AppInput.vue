<script setup lang="ts">
defineProps<{
  modelValue?: string | number
  label?: string
  error?: string
  hint?: string
  type?: string
  placeholder?: string
  disabled?: boolean
  required?: boolean
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

    <div class="relative">
      <div v-if="$slots.prefix" class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-[#9CA3AF]">
        <slot name="prefix" />
      </div>

      <input
        :id="id"
        :type="type ?? 'text'"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :class="[
          'w-full rounded-lg border px-3 py-2 text-sm text-[#111827] placeholder-[#9CA3AF] transition-colors focus:outline-none focus:ring-2 focus:ring-offset-0',
          error
            ? 'border-[#EF4444] focus:ring-[#EF4444]/30 focus:border-[#EF4444]'
            : 'border-[#E5E7EB] focus:ring-[#10B981]/30 focus:border-[#10B981]',
          disabled ? 'bg-[#F9FAFB] cursor-not-allowed' : 'bg-white',
          $slots.prefix ? 'pl-9' : '',
          $slots.suffix ? 'pr-9' : '',
        ]"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      />

      <div v-if="$slots.suffix" class="absolute inset-y-0 right-0 flex items-center pr-3 text-[#9CA3AF]">
        <slot name="suffix" />
      </div>
    </div>

    <p v-if="error" class="text-xs text-[#EF4444]">{{ error }}</p>
    <p v-else-if="hint" class="text-xs text-[#6B7280]">{{ hint }}</p>
  </div>
</template>
