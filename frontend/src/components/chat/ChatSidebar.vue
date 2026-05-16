<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{
  messages: Array<{ id?: string; role: 'user' | 'assistant'; content: string; created_at?: string }>
  loading?: boolean
}>()

const isCollapsed = ref(false)

const userMessages = computed(() => {
  return props.messages.filter((m) => m.role === 'user').reverse()
})

function formatTime(dateString?: string) {
  if (!dateString) return 'Vừa xong'
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('vi-VN', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
  }).format(date)
}
</script>

<template>
  <div 
    class="bg-white border-r border-[#E5E7EB] flex flex-col h-full transition-all duration-300 relative shrink-0"
    :class="isCollapsed ? 'w-16' : 'w-72'"
  >
    <!-- Header -->
    <div class="h-16 flex items-center border-b border-[#E5E7EB]" :class="isCollapsed ? 'justify-center' : 'justify-between px-6'">
      <h2 v-show="!isCollapsed" class="text-[17px] font-bold tracking-tight whitespace-nowrap" style="color: #0C1D42;">Cuộc trò chuyện</h2>
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

    <!-- Session list -->
    <div v-show="!isCollapsed" class="flex-1 overflow-y-auto p-4 space-y-1 min-w-[18rem]">
      <div v-if="loading" class="text-center py-8 text-sm text-outline">Đang tải...</div>
      <div v-else-if="userMessages.length === 0" class="text-center py-8 text-sm text-outline">
        Chưa có câu hỏi nào
      </div>
      <div
        v-else
        v-for="(msg, idx) in userMessages"
        :key="msg.id ?? idx"
        class="p-4 rounded-[1rem] cursor-pointer transition-colors border"
        :style="idx === 0 ? 'background: #F0F4FF; border-color: rgba(69,85,183,0.1);' : 'background: transparent; border-color: transparent; hover: background: #F9FAFB;'"
      >
        <p class="text-[13px] font-bold mb-1 line-clamp-1" :style="idx === 0 ? 'color: #0C1D42;' : 'color: #5A6985;'">{{ msg.content }}</p>
        <p class="text-[11px]" style="color: #8A95AC;">{{ formatTime(msg.created_at) }}</p>
      </div>
    </div>

    <!-- Icons only for collapsed state if needed -->
    <div v-show="isCollapsed" class="flex-1 flex flex-col items-center py-4 space-y-4">
      <div v-for="i in Math.min(userMessages.length, 5)" :key="i" class="w-8 h-8 rounded-lg bg-surface-container-low flex items-center justify-center text-[10px] text-outline">
        {{ i }}
      </div>
    </div>
  </div>
</template>
