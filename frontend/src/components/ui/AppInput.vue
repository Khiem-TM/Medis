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
  autocomplete?: string
}>()

defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" :for="id" class="text-xs font-semibold tracking-tight" style="color: #5A6985;">
      {{ label }}
      <span v-if="required" class="text-error ml-0.5">*</span>
    </label>

    <div class="relative">
      <div v-if="$slots.prefix" class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none" style="color: #8A95AC;">
        <slot name="prefix" />
      </div>

      <input
        :id="id"
        :type="type ?? 'text'"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :autocomplete="autocomplete"
        :class="[
          'w-full rounded-xl border px-3 py-2.5 text-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-0',
          error
            ? 'border-error focus:ring-error/20 focus:border-error bg-white'
            : 'focus:ring-primary/20 focus:border-primary focus:bg-white',
          disabled ? 'cursor-not-allowed opacity-60' : '',
          $slots.prefix ? 'pl-9' : '',
          $slots.suffix ? 'pr-9' : '',
        ]"
        :style="error
          ? ''
          : disabled
            ? 'background: #F3F5F7; border-color: rgba(12,29,66,0.10); color: #0C1D42;'
            : 'background: #F8FAFB; border-color: rgba(12,29,66,0.10); color: #0C1D42;'"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      />

      <div v-if="$slots.suffix" class="absolute inset-y-0 right-0 flex items-center pr-3" style="color: #8A95AC;">
        <slot name="suffix" />
      </div>
    </div>

    <p v-if="error" class="text-xs text-error">{{ error }}</p>
    <p v-else-if="hint" class="text-xs" style="color: #8A95AC;">{{ hint }}</p>
  </div>
</template>
