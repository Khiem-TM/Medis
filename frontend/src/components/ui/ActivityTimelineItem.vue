<script setup lang="ts">
defineProps<{
  action: string
  detail?: string
  timestamp: string
  variant?: 'default' | 'info' | 'warning' | 'success' | 'danger'
  last?: boolean
}>()
</script>

<template>
  <div class="flex gap-3">
    <!-- Dot + line -->
    <div class="flex flex-col items-center flex-shrink-0">
      <div :class="[
        'w-2.5 h-2.5 rounded-full mt-1.5 flex-shrink-0',
        variant === 'success' ? 'bg-tertiary' :
        variant === 'warning' ? 'bg-warning' :
        variant === 'danger'  ? 'bg-error' :
        variant === 'info'    ? 'bg-secondary' : 'bg-primary',
      ]" />
      <div v-if="!last" class="w-px flex-1 bg-outline-variant mt-1" />
    </div>

    <!-- Content -->
    <div class="pb-4 flex-1 min-w-0">
      <p class="text-sm font-medium text-on-surface truncate">{{ action }}</p>
      <p v-if="detail" class="text-xs text-outline truncate mt-0.5">{{ detail }}</p>
      <p class="text-xs text-outline mt-0.5">{{ timestamp }}</p>
    </div>
  </div>
</template>
