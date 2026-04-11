<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useChatHistory, useSendMessageMutation, useClearHistoryMutation, useChatSuggestions } from '@/api/chatbot.api'
import { useToast } from '@/composables/useToast'
import type { ChatMessage } from '@/types/chatbot.types'
import ChatMessageComp from '@/components/chat/ChatMessage.vue'
import ChatTypingIndicator from '@/components/chat/ChatTypingIndicator.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppButton from '@/components/ui/AppButton.vue'

interface LocalMessage {
  id?: string
  user_id?: string
  role: 'user' | 'assistant'
  content: string
  created_at?: string
  optimistic?: boolean
  tempId?: string
}

const toast = useToast()
const input = ref('')
const messagesEl = ref<HTMLDivElement | null>(null)
const page = ref(1)
const pageSize = 30
const localMessages = ref<LocalMessage[]>([])
const historyLoaded = ref(false)

const { data: historyData, isLoading: loadingHistory } = useChatHistory({ page: 1, size: pageSize })
const { data: suggestions } = useChatSuggestions()
const { mutate: sendMessage, isPending: sending } = useSendMessageMutation()
const { mutate: clearHistory, isPending: clearing } = useClearHistoryMutation()

// Load history once on mount
watch(historyData, (data) => {
  if (data && !historyLoaded.value) {
    historyLoaded.value = true
    // History comes newest-first, reverse to show oldest at top
    const historical: LocalMessage[] = [...data.items].reverse().map((m) => ({
      id: m.id,
      role: m.role,
      content: m.content,
      created_at: m.created_at,
    }))
    localMessages.value = historical
    nextTick(scrollToBottom)
  }
}, { immediate: true })

function scrollToBottom() {
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

function doSend() {
  const text = input.value.trim()
  if (!text || sending.value) return
  input.value = ''

  // Optimistic: add user message immediately
  const tempId = `temp-${Date.now()}`
  localMessages.value.push({ role: 'user', content: text, optimistic: true, tempId })
  nextTick(scrollToBottom)

  sendMessage(text, {
    onSuccess: (data) => {
      // Replace optimistic user msg and add assistant reply
      const idx = localMessages.value.findIndex((m) => m.tempId === tempId)
      if (idx !== -1) {
        localMessages.value[idx] = {
          id: data.user_message.id,
          role: 'user',
          content: data.user_message.content,
          created_at: data.user_message.created_at,
        }
      }
      localMessages.value.push({
        id: data.assistant_message.id,
        role: 'assistant',
        content: data.assistant_message.content,
        created_at: data.assistant_message.created_at,
      })
      nextTick(scrollToBottom)
    },
    onError: () => {
      // Remove failed optimistic message
      localMessages.value = localMessages.value.filter((m) => m.tempId !== tempId)
      toast.error('Không thể gửi tin nhắn. Vui lòng thử lại.')
    },
  })
}

function useSuggestion(text: string) {
  input.value = text
  doSend()
}

function doClear() {
  clearHistory(undefined, {
    onSuccess: () => {
      localMessages.value = []
      historyLoaded.value = false
      toast.success('Đã xóa lịch sử trò chuyện')
    },
    onError: () => toast.error('Không thể xóa lịch sử'),
  })
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    doSend()
  }
}

const showEmpty = computed(() => !loadingHistory.value && localMessages.value.length === 0)
</script>

