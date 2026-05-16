<script setup lang="ts">
defineProps<{
  modelValue?: string | number | null
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
  'update:modelValue': [value: string | number | null]
}>()
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" :for="id" class="text-xs font-semibold uppercase tracking-[0.16em] text-outline">
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
        :value="modelValue ?? ''"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :autocomplete="autocomplete"
        :class="[
          'w-full rounded-2xl border px-3.5 py-3 text-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-0',
          error
            ? 'border-error focus:ring-error/20 focus:border-error bg-white/90'
            : 'focus:ring-primary/20 focus:border-primary focus:bg-white/90',
          disabled ? 'cursor-not-allowed opacity-60' : '',
          $slots.prefix ? 'pl-9' : '',
          $slots.suffix ? 'pr-9' : '',
        ]"
        :style="error
          ? 'backdrop-filter: blur(10px);'
          : disabled
            ? 'background: rgba(243,243,243,0.85); border-color: rgba(188,201,197,0.9); color: #1a1c1c; backdrop-filter: blur(10px);'
            : 'background: rgba(255,255,255,0.62); border-color: rgba(188,201,197,0.72); color: #1a1c1c; backdrop-filter: blur(10px);'"
        @input="$emit('update:modelValue', type === 'number'
          ? (($event.target as HTMLInputElement).value === '' ? null : Number(($event.target as HTMLInputElement).value))
          : ($event.target as HTMLInputElement).value)"
      />

      <div v-if="$slots.suffix" class="absolute inset-y-0 right-0 flex items-center pr-3 text-outline">
        <slot name="suffix" />
      </div>
    </div>

    <p v-if="error" class="text-xs text-error">{{ error }}</p>
    <p v-else-if="hint" class="text-xs text-outline">{{ hint }}</p>
  </div>
</template>
