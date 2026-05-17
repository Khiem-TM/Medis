<script setup lang="ts">
import { ref } from 'vue'
import type { ChatSession } from '@/types/chatbot.types'

defineProps<{
  sessions: ChatSession[]
  activeSessionId?: string | null
  loading?: boolean
}>()

defineEmits<{
  select: [sessionId: string]
  new: []
  delete: [sessionId: string]
}>()

const isCollapsed = ref(false)

function formatTime(dateString?: string | null) {
  if (!dateString) return 'Chưa có tin nhắn'
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('vi-VN', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}
</script>

<template>
  <div
    class="bg-surface-container-low border-r border-outline-variant flex flex-col h-full transition-all duration-300 relative shrink-0"
    :class="isCollapsed ? 'w-16' : 'w-72'"
  >
    <div
      class="h-16 flex items-center border-b border-outline-variant"
      :class="isCollapsed ? 'justify-center' : 'justify-between px-4'"
    >
      <div v-show="!isCollapsed" class="flex items-center gap-2 min-w-0">
        <h2 class="text-[17px] font-bold tracking-tight whitespace-nowrap text-on-surface">
          Phiên trò chuyện
        </h2>
        <button
          class="w-8 h-8 rounded-lg bg-primary text-white flex items-center justify-center hover:opacity-90 transition-opacity"
          title="Tạo phiên mới"
          @click="$emit('new')"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
        </button>
      </div>
      <button
        @click="isCollapsed = !isCollapsed"
        class="p-2 text-outline hover:text-primary transition-all duration-300 rounded-lg hover:bg-surface-container-low"
        :class="{ 'rotate-180': isCollapsed }"
        :title="isCollapsed ? 'Mở rộng menu' : 'Thu gọn menu'"
      >
        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect width="18" height="18" x="3" y="3" rx="2"/><path d="M9 3v18"/>
        </svg>
      </button>
    </div>

    <div v-show="!isCollapsed" class="flex-1 overflow-y-auto p-4 space-y-1 min-w-[18rem]">
      <div v-if="loading" class="text-center py-8 text-sm text-outline">Đang tải...</div>
      <div v-else-if="sessions.length === 0" class="text-center py-8 text-sm text-outline">
        Chưa có phiên trò chuyện
      </div>
      <template v-else>
        <div
          v-for="session in sessions"
          :key="session.id"
          class="group p-4 rounded-[1rem] cursor-pointer transition-colors border"
          :class="String(session.id) === activeSessionId ? 'bg-surface-container-highest border-primary/20 shadow-sm' : 'border-transparent hover:bg-surface-container-high/50'"
          @click="$emit('select', String(session.id))"
        >
          <div class="flex items-start gap-2">
            <div class="flex-1 min-w-0">
              <p
                class="text-[13px] font-bold mb-1 line-clamp-1"
                :class="String(session.id) === activeSessionId ? 'text-on-surface' : 'text-on-surface-variant'"
              >
                {{ session.title }}
              </p>
              <p class="text-[12px] line-clamp-1 text-on-surface-variant/70">
                {{ session.last_message_preview || 'Phiên mới' }}
              </p>
              <p class="text-[11px] mt-1 text-outline">
                {{ formatTime(session.last_message_at || session.updated_at) }} · {{ session.message_count }} tin nhắn
              </p>
            </div>
            <button
              class="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg text-outline hover:text-error hover:bg-error-container/40 transition-all"
              title="Xóa phiên"
              @click.stop="$emit('delete', String(session.id))"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </template>
    </div>


  </div>
</template>
