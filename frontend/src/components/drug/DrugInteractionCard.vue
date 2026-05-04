<script setup lang="ts">
defineProps<{
  drug1: string
  drug2: string
  severity?: 'danger' | 'warning' | 'safe'
  description?: string
  recommendation?: string
}>()
</script>

<template>
  <div :class="[
    'bg-card rounded-xl border border-outline-variant border-l-4 p-4 transition-shadow hover:shadow-sm',
    severity === 'danger'  ? 'border-l-error' :
    severity === 'warning' ? 'border-l-warning' :
    severity === 'safe'    ? 'border-l-tertiary' : 'border-l-outline',
  ]">
    <!-- Drug pair -->
    <div class="flex items-center gap-2 mb-3 flex-wrap">
      <span class="px-2.5 py-1 bg-surface-container rounded-lg text-xs font-semibold text-on-surface-variant">
        {{ drug1 }}
      </span>
      <svg class="w-4 h-4 text-outline flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
      </svg>
      <span class="px-2.5 py-1 bg-surface-container rounded-lg text-xs font-semibold text-on-surface-variant">
        {{ drug2 }}
      </span>
      <!-- Severity badge -->
      <span :class="[
        'ml-auto px-2 py-0.5 rounded-full text-xs font-semibold',
        severity === 'danger'  ? 'bg-error-container text-error' :
        severity === 'warning' ? 'bg-yellow-100 text-yellow-800' :
        severity === 'safe'    ? 'bg-tertiary-fixed text-tertiary' : 'bg-surface-container text-outline',
      ]">
        {{ severity === 'danger' ? 'Nguy hiểm' : severity === 'warning' ? 'Cẩn thận' : severity === 'safe' ? 'An toàn' : 'Không rõ' }}
      </span>
    </div>

    <!-- Description -->
    <p v-if="description" class="text-sm text-on-surface-variant mb-2">{{ description }}</p>

    <!-- Recommendation -->
    <p v-if="recommendation" class="text-xs text-outline bg-surface-container-low rounded-lg px-3 py-2">
      💡 {{ recommendation }}
    </p>
  </div>
</template>
