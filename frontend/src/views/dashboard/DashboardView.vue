<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminStats } from '@/api/admin.api'
import { usePrescriptions } from '@/api/prescriptions.api'
import { useActivityLogs } from '@/api/activity.api'
import { useIntakeStats } from '@/api/intakes.api'
import { useAuthStore } from '@/stores/auth.store'
import { formatDateTime } from '@/utils/format'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import type { ActivityAction } from '@/types/activity.types'

const router = useRouter()
const authStore = useAuthStore()
const isAdmin = computed(() => authStore.isAdmin)

const { data: stats } = useAdminStats(isAdmin)
const prescriptionParams = ref({ page: 1, size: 5 })
const { data: prescriptions, isLoading: loadingRx } = usePrescriptions(computed(() => prescriptionParams.value))
const { data: weekStats, isLoading: loadingWeekStats } = useIntakeStats(ref('week'))
const { data: monthStats, isLoading: loadingMonthStats } = useIntakeStats(ref('month'))
const activityParams = ref({ page: 1, size: 5 })
const { data: activityData, isLoading: loadingActivity } = useActivityLogs(computed(() => activityParams.value))

const userName = computed(() => authStore.user?.full_name || authStore.user?.username || 'Bạn')
const activeCount = computed(() => prescriptions.value?.items.filter((r) => r.status === 'active').length ?? 0)
const totalCount = computed(() => prescriptions.value?.meta.total ?? 0)
const ringPct = computed(() => (totalCount.value > 0 ? activeCount.value / totalCount.value : 0))

const quickActions = [
  {
    label: 'Hỏi AI',
    sub: 'Tư vấn về triệu chứng & thuốc',
    icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
    path: '/chatbot',
    iconBg: '#F8D8FF',
    iconColor: '#8A30B0',
  },
  {
    label: 'Thêm đơn thuốc',
    sub: 'Nhập thủ công hoặc ảnh đơn',
    icon: 'M12 4v16m8-8H4',
    path: '/profile/prescriptions',
    iconBg: '#8DF5E4',
    iconColor: '#00685D',
  },
  {
    label: 'Tra cứu tương tác',
    sub: 'Kiểm tra 2–20 thuốc',
    icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
    path: '/interactions',
    iconBg: '#DEE0FF',
    iconColor: '#4555B7',
  },
  {
    label: 'Tra cứu thuốc',
    sub: 'Tìm theo tên / hoạt chất',
    icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
    path: '/drugs',
    iconBg: '#F3F3F3',
    iconColor: '#1A1C1C',
  },
]

type ActivityMeta = { icon: string; color: string; bg: string; label: string }

