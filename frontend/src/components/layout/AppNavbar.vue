<script setup lang="ts">
import { useUiStore } from '@/stores/ui.store'
import { useAuthStore } from '@/stores/auth.store'
import { useRouter } from 'vue-router'
import AppAvatar from '@/components/ui/AppAvatar.vue'

defineProps<{ offset?: boolean }>()

const uiStore = useUiStore()
const authStore = useAuthStore()
const router = useRouter()

async function logout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<template>
  <header class="fixed top-0 right-0 z-30 left-0 bg-white border-b border-[#E5E7EB]"
    :class="uiStore.sidebarOpen ? 'lg:left-60' : 'lg:left-16'"
  >
    <div class="flex items-center justify-between px-4 h-14">
      <!-- Sidebar toggle -->
      <button
        @click="uiStore.toggleSidebar()"
        class="p-2 rounded-lg text-[#6B7280] hover:bg-[#F3F4F6] hover:text-[#111827] transition-colors"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <!-- Right actions -->
      <div class="flex items-center gap-2">
        <!-- Admin link -->
        <router-link
          v-if="authStore.isAdmin"
          to="/admin"
          class="text-xs font-medium px-3 py-1.5 rounded-lg bg-purple-100 text-purple-700 hover:bg-purple-200 transition-colors"
        >
          Admin
        </router-link>

        <!-- User menu -->
        <div class="relative group">
          <button class="flex items-center gap-2 p-1.5 rounded-lg hover:bg-[#F3F4F6] transition-colors">
            <AppAvatar :src="authStore.user?.avatar_url" :name="authStore.user?.full_name" size="sm" />
            <svg class="w-4 h-4 text-[#6B7280]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <!-- Dropdown -->
          <div class="absolute right-0 top-full mt-1 w-48 bg-white rounded-xl shadow-lg border border-[#E5E7EB] overflow-hidden opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all">
            <div class="px-4 py-3 border-b border-[#E5E7EB]">
              <p class="text-sm font-medium text-[#111827] truncate">{{ authStore.user?.full_name ?? authStore.user?.username }}</p>
              <p class="text-xs text-[#6B7280] truncate">{{ authStore.user?.email }}</p>
            </div>
            <div class="p-1">
              <router-link to="/profile" class="flex items-center gap-2 px-3 py-2 text-sm text-[#374151] rounded-lg hover:bg-[#F9FAFB]">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                Hồ sơ cá nhân
              </router-link>
              <button @click="logout" class="w-full flex items-center gap-2 px-3 py-2 text-sm text-[#EF4444] rounded-lg hover:bg-red-50">
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
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
