export type ChatRole = 'user' | 'assistant'

export interface ChatMessage {
  id: string
  user_id: string
  role: ChatRole
  content: string
  created_at: string
}

export interface ChatSendRequest {
  message: string
}

export interface ChatSendResponse {
  user_message: ChatMessage
  assistant_message: ChatMessage
}

export interface ChatHistoryParams {
  page?: number
  size?: number
}
