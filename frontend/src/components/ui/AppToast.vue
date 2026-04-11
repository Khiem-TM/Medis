<script setup lang="ts">
import type { Toast } from '@/stores/ui.store'

defineProps<{ toast: Toast }>()
defineEmits<{ dismiss: [] }>()
</script>

<template>
  <div
    :class="[
      'flex items-start gap-3 px-4 py-3 rounded-lg shadow-lg border text-sm max-w-sm w-full',
      toast.type === 'success'
        ? 'bg-white border-[#10B981] text-[#065F46]'
        : toast.type === 'error'
          ? 'bg-white border-[#EF4444] text-red-800'
          : toast.type === 'warning'
            ? 'bg-white border-[#F59E0B] text-yellow-800'
            : 'bg-white border-[#3B82F6] text-blue-800',
    ]"
  >
    <div class="flex-shrink-0 mt-0.5">
      <div
        :class="[
          'w-2 h-2 rounded-full mt-1',
          toast.type === 'success'
            ? 'bg-[#10B981]'
            : toast.type === 'error'
              ? 'bg-[#EF4444]'
              : toast.type === 'warning'
                ? 'bg-[#F59E0B]'
                : 'bg-[#3B82F6]',
        ]"
      />
    </div>
    <p class="flex-1">{{ toast.message }}</p>
    <button @click="$emit('dismiss')" class="flex-shrink-0 opacity-50 hover:opacity-100">
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </div>
</template>
