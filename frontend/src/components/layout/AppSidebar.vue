<script setup lang="ts">
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store'
import { useUiStore } from '@/stores/ui.store'
import AppAvatar from '@/components/ui/AppAvatar.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const uiStore = useUiStore()

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
  { to: '/profile/health', label: 'Hồ sơ bệnh án', icon: 'records' },
  { to: '/profile/prescriptions', label: 'Đơn thuốc', icon: 'prescription' },
  { to: '/schedule', label: 'Nhắc nhở', icon: 'bell', badge: '3' },
  { to: '/chatbot', label: 'AI Chat', icon: 'ai' },
  { to: '/interactions', label: 'Tương tác thuốc', icon: 'shield' },
  { to: '/drugs', label: 'Tra cứu thuốc', icon: 'search' },
]

function isActive(to: string) {
  return route.path === to || route.path.startsWith(to + '/')
}

async function logout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<template>
  <aside
    :class="['fixed inset-y-0 left-0 z-40 flex flex-col transition-all duration-200', uiStore.sidebarOpen ? 'w-60' : 'w-16']"
    style="background: #0C1D42;"
  >
    <!-- Logo -->
    <div
      class="flex items-center gap-3 px-4 py-5 flex-shrink-0"
      style="border-bottom: 1px solid rgba(255,255,255,0.08);"
    >
      <div
        class="w-8 h-8 flex-shrink-0 rounded-lg flex items-center justify-center"
        style="background: rgba(37,99,235,0.85);"
      >
        <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <span v-if="uiStore.sidebarOpen" class="text-lg font-bold text-white tracking-tight">Medis</span>
    </div>

    <!-- Nav -->
    <nav class="flex-1 overflow-y-auto py-4 px-2 space-y-0.5">
      <div
        v-if="uiStore.sidebarOpen"
        class="px-3 mb-2 text-xs font-bold tracking-widest uppercase"
        style="color: rgba(255,255,255,0.30);"
      >MENU</div>

      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :title="!uiStore.sidebarOpen ? item.label : undefined"
        class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150"
        :style="isActive(item.to)
          ? 'background: rgba(255,255,255,0.12); color: #fff;'
          : 'color: rgba(255,255,255,0.58);'"
      >
        <!-- Dashboard -->
        <svg v-if="item.icon === 'dashboard'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 5a1 1 0 011-1h4a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm0 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zm10-10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zm0 8a1 1 0 011-1h4a1 1 0 011 1v6a1 1 0 01-1 1h-4a1 1 0 01-1-1v-6z" />
        </svg>
        <!-- Records -->
        <svg v-else-if="item.icon === 'records'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <!-- Prescription -->
        <svg v-else-if="item.icon === 'prescription'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
        </svg>
        <!-- Bell -->
        <svg v-else-if="item.icon === 'bell'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        <!-- AI -->
        <svg v-else-if="item.icon === 'ai'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <!-- Shield -->
        <svg v-else-if="item.icon === 'shield'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
        <!-- Search -->
        <svg v-else-if="item.icon === 'search'" class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>

        <span v-if="uiStore.sidebarOpen" class="truncate flex-1">{{ item.label }}</span>
        <span
          v-if="uiStore.sidebarOpen && item.badge"
          class="flex-shrink-0 text-xs font-bold px-1.5 py-0.5 rounded-full text-center"
          style="background: #2563EB; color: white; min-width: 20px;"
        >{{ item.badge }}</span>
      </RouterLink>

      <!-- Account section -->
      <div
        v-if="uiStore.sidebarOpen"
        class="px-3 pt-5 pb-2 text-xs font-bold tracking-widest uppercase"
        style="color: rgba(255,255,255,0.30);"
      >ACCOUNT</div>
      <div v-else class="my-3" style="border-top: 1px solid rgba(255,255,255,0.08);"></div>

      <RouterLink
        to="/profile"
        :title="!uiStore.sidebarOpen ? 'Cài đặt' : undefined"
        class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150"
        :style="isActive('/profile') && !isActive('/profile/health') && !isActive('/profile/prescriptions')
          ? 'background: rgba(255,255,255,0.12); color: #fff;'
          : 'color: rgba(255,255,255,0.58);'"
      >
        <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <span v-if="uiStore.sidebarOpen" class="truncate">Cài đặt</span>
      </RouterLink>

      <button
        @click="logout"
        :title="!uiStore.sidebarOpen ? 'Đăng xuất' : undefined"
        class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150"
        style="color: rgba(255,255,255,0.58);"
        @mouseenter="($event.currentTarget as HTMLElement).style.color = 'white'"
        @mouseleave="($event.currentTarget as HTMLElement).style.color = 'rgba(255,255,255,0.58)'"
      >
        <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
        </svg>
        <span v-if="uiStore.sidebarOpen" class="truncate">Đăng xuất</span>
      </button>
    </nav>

    <!-- Bottom consultation card (expanded only) -->
    <div v-if="uiStore.sidebarOpen" class="mx-3 mb-3 rounded-2xl p-4 flex-shrink-0" style="background: #142853;">
      <div
        class="w-9 h-9 rounded-xl flex items-center justify-center mb-3"
        style="background: rgba(37,99,235,0.25);"
      >
        <svg class="w-5 h-5" style="color: #93C5FD;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
        </svg>
      </div>
      <div class="text-sm font-bold text-white mb-1">Cần tư vấn?</div>
      <div class="text-xs mb-3" style="color: rgba(255,255,255,0.50);">Đặt lịch với bác sĩ chuyên khoa.</div>
      <RouterLink
        to="/chatbot"
        class="flex items-center gap-1 text-xs font-semibold rounded-lg px-3 py-2 text-white transition-opacity hover:opacity-90"
        style="background: rgba(37,99,235,0.75);"
      >
        Hỏi AI ngay
        <svg class="w-3 h-3 ml-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
        </svg>
      </RouterLink>
    </div>

    <!-- User footer -->
    <div class="p-3 flex-shrink-0" style="border-top: 1px solid rgba(255,255,255,0.08);">
      <RouterLink
        to="/profile"
        class="flex items-center gap-3 p-2 rounded-xl transition-all hover:bg-white/5"
      >
        <AppAvatar :src="authStore.user?.avatar_url" :name="authStore.user?.full_name" size="sm" class="flex-shrink-0" />
        <div v-if="uiStore.sidebarOpen" class="flex-1 min-w-0">
          <p class="text-sm font-semibold text-white truncate">{{ authStore.user?.full_name ?? authStore.user?.username }}</p>
          <p class="text-xs truncate" style="color: rgba(255,255,255,0.40);">Bệnh nhân</p>
        </div>
      </RouterLink>
    </div>
  </aside>
</template>
