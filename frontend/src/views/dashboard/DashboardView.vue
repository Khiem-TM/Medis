<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminStats } from '@/api/admin.api'
import { usePrescriptions } from '@/api/prescriptions.api'
import { useActivityLogs } from '@/api/activity.api'
import { useAuthStore } from '@/stores/auth.store'
import { formatDateTime } from '@/utils/format'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'

const router = useRouter()
const authStore = useAuthStore()

// Admin stats (only for admin users)
const { data: stats, isLoading: loadingStats } = useAdminStats()

// Recent prescriptions
const prescriptionParams = ref({ page: 1, size: 5 })
const { data: prescriptions, isLoading: loadingRx } = usePrescriptions(computed(() => prescriptionParams.value))

// Recent activity
const activityParams = ref({ page: 1, size: 8 })
const { data: activityData, isLoading: loadingActivity } = useActivityLogs(computed(() => activityParams.value))

const isAdmin = computed(() => authStore.isAdmin)
const userName = computed(() => authStore.user?.full_name || authStore.user?.username || 'Bạn')

const quickActions = [
  { label: 'Kiểm tra tương tác thuốc', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2', path: '/interactions', color: 'bg-red-50 text-red-600 hover:bg-red-100' },
  { label: 'Tra cứu thuốc', icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z', path: '/drugs', color: 'bg-blue-50 text-blue-600 hover:bg-blue-100' },
  { label: 'Chatbot AI', icon: 'M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z', path: '/chatbot', color: 'bg-purple-50 text-purple-600 hover:bg-purple-100' },
  { label: 'Đơn thuốc của tôi', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z', path: '/profile/prescriptions', color: 'bg-[#D1FAE5] text-[#065F46] hover:bg-[#A7F3D0]' },
]
</script>

<template>
  <div class="space-y-6">
    <!-- Welcome -->
    <div>
      <h1 class="text-2xl font-bold text-[#111827]">Xin chào, {{ userName }} 👋</h1>
      <p class="text-sm text-[#6B7280] mt-0.5">Đây là tổng quan sức khỏe của bạn hôm nay</p>
    </div>

    <!-- Admin Stats (admin only) -->
    <template v-if="isAdmin">
      <div v-if="loadingStats" class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <AppSkeleton v-for="i in 8" :key="i" class="h-24 rounded-2xl" />
      </div>
      <div v-else-if="stats" class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="bg-white rounded-2xl border border-[#E5E7EB] p-4">
          <p class="text-xs text-[#6B7280] font-medium uppercase tracking-wide">Tổng người dùng</p>
          <p class="text-3xl font-bold text-[#111827] mt-1">{{ stats.total_users.toLocaleString() }}</p>
          <p class="text-xs text-[#10B981] mt-1">+{{ stats.new_users_today }} hôm nay</p>
        </div>
        <div class="bg-white rounded-2xl border border-[#E5E7EB] p-4">
          <p class="text-xs text-[#6B7280] font-medium uppercase tracking-wide">Đang hoạt động</p>
          <p class="text-3xl font-bold text-[#111827] mt-1">{{ stats.active_users.toLocaleString() }}</p>
          <p class="text-xs text-[#6B7280] mt-1">người dùng</p>
        </div>
        <div class="bg-white rounded-2xl border border-[#E5E7EB] p-4">
          <p class="text-xs text-[#6B7280] font-medium uppercase tracking-wide">Thuốc</p>
          <p class="text-3xl font-bold text-[#111827] mt-1">{{ stats.total_drugs.toLocaleString() }}</p>
          <p class="text-xs text-[#6B7280] mt-1">trong danh mục</p>
        </div>
        <div class="bg-white rounded-2xl border border-[#E5E7EB] p-4">
          <p class="text-xs text-[#6B7280] font-medium uppercase tracking-wide">Tương tác thuốc</p>
          <p class="text-3xl font-bold text-[#111827] mt-1">{{ stats.total_interactions.toLocaleString() }}</p>
          <p class="text-xs text-[#6B7280] mt-1">cặp đã biết</p>
        </div>
        <div class="bg-white rounded-2xl border border-[#E5E7EB] p-4">
          <p class="text-xs text-[#6B7280] font-medium uppercase tracking-wide">Đơn thuốc</p>
          <p class="text-3xl font-bold text-[#111827] mt-1">{{ stats.total_prescriptions.toLocaleString() }}</p>
          <p class="text-xs text-[#6B7280] mt-1">đã tạo</p>
        </div>
        <div class="bg-white rounded-2xl border border-[#E5E7EB] p-4">
          <p class="text-xs text-[#6B7280] font-medium uppercase tracking-wide">Hồ sơ khám</p>
          <p class="text-3xl font-bold text-[#111827] mt-1">{{ stats.total_health_profiles.toLocaleString() }}</p>
          <p class="text-xs text-[#6B7280] mt-1">đã lưu</p>
        </div>
        <div class="bg-white rounded-2xl border border-[#E5E7EB] p-4">
          <p class="text-xs text-[#6B7280] font-medium uppercase tracking-wide">Tin nhắn AI</p>
          <p class="text-3xl font-bold text-[#111827] mt-1">{{ stats.total_chat_messages.toLocaleString() }}</p>
          <p class="text-xs text-[#6B7280] mt-1">câu hỏi</p>
        </div>
        <div class="bg-white rounded-2xl border border-[#E5E7EB] p-4 flex items-center justify-center cursor-pointer hover:bg-[#F9FAFB]" @click="router.push('/admin/users')">
          <div class="text-center">
            <p class="text-sm font-medium text-[#10B981]">Quản lý hệ thống</p>
            <p class="text-xs text-[#6B7280] mt-0.5">Admin dashboard →</p>
          </div>
        </div>
      </div>
    </template>

    <!-- Quick actions -->
    <div>
      <h2 class="text-base font-semibold text-[#111827] mb-3">Truy cập nhanh</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <button
          v-for="action in quickActions"
          :key="action.path"
          @click="router.push(action.path)"
          :class="['rounded-2xl p-4 text-left transition-colors', action.color]"
        >
          <svg class="w-6 h-6 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="action.icon" />
          </svg>
          <p class="text-sm font-medium">{{ action.label }}</p>
        </button>
      </div>
    </div>

    <!-- Two columns: recent prescriptions + activity -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Recent prescriptions -->
      <div class="bg-white rounded-2xl border border-[#E5E7EB] p-5">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-base font-semibold text-[#111827]">Đơn thuốc gần đây</h2>
          <button class="text-xs text-[#10B981] hover:underline" @click="router.push('/profile/prescriptions')">Xem tất cả →</button>
        </div>

        <div v-if="loadingRx" class="space-y-3">
          <AppSkeleton v-for="i in 4" :key="i" class="h-12" />
        </div>
        <div v-else-if="!prescriptions?.items.length" class="text-center py-8">
          <p class="text-sm text-[#9CA3AF]">Chưa có đơn thuốc nào</p>
          <button class="mt-2 text-sm text-[#10B981] hover:underline" @click="router.push('/profile/prescriptions')">Tạo đơn thuốc đầu tiên</button>
        </div>
        <div v-else class="space-y-2">
          <div
            v-for="rx in prescriptions.items"
            :key="rx.id"
            class="flex items-center justify-between py-2 px-3 rounded-xl hover:bg-[#F9FAFB] cursor-pointer transition-colors"
            @click="router.push(`/profile/prescriptions/${rx.id}`)"
          >
            <div>
              <p class="text-sm font-medium text-[#111827]">{{ rx.name }}</p>
              <p class="text-xs text-[#9CA3AF]">{{ rx.items?.length ?? 0 }} thuốc · {{ formatDateTime(rx.created_at) }}</p>
            </div>
            <svg class="w-4 h-4 text-[#9CA3AF]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </div>
      </div>

      <!-- Recent activity -->
      <div class="bg-white rounded-2xl border border-[#E5E7EB] p-5">
        <h2 class="text-base font-semibold text-[#111827] mb-4">Hoạt động gần đây</h2>

        <div v-if="loadingActivity" class="space-y-3">
          <AppSkeleton v-for="i in 5" :key="i" class="h-10" />
        </div>
        <div v-else-if="!activityData?.items.length" class="text-center py-8">
          <p class="text-sm text-[#9CA3AF]">Chưa có hoạt động nào được ghi nhận</p>
        </div>
        <div v-else class="space-y-2">
          <div
            v-for="log in activityData.items"
            :key="log.id"
            class="flex items-start gap-3 py-1.5"
          >
            <div class="w-2 h-2 rounded-full bg-[#10B981] mt-1.5 flex-shrink-0" />
            <div class="flex-1 min-w-0">
              <p class="text-sm text-[#374151] truncate">{{ log.action }}</p>
              <p class="text-xs text-[#9CA3AF]">{{ formatDateTime(log.created_at) }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
