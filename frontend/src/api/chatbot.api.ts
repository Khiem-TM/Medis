import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { api } from './axios'
import type { ChatMessage, ChatSendResponse, ChatHistoryParams, QuickSuggestion } from '@/types/chatbot.types'
import type { PaginatedResponse } from '@/types/api.types'

export const chatKeys = {
  all: ['chat'] as const,
  history: (params?: ChatHistoryParams) => [...chatKeys.all, 'history', params] as const,
  suggestions: () => [...chatKeys.all, 'suggestions'] as const,
}

const chatbotUnavailableReply = 'Hiện tại Medis AI chưa thể kết nối tới dịch vụ AI. Bạn vẫn có thể xem lại câu hỏi vừa gửi trong màn hình trò chuyện. Với triệu chứng khẩn cấp như đau ngực, khó thở, ngất hoặc dị ứng nặng, hãy gọi cấp cứu hoặc đến cơ sở y tế gần nhất. Thông tin này chỉ mang tính tham khảo, không thay thế khám bác sĩ.'

export const chatbotApi = {
  send: async (message: string) => {
    try {
      return await api.post<ChatSendResponse>('/chatbot/message', { content: message }).then((r) => r.data)
    } catch (error) {
      if ((error as { status?: number })?.status !== 503) throw error
      const now = new Date().toISOString()
      return {
        user_message: {
          id: `local-user-${Date.now()}`,
          user_id: 'local',
          role: 'user',
          content: message,
          created_at: now,
        },
        assistant_message: {
          id: `local-assistant-${Date.now()}`,
          user_id: 'local',
          role: 'assistant',
          content: chatbotUnavailableReply,
          created_at: now,
        },
      } satisfies ChatSendResponse
    }
  },
  history: (params?: ChatHistoryParams) =>
    api.get<PaginatedResponse<ChatMessage>>('/chatbot/history', { params }).then((r) => r.data),
  suggestions: () => api.get<QuickSuggestion[]>('/chatbot/suggestions').then((r) => r.data),
  clearHistory: () => api.delete('/chatbot/history').then((r) => r.data),
}

export function useChatHistory(params?: ChatHistoryParams) {
  return useQuery({
    queryKey: chatKeys.history(params),
    queryFn: () => chatbotApi.history(params),
  })
}

export function useChatSuggestions() {
  return useQuery({
    queryKey: chatKeys.suggestions(),
    queryFn: chatbotApi.suggestions,
    staleTime: Infinity,
  })
}

export function useSendMessageMutation() {
  return useMutation({ mutationFn: chatbotApi.send })
}

export function useClearHistoryMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: chatbotApi.clearHistory,
    onSuccess: () => qc.invalidateQueries({ queryKey: chatKeys.all }),
  })
}
