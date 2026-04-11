<script setup lang="ts">
defineProps<{
  title?: string
  description?: string
  icon?: string
}>()
</script>

<template>
  <div class="flex flex-col items-center justify-center py-16 text-center">
    <div class="w-16 h-16 bg-[#F3F4F6] rounded-full flex items-center justify-center mb-4">
      <svg v-if="!icon" class="w-8 h-8 text-[#9CA3AF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
          d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
      </svg>
    </div>
    <h3 class="text-base font-medium text-[#374151]">{{ title ?? 'Không có dữ liệu' }}</h3>
    <p v-if="description" class="text-sm text-[#6B7280] mt-1 max-w-xs">{{ description }}</p>
    <div v-if="$slots.action" class="mt-4">
      <slot name="action" />
    </div>
  </div>
</template>
