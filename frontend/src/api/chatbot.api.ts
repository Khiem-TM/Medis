import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { computed } from 'vue'
import type { Ref } from 'vue'
import { api } from './axios'
import type { ChatMessage, ChatSendResponse, ChatHistoryParams, QuickSuggestion, ChatSession } from '@/types/chatbot.types'
import type { PaginatedResponse } from '@/types/api.types'

export const chatKeys = {
  all: ['chat'] as const,
  sessions: () => [...chatKeys.all, 'sessions'] as const,
  sessionMessages: (sessionId?: string | number | null, params?: ChatHistoryParams) => [...chatKeys.all, 'sessions', sessionId, 'messages', params] as const,
  history: (params?: ChatHistoryParams) => [...chatKeys.all, 'history', params] as const,
  suggestions: () => [...chatKeys.all, 'suggestions'] as const,
}

const chatbotUnavailableReply = 'Hiện tại Medis AI chưa thể kết nối tới dịch vụ AI. Bạn vẫn có thể xem lại câu hỏi vừa gửi trong màn hình trò chuyện. Với triệu chứng khẩn cấp như đau ngực, khó thở, ngất hoặc dị ứng nặng, hãy gọi cấp cứu hoặc đến cơ sở y tế gần nhất. Thông tin này chỉ mang tính tham khảo, không thay thế khám bác sĩ.'

export const chatbotApi = {
  send: async ({ message, sessionId }: { message: string; sessionId?: string | number | null }) => {
    try {
      return await api.post<ChatSendResponse>('/chatbot/message', {
        content: message,
        session_id: sessionId ? Number(sessionId) : undefined,
      }).then((r) => r.data)
    } catch (error) {
      if ((error as { status?: number })?.status !== 503) throw error
      const now = new Date().toISOString()
      return {
        user_message: {
          id: `local-user-${Date.now()}`,
          user_id: 'local',
          session_id: sessionId ? String(sessionId) : 'local',
          role: 'user',
          content: message,
          created_at: now,
        },
        assistant_message: {
          id: `local-assistant-${Date.now()}`,
          user_id: 'local',
          session_id: sessionId ? String(sessionId) : 'local',
          role: 'assistant',
          content: chatbotUnavailableReply,
          created_at: now,
        },
        session: {
          id: sessionId ? String(sessionId) : 'local',
          title: message.slice(0, 80) || 'Cuộc trò chuyện mới',
          message_count: 2,
          last_message_preview: chatbotUnavailableReply,
          created_at: now,
          updated_at: now,
          last_message_at: now,
        },
      } satisfies ChatSendResponse
    }
  },
  sessions: () => api.get<ChatSession[]>('/chatbot/sessions').then((r) => r.data),
  createSession: (title?: string) =>
    api.post<ChatSession>('/chatbot/sessions', { title }).then((r) => r.data),
  sessionMessages: (sessionId: string | number, params?: ChatHistoryParams) =>
    api.get<PaginatedResponse<ChatMessage>>(`/chatbot/sessions/${sessionId}/messages`, { params }).then((r) => r.data),
  deleteSession: (sessionId: string | number) =>
    api.delete(`/chatbot/sessions/${sessionId}`).then((r) => r.data),
  history: (params?: ChatHistoryParams) =>
    api.get<PaginatedResponse<ChatMessage>>('/chatbot/history', { params }).then((r) => r.data),
  suggestions: () => api.get<QuickSuggestion[]>('/chatbot/suggestions').then((r) => r.data),
  clearHistory: () => api.delete('/chatbot/history').then((r) => r.data),
}

export function useChatSessions() {
  return useQuery({
    queryKey: chatKeys.sessions(),
    queryFn: chatbotApi.sessions,
  })
}

export function useChatSessionMessages(sessionId: Ref<string | null>, params?: ChatHistoryParams) {
  return useQuery({
    queryKey: computed(() => chatKeys.sessionMessages(sessionId.value, params)),
    queryFn: () => chatbotApi.sessionMessages(sessionId.value as string, params),
    enabled: computed(() => !!sessionId.value),
  })
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
  const qc = useQueryClient()
  return useMutation({
    mutationFn: chatbotApi.send,
    onSuccess: () => qc.invalidateQueries({ queryKey: chatKeys.sessions() }),
  })
}

export function useClearHistoryMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: chatbotApi.clearHistory,
    onSuccess: () => qc.invalidateQueries({ queryKey: chatKeys.all }),
  })
}

export function useCreateChatSessionMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: chatbotApi.createSession,
    onSuccess: () => qc.invalidateQueries({ queryKey: chatKeys.sessions() }),
  })
}

export function useDeleteChatSessionMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: chatbotApi.deleteSession,
    onSuccess: () => qc.invalidateQueries({ queryKey: chatKeys.sessions() }),
  })
}
