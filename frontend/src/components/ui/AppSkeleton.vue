<script setup lang="ts">
defineProps<{
  class?: string
  lines?: number
}>()
</script>

<template>
  <div v-if="lines && lines > 1" class="space-y-2">
    <div
      v-for="i in lines"
      :key="i"
      :class="['h-4 bg-[#E5E7EB] rounded animate-pulse', i === lines ? 'w-3/4' : 'w-full']"
    />
  </div>
  <div v-else :class="['bg-[#E5E7EB] rounded animate-pulse', $props.class ?? 'h-4 w-full']" />
</template>
