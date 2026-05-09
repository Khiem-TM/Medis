<script setup lang="ts">
import { useUiStore } from '@/stores/ui.store'
import { useAuthStore } from '@/stores/auth.store'
import { useRouter } from 'vue-router'
import AppAvatar from '@/components/ui/AppAvatar.vue'

const uiStore = useUiStore()
const authStore = useAuthStore()
const router = useRouter()

async function logout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<template>
  <header
    class="fixed top-0 right-0 z-30 bg-white transition-[left] duration-200"
    :class="uiStore.sidebarOpen ? 'left-60' : 'left-16'"
    style="border-bottom: 1px solid rgba(12,29,66,0.08);"
  >
    <div class="flex items-center justify-between px-5 h-14 gap-4">
      <!-- Sidebar toggle -->
      <button
        @click="uiStore.toggleSidebar()"
        class="p-2 rounded-lg transition-colors flex-shrink-0 hover:bg-[#F3F5F7]"
        style="color: #5A6985;"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <!-- Search bar -->
      <div class="flex-1 max-w-xs hidden md:block">
        <div class="flex items-center gap-2 px-3 py-2 rounded-xl" style="background: #F3F5F7;">
          <svg class="w-4 h-4 flex-shrink-0" style="color: #8A95AC;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            class="flex-1 bg-transparent outline-none text-sm"
            style="color: #0C1D42;"
            placeholder="Tìm thuốc, bệnh, bác sĩ..."
          />
          <kbd class="text-xs px-1.5 py-0.5 rounded font-mono hidden lg:block" style="background: rgba(12,29,66,0.07); color: #8A95AC;">⌘K</kbd>
        </div>
      </div>

      <!-- Right tools -->
      <div class="flex items-center gap-1.5 ml-auto">
        <!-- Admin link -->
        <RouterLink
          v-if="authStore.isAdmin"
          to="/admin"
          class="text-xs font-semibold px-3 py-1.5 rounded-lg transition-opacity hover:opacity-80"
          style="background: #DCEDFF; color: #1D4FD8;"
        >
          Admin
        </RouterLink>

        <!-- Notification bell -->
        <button
          class="relative p-2 rounded-lg transition-colors hover:bg-[#F3F5F7]"
          style="color: #5A6985;"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <span class="absolute top-1.5 right-1.5 w-2 h-2 rounded-full" style="background: #EF4444;"></span>
        </button>

        <!-- Divider -->
        <div class="w-px h-6 mx-1" style="background: rgba(12,29,66,0.10);"></div>

        <!-- User menu -->
        <div class="relative group">
          <button class="flex items-center gap-2 px-2 py-1.5 rounded-xl transition-colors hover:bg-[#F3F5F7]">
            <AppAvatar :src="authStore.user?.avatar_url" :name="authStore.user?.full_name" size="sm" />
            <div class="hidden md:block text-left">
              <p class="text-sm font-semibold leading-none" style="color: #0C1D42;">
                {{ authStore.user?.full_name?.split(' ').slice(-1)[0] ?? authStore.user?.username }}
              </p>
              <p class="text-xs leading-none mt-0.5" style="color: #8A95AC;">Bệnh nhân</p>
            </div>
            <svg class="w-3.5 h-3.5 hidden md:block" style="color: #B5BCCB;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- Dropdown -->
          <div
            class="absolute right-0 top-full mt-1 w-48 bg-white rounded-xl overflow-hidden opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all"
            style="border: 1px solid rgba(12,29,66,0.08); box-shadow: 0 8px 24px -8px rgba(12,29,66,0.16);"
          >
            <div class="px-4 py-3" style="border-bottom: 1px solid rgba(12,29,66,0.07);">
              <p class="text-sm font-semibold truncate" style="color: #0C1D42;">{{ authStore.user?.full_name ?? authStore.user?.username }}</p>
              <p class="text-xs truncate mt-0.5" style="color: #8A95AC;">{{ authStore.user?.email }}</p>
            </div>
            <div class="p-1">
              <RouterLink
                to="/profile"
                class="flex items-center gap-2 px-3 py-2 text-sm rounded-lg transition-colors hover:bg-[#F8FAFB]"
                style="color: #2A3A5E;"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                Hồ sơ cá nhân
              </RouterLink>
              <button
                @click="logout"
                class="w-full flex items-center gap-2 px-3 py-2 text-sm rounded-lg transition-colors hover:bg-[#FEE2E2]"
                style="color: #EF4444;"
              >
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                Đăng xuất
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>
