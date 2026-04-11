import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { api } from './axios'
import type { ChatMessage, ChatSendResponse, ChatHistoryParams } from '@/types/chatbot.types'
import type { PaginatedResponse } from '@/types/api.types'

export const chatKeys = {
  all: ['chat'] as const,
  history: (params?: ChatHistoryParams) => [...chatKeys.all, 'history', params] as const,
  suggestions: () => [...chatKeys.all, 'suggestions'] as const,
}

export const chatbotApi = {
  send: (message: string) =>
    api.post<ChatSendResponse>('/chatbot/message', { message }).then((r) => r.data),
  history: (params?: ChatHistoryParams) =>
    api.get<PaginatedResponse<ChatMessage>>('/chatbot/history', { params }).then((r) => r.data),
  suggestions: () => api.get<string[]>('/chatbot/suggestions').then((r) => r.data),
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
