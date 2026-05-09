<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  change?: string
  changePositive?: boolean
  iconColor?: string
}>()
</script>

<template>
  <div
    class="bg-white rounded-2xl p-5 flex items-start justify-between gap-4"
    style="border: 1px solid rgba(12,29,66,0.08); box-shadow: 0 1px 2px rgba(12,29,66,.04);"
  >
    <div class="flex-1 min-w-0">
      <p class="text-xs font-bold uppercase tracking-widest truncate" style="color: #8A95AC;">{{ label }}</p>
      <p class="text-3xl font-bold mt-1 tracking-tight tabular-nums" style="color: #0C1D42;">{{ value }}</p>
      <p v-if="change" :class="['text-xs mt-1 font-semibold', changePositive ? 'text-tertiary' : 'text-error']">
        {{ change }}
      </p>
    </div>
    <div
      :class="['w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0', iconColor ?? 'bg-primary-fixed']"
    >
      <slot name="icon">
        <svg class="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      </slot>
    </div>
  </div>
</template>
