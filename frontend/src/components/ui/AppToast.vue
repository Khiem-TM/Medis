<script setup lang="ts">
import type { Toast } from '@/stores/ui.store'

defineProps<{ toast: Toast }>()
defineEmits<{ dismiss: [] }>()
</script>

<template>
  <div
    :class="[
      'flex items-start gap-3 px-4 py-3 rounded-xl shadow-lg border text-sm max-w-sm w-full bg-card',
      toast.type === 'success'
        ? 'border-tertiary text-tertiary'
        : toast.type === 'error'
          ? 'border-error text-error'
          : toast.type === 'warning'
            ? 'border-yellow-400 text-yellow-700'
            : 'border-primary text-primary',
    ]"
  >
    <div class="flex-shrink-0 mt-0.5">
      <div
        :class="[
          'w-2 h-2 rounded-full mt-1',
          toast.type === 'success'
            ? 'bg-tertiary'
            : toast.type === 'error'
              ? 'bg-error'
              : toast.type === 'warning'
                ? 'bg-yellow-400'
                : 'bg-primary',
        ]"
      />
    </div>
    <p class="flex-1 text-on-surface">{{ toast.message }}</p>
    <button @click="$emit('dismiss')" class="flex-shrink-0 opacity-50 hover:opacity-100 text-outline">
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </div>
</template>