function getActivityMeta(action: ActivityAction): ActivityMeta {
  const map: Record<ActivityAction, ActivityMeta> = {
    LOGIN: { icon: 'M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1', color: 'text-primary', bg: 'bg-primary-fixed', label: 'Đăng nhập' },
    LOGOUT: { icon: 'M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1', color: 'text-outline', bg: 'bg-surface-container', label: 'Đăng xuất' },
    REGISTER: { icon: 'M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z', color: 'text-tertiary', bg: 'bg-tertiary-fixed', label: 'Đăng ký tài khoản' },
    DRUG_SEARCH: { icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z', color: 'text-secondary', bg: 'bg-secondary-container', label: 'Tra cứu thuốc' },
    INTERACTION_CHECK: { icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z', color: 'text-error', bg: 'bg-error-container', label: 'Kiểm tra tương tác thuốc' },
    PRESCRIPTION_CREATE: { icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z', color: 'text-primary', bg: 'bg-primary-fixed', label: 'Tạo đơn thuốc mới' },
    PRESCRIPTION_UPDATE: { icon: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z', color: 'text-primary', bg: 'bg-primary-fixed', label: 'Cập nhật đơn thuốc' },
    PRESCRIPTION_DELETE: { icon: 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16', color: 'text-error', bg: 'bg-error-container', label: 'Xóa đơn thuốc' },
    PRESCRIPTION_VIEW: { icon: 'M15 12a3 3 0 11-6 0 3 3 0 016 0zM2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z', color: 'text-outline', bg: 'bg-surface-container', label: 'Xem đơn thuốc' },
    HEALTH_PROFILE_CREATE: { icon: 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z', color: 'text-tertiary', bg: 'bg-tertiary-fixed', label: 'Tạo hồ sơ sức khỏe' },
    HEALTH_PROFILE_UPDATE: { icon: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z', color: 'text-tertiary', bg: 'bg-tertiary-fixed', label: 'Cập nhật hồ sơ sức khỏe' },
    HEALTH_PROFILE_DELETE: { icon: 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16', color: 'text-error', bg: 'bg-error-container', label: 'Xóa hồ sơ sức khỏe' },
    HEALTH_PROFILE_VIEW: { icon: 'M15 12a3 3 0 11-6 0 3 3 0 016 0zM2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z', color: 'text-outline', bg: 'bg-surface-container', label: 'Xem hồ sơ sức khỏe' },
    CHATBOT_MESSAGE: { icon: 'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z', color: 'text-secondary', bg: 'bg-secondary-container', label: 'Hỏi chatbot AI' },
    PROFILE_UPDATE: { icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z', color: 'text-primary', bg: 'bg-primary-fixed', label: 'Cập nhật thông tin cá nhân' },
    PASSWORD_CHANGE: { icon: 'M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z', color: 'text-outline', bg: 'bg-surface-container', label: 'Đổi mật khẩu' },
  }
  return map[action] ?? { icon: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z', color: 'text-outline', bg: 'bg-surface-container', label: action }
}
</script>

<template>
  <div class="flex flex-col gap-8">

    <!-- Hero row: gradient card + ring stats -->
    <div class="grid grid-cols-1 lg:grid-cols-[1fr_260px] gap-8">

      <!-- Hero gradient card -->
      <div
        class="glass-panel-strong relative overflow-hidden rounded-[2rem] p-6 flex flex-col justify-between min-h-[220px]"
        style="background: linear-gradient(135deg, rgba(0,104,93,0.96) 0%, rgba(69,85,183,0.88) 55%, rgba(138,48,176,0.86) 100%);"
      >
        <div class="absolute -top-10 -right-10 w-44 h-44 rounded-full pointer-events-none" style="background: rgba(255,255,255,0.04);"></div>
        <div class="absolute bottom-4 left-1/3 w-32 h-32 rounded-full pointer-events-none" style="background: rgba(255,255,255,0.03);"></div>

        <div class="relative z-10">
          <div class="flex items-center gap-2 mb-4">
            <span class="w-2 h-2 rounded-full animate-pulse" style="background: #4ADE80;"></span>
            <span class="text-xs font-bold tracking-widest uppercase" style="color: rgba(255,255,255,0.65);">TỔNG QUAN · OVERVIEW</span>
          </div>
          <h1 class="text-2xl font-bold text-white mb-1 tracking-tight">Xin chào, {{ userName }} 👋</h1>
          <p class="text-sm mb-5" style="color: rgba(255,255,255,0.58);">Đây là tổng quan sức khỏe của bạn hôm nay</p>

          <div class="flex flex-wrap gap-2">
            <button
              @click="router.push('/chatbot')"
              class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold text-white transition-opacity hover:opacity-90"
              style="background: rgba(255,255,255,0.15);"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              Hỏi AI
            </button>
            <button
              @click="router.push('/drugs')"
              class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-opacity hover:opacity-90"
              style="background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.75);"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Tra cứu thuốc
            </button>
          </div>
        </div>

        <!-- Stats bar at bottom -->
        <div
          class="relative z-10 mt-5 flex gap-6 pt-4"
          style="border-top: 1px solid rgba(255,255,255,0.12);"
        >
          <template v-if="isAdmin && stats">
            <div>
              <div class="text-xl font-bold text-white tabular-nums">{{ stats.total_users.toLocaleString() }}</div>
              <div class="text-xs" style="color: rgba(255,255,255,0.50);">Người dùng</div>
            </div>
            <div>
              <div class="text-xl font-bold text-white tabular-nums">{{ stats.total_drugs.toLocaleString() }}</div>
              <div class="text-xs" style="color: rgba(255,255,255,0.50);">Thuốc</div>
            </div>
            <div>
              <div class="text-xl font-bold text-white tabular-nums">{{ stats.total_interactions.toLocaleString() }}</div>
              <div class="text-xs" style="color: rgba(255,255,255,0.50);">Tương tác</div>
            </div>
            <div>
              <div class="text-xl font-bold text-white tabular-nums">{{ stats.total_chat_messages.toLocaleString() }}</div>
              <div class="text-xs" style="color: rgba(255,255,255,0.50);">Tin nhắn AI</div>
            </div>
          </template>
          <template v-else>
            <div>
              <div class="text-xl font-bold text-white tabular-nums">{{ totalCount }}</div>
              <div class="text-xs" style="color: rgba(255,255,255,0.50);">Đơn thuốc</div>
            </div>
            <div>
              <div class="text-xl font-bold text-white tabular-nums">{{ activeCount }}</div>
              <div class="text-xs" style="color: rgba(255,255,255,0.50);">Đang dùng</div>
            </div>
          </template>
        </div>
      </div>

      <!-- Circular stats card -->
      <div
        class="bg-white rounded-2xl p-5 flex flex-col"
        style="border: 1px solid rgba(12,29,66,0.08); box-shadow: 0 1px 2px rgba(12,29,66,.04);"
      >
        <div class="flex items-center justify-between mb-1">
          <div class="text-xs font-bold tracking-widest uppercase" style="color: #8A95AC;">Hôm nay</div>
        </div>

        <div class="flex items-center justify-center flex-1 py-2">
          <div class="relative" style="width: 110px; height: 110px;">
            <svg viewBox="0 0 120 120" class="w-full h-full" style="transform: rotate(-90deg);">
              <circle cx="60" cy="60" r="50" fill="none" stroke="rgba(12,29,66,0.07)" stroke-width="10" />
              <circle
                cx="60" cy="60" r="50"
                fill="none" stroke="#2563EB" stroke-width="10"
                stroke-linecap="round"
                :stroke-dasharray="`${ringPct * 314} 314`"
              />
            </svg>
            <div class="absolute inset-0 flex flex-col items-center justify-center">
              <div class="text-2xl font-bold tracking-tight" style="color: #0C1D42;">
                {{ loadingRx ? '—' : activeCount }}
              </div>
              <div class="text-xs" style="color: #8A95AC;">đang dùng</div>
            </div>
          </div>
        </div>

        <div class="space-y-2.5 mt-2">
          <div class="flex items-center gap-2 text-xs">
            <span class="flex-1 truncate" style="color: #5A6985;">Tuân thủ tuần này</span>
            <div class="w-16 h-1.5 rounded-full overflow-hidden flex-shrink-0" style="background: rgba(12,29,66,0.08);">
              <div
                class="h-full rounded-full"
                :style="`width: ${weekStats ? Math.round(weekStats.adherence_rate * 100) : 0}%; background: #2563EB;`"
              ></div>
            </div>
            <b class="w-7 text-right font-bold tabular-nums" style="color: #0C1D42;">
              {{ loadingWeekStats ? '—' : (weekStats ? Math.round(weekStats.adherence_rate * 100) + '%' : '—') }}
            </b>
          </div>
          <div class="flex items-center gap-2 text-xs">
            <span class="flex-1 truncate" style="color: #5A6985;">Tháng này</span>
            <div class="w-16 h-1.5 rounded-full overflow-hidden flex-shrink-0" style="background: rgba(12,29,66,0.08);">
              <div
                class="h-full rounded-full"
                :style="`width: ${monthStats ? Math.round(monthStats.adherence_rate * 100) : 0}%; background: #10B981;`"
              ></div>
            </div>
            <b class="w-7 text-right font-bold tabular-nums" style="color: #0C1D42;">
              {{ loadingMonthStats ? '—' : (monthStats ? Math.round(monthStats.adherence_rate * 100) + '%' : '—') }}
            </b>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick action tiles -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-5">
      <button
        v-for="action in quickActions"
        :key="action.path"
        @click="router.push(action.path)"
        class="flex items-center gap-3 px-4 py-4 rounded-2xl text-left transition-all duration-150 group hover:-translate-y-0.5"
        style="background: white; border: 1px solid rgba(12,29,66,0.08); box-shadow: 0 1px 2px rgba(12,29,66,.04);"
        @mouseenter="($event.currentTarget as HTMLElement).style.boxShadow = '0 1px 2px rgba(12,29,66,.04), 0 8px 24px -8px rgba(12,29,66,.10)'"
        @mouseleave="($event.currentTarget as HTMLElement).style.boxShadow = '0 1px 2px rgba(12,29,66,.04)'"
      >
        <span
          class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
          :style="`background: ${action.iconBg};`"
        >
          <svg class="w-5 h-5" :style="`color: ${action.iconColor};`" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" :d="action.icon" />
          </svg>
        </span>
        <span class="flex-1 min-w-0">
          <b class="block text-sm font-bold truncate tracking-tight" style="color: #0C1D42;">{{ action.label }}</b>
          <em class="block text-xs not-italic truncate mt-0.5" style="color: #8A95AC;">{{ action.sub }}</em>
        </span>
        <svg class="w-4 h-4 flex-shrink-0 transition-transform group-hover:translate-x-0.5" style="color: #C8D0DC;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </div>

    <!-- Main grid -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">

      <!-- Recent prescriptions (7 cols) -->
      <section
        class="lg:col-span-7 bg-white rounded-2xl"
        style="border: 1px solid rgba(12,29,66,0.08); box-shadow: 0 1px 2px rgba(12,29,66,.04);"
      >
        <div class="flex items-center justify-between px-6 py-4" style="border-bottom: 1px solid rgba(12,29,66,0.06);">
          <div>
            <div class="text-xs font-bold tracking-widest uppercase mb-0.5" style="color: #8A95AC;">Đơn thuốc · Prescriptions</div>
            <h2 class="text-base font-bold tracking-tight" style="color: #0C1D42;">Đơn thuốc gần đây</h2>
          </div>
          <button class="text-sm font-semibold hover:underline" style="color: #2563EB;" @click="router.push('/profile/prescriptions')">
            Xem tất cả →
          </button>
        </div>

        <div class="p-4">
          <div v-if="loadingRx" class="space-y-2">
            <AppSkeleton v-for="i in 3" :key="i" class="h-14 rounded-xl" />
          </div>
          <div v-else-if="!prescriptions?.items.length" class="text-center py-10">
            <div class="w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-3" style="background: #EFF3F8;">
              <svg class="w-6 h-6" style="color: #B5BCCB;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <p class="text-sm font-semibold" style="color: #0C1D42;">Chưa có đơn thuốc nào</p>
            <p class="text-xs mt-1 mb-3" style="color: #8A95AC;">Tạo đơn thuốc đầu tiên để bắt đầu theo dõi</p>
            <button class="text-sm font-semibold" style="color: #2563EB;" @click="router.push('/profile/prescriptions')">
              Tạo đơn thuốc →
            </button>
          </div>
          <div v-else class="space-y-0.5">
            <div
              v-for="rx in prescriptions.items"
              :key="rx.id"
              class="flex items-center gap-3 px-3 py-3 rounded-xl cursor-pointer transition-colors hover:bg-[#F8FAFB]"
              @click="router.push(`/profile/prescriptions/${rx.id}`)"
            >
              <div class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style="background: #DCEDFF;">
                <svg class="w-4 h-4" style="color: #2563EB;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold truncate tracking-tight" style="color: #0C1D42;">{{ rx.name }}</p>
                <p class="text-xs mt-0.5" style="color: #8A95AC;">{{ rx.items?.length ?? 0 }} thuốc · {{ formatDateTime(rx.created_at) }}</p>
              </div>
              <div class="flex items-center gap-2 flex-shrink-0">
                <span
                  class="text-xs px-2.5 py-1 rounded-full font-semibold"
                  :style="rx.status === 'active' ? 'background: #DCEDFF; color: #1D4FD8;' : 'background: #F3F5F7; color: #8A95AC;'"
                >{{ rx.status === 'active' ? 'Đang dùng' : 'Hoàn thành' }}</span>
                <svg class="w-4 h-4" style="color: #C8D0DC;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Right column (5 cols) -->
      <section class="lg:col-span-5 flex flex-col gap-6">

        <!-- AI highlight card -->
        <div
          class="relative overflow-hidden rounded-2xl p-5"
          style="background: linear-gradient(135deg, #2563EB, #1D4FD8);"
        >
          <div class="absolute -right-6 -bottom-6 w-28 h-28 rounded-full pointer-events-none" style="background: rgba(255,255,255,0.08);"></div>
          <div class="absolute -right-2 -top-2 w-16 h-16 rounded-full pointer-events-none" style="background: rgba(255,255,255,0.05);"></div>
          <div class="relative z-10">
            <div class="flex items-center gap-2 mb-2">
              <svg class="w-4 h-4" style="color: #86EFAC;" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              <span class="text-xs font-bold tracking-widest uppercase" style="color: rgba(255,255,255,0.70);">GỢI Ý THÔNG MINH</span>
            </div>
            <h3 class="text-lg font-bold text-white mb-1 tracking-tight leading-snug">Nhận gợi ý thuốc từ AI</h3>
            <p class="text-sm mb-4 leading-relaxed" style="color: rgba(255,255,255,0.68);">
              Nhập triệu chứng và nhận gợi ý thuốc phù hợp với hồ sơ sức khỏe của bạn.
            </p>
            <button
              @click="router.push('/recommendations')"
              class="w-full py-2.5 rounded-xl text-sm font-bold text-white transition-colors"
              style="background: rgba(255,255,255,0.15);"
              @mouseenter="($event.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.22)'"
              @mouseleave="($event.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.15)'"
            >
              Thử gợi ý AI ngay →
            </button>
          </div>
        </div>

        <!-- Update Profile Card -->
        <div
          class="bg-white rounded-2xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
          style="border: 1px solid rgba(12,29,66,0.08); box-shadow: 0 1px 2px rgba(12,29,66,.04);"
        >
          <div>
            <div class="flex items-center gap-2 mb-1">
              <div class="w-8 h-8 rounded-lg bg-primary-fixed flex items-center justify-center">
                <svg class="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <span class="text-sm font-bold tracking-tight" style="color: #0C1D42;">Hồ sơ sức khỏe</span>
            </div>
            <p class="text-xs ml-10" style="color: #8A95AC;">Cập nhật thông tin bệnh nền, dị ứng để AI tư vấn chính xác hơn.</p>
          </div>
          <button 
            @click="router.push('/onboarding?update=true')"
            class="whitespace-nowrap w-full sm:w-auto text-sm font-semibold px-4 py-2.5 rounded-xl bg-[#F0FAF9] text-[#00897B] border border-[#00897B]/20 hover:bg-[#E0F5F3] transition-colors"
          >
            Cập nhật ngay
          </button>
        </div>

        <!-- Recent activity -->
        <div
          class="bg-white rounded-2xl flex-1"
          style="border: 1px solid rgba(12,29,66,0.08); box-shadow: 0 1px 2px rgba(12,29,66,.04);"
        >
          <div class="px-5 py-4" style="border-bottom: 1px solid rgba(12,29,66,0.06);">
            <h2 class="text-sm font-bold tracking-tight" style="color: #0C1D42;">Hoạt động gần đây</h2>
          </div>
          <div class="p-3">
            <div v-if="loadingActivity" class="space-y-2">
              <AppSkeleton v-for="i in 4" :key="i" class="h-11 rounded-xl" />
            </div>
            <div v-else-if="!activityData?.items.length" class="text-center py-8">
              <p class="text-sm" style="color: #8A95AC;">Chưa có hoạt động nào</p>
            </div>
            <div v-else class="space-y-0.5">
              <div
                v-for="log in activityData.items"
                :key="log.id"
                class="flex items-center gap-3 p-2.5 rounded-xl transition-colors hover:bg-[#F8FAFB]"
              >
                <div :class="['w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0', getActivityMeta(log.action).bg]">
                  <svg :class="['w-4 h-4', getActivityMeta(log.action).color]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" :d="getActivityMeta(log.action).icon" />
                  </svg>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-xs font-semibold truncate" style="color: #0C1D42;">{{ getActivityMeta(log.action).label }}</p>
                  <p class="text-xs" style="color: #8A95AC;">{{ formatDateTime(log.created_at) }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Admin link -->
        <div
          v-if="isAdmin"
          class="rounded-2xl p-4 flex items-center justify-between"
          style="background: #F8FAFB; border: 1px solid rgba(12,29,66,0.08);"
        >
          <div>
            <p class="text-sm font-semibold tracking-tight" style="color: #0C1D42;">Quản lý hệ thống</p>
            <p class="text-xs mt-0.5" style="color: #8A95AC;">Truy cập admin dashboard</p>
          </div>
          <button class="text-sm font-semibold flex items-center gap-1 whitespace-nowrap" style="color: #2563EB;" @click="router.push('/admin/users')">
            Admin →
          </button>
        </div>
      </section>
    </div>
  </div>
</template>
