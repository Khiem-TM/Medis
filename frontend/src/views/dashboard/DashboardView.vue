<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminStats } from '@/api/admin.api'
import { usePrescriptions } from '@/api/prescriptions.api'
import { useActivityLogs } from '@/api/activity.api'
import { useAuthStore } from '@/stores/auth.store'
import { formatDateTime } from '@/utils/format'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import StatCard from '@/components/ui/StatCard.vue'
import type { ActivityAction } from '@/types/activity.types'

const router = useRouter()
const authStore = useAuthStore()

const { data: stats, isLoading: loadingStats } = useAdminStats()
const prescriptionParams = ref({ page: 1, size: 5 })
const { data: prescriptions, isLoading: loadingRx } = usePrescriptions(computed(() => prescriptionParams.value))
const activityParams = ref({ page: 1, size: 6 })
const { data: activityData, isLoading: loadingActivity } = useActivityLogs(computed(() => activityParams.value))

const isAdmin = computed(() => authStore.isAdmin)
const userName = computed(() => authStore.user?.full_name || authStore.user?.username || 'Bạn')

const quickActions = [
  {
    label: 'Kiểm tra tương tác',
    icon: 'M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4',
    path: '/interactions',
  },
  {
    label: 'Tra cứu thuốc',
    icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
    path: '/drugs',
  },
  {
    label: 'Đơn thuốc của tôi',
    icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    path: '/profile/prescriptions',
  },
  {
    label: 'Chatbot AI',
    icon: 'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z',
    path: '/chatbot',
  },
]

type ActivityMeta = { icon: string; color: string; bg: string; label: string }