<template>
  <div class="flex flex-col h-[calc(100vh-8rem)]">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div>
        <h1 class="text-2xl font-bold text-[#111827]">Chatbot Sức Khỏe AI</h1>
        <p class="text-sm text-[#6B7280] mt-0.5">Hỏi đáp về thuốc, triệu chứng và sức khỏe</p>
      </div>
      <AppButton v-if="localMessages.length > 0" variant="ghost" size="sm" :loading="clearing" @click="doClear">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
        Xóa lịch sử
      </AppButton>
    </div>

    <!-- Messages area -->
    <div class="flex-1 bg-white rounded-2xl border border-[#E5E7EB] flex flex-col overflow-hidden">
      <div ref="messagesEl" class="flex-1 overflow-y-auto p-4 space-y-4">
        <!-- Loading history -->
        <div v-if="loadingHistory" class="flex justify-center py-8">
          <AppSpinner size="lg" class="text-[#10B981]" />
        </div>

        <!-- Empty state -->
        <div v-else-if="showEmpty" class="flex flex-col items-center justify-center h-full py-12 text-center">
          <div class="w-16 h-16 bg-[#D1FAE5] rounded-full flex items-center justify-center mb-4">
            <svg class="w-8 h-8 text-[#10B981]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          </div>
          <h3 class="font-semibold text-[#111827] mb-1">Bắt đầu cuộc trò chuyện</h3>
          <p class="text-sm text-[#6B7280] mb-6">Đặt câu hỏi về thuốc, triệu chứng hoặc lời khuyên sức khỏe</p>

          <!-- Suggestions -->
          <div v-if="suggestions && suggestions.length > 0" class="flex flex-wrap gap-2 justify-center max-w-lg">
            <button
              v-for="s in suggestions"
              :key="s"
              @click="useSuggestion(s)"
              class="text-sm px-4 py-2 rounded-full border border-[#E5E7EB] bg-[#F9FAFB] hover:border-[#10B981] hover:bg-[#D1FAE5] hover:text-[#065F46] transition-colors"
            >
              {{ s }}
            </button>
          </div>
        </div>

        <!-- Message list -->
        <template v-else>
          <ChatMessageComp
            v-for="msg in localMessages"
            :key="msg.id ?? msg.tempId"
            :role="msg.role"
            :content="msg.content"
            :created-at="msg.created_at"
            :optimistic="msg.optimistic"
          />

          <!-- Typing indicator -->
          <ChatTypingIndicator v-if="sending" />
        </template>
      </div>

      <!-- Input area -->
      <div class="border-t border-[#E5E7EB] p-3">
        <!-- Suggestions (when there are messages) -->
        <div v-if="!showEmpty && suggestions && suggestions.length > 0" class="flex gap-2 mb-2 overflow-x-auto pb-1 no-scrollbar">
          <button
            v-for="s in suggestions.slice(0, 3)"
            :key="s"
            @click="useSuggestion(s)"
            class="text-xs px-3 py-1.5 rounded-full border border-[#E5E7EB] bg-[#F9FAFB] hover:border-[#10B981] hover:bg-[#D1FAE5] hover:text-[#065F46] transition-colors whitespace-nowrap flex-shrink-0"
          >
            {{ s }}
          </button>
        </div>

        <div class="flex gap-2 items-end">
          <textarea
            v-model="input"
            rows="1"
            :disabled="sending"
            placeholder="Nhập câu hỏi... (Enter để gửi, Shift+Enter để xuống dòng)"
            class="flex-1 resize-none rounded-xl border border-[#E5E7EB] px-3 py-2 text-sm text-[#111827] placeholder-[#9CA3AF] focus:outline-none focus:ring-2 focus:ring-[#10B981]/30 focus:border-[#10B981] disabled:opacity-50 max-h-32 leading-relaxed"
            @keydown="onKeydown"
            @input="($event.target as HTMLTextAreaElement).style.height = 'auto'; ($event.target as HTMLTextAreaElement).style.height = Math.min(($event.target as HTMLTextAreaElement).scrollHeight, 128) + 'px'"
          />
          <AppButton :disabled="!input.trim() || sending" :loading="sending" @click="doSend" class="flex-shrink-0">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
            Gửi
          </AppButton>
        </div>
        <p class="text-xs text-[#9CA3AF] mt-1.5 px-1">AI có thể mắc lỗi. Hãy tham khảo ý kiến bác sĩ cho các quyết định y tế quan trọng.</p>
      </div>
    </div>
  </div>
</template>
