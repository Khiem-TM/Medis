<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store'
import { useNotificationStore } from '@/stores/notification.store'
import { useUiStore } from '@/stores/ui.store'
import AppAvatar from '@/components/ui/AppAvatar.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()
const uiStore = useUiStore()

const navItems = computed(() => [
  { to: '/dashboard', label: 'Bảng điều khiển', icon: 'dashboard' },
  { to: '/profile/prescriptions', label: 'Đơn thuốc cá nhân', icon: 'prescription' },
  { to: '/profile/health', label: 'Hồ sơ sức khoẻ', icon: 'health' },
  { to: '/interactions', label: 'Thuốc & Tương tác', icon: 'shield' },
  { to: '/chatbot', label: 'Chatbot AI', icon: 'bot' },
  { to: '/schedule', label: 'Lịch trình', icon: 'calendar', badge: notificationStore.unreadCount || undefined },
])

function isActive(to: string) {
  return route.path === to || route.path.startsWith(`${to}/`)
}

function iconPath(icon: string) {
  switch (icon) {
    case 'dashboard':
      return 'M4 5a1 1 0 011-1h4a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm0 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zm10-10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zm0 8a1 1 0 011-1h4a1 1 0 011 1v6a1 1 0 01-1 1h-4a1 1 0 01-1-1v-6z'
    case 'profile':
      return 'M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 11a3 3 0 11-6 0 3 3 0 016 0zM12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10z'
    case 'prescription':
      return 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'
    case 'health':
      return 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z'
    case 'search':
      return 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z'
    case 'shield':
      return 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z'
    case 'bot':
      return 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z'
    case 'spark':
      return 'M12 3l1.912 5.813L20 10.725l-4.5 3.275L17.412 20 12 16.725 6.588 20 8.5 14 4 10.725l6.088-1.912L12 3z'
    case 'calendar':
      return 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z'
    default:
      return 'M12 8v4l3 3'
  }
}

async function logout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<template>
  <aside
    class="fixed inset-y-3 left-3 z-50 flex flex-col rounded-[2rem] glass-panel-strong transition-all duration-300 lg:inset-y-4 lg:left-4"
    :class="[
      uiStore.sidebarOpen ? 'w-[17rem]' : 'w-[5.25rem]',
      uiStore.mobileSidebarOpen ? 'translate-x-0' : '-translate-x-[120%] lg:translate-x-0',
    ]"
  >
    <div class="flex items-center gap-3 px-4 py-5 soft-divider">
      <img src="@/assets/logo.png" alt="Medis Logo" class="w-12 h-12 object-contain rounded-2xl shadow-sm" />
      <div v-if="uiStore.sidebarOpen" class="min-w-0">
        <p class="text-lg font-bold tracking-tight text-on-surface">Medis</p>
        <p class="text-xs uppercase tracking-[0.22em] text-outline">Health AI</p>
      </div>
    </div>

    <nav class="flex-1 space-y-1 overflow-y-auto px-3 py-4 no-scrollbar">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="group flex items-center gap-3 rounded-2xl px-3 py-3 text-sm font-medium transition-all"
        :class="isActive(item.to)
          ? 'bg-gradient-to-r from-primary/10 to-secondary/10 text-primary shadow-sm ring-1 ring-primary/20'
          : 'text-on-surface-variant hover:bg-surface-container-low/80 hover:text-on-surface'"
      >
        <span
          class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-2xl transition"
          :class="isActive(item.to) ? 'bg-surface-container-lowest text-primary shadow-sm' : 'bg-surface-container-low/60 text-outline group-hover:text-primary'"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" :d="iconPath(item.icon)" />
          </svg>
        </span>
        <span v-if="uiStore.sidebarOpen" class="min-w-0 flex-1 truncate">{{ item.label }}</span>
        <span
          v-if="uiStore.sidebarOpen && item.badge"
          class="rounded-full bg-tertiary-fixed/30 px-2 py-1 text-[11px] font-semibold text-tertiary"
        >
          {{ item.badge }}
        </span>
      </RouterLink>
    </nav>

  </aside>
</template>
