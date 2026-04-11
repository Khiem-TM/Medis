<script setup lang="ts">
defineProps<{
  type?: 'success' | 'error' | 'warning' | 'info'
  title?: string
  dismissible?: boolean
}>()

const emit = defineEmits<{ dismiss: [] }>()
</script>

<template>
  <div
    :class="[
      'rounded-lg border p-4 flex gap-3',
      type === 'success'
        ? 'bg-[#D1FAE5] border-[#6EE7B7] text-[#065F46]'
        : type === 'error'
          ? 'bg-red-50 border-red-200 text-red-800'
          : type === 'warning'
            ? 'bg-yellow-50 border-yellow-200 text-yellow-800'
            : 'bg-blue-50 border-blue-200 text-blue-800',
    ]"
  >
    <!-- Icon -->
    <div class="flex-shrink-0 mt-0.5">
      <svg v-if="type === 'success'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <svg v-else-if="type === 'error'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <svg v-else-if="type === 'warning'" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    </div>

    <div class="flex-1 min-w-0">
      <p v-if="title" class="font-medium text-sm">{{ title }}</p>
      <div class="text-sm mt-0.5"><slot /></div>
    </div>

    <button v-if="dismissible" @click="emit('dismiss')" class="flex-shrink-0 opacity-60 hover:opacity-100">
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </div>
</template>