function getActivityMeta(action: ActivityAction): ActivityMeta {
  const map: Record<ActivityAction, ActivityMeta> = {
    LOGIN: {
      icon: 'M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1',
      color: 'text-primary', bg: 'bg-primary-fixed', label: 'Đăng nhập',
    },
    LOGOUT: {
      icon: 'M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1',
      color: 'text-outline', bg: 'bg-surface-container', label: 'Đăng xuất',
    },
    REGISTER: {
      icon: 'M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z',
      color: 'text-tertiary', bg: 'bg-tertiary-fixed', label: 'Đăng ký tài khoản',
    },
    DRUG_SEARCH: {
      icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
      color: 'text-secondary', bg: 'bg-secondary-container', label: 'Tra cứu thuốc',
    },
    INTERACTION_CHECK: {
      icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
      color: 'text-error', bg: 'bg-error-container', label: 'Kiểm tra tương tác thuốc',
    },
    PRESCRIPTION_CREATE: {
      icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
      color: 'text-primary', bg: 'bg-primary-fixed', label: 'Tạo đơn thuốc mới',
    },
    PRESCRIPTION_UPDATE: {
      icon: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z',
      color: 'text-primary', bg: 'bg-primary-fixed', label: 'Cập nhật đơn thuốc',
    },
    PRESCRIPTION_DELETE: {
      icon: 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16',
      color: 'text-error', bg: 'bg-error-container', label: 'Xóa đơn thuốc',
    },
    PRESCRIPTION_VIEW: {
      icon: 'M15 12a3 3 0 11-6 0 3 3 0 016 0zM2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z',
      color: 'text-outline', bg: 'bg-surface-container', label: 'Xem đơn thuốc',
    },
    HEALTH_PROFILE_CREATE: {
      icon: 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z',
      color: 'text-tertiary', bg: 'bg-tertiary-fixed', label: 'Tạo hồ sơ sức khỏe',
    },
    HEALTH_PROFILE_UPDATE: {
      icon: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z',
      color: 'text-tertiary', bg: 'bg-tertiary-fixed', label: 'Cập nhật hồ sơ sức khỏe',
    },
    HEALTH_PROFILE_DELETE: {
      icon: 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16',
      color: 'text-error', bg: 'bg-error-container', label: 'Xóa hồ sơ sức khỏe',
    },
    HEALTH_PROFILE_VIEW: {
      icon: 'M15 12a3 3 0 11-6 0 3 3 0 016 0zM2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z',
      color: 'text-outline', bg: 'bg-surface-container', label: 'Xem hồ sơ sức khỏe',
    },
    CHATBOT_MESSAGE: {
      icon: 'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z',
      color: 'text-secondary', bg: 'bg-secondary-container', label: 'Hỏi chatbot AI',
    },
    PROFILE_UPDATE: {
      icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
      color: 'text-primary', bg: 'bg-primary-fixed', label: 'Cập nhật thông tin cá nhân',
    },
    PASSWORD_CHANGE: {
      icon: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z',
      color: 'text-outline', bg: 'bg-surface-container', label: 'Đổi mật khẩu',
    },
  }
  return map[action] ?? {
    icon: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    color: 'text-outline', bg: 'bg-surface-container', label: action,
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Welcome header -->
    <div>
      <h1 class="text-2xl font-bold text-on-surface">Xin chào, {{ userName }}</h1>
      <p class="text-sm text-outline mt-0.5">Đây là tổng quan sức khỏe của bạn hôm nay</p>
    </div>

    <!-- Admin stats row -->
    <template v-if="isAdmin">
      <div v-if="loadingStats" class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <AppSkeleton v-for="i in 4" :key="i" class="h-28 rounded-2xl" />
      </div>
      <div v-else-if="stats" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Tổng người dùng" :value="stats.total_users.toLocaleString()" :change="`+${stats.new_users_today} hôm nay`" :changePositive="true">
          <template #icon>
            <svg class="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          </template>
        </StatCard>
        <StatCard label="Thuốc trong danh mục" :value="stats.total_drugs.toLocaleString()" iconColor="bg-secondary-container">
          <template #icon>
            <svg class="w-5 h-5 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
          </template>
        </StatCard>
        <StatCard label="Cặp tương tác thuốc" :value="stats.total_interactions.toLocaleString()" iconColor="bg-error-container">
          <template #icon>
            <svg class="w-5 h-5 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </template>
        </StatCard>
        <StatCard label="Tin nhắn AI" :value="stats.total_chat_messages.toLocaleString()" iconColor="bg-surface-container-high">
          <template #icon>
            <svg class="w-5 h-5 text-on-surface-variant" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          </template>
        </StatCard>
      </div>
    </template>

    <!-- Main asymmetric grid: Activity (7/12) | Quick Actions (5/12) -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
      <!-- Left: Clinical Activity -->
      <section class="lg:col-span-7 bg-surface-container-low rounded-2xl p-6">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-lg font-bold text-on-surface">Hoạt động gần đây</h2>
        </div>

        <div v-if="loadingActivity" class="space-y-3">
          <AppSkeleton v-for="i in 4" :key="i" class="h-16 rounded-xl" />
        </div>
        <div v-else-if="!activityData?.items.length" class="text-center py-10">
          <p class="text-sm text-outline">Chưa có hoạt động nào được ghi nhận</p>
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="log in activityData.items"
            :key="log.id"
            class="bg-card p-4 rounded-xl flex items-start gap-4 border border-transparent hover:border-primary/10 transition-all shadow-sm"
          >
            <div :class="['w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0', getActivityMeta(log.action).bg]">
              <svg :class="['w-5 h-5', getActivityMeta(log.action).color]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getActivityMeta(log.action).icon" />
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-start justify-between gap-2">
                <p class="text-sm font-semibold text-on-surface truncate">{{ getActivityMeta(log.action).label }}</p>
                <span class="text-xs text-outline whitespace-nowrap flex-shrink-0">{{ formatDateTime(log.created_at) }}</span>
              </div>
              <p v-if="log.entity_type" class="text-xs text-outline mt-0.5">{{ log.entity_type }}</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Right: Quick Actions + AI card -->
      <section class="lg:col-span-5 flex flex-col gap-4">
        <h2 class="text-lg font-bold text-on-surface px-1">Truy cập nhanh</h2>
        <div class="grid grid-cols-2 gap-3">
          <button
            v-for="action in quickActions"
            :key="action.path"
            @click="router.push(action.path)"
            class="bg-card hover:bg-primary p-5 rounded-xl flex flex-col items-center justify-center text-center group transition-all duration-300 border border-outline-variant shadow-sm"
          >
            <svg class="w-7 h-7 mb-2 text-primary group-hover:text-white transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="action.icon" />
            </svg>
            <span class="text-sm font-semibold text-on-surface group-hover:text-white transition-colors">{{ action.label }}</span>
          </button>
        </div>

        <!-- AI highlight card -->
        <div class="relative overflow-hidden bg-gradient-to-br from-primary to-primary-container rounded-2xl p-6 text-white flex-1">
          <div class="relative z-10 h-full flex flex-col">
            <div class="flex items-center gap-2 mb-3">
              <svg class="w-4 h-4 text-tertiary-fixed" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <span class="text-xs font-bold tracking-widest uppercase text-tertiary-fixed">Gợi ý thông minh</span>
            </div>
            <h3 class="text-lg font-bold mb-2 leading-tight">Nhận gợi ý thuốc từ AI</h3>
            <p class="text-sm text-primary-fixed-dim mb-4 leading-relaxed flex-1">
              Nhập triệu chứng và nhận gợi ý thuốc phù hợp. Kết nối với hồ sơ sức khỏe cá nhân của bạn.
            </p>
            <button
              @click="router.push('/recommendations')"
              class="w-full py-3 bg-white text-primary rounded-xl font-bold text-sm hover:bg-primary-fixed transition-colors"
            >
              Thử gợi ý AI ngay
            </button>
          </div>
          <div class="absolute -right-8 -bottom-8 w-32 h-32 rounded-full bg-white/10" />
          <div class="absolute -right-4 -top-4 w-20 h-20 rounded-full bg-white/5" />
        </div>
      </section>
    </div>

    <!-- Recent prescriptions -->
    <div class="bg-card rounded-2xl border border-outline-variant p-5">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-base font-semibold text-on-surface">Đơn thuốc gần đây</h2>
        <button class="text-sm font-semibold text-primary hover:underline" @click="router.push('/profile/prescriptions')">
          Xem tất cả →
        </button>
      </div>
      <div v-if="loadingRx" class="space-y-2">
        <AppSkeleton v-for="i in 3" :key="i" class="h-14 rounded-xl" />
      </div>
      <div v-else-if="!prescriptions?.items.length" class="text-center py-8">
        <p class="text-sm text-outline">Chưa có đơn thuốc nào</p>
        <button class="mt-2 text-sm text-primary hover:underline" @click="router.push('/profile/prescriptions')">
          Tạo đơn thuốc đầu tiên
        </button>
      </div>
      <div v-else class="space-y-1">
        <div
          v-for="rx in prescriptions.items"
          :key="rx.id"
          class="flex items-center justify-between py-3 px-3 hover:bg-surface-container-low rounded-xl cursor-pointer transition-colors"
          @click="router.push(`/profile/prescriptions/${rx.id}`)"
        >
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 bg-primary-fixed rounded-xl flex items-center justify-center flex-shrink-0">
              <svg class="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <p class="text-sm font-medium text-on-surface">{{ rx.name }}</p>
              <p class="text-xs text-outline">{{ rx.items?.length ?? 0 }} thuốc · {{ formatDateTime(rx.created_at) }}</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <span :class="[
              'text-xs px-2 py-0.5 rounded-full font-medium',
              rx.status === 'active' ? 'bg-primary-fixed text-primary' : 'bg-surface-container text-outline'
            ]">
              {{ rx.status === 'active' ? 'Đang dùng' : 'Hoàn thành' }}
            </span>
            <svg class="w-4 h-4 text-outline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- Admin system link -->
    <div v-if="isAdmin" class="bg-secondary-container/30 border border-secondary-container rounded-2xl p-4 flex items-center justify-between">
      <div>
        <p class="text-sm font-semibold text-on-surface">Quản lý hệ thống</p>
        <p class="text-xs text-outline mt-0.5">Truy cập admin dashboard để quản lý toàn bộ hệ thống</p>
      </div>
      <button
        @click="router.push('/admin/users')"
        class="text-sm font-semibold text-primary hover:text-primary-dk flex items-center gap-1 whitespace-nowrap"
      >
        Admin →
      </button>
    </div>
  </div>
</template>
