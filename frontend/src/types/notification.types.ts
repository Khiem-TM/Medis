export type NotificationType = 'medication_reminder' | 'health_alert' | 'system' | 'daily_summary'
export type NotificationPriority = 'low' | 'medium' | 'high' | 'urgent'

export interface NotificationItem {
  id: number
  user_id: number
  type: NotificationType
  priority: NotificationPriority
  title: string
  body: string
  data: Record<string, unknown> | null
  is_read: boolean
  reminder_id: number | null
  scheduled_at: string | null
  sent_at: string | null
  created_at: string
}

export interface NotificationListResponse {
  items: NotificationItem[]
  total: number
  unread_count: number
}

export interface NotificationEventPayload {
  id: number
  notification_type: NotificationType
  priority: NotificationPriority
  title: string
  body: string
  data?: Record<string, unknown> | null
  reminder_id?: number | null
}

export type NotificationSocketEvent =
  | { type: 'connected'; user_id: number }
  | { type: 'pong' }
  | { type: 'notification'; payload: NotificationEventPayload }

