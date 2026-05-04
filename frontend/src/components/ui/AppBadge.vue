<script setup lang="ts">
defineProps<{
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'purple' | 'primary'
  size?: 'sm' | 'md'
}>()
</script>

<template>
  <span
    :class="[
      'inline-flex items-center font-medium rounded-full',
      size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-0.5 text-xs',
      variant === 'success'
        ? 'bg-tertiary-fixed text-tertiary'
        : variant === 'warning'
          ? 'bg-yellow-100 text-yellow-800'
          : variant === 'danger'
            ? 'bg-error-container text-error'
            : variant === 'info'
              ? 'bg-secondary-container text-secondary'
              : variant === 'primary'
                ? 'bg-primary-fixed text-primary'
                : variant === 'purple'
                  ? 'bg-purple-100 text-purple-800'
                  : 'bg-surface-container text-on-surface-variant',
    ]"
  >
    <slot />
  </span>
</template>
