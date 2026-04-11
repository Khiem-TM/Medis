<script setup lang="ts">
import { computed } from 'vue'
import { formatDateTime } from '@/utils/format'
import type { ChatRole } from '@/types/chatbot.types'

const props = defineProps<{
  role: ChatRole
  content: string
  createdAt?: string
  optimistic?: boolean
}>()

const isUser = computed(() => props.role === 'user')
</script>

<template>
  <div :class="['flex gap-3', isUser ? 'flex-row-reverse' : 'flex-row']">
    <!-- Avatar -->
    <div
      :class="[
        'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold',
        isUser ? 'bg-[#10B981] text-white' : 'bg-[#F3F4F6] text-[#374151]',
      ]"
    >
      {{ isUser ? 'B' : 'AI' }}
    </div>

    <!-- Bubble -->
    <div :class="['max-w-[75%] space-y-1', isUser ? 'items-end' : 'items-start', 'flex flex-col']">
      <div
        :class="[
          'px-4 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap',
          isUser
            ? 'bg-[#10B981] text-white rounded-tr-sm'
            : 'bg-white border border-[#E5E7EB] text-[#111827] rounded-tl-sm',
          optimistic ? 'opacity-70' : '',
        ]"
      >
        {{ content }}
      </div>
      <span v-if="createdAt" class="text-[10px] text-[#9CA3AF] px-1">
        {{ formatDateTime(createdAt) }}
      </span>
    </div>
  </div>
</template>
