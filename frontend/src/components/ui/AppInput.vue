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
    <label v-if="label" :for="id" class="text-sm font-medium text-on-surface-variant">
      {{ label }}
      <span v-if="required" class="text-error ml-0.5">*</span>
    </label>

    <div class="relative">
      <div v-if="$slots.prefix" class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-outline">
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
          'w-full rounded-lg border px-3 py-2 text-sm text-on-surface placeholder-outline transition-colors focus:outline-none focus:ring-2 focus:ring-offset-0',
          error
            ? 'border-error focus:ring-error/30 focus:border-error'
            : 'border-outline-variant focus:ring-primary/30 focus:border-primary',
          disabled ? 'bg-surface-container-low cursor-not-allowed' : 'bg-card',
          $slots.prefix ? 'pl-9' : '',
          $slots.suffix ? 'pr-9' : '',
        ]"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      />

      <div v-if="$slots.suffix" class="absolute inset-y-0 right-0 flex items-center pr-3 text-outline">
        <slot name="suffix" />
      </div>
    </div>

    <p v-if="error" class="text-xs text-error">{{ error }}</p>
    <p v-else-if="hint" class="text-xs text-outline">{{ hint }}</p>
  </div>
</template>
