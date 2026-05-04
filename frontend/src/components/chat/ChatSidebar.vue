<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth.store'
import type { ChatMessage } from '@/types/chatbot.types'

const props = defineProps<{
  messages: Array<{ role: 'user' | 'assistant'; content: string; created_at?: string }>
  loading?: boolean
}>()

const authStore = useAuthStore()
const userName = computed(() => authStore.user?.full_name || authStore.user?.username || 'Bạn')

// Get a short preview from the first user message in the session
const sessionPreview = computed(() => {
  const firstUser = props.messages.find((m) => m.role === 'user')
  if (!firstUser) return 'Cuộc trò chuyện mới'
  const text = firstUser.content
  return text.length > 60 ? text.slice(0, 60) + '...' : text
})

const userMessageCount = computed(() => props.messages.filter((m) => m.role === 'user').length)
</script>

<template>
  <div class="w-72 bg-card/60 border-r border-outline-variant flex flex-col h-full">
    <!-- Header -->
    <div class="p-5 border-b border-outline-variant">
      <h2 class="text-base font-bold text-on-surface mb-3">Cuộc trò chuyện</h2>
      <div class="relative">
        <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-outline pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          type="text"
          placeholder="Tìm cuộc trò chuyện..."
          class="w-full pl-9 pr-3 py-2 bg-surface-container-low border-none rounded-xl text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/20"
          readonly
        />
      </div>
    </div>

    <!-- Session list -->
    <div class="flex-1 overflow-y-auto p-3 space-y-2">
      <!-- Current session (active) -->
      <div v-if="!loading && messages.length > 0" class="p-4 rounded-xl bg-card shadow-sm border border-primary/10 cursor-pointer">
        <div class="flex items-center justify-between mb-1">
          <span class="text-xs font-bold text-primary uppercase tracking-tight">Đang diễn ra</span>
          <span class="text-xs text-outline">{{ userMessageCount }} tin nhắn</span>
        </div>
        <p class="text-sm font-semibold text-on-surface line-clamp-1 mb-1">{{ sessionPreview }}</p>
        <p class="text-xs text-outline line-clamp-2 leading-relaxed">Nhấn để xem cuộc trò chuyện</p>
      </div>

      <!-- Empty state -->
      <div v-else-if="!loading" class="text-center py-8">
        <svg class="w-10 h-10 text-outline/50 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <p class="text-xs text-outline">Chưa có cuộc trò chuyện</p>
        <p class="text-xs text-outline mt-0.5">Bắt đầu câu hỏi đầu tiên</p>
      </div>
    </div>

    <!-- Health profile indicator -->
    <div class="p-4 border-t border-outline-variant">
      <div class="flex items-center gap-3 p-3 rounded-xl bg-primary-fixed/50">
        <div class="w-9 h-9 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
          <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
        <div class="flex-1 overflow-hidden">
          <p class="text-sm font-bold text-on-surface truncate">{{ userName }}</p>
          <p class="text-xs text-primary font-medium">Hồ sơ đã kết nối</p>
        </div>
      </div>
    </div>
  </div>
</template>
