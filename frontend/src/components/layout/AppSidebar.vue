<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store'
import { useUiStore } from '@/stores/ui.store'
import AppAvatar from '@/components/ui/AppAvatar.vue'

const route = useRoute()
const authStore = useAuthStore()
const uiStore = useUiStore()

interface NavItem {
  to: string
  label: string
  icon: string
  exact?: boolean
}

const navItems: NavItem[] = [
  { to: '/dashboard', label: 'Tổng quan', icon: 'dashboard' },
  { to: '/profile', label: 'Hồ sơ cá nhân', icon: 'person' },
  { to: '/profile/prescriptions', label: 'Đơn thuốc', icon: 'prescription' },
  { to: '/profile/health', label: 'Hồ sơ khám bệnh', icon: 'health' },
  { to: '/schedule', label: 'Lịch uống thuốc', icon: 'schedule' },
  { to: '/drugs', label: 'Tra cứu thuốc', icon: 'drugs' },
  { to: '/interactions', label: 'Kiểm tra tương tác', icon: 'interaction' },
  { to: '/recommendations', label: 'Gợi ý thuốc AI', icon: 'recommendation' },
  { to: '/chatbot', label: 'Chatbot AI', icon: 'chat' },
]

function isActive(to: string) {
  return route.path === to || route.path.startsWith(to + '/')
}
</script>

<template>
  <aside
    :class="[
      'fixed inset-y-0 left-0 z-40 bg-card border-r border-outline-variant flex flex-col transition-all duration-200',
      uiStore.sidebarOpen ? 'w-60' : 'w-16',
    ]"
  >
    <!-- Logo -->
    <div class="flex items-center gap-3 px-4 py-5 border-b border-outline-variant">
      <div class="w-8 h-8 flex-shrink-0 bg-primary rounded-lg flex items-center justify-center shadow-sm">
        <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <span v-if="uiStore.sidebarOpen" class="text-lg font-bold text-on-surface truncate">Medis</span>
    </div>

    <!-- Nav -->
    <nav class="flex-1 px-2 py-4 space-y-0.5 overflow-y-auto">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :title="!uiStore.sidebarOpen ? item.label : undefined"
        :class="[
          'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
          isActive(item.to)
            ? 'bg-primary-fixed text-primary'
            : 'text-outline hover:bg-surface-container-low hover:text-on-surface',
        ]"
      >
        <!-- Dashboard icon -->
        <svg v-if="item.icon === 'dashboard'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h4a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm0 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zm10-10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zm0 8a1 1 0 011-1h4a1 1 0 011 1v6a1 1 0 01-1 1h-4a1 1 0 01-1-1v-6z" />
        </svg>
        <!-- Person icon -->
        <svg v-else-if="item.icon === 'person'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
        <!-- Prescription icon -->
        <svg v-else-if="item.icon === 'prescription'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
        </svg>
        <!-- Health icon -->
        <svg v-else-if="item.icon === 'health'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
        </svg>
        <!-- Schedule icon -->
        <svg v-else-if="item.icon === 'schedule'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <!-- Drugs icon -->
        <svg v-else-if="item.icon === 'drugs'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
        </svg>
        <!-- Interaction icon -->
        <svg v-else-if="item.icon === 'interaction'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <!-- Recommendation / AI icon -->
        <svg v-else-if="item.icon === 'recommendation'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <!-- Chat icon -->
        <svg v-else-if="item.icon === 'chat'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>

        <span v-if="uiStore.sidebarOpen" class="truncate">{{ item.label }}</span>
      </RouterLink>
    </nav>

    <!-- User footer -->
    <div class="border-t border-outline-variant p-3">
      <RouterLink
        to="/profile"
        class="flex items-center gap-3 p-2 rounded-lg hover:bg-surface-container-low transition-colors"
      >
        <AppAvatar :src="authStore.user?.avatar_url" :name="authStore.user?.full_name" size="sm" />
        <div v-if="uiStore.sidebarOpen" class="flex-1 min-w-0">
          <p class="text-sm font-medium text-on-surface truncate">{{ authStore.user?.full_name ?? authStore.user?.username }}</p>
          <p class="text-xs text-outline truncate">{{ authStore.user?.email }}</p>
        </div>
      </RouterLink>
    </div>
  </aside>
</template>
