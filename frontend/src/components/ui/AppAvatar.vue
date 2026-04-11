<script setup lang="ts">
import { computed } from 'vue'
import { initials } from '@/utils/format'

const props = defineProps<{
  src?: string | null
  name?: string | null
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
}>()

const sizeClasses = computed(() => {
  switch (props.size) {
    case 'xs': return 'w-6 h-6 text-xs'
    case 'sm': return 'w-8 h-8 text-xs'
    case 'lg': return 'w-14 h-14 text-lg'
    case 'xl': return 'w-20 h-20 text-2xl'
    default: return 'w-10 h-10 text-sm'
  }
})

const abbr = computed(() => initials(props.name))
</script>

<template>
  <div :class="['rounded-full overflow-hidden flex-shrink-0 bg-[#D1FAE5] flex items-center justify-center', sizeClasses]">
    <img v-if="src" :src="src" :alt="name ?? ''" class="w-full h-full object-cover" />
    <span v-else class="font-semibold text-[#065F46]">{{ abbr }}</span>
  </div>
</template>
