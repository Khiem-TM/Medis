<script setup lang="ts">
defineProps<{
  tabs: Array<{ key: string; label: string; count?: number }>
  modelValue: string
}>()

defineEmits<{
  'update:modelValue': [key: string]
}>()
</script>

<template>
  <div class="flex border-b border-outline-variant gap-1">
    <button
      v-for="tab in tabs"
      :key="tab.key"
      @click="$emit('update:modelValue', tab.key)"
      :class="[
        'px-4 py-3 text-sm font-medium transition-colors relative -mb-px',
        modelValue === tab.key
          ? 'text-primary border-b-2 border-primary'
          : 'text-outline hover:text-on-surface',
      ]"
    >
      {{ tab.label }}
      <span
        v-if="tab.count !== undefined"
        :class="[
          'ml-1.5 px-1.5 py-0.5 text-xs rounded-full font-semibold',
          modelValue === tab.key ? 'bg-primary-fixed text-primary' : 'bg-surface-container text-outline',
        ]"
      >{{ tab.count }}</span>
    </button>
  </div>
</template>
