<script setup lang="ts">
defineProps<{
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'purple'
  size?: 'sm' | 'md'
}>()
</script>

<template>
  <span
    :class="[
      'inline-flex items-center font-medium rounded-full',
      size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-0.5 text-xs',
      variant === 'success'
        ? 'bg-[#D1FAE5] text-[#065F46]'
        : variant === 'warning'
          ? 'bg-yellow-100 text-yellow-800'
          : variant === 'danger'
            ? 'bg-red-100 text-red-800'
            : variant === 'info'
              ? 'bg-blue-100 text-blue-800'
              : variant === 'purple'
                ? 'bg-purple-100 text-purple-800'
                : 'bg-[#F3F4F6] text-[#374151]',
    ]"
  >
    <slot />
  </span>
</template>
