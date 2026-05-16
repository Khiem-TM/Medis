<script setup lang="ts">
import { computed, ref } from 'vue'
import { onClickOutside } from '@vueuse/core'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store'
import { useNotificationStore } from '@/stores/notification.store'
import { useUiStore } from '@/stores/ui.store'
import AppAvatar from '@/components/ui/AppAvatar.vue'
import MarketDrugSearchModal from '@/components/drug/MarketDrugSearchModal.vue'
import NotificationDropdown from '@/components/layout/NotificationDropdown.vue'

const router = useRouter()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()
const uiStore = useUiStore()

const searchOpen = ref(false)
const userMenuOpen = ref(false)
const settingsOpen = ref(false)
const notificationRef = ref<HTMLElement | null>(null)
const userMenuRef = ref<HTMLElement | null>(null)
const settingsMenuRef = ref<HTMLElement | null>(null)

onClickOutside(notificationRef, () => uiStore.setNotificationDropdown(false))
onClickOutside(userMenuRef, () => {
  userMenuOpen.value = false
})
onClickOutside(settingsMenuRef, () => {
  settingsOpen.value = false
})

const userLabel = computed(() => authStore.user?.full_name ?? authStore.user?.username ?? 'Người dùng')

function toggleSidebar() {
  if (window.innerWidth < 1024) {
    uiStore.toggleMobileSidebar()
    return
  }
  uiStore.toggleSidebar()
}

async function logout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<template>
  <header
    class="fixed right-0 top-0 z-30 h-20 px-4 sm:px-6 lg:px-8"
    :class="uiStore.sidebarOpen ? 'lg:left-[19rem]' : 'lg:left-[7.25rem]'"
  >
    <div class="mx-auto flex h-full max-w-screen-2xl items-center">
      <div class="glass-panel-strong flex h-16 w-full items-center justify-between rounded-[1.6rem] px-4 sm:px-5">
        <div class="flex items-center gap-3">
          <button
            type="button"
            class="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/65 text-on-surface transition hover:bg-white"
            @click="toggleSidebar"
          >
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          <button
            type="button"
            class="hidden min-w-[16rem] items-center gap-3 rounded-2xl bg-white/65 px-4 py-3 text-left text-sm text-outline transition hover:bg-white md:flex"
            @click="searchOpen = true"
          >
            <svg class="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <span class="flex-1">Tra cứu thuốc, sản phẩm, số đăng ký...</span>
            <kbd class="rounded-full bg-surface-container px-2 py-1 text-[11px] font-semibold text-on-surface-variant">⌘K</kbd>
          </button>
        </div>

        <div class="flex items-center gap-2 sm:gap-3">
          <!-- Notification Icon -->
          <div ref="notificationRef" class="relative">
            <button
              type="button"
              class="relative flex h-11 w-11 items-center justify-center rounded-2xl bg-white/65 text-on-surface transition hover:bg-white"
              @click="uiStore.setNotificationDropdown(!uiStore.notificationDropdownOpen)"
            >
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              <span
                v-if="notificationStore.unreadCount"
                class="absolute right-1.5 top-1.5 inline-flex min-h-5 min-w-5 items-center justify-center rounded-full bg-tertiary px-1 text-[10px] font-bold text-white"
              >
                {{ notificationStore.unreadCount > 9 ? '9+' : notificationStore.unreadCount }}
              </span>
            </button>
            <div v-if="uiStore.notificationDropdownOpen" class="absolute right-0 top-[calc(100%+0.75rem)] z-20">
              <NotificationDropdown />
            </div>
          </div>

          <!-- Settings Icon -->
          <div ref="settingsMenuRef" class="relative">
            <button
              type="button"
              class="relative flex h-11 w-11 items-center justify-center rounded-2xl bg-white/65 text-on-surface transition hover:bg-white"
              @click="settingsOpen = !settingsOpen"
            >
              <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
            <div
              v-if="settingsOpen"
              class="glass-panel-strong absolute right-0 top-[calc(100%+0.75rem)] z-20 w-48 rounded-[1.4rem] p-2"
            >
              <div class="mt-1 space-y-1">
                <button
                  type="button"
                  class="flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-sm text-on-surface transition hover:bg-white/70"
                  @click="settingsOpen = false"
                >
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                  </svg>
                  Tùy chọn hệ thống
                </button>
                <button
                  type="button"
                  class="flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-sm text-on-surface transition hover:bg-white/70"
                  @click="settingsOpen = false"
                >
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                  </svg>
                  Giao diện
                </button>
              </div>
            </div>
          </div>

          <!-- Avatar / Profile Icon -->
          <div ref="userMenuRef" class="relative">
            <button
              type="button"
              class="flex h-11 w-11 items-center justify-center rounded-full bg-white/65 transition hover:bg-white overflow-hidden p-0.5 border-2 border-transparent hover:border-primary/20"
              @click="userMenuOpen = !userMenuOpen"
            >
              <AppAvatar :src="authStore.user?.avatar_url" :name="authStore.user?.full_name" size="sm" class="w-full h-full" />
            </button>

            <div
              v-if="userMenuOpen"
              class="glass-panel-strong absolute right-0 top-[calc(100%+0.75rem)] z-20 w-60 rounded-[1.4rem] p-2"
            >
              <div class="rounded-2xl bg-white/65 px-4 py-3 text-center">
                <AppAvatar :src="authStore.user?.avatar_url" :name="authStore.user?.full_name" size="md" class="mx-auto mb-2" />
                <p class="truncate text-sm font-semibold text-on-surface">{{ userLabel }}</p>
                <p class="mt-1 truncate text-xs text-outline">{{ authStore.user?.email }}</p>
              </div>
              <div class="mt-2 space-y-1">
                <button
                  type="button"
                  class="flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-sm text-on-surface transition hover:bg-white/70"
                  @click="router.push('/profile'); userMenuOpen = false"
                >
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 11a3 3 0 11-6 0 3 3 0 016 0zM12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10z" />
                  </svg>
                  Hồ sơ cá nhân
                </button>
                <button
                  type="button"
                  class="flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-sm text-error transition hover:bg-error-container/60"
                  @click="logout"
                >
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  Đăng xuất
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <MarketDrugSearchModal v-model:open="searchOpen" />
  </header>
</template>
