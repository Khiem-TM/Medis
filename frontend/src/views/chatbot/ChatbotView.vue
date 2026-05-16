<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import {
  useChatHistory,
  useSendMessageMutation,
  useClearHistoryMutation,
  useChatSuggestions,
} from '@/api/chatbot.api'
import { useToast } from '@/composables/useToast'
import ChatMessageComp from '@/components/chat/ChatMessage.vue'
import ChatTypingIndicator from '@/components/chat/ChatTypingIndicator.vue'
import ChatSidebar from '@/components/chat/ChatSidebar.vue'
import AppSpinner from '@/components/ui/AppSpinner.vue'

// Lock global scroll on mount
onMounted(() => {
  document.body.classList.add('overflow-hidden')
  const main = document.querySelector('main')
  if (main) {
    main.classList.add('h-screen', 'overflow-hidden')
  }
})

onUnmounted(() => {
  document.body.classList.remove('overflow-hidden')
  const main = document.querySelector('main')
  if (main) {
    main.classList.remove('h-screen', 'overflow-hidden')
  }
})

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

watch(
  historyData,
  (data) => {
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
  },
  { immediate: true },
)

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
  <div class="flex h-[calc(100vh-5rem)] -mx-6 -mb-8 overflow-hidden rounded-3xl border border-outline-variant bg-surface shadow-sm">
    <!-- Left sidebar: chat history (hidden on mobile) -->
    <ChatSidebar class="hidden lg:flex" :messages="localMessages" :loading="loadingHistory" />

    <!-- Main chat area -->
    <section class="flex-1 flex flex-col bg-white overflow-hidden">
      <!-- Chat header -->
      <header
        class="h-16 px-6 flex items-center justify-between border-b border-outline-variant bg-white/80 backdrop-blur-xl sticky top-0 z-10 flex-shrink-0"
      >
        <div class="flex items-center gap-3">
          <div
            class="w-10 h-10 rounded-xl bg-primary-fixed flex items-center justify-center flex-shrink-0 overflow-hidden"
          >
            <img
              src="/assets/images/chatbot_logo.png"
              class="w-14 h-14 object-contain scale-125"
              alt="Medis AI"
            />
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-base font-bold text-on-surface">Medis AI</h2>
              <span
                class="px-2 py-0.5 bg-tertiary-fixed text-tertiary text-xs font-bold rounded-full"
                >Gemini</span
              >
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
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
          Xóa lịch sử
        </button>
      </header>

      <!-- Health profile context banner -->
      <div
        class="px-6 py-2.5 bg-primary-fixed border-b border-primary/10 flex items-center gap-2 text-sm flex-shrink-0"
      >
        <svg
          class="w-4 h-4 text-primary flex-shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
          />
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
        <div
          v-else-if="showEmpty"
          class="flex flex-col items-center justify-center h-full py-10 px-4 text-center"
        >
          <div
            class="w-24 h-24 rounded-full bg-primary-fixed flex items-center justify-center mb-6 overflow-hidden"
          >
            <img
              src="/assets/images/chatbot_logo.png"
              class="w-32 h-32 object-contain scale-150"
              alt="Medis AI"
            />
          </div>
          <h1
            class="text-3xl font-bold mb-3 tracking-tight animate-fade-in-up"
            style="color: #0c1d42"
          >
            Xin chào, tôi là Medis AI
          </h1>
          <p
            class="text-[15px] mb-8 max-w-xl mx-auto leading-relaxed animate-fade-in-up delay-100"
            style="color: #5a6985"
          >
            Tôi có thể giúp bạn giải đáp các thắc mắc về sức khỏe, phân tích triệu chứng hoặc hướng
            dẫn sử dụng thuốc.
          </p>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl w-full mx-auto text-left">
            <button
              @click="useSuggestion('Thuốc này uống trước hay sau ăn?')"
              class="bg-white p-3.5 rounded-xl border border-[#E5E7EB] hover:border-[#00897B]/40 hover:bg-gray-50 hover:shadow-sm transition-all duration-300 group flex items-center gap-3 animate-fade-in-up delay-100"
            >
              <div
                class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                style="background: #f0faf9"
              >
                <svg
                  class="w-4 h-4"
                  style="color: #00897b"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="font-bold text-sm mb-0.5 truncate" style="color: #0c1d42">
                  Cách dùng thuốc
                </h3>
                <p class="text-xs truncate" style="color: #5a6985">
                  "Thuốc này uống trước hay sau ăn?"
                </p>
              </div>
            </button>

            <button
              @click="useSuggestion('Tôi bị đau đầu và buồn nôn, nên làm gì?')"
              class="bg-white p-3.5 rounded-xl border border-[#E5E7EB] hover:border-[#4555B7]/40 hover:bg-gray-50 hover:shadow-sm transition-all duration-300 group flex items-center gap-3 animate-fade-in-up delay-200"
            >
              <div
                class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                style="background: #edf0ff"
              >
                <svg
                  class="w-4 h-4"
                  style="color: #4555b7"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                  />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="font-bold text-sm mb-0.5 truncate" style="color: #0c1d42">
                  Tư vấn triệu chứng
                </h3>
                <p class="text-xs truncate" style="color: #5a6985">
                  "Tôi bị đau đầu và buồn nôn..."
                </p>
              </div>
            </button>

            <button
              @click="useSuggestion('Chỉ số đường huyết 120 mg/dL có bình thường không?')"
              class="bg-white p-3.5 rounded-xl border border-[#E5E7EB] hover:border-[#8A30B0]/40 hover:bg-gray-50 hover:shadow-sm transition-all duration-300 group flex items-center gap-3 animate-fade-in-up delay-300"
            >
              <div
                class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                style="background: #f8edff"
              >
                <svg
                  class="w-4 h-4"
                  style="color: #8a30b0"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
                  />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="font-bold text-sm mb-0.5 truncate" style="color: #0c1d42">
                  Phân tích chỉ số
                </h3>
                <p class="text-xs truncate" style="color: #5a6985">
                  "Chỉ số đường huyết 120 mg/dL..."
                </p>
              </div>
            </button>

            <button
              @click="useSuggestion('Thực đơn cho người cao huyết áp?')"
              class="bg-white p-3.5 rounded-xl border border-[#E5E7EB] hover:border-[#F59E0B]/40 hover:bg-gray-50 hover:shadow-sm transition-all duration-300 group flex items-center gap-3 animate-fade-in-up delay-400"
            >
              <div
                class="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                style="background: #fff4ed"
              >
                <svg
                  class="w-4 h-4"
                  style="color: #f59e0b"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"
                  />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="font-bold text-sm mb-0.5 truncate" style="color: #0c1d42">Dinh dưỡng</h3>
                <p class="text-xs truncate" style="color: #5a6985">
                  "Thực đơn cho người cao huyết áp?"
                </p>
              </div>
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
      <footer class="px-6 py-4 bg-white flex-shrink-0">
        <!-- Input box -->
        <div class="max-w-4xl mx-auto relative">
          <div
            class="bg-white rounded-[2rem] border border-[#E5E7EB] flex items-end gap-2 p-2 focus-within:border-[#00897B] focus-within:ring-1 focus-within:ring-[#00897B] transition-all shadow-sm"
          >
            <div class="flex-1 py-3 px-6">
              <textarea
                v-model="input"
                rows="1"
                :disabled="sending"
                placeholder="Nhập câu hỏi của bạn tại đây..."
                class="w-full bg-transparent border-none outline-none focus:ring-0 text-[15px] text-[#0C1D42] placeholder:text-[#8A95AC] resize-none max-h-32 leading-relaxed disabled:opacity-50 p-0 m-0"
                @keydown="onKeydown"
                @input="autoResize"
                style="box-shadow: none"
              />
            </div>
            <button
              :disabled="!input.trim() || sending"
              @click="doSend"
              class="w-12 h-12 rounded-[1.5rem] flex items-center justify-center transition-all disabled:opacity-40 disabled:cursor-not-allowed hover:scale-105 active:scale-95 flex-shrink-0"
              style="background: #00c2a8; color: white"
            >
              <svg
                v-if="!sending"
                class="w-5 h-5 ml-0.5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                />
              </svg>
              <svg v-else class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                />
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
            </button>
          </div>
        </div>
        <p class="text-[13px] mt-3 text-center font-medium" style="color: #8a95ac">
          Medis AI có thể mắc lỗi. Vui lòng kiểm tra lại các thông tin y tế quan trọng.
        </p>
      </footer>
    </section>
  </div>
</template>

<style scoped>
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in-up {
  animation: fadeInUp 0.5s ease-out forwards;
  opacity: 0;
}

.delay-100 {
  animation-delay: 100ms;
}
.delay-200 {
  animation-delay: 200ms;
}
.delay-300 {
  animation-delay: 300ms;
}
.delay-400 {
  animation-delay: 400ms;
}
</style>
