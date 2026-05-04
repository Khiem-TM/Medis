<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminUsers, useAdminStats, useToggleUserActiveMutation } from '@/api/admin.api'
import { usePagination } from '@/composables/usePagination'
import { useDebounce } from '@/composables/useDebounce'
import { useToast } from '@/composables/useToast'
import { formatDateTime } from '@/utils/format'
import type { AdminUserSearchParams } from '@/types/admin.types'
import AppPagination from '@/components/ui/AppPagination.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import StatCard from '@/components/ui/StatCard.vue'

const router = useRouter()
const toast = useToast()
const { page, size, params: paginationParams, setPage, setSize } = usePagination(20)
const searchInput = ref('')
const roleFilter = ref<'' | 'user' | 'admin'>('')
const activeFilter = ref<'' | 'true' | 'false'>('')
const debouncedSearch = useDebounce(searchInput, 400)

const queryParams = computed<AdminUserSearchParams>(() => ({
  ...paginationParams.value,
  search: debouncedSearch.value || undefined,
  role: roleFilter.value || undefined,
  is_active: activeFilter.value === '' ? undefined : activeFilter.value === 'true',
}))

const { data, isLoading } = useAdminUsers(queryParams)
const { data: stats, isLoading: loadingStats } = useAdminStats()
const { mutate: toggleActive, isPending: toggling } = useToggleUserActiveMutation()

const roleOptions = [
  { label: 'Tất cả vai trò', value: '' },
  { label: 'Người dùng', value: 'user' },
  { label: 'Admin', value: 'admin' },
]

const activeOptions = [
  { label: 'Tất cả', value: '' },
  { label: 'Đang hoạt động', value: 'true' },
  { label: 'Đã khóa', value: 'false' },
]

function doToggle(id: string) {
  toggleActive(id, {
    onSuccess: () => toast.success('Đã cập nhật trạng thái người dùng'),
    onError: () => toast.error('Không thể cập nhật trạng thái'),
  })
}

