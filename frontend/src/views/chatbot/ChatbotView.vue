<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useChatHistory, useSendMessageMutation, useClearHistoryMutation, useChatSuggestions } from '@/api/chatbot.api'
import { useToast } from '@/composables/useToast'
import ChatMessageComp from '@/components/chat/ChatMessage.vue'
import ChatTypingIndicator from '@/components/chat/ChatTypingIndicator.vue'
import ChatSidebar from '@/components/chat/ChatSidebar.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'

interface LocalMessage {
  id?: string
  role: 'user' | 'assistant'
  content: string
  created_at?: string
  optimistic?: boolean
  tempId?: string
}

const toast = useToast()
const input = ref('')
const messagesEl = ref<HTMLDivElement | null>(null)
const localMessages = ref<LocalMessage[]>([])
const historyLoaded = ref(false)

const { data: historyData, isLoading: loadingHistory } = useChatHistory({ page: 1, size: 30 })
const { data: suggestions } = useChatSuggestions()
const { mutate: sendMessage, isPending: sending } = useSendMessageMutation()
const { mutate: clearHistory, isPending: clearing } = useClearHistoryMutation()

watch(historyData, (data) => {
  if (data && !historyLoaded.value) {
    historyLoaded.value = true
    localMessages.value = [...data.items].reverse().map((m) => ({
      id: m.id,
      role: m.role,
      content: m.content,
      created_at: m.created_at,
    }))
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

  const tempId = `temp-${Date.now()}`
  localMessages.value.push({ role: 'user', content: text, optimistic: true, tempId })
  nextTick(scrollToBottom)

  sendMessage(text, {
    onSuccess: (data) => {
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

function autoResize(e: Event) {
  const el = e.target as HTMLTextAreaElement
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 128) + 'px'
}

const showEmpty = computed(() => !loadingHistory.value && localMessages.value.length === 0)
</script>

<template>
  <div class="flex h-[calc(100vh-3.5rem)] -mx-6 -my-6 overflow-hidden">
    <!-- Left sidebar: chat history (hidden on mobile) -->
    <ChatSidebar
      class="hidden lg:flex"
      :messages="localMessages"
      :loading="loadingHistory"
    />

    <!-- Main chat area -->
    <section class="flex-1 flex flex-col bg-white overflow-hidden">
      <!-- Chat header -->
      <header class="h-16 px-6 flex items-center justify-between border-b border-outline-variant bg-white/80 backdrop-blur-xl sticky top-0 z-10 flex-shrink-0">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-surface-container-high flex items-center justify-center flex-shrink-0">
            <svg class="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-base font-bold text-on-surface">MediBot AI</h2>
              <span class="px-2 py-0.5 bg-tertiary-fixed text-tertiary text-xs font-bold rounded-full">GPT-4o-mini</span>
            </div>
            <p class="text-xs text-outline flex items-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full bg-tertiary inline-block" />
              Sẵn sàng hỗ trợ
            </p>
          </div>
        </div>
        <button
          v-if="localMessages.length > 0"
          :disabled="clearing"
          @click="doClear"
          class="text-xs font-medium text-outline hover:text-error transition-colors flex items-center gap-1.5 px-3 py-1.5 hover:bg-error-container/30 rounded-lg"
        >
          <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          Xóa lịch sử
        </button>
      </header>

      <!-- Health profile context banner -->
      <div class="px-6 py-2.5 bg-primary-fixed border-b border-primary/10 flex items-center gap-2 text-sm flex-shrink-0">
        <svg class="w-4 h-4 text-primary flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
        </svg>
        <span class="text-primary font-medium">Kết nối với hồ sơ sức khỏe cá nhân của bạn</span>
        <span class="text-primary/60 text-xs">· AI biết tiền sử bệnh và đơn thuốc của bạn</span>
      </div>

      <!-- Messages area -->
      <div ref="messagesEl" class="flex-1 overflow-y-auto p-6 space-y-6 bg-[#fdfcff]">
        <!-- Loading state -->
        <div v-if="loadingHistory" class="flex justify-center py-12">
          <AppSpinner size="lg" class="text-primary" />
        </div>

        <!-- Empty state with suggestions -->
        <div v-else-if="showEmpty" class="flex flex-col items-center justify-center h-full py-16 text-center">
          <div class="w-16 h-16 bg-primary-fixed rounded-2xl flex items-center justify-center mb-4">
            <svg class="w-8 h-8 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          </div>
          <h3 class="text-lg font-bold text-on-surface mb-2">Bắt đầu cuộc trò chuyện</h3>
          <p class="text-sm text-outline mb-8 max-w-sm">Đặt câu hỏi về thuốc, triệu chứng hoặc lời khuyên sức khỏe. AI sẽ sử dụng hồ sơ của bạn để cung cấp câu trả lời phù hợp.</p>

          <div v-if="suggestions && suggestions.length > 0" class="flex flex-wrap gap-2 justify-center max-w-lg">
            <button
              v-for="s in suggestions"
              :key="s"
              @click="useSuggestion(s)"
              class="text-sm px-4 py-2 rounded-full border border-outline-variant bg-card hover:border-primary hover:bg-primary hover:text-white transition-all shadow-sm"
            >
              {{ s }}
            </button>
          </div>
        </div>

        <!-- Messages -->
        <template v-else>
          <ChatMessageComp
            v-for="msg in localMessages"
            :key="msg.id ?? msg.tempId"
            :role="msg.role"
            :content="msg.content"
            :created-at="msg.created_at"
            :optimistic="msg.optimistic"
          />
          <ChatTypingIndicator v-if="sending" />
        </template>
      </div>

      <!-- Input area -->
      <footer class="p-4 bg-white border-t border-outline-variant flex-shrink-0">
        <!-- Quick suggestions while chatting -->
        <div v-if="!showEmpty && suggestions && suggestions.length > 0" class="flex gap-2 mb-3 overflow-x-auto pb-1 no-scrollbar">
          <button
            v-for="s in suggestions.slice(0, 4)"
            :key="s"
            @click="useSuggestion(s)"
            class="text-xs px-3 py-1.5 rounded-full border border-outline-variant bg-surface-container-low hover:border-primary hover:bg-primary hover:text-white transition-all whitespace-nowrap flex-shrink-0"
          >
            {{ s }}
          </button>
        </div>

        <!-- Input box -->
        <div class="relative group">
          <div class="absolute -inset-0.5 bg-gradient-to-r from-primary/10 to-primary-container/10 rounded-2xl blur opacity-0 group-focus-within:opacity-40 transition duration-500" />
          <div class="relative bg-card rounded-2xl border border-outline-variant shadow-sm flex items-end gap-2 p-2 focus-within:border-primary transition-colors">
            <div class="flex-1 px-2 py-1">
              <textarea
                v-model="input"
                rows="1"
                :disabled="sending"
                placeholder="Nhập câu hỏi... (Enter để gửi, Shift+Enter để xuống dòng)"
                class="w-full bg-transparent border-none focus:ring-0 text-sm text-on-surface placeholder:text-outline resize-none max-h-32 leading-relaxed disabled:opacity-50"
                @keydown="onKeydown"
                @input="autoResize"
              />
            </div>
            <button
              :disabled="!input.trim() || sending"
              @click="doSend"
              class="w-10 h-10 bg-gradient-to-br from-primary to-primary-container text-white rounded-xl flex items-center justify-center shadow-md hover:scale-105 active:scale-95 transition-all disabled:opacity-40 disabled:cursor-not-allowed disabled:scale-100 flex-shrink-0"
            >
              <svg v-if="!sending" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
              <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            </button>
          </div>
        </div>
        <p class="text-xs text-outline mt-2 text-center">AI có thể mắc lỗi. Hãy tham khảo ý kiến bác sĩ cho các quyết định y tế quan trọng.</p>
      </footer>
    </section>
  </div>
</template>
