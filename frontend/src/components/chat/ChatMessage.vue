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
        isUser ? 'bg-primary text-white' : 'bg-surface-container text-on-surface-variant',
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
            ? 'bg-primary text-white rounded-tr-sm'
            : 'bg-card border border-outline-variant text-on-surface rounded-tl-sm',
          optimistic ? 'opacity-70' : '',
        ]"
      >
        {{ content }}
      </div>
      <span v-if="createdAt" class="text-[10px] text-outline px-1">
        {{ formatDateTime(createdAt) }}
      </span>
    </div>
  </div>
</template>
