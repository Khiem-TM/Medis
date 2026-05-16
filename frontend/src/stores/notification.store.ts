import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { notificationsApi } from '@/api/notifications.api'
import { WS_BASE_URL } from '@/api/axios'
import type {
  NotificationEventPayload,
  NotificationItem,
  NotificationSocketEvent,
} from '@/types/notification.types'

function toNotificationItem(payload: NotificationEventPayload): NotificationItem {
  return {
    id: payload.id,
    user_id: 0,
    type: payload.notification_type,
    priority: payload.priority,
    title: payload.title,
    body: payload.body,
    data: payload.data ?? null,
    is_read: false,
    reminder_id: payload.reminder_id ?? null,
    scheduled_at: null,
    sent_at: null,
    created_at: new Date().toISOString(),
  }
}

export const useNotificationStore = defineStore('notifications', () => {
  const items = ref<NotificationItem[]>([])
  const unreadCountState = ref(0)
  const wsConnected = ref(false)
  const reconnectAttempts = ref(0)

  let socket: WebSocket | null = null
  let reconnectTimer: number | null = null
  let pingTimer: number | null = null
  let currentToken: string | null = null

  const unreadCount = computed(() => unreadCountState.value)

  async function loadLatest() {
    const data = await notificationsApi.list({ page: 1, size: 8 })
    items.value = data.items
    unreadCountState.value = data.unread_count
    return data
  }

  function clearTimers() {
    if (reconnectTimer) {
      window.clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (pingTimer) {
      window.clearInterval(pingTimer)
      pingTimer = null
    }
  }

  function cleanupSocket(resetToken = false) {
    clearTimers()
    if (socket) {
      socket.onopen = null
      socket.onmessage = null
      socket.onclose = null
      socket.onerror = null
      socket.close()
      socket = null
    }
    wsConnected.value = false
    if (resetToken) currentToken = null
  }

  function scheduleReconnect() {
    if (!currentToken) return
    const delay = Math.min(1000 * 2 ** reconnectAttempts.value, 30000)
    reconnectAttempts.value += 1
    reconnectTimer = window.setTimeout(() => {
      connect(currentToken!)
    }, delay)
  }

  function ingest(notification: NotificationItem) {
    const existing = items.value.findIndex((item) => item.id === notification.id)
    if (existing >= 0) {
      items.value[existing] = notification
      return
    }
    items.value.unshift(notification)
    items.value = items.value.slice(0, 20)
    if (!notification.is_read) {
      unreadCountState.value += 1
    }
  }

  function handleSocketMessage(event: MessageEvent<string>) {
    const data = JSON.parse(event.data) as NotificationSocketEvent
    if (data.type === 'connected') {
      wsConnected.value = true
      reconnectAttempts.value = 0
      return
    }
    if (data.type === 'notification') {
      ingest(toNotificationItem(data.payload))
    }
  }

  function startPing() {
    clearTimers()
    pingTimer = window.setInterval(() => {
      if (socket?.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000)
  }

  function connect(token: string) {
    currentToken = token
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
      return
    }

    const url = `${WS_BASE_URL}/api/v1/notifications/ws?token=${encodeURIComponent(token)}`
    socket = new WebSocket(url)

    socket.onopen = () => {
      wsConnected.value = true
      reconnectAttempts.value = 0
      startPing()
    }
    socket.onmessage = handleSocketMessage
    socket.onerror = () => {
      wsConnected.value = false
    }
    socket.onclose = () => {
      wsConnected.value = false
      clearTimers()
      if (currentToken) scheduleReconnect()
    }

    void loadLatest().catch(() => {})
  }

  function disconnect() {
    cleanupSocket(true)
  }

  async function markAsRead(id: number) {
    const target = items.value.find((item) => item.id === id)
    if (!target || target.is_read) return
    target.is_read = true
    unreadCountState.value = Math.max(0, unreadCountState.value - 1)
    try {
      await notificationsApi.markRead(id)
      if (socket?.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'mark_read', notification_id: id }))
      }
    } catch {
      target.is_read = false
      unreadCountState.value += 1
      throw new Error('Không thể đánh dấu đã đọc')
    }
  }

  async function markAllRead() {
    const previous = items.value.map((item) => ({ ...item }))
    items.value = items.value.map((item) => ({ ...item, is_read: true }))
    unreadCountState.value = 0
    try {
      await notificationsApi.markAllRead()
    } catch {
      items.value = previous
      unreadCountState.value = previous.filter((item) => !item.is_read).length
      throw new Error('Không thể đánh dấu tất cả đã đọc')
    }
  }

  return {
    items,
    unreadCount,
    wsConnected,
    connect,
    disconnect,
    loadLatest,
    markAsRead,
    markAllRead,
    ingest,
  }
})