function getAvatarInitials(name: string | null, username: string) {
  if (name) return name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
  return username.slice(0, 2).toUpperCase()
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-on-surface">Quản lý người dùng</h1>
      <p class="text-sm text-outline mt-0.5">Xem và quản lý tài khoản người dùng trong hệ thống</p>
    </div>

    <!-- Stats row -->
    <div v-if="loadingStats" class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <AppSkeleton v-for="i in 4" :key="i" class="h-24 rounded-2xl" />
    </div>
    <div v-else-if="stats" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard label="Tổng người dùng" :value="stats.total_users.toLocaleString()" :change="`+${stats.new_users_today} hôm nay`" :changePositive="true">
        <template #icon>
          <svg class="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </template>
      </StatCard>
      <StatCard label="Đang hoạt động" :value="stats.active_users.toLocaleString()" iconColor="bg-tertiary-fixed">
        <template #icon>
          <svg class="w-5 h-5 text-tertiary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </template>
      </StatCard>
      <StatCard label="Đơn thuốc" :value="stats.total_prescriptions.toLocaleString()" iconColor="bg-secondary-container">
        <template #icon>
          <svg class="w-5 h-5 text-secondary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </template>
      </StatCard>
      <StatCard label="Hồ sơ sức khỏe" :value="stats.total_health_profiles.toLocaleString()" iconColor="bg-error-container">
        <template #icon>
          <svg class="w-5 h-5 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
          </svg>
        </template>
      </StatCard>
    </div>

    <!-- Filters + table -->
    <div class="bg-card rounded-2xl border border-outline-variant overflow-hidden shadow-sm">
      <!-- Filter bar -->
      <div class="px-5 py-4 border-b border-outline-variant flex flex-wrap gap-3 bg-card">
        <div class="relative flex-1 min-w-48">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-outline pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            v-model="searchInput"
            type="text"
            placeholder="Tìm username, email..."
            class="w-full pl-9 pr-3 py-2 bg-surface-container-low border border-outline-variant rounded-xl text-sm text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-all"
          />
        </div>
        <select v-model="roleFilter" class="px-3 py-2 bg-surface-container-low border border-outline-variant rounded-xl text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30">
          <option v-for="opt in roleOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
        <select v-model="activeFilter" class="px-3 py-2 bg-surface-container-low border border-outline-variant rounded-xl text-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/30">
          <option v-for="opt in activeOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
        <div class="ml-auto flex items-center gap-2 text-sm text-outline">
          <template v-if="!isLoading && data">{{ data.meta.total.toLocaleString() }} người dùng</template>
        </div>
      </div>

      <!-- Table -->
      <div v-if="isLoading" class="p-5 space-y-3">
        <AppSkeleton v-for="i in 5" :key="i" class="h-14 rounded-xl" />
      </div>
      <div v-else-if="!data?.items.length" class="text-center py-16">
        <p class="text-sm text-outline">Không tìm thấy người dùng</p>
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-surface-container-low border-b border-outline-variant">
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Người dùng</th>
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Email</th>
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider text-center">Vai trò</th>
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider text-center">Trạng thái</th>
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider">Ngày tạo</th>
              <th class="px-5 py-3 text-xs font-bold text-on-surface-variant uppercase tracking-wider text-right">Thao tác</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-outline-variant/50">
            <tr
              v-for="user in data.items"
              :key="user.id"
              class="hover:bg-surface-container-low transition-colors"
            >
              <td class="px-5 py-4">
                <div class="flex items-center gap-3">
                  <div class="w-9 h-9 rounded-xl bg-primary-fixed flex items-center justify-center flex-shrink-0">
                    <span class="text-xs font-bold text-primary">{{ getAvatarInitials(user.full_name, user.username) }}</span>
                  </div>
                  <div>
                    <p class="text-sm font-semibold text-on-surface">{{ user.username }}</p>
                    <p class="text-xs text-outline">{{ user.full_name ?? '—' }}</p>
                  </div>
                </div>
              </td>
              <td class="px-5 py-4 text-sm text-on-surface-variant">{{ user.email }}</td>
              <td class="px-5 py-4 text-center">
                <span :class="[
                  'px-2.5 py-0.5 rounded-full text-xs font-bold',
                  user.role === 'admin' ? 'bg-secondary-container text-secondary' : 'bg-surface-container text-outline'
                ]">
                  {{ user.role === 'admin' ? 'Admin' : 'User' }}
                </span>
              </td>
              <td class="px-5 py-4 text-center">
                <span :class="[
                  'px-2.5 py-0.5 rounded-full text-xs font-bold',
                  user.is_active ? 'bg-tertiary-fixed text-tertiary' : 'bg-error-container text-error'
                ]">
                  {{ user.is_active ? 'Hoạt động' : 'Đã khóa' }}
                </span>
              </td>
              <td class="px-5 py-4 text-sm text-on-surface-variant">{{ formatDateTime(user.created_at) }}</td>
              <td class="px-5 py-4">
                <div class="flex items-center gap-2 justify-end">
                  <button
                    @click="router.push(`/admin/users/${user.id}`)"
                    class="px-3 py-1.5 text-xs font-medium text-primary border border-primary/30 rounded-lg hover:bg-primary hover:text-white transition-colors"
                  >
                    Chi tiết
                  </button>
                  <button
                    @click="doToggle(user.id)"
                    :disabled="toggling"
                    :class="[
                      'px-3 py-1.5 text-xs font-medium rounded-lg transition-colors',
                      user.is_active
                        ? 'text-error border border-error/30 hover:bg-error hover:text-white'
                        : 'text-tertiary border border-tertiary/30 hover:bg-tertiary hover:text-white',
                    ]"
                  >
                    {{ user.is_active ? 'Khóa' : 'Mở khóa' }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div v-if="data?.meta" class="px-5 border-t border-outline-variant">
        <AppPagination :meta="data.meta" :model-value="page" show-size-selector :size="size" @update:model-value="setPage" @update:size="setSize" />
      </div>
    </div>
  </div>
</template>
