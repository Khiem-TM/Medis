<script setup lang="ts">
import { computed } from 'vue'
import { useNotificationStore } from '@/stores/notification.store'
import { formatDateTime } from '@/utils/format'

const notificationStore = useNotificationStore()

const items = computed(() => notificationStore.items.slice(0, 6))

function priorityTone(priority: string) {
  if (priority === 'urgent') return 'bg-error-container text-error'
  if (priority === 'high') return 'bg-tertiary-fixed text-tertiary'
  if (priority === 'medium') return 'bg-primary-fixed text-primary'
  return 'bg-surface-container text-on-surface-variant'
}
</script>

<template>
  <div class="glass-panel-strong w-[min(24rem,calc(100vw-2rem))] rounded-[1.4rem] p-3">
    <div class="flex items-center justify-between px-2 py-2">
      <div>
        <p class="text-sm font-semibold text-on-surface">Thông báo</p>
        <p class="text-xs text-outline">{{ notificationStore.unreadCount }} chưa đọc</p>
      </div>
      <button
        type="button"
        class="rounded-full px-3 py-1.5 text-xs font-semibold text-primary transition hover:bg-primary/8 disabled:opacity-50"
        :disabled="notificationStore.unreadCount === 0"
        @click="notificationStore.markAllRead()"
      >
        Đánh dấu tất cả
      </button>
    </div>

    <div v-if="items.length === 0" class="rounded-2xl bg-white/55 px-4 py-8 text-center">
      <p class="text-sm font-medium text-on-surface">Chưa có thông báo nào</p>
      <p class="mt-1 text-xs text-outline">Các nhắc nhở và cảnh báo sẽ xuất hiện tại đây.</p>
    </div>

    <div v-else class="space-y-2">
      <button
        v-for="item in items"
        :key="item.id"
        type="button"
        class="w-full rounded-2xl border border-white/70 bg-white/60 p-3 text-left transition hover:bg-white/80"
        @click="notificationStore.markAsRead(item.id)"
      >
        <div class="flex items-start gap-3">
          <span
            :class="[
              'mt-0.5 inline-flex rounded-full px-2 py-1 text-[11px] font-semibold uppercase tracking-wide',
              priorityTone(item.priority),
            ]"
          >
            {{ item.priority }}
          </span>
          <div class="min-w-0 flex-1">
            <div class="flex items-start justify-between gap-3">
              <p class="text-sm font-semibold text-on-surface">{{ item.title }}</p>
              <span v-if="!item.is_read" class="mt-1 h-2.5 w-2.5 rounded-full bg-primary" />
            </div>
            <p class="mt-1 text-sm text-on-surface-variant">{{ item.body }}</p>
            <p class="mt-2 text-xs text-outline">{{ formatDateTime(item.created_at) }}</p>
          </div>
        </div>
      </button>
    </div>
  </div>
</template>
