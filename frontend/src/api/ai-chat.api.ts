import { api } from '@/api/axios'

export interface AiChatResponse {
  reply: string
  model: string
}

export async function sendAiChatMessage(message: string): Promise<AiChatResponse> {
  const { data } = await api.post<AiChatResponse>('/ai-chat', { message })
  return data
}

export async function demoAiChatToConsole(message: string) {
  const result = await sendAiChatMessage(message)
  console.log('Gemini reply:', result.reply)
  return result
}
