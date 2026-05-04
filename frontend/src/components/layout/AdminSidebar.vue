<script setup lang="ts">
import { RouterLink, useRoute } from 'vue-router'
import { useUiStore } from '@/stores/ui.store'

const route = useRoute()
const uiStore = useUiStore()

const navItems = [
  { to: '/admin/users', label: 'Người dùng', icon: 'users' },
  { to: '/admin/drugs', label: 'Thuốc', icon: 'drugs' },
  { to: '/admin/interactions', label: 'Tương tác', icon: 'interaction' },
  { to: '/admin/logs', label: 'Nhật ký', icon: 'logs' },
]

function isActive(to: string) {
  return route.path.startsWith(to)
}
</script>

<template>
  <aside
    :class="[
      'fixed inset-y-0 left-0 z-40 bg-on-surface flex flex-col transition-all duration-200',
      uiStore.sidebarOpen ? 'w-60' : 'w-16',
    ]"
  >
    <!-- Logo -->
    <div class="flex items-center gap-3 px-4 py-5 border-b border-white/10">
      <div class="w-8 h-8 flex-shrink-0 bg-primary rounded-lg flex items-center justify-center">
        <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <div v-if="uiStore.sidebarOpen">
        <span class="text-lg font-bold text-white">Medis</span>
        <span class="text-xs text-white/50 ml-1">Admin</span>
      </div>
    </div>

    <!-- Back to app -->
    <div class="px-2 pt-3">
      <RouterLink
        to="/dashboard"
        class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-white/60 hover:text-white hover:bg-white/10 transition-colors"
      >
        <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 17l-5-5m0 0l5-5m-5 5h12" />
        </svg>
        <span v-if="uiStore.sidebarOpen">Về ứng dụng</span>
      </RouterLink>
    </div>

    <!-- Nav -->
    <nav class="flex-1 px-2 py-2 space-y-0.5">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :class="[
          'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
          isActive(item.to)
            ? 'bg-primary text-white'
            : 'text-white/60 hover:bg-white/10 hover:text-white',
        ]"
      >
        <svg v-if="item.icon === 'users'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
        <svg v-else-if="item.icon === 'drugs'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
        </svg>
        <svg v-else-if="item.icon === 'interaction'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <svg v-else-if="item.icon === 'logs'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <span v-if="uiStore.sidebarOpen" class="truncate">{{ item.label }}</span>
      </RouterLink>
    </nav>
  </aside>
</template>
