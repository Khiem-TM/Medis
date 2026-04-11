<script setup lang="ts">
import AppSpinner from './AppSpinner.vue'

defineProps<{
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  disabled?: boolean
  type?: 'button' | 'submit' | 'reset'
  full?: boolean
}>()
</script>

<template>
  <button
    :type="type ?? 'button'"
    :disabled="disabled || loading"
    :class="[
      'inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed',
      // Size
      size === 'sm'
        ? 'px-3 py-1.5 text-sm'
        : size === 'lg'
          ? 'px-6 py-3 text-base'
          : 'px-4 py-2 text-sm',
      // Variant
      variant === 'primary' || !variant
        ? 'bg-[#10B981] text-white hover:bg-[#059669] focus:ring-[#10B981]'
        : variant === 'secondary'
          ? 'bg-[#F3F4F6] text-[#111827] hover:bg-[#E5E7EB] focus:ring-gray-300'
          : variant === 'ghost'
            ? 'bg-transparent text-[#6B7280] hover:bg-[#F9FAFB] hover:text-[#111827] focus:ring-gray-200'
            : variant === 'danger'
              ? 'bg-[#EF4444] text-white hover:bg-red-600 focus:ring-red-400'
              : 'border border-[#E5E7EB] bg-white text-[#374151] hover:bg-[#F9FAFB] focus:ring-gray-200',
      full ? 'w-full' : '',
    ]"
  >
    <AppSpinner v-if="loading" size="sm" />
    <slot />
  </button>
</template>
