export type ChatRole = 'user' | 'assistant'

export interface ChatMessage {
  id: string
  user_id: string
  session_id: string
  role: ChatRole
  content: string
  created_at: string
}

export interface ChatSendRequest {
  message: string
  session_id?: string | number | null
}

export interface ChatSession {
  id: string
  title: string
  message_count: number
  last_message_preview: string | null
  created_at: string
  updated_at: string
  last_message_at: string | null
}

export interface ChatSendResponse {
  session: ChatSession
  user_message: ChatMessage
  assistant_message: ChatMessage
}

export interface ChatHistoryParams {
  page?: number
  size?: number
}

export interface QuickSuggestion {
  text: string
  category: 'drug_usage' | 'symptom' | 'interaction'
}
