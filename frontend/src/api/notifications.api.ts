import { api } from './axios'
import type { NotificationListResponse } from '@/types/notification.types'

export const notificationKeys = {
  all: ['notifications'] as const,
  list: (page = 1, size = 8, unreadOnly = false) =>
    [...notificationKeys.all, 'list', { page, size, unreadOnly }] as const,
}

export const notificationsApi = {
  list: (params?: { page?: number; size?: number; unread_only?: boolean }) =>
    api.get<NotificationListResponse>('/notifications', { params }).then((r) => r.data),
  markRead: (notificationId: number) =>
    api.patch(`/notifications/${notificationId}/read`).then((r) => r.data),
  markAllRead: () =>
    api.patch('/notifications/read-all').then((r) => r.data),
}
