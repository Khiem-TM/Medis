<script setup lang="ts">
import { computed } from 'vue'
import type { PaginationMeta } from '@/types/api.types'

const props = defineProps<{
  meta: PaginationMeta
  modelValue: number
  showSizeSelector?: boolean
  size?: number
}>()

const emit = defineEmits<{
  'update:modelValue': [page: number]
  'update:size': [size: number]
}>()

const pages = computed(() => {
  const total = props.meta.total_pages
  const current = props.meta.page
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)

  const pages: (number | '...')[] = [1]
  if (current > 3) pages.push('...')
  for (let i = Math.max(2, current - 1); i <= Math.min(total - 1, current + 1); i++) pages.push(i)
  if (current < total - 2) pages.push('...')
  pages.push(total)
  return pages
})

const sizeOptions = [10, 20, 50, 100]
</script>

<template>
  <div class="flex items-center justify-between gap-4 py-3">
    <p class="text-sm text-[#6B7280]">
      Hiển thị {{ (meta.page - 1) * meta.size + 1 }}–{{ Math.min(meta.page * meta.size, meta.total) }}
      trong {{ meta.total }} kết quả
    </p>

    <div class="flex items-center gap-1">
      <!-- Prev -->
      <button
        :disabled="meta.page <= 1"
        class="p-1.5 rounded-lg hover:bg-[#F3F4F6] disabled:opacity-40 disabled:cursor-not-allowed text-[#6B7280]"
        @click="emit('update:modelValue', meta.page - 1)"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      <!-- Pages -->
      <template v-for="(p, i) in pages" :key="i">
        <span v-if="p === '...'" class="px-1 text-[#9CA3AF] text-sm">…</span>
        <button
          v-else
          :class="[
            'min-w-[32px] h-8 px-2 rounded-lg text-sm font-medium transition-colors',
            p === meta.page
              ? 'bg-[#10B981] text-white'
              : 'text-[#374151] hover:bg-[#F3F4F6]',
          ]"
          @click="emit('update:modelValue', p as number)"
        >
          {{ p }}
        </button>
      </template>

      <!-- Next -->
      <button
        :disabled="meta.page >= meta.total_pages"
        class="p-1.5 rounded-lg hover:bg-[#F3F4F6] disabled:opacity-40 disabled:cursor-not-allowed text-[#6B7280]"
        @click="emit('update:modelValue', meta.page + 1)"
      >
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </div>

    <!-- Size selector -->
    <select
      v-if="showSizeSelector"
      :value="size ?? meta.size"
      class="text-sm border border-[#E5E7EB] rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-[#10B981]/30"
      @change="emit('update:size', +($event.target as HTMLSelectElement).value)"
    >
      <option v-for="s in sizeOptions" :key="s" :value="s">{{ s }} / trang</option>
    </select>
  </div>
</template>
