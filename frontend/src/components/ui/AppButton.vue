<script setup lang="ts">
import AppSpinner from './AppSpinner.vue'

defineProps<{
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline' | 'gradient'
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
      'inline-flex items-center justify-center gap-2 rounded-2xl font-semibold tracking-tight transition-all focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-50',
      size === 'sm'
        ? 'px-3.5 py-2 text-xs'
        : size === 'lg'
          ? 'px-6 py-3.5 text-sm'
          : 'px-4 py-2.5 text-sm',
      variant === 'primary' || !variant
        ? 'bg-primary text-white hover:bg-primary-dk focus:ring-primary/40 shadow-sm'
        : variant === 'gradient'
          ? 'text-white hover:opacity-92 focus:ring-primary/40 shadow-sm'
          : variant === 'secondary'
            ? 'bg-white/70 text-on-surface hover:bg-white focus:ring-outline-variant'
            : variant === 'ghost'
              ? 'bg-transparent text-outline hover:bg-white/55 hover:text-on-surface focus:ring-outline-variant'
              : variant === 'danger'
                ? 'bg-error text-white hover:opacity-90 focus:ring-error/40 shadow-sm'
                : 'border border-outline-variant bg-white/60 text-on-surface-variant hover:bg-white/90 focus:ring-outline-variant',
      variant === 'gradient' ? 'bg-gradient-to-r from-primary to-secondary' : '',
      full ? 'w-full' : '',
    ]"
  >
    <AppSpinner v-if="loading" size="sm" />
    <slot />
  </button>
</template>
