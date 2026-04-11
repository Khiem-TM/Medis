<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminUsers, useToggleUserActiveMutation } from '@/api/admin.api'
import { usePagination } from '@/composables/usePagination'
import { useDebounce } from '@/composables/useDebounce'
import { useToast } from '@/composables/useToast'
import { formatDateTime } from '@/utils/format'
import type { AdminUserSearchParams } from '@/types/admin.types'
import AppTable from '@/components/ui/AppTable.vue'
import AppPagination from '@/components/ui/AppPagination.vue'
import AppInput from '@/components/ui/AppInput.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppButton from '@/components/ui/AppButton.vue'

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
const { mutate: toggleActive, isPending: toggling } = useToggleUserActiveMutation()

const columns = [
  { key: 'username', label: 'Tên đăng nhập' },
  { key: 'email', label: 'Email' },
  { key: 'role', label: 'Vai trò', align: 'center' as const },
  { key: 'is_active', label: 'Trạng thái', align: 'center' as const },
  { key: 'created_at', label: 'Ngày tạo' },
  { key: 'actions', label: '', align: 'right' as const },
]

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
</script>

<template>
  <div class="space-y-4">
    <div>
      <h1 class="text-2xl font-bold text-[#111827]">Quản lý người dùng</h1>
      <p class="text-sm text-[#6B7280] mt-1">Xem và quản lý tài khoản người dùng trong hệ thống</p>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-3 bg-white p-3 rounded-xl border border-[#E5E7EB]">
      <div class="flex-1 min-w-48">
        <AppInput v-model="searchInput" placeholder="Tìm username, email...">
          <template #prefix>
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </template>
        </AppInput>
      </div>
      <AppSelect v-model="roleFilter" :options="roleOptions" class="w-40" />
      <AppSelect v-model="activeFilter" :options="activeOptions" class="w-44" />
    </div>

    <!-- Table -->
    <div class="bg-white rounded-2xl border border-[#E5E7EB] overflow-hidden">
      <div class="px-4 py-3 border-b border-[#E5E7EB]">
        <p class="text-sm text-[#6B7280]">
          <template v-if="!isLoading && data">{{ data.meta.total.toLocaleString() }} người dùng</template>
          <template v-else>Đang tải...</template>
        </p>
      </div>

      <AppTable :columns="columns" :data="(data?.items ?? []) as any[]" :loading="isLoading" empty-message="Không tìm thấy người dùng">
        <template #username="{ row }">
          <div>
            <p class="font-medium text-[#111827]">{{ row.username }}</p>
            <p class="text-xs text-[#9CA3AF]">{{ row.full_name ?? '—' }}</p>
          </div>
        </template>
        <template #role="{ row }">
          <AppBadge :variant="row.role === 'admin' ? 'warning' : 'default'">{{ row.role === 'admin' ? 'Admin' : 'User' }}</AppBadge>
        </template>
        <template #is_active="{ row }">
          <AppBadge :variant="row.is_active ? 'success' : 'danger'">{{ row.is_active ? 'Hoạt động' : 'Đã khóa' }}</AppBadge>
        </template>
        <template #created_at="{ row }">
          <span class="text-sm text-[#374151]">{{ formatDateTime(row.created_at) }}</span>
        </template>
        <template #actions="{ row }">
          <div class="flex items-center gap-2 justify-end">
            <AppButton variant="ghost" size="sm" @click="router.push(`/admin/users/${row.id}`)">Chi tiết</AppButton>
            <AppButton variant="outline" size="sm" :loading="toggling" @click="doToggle(row.id)">
              {{ row.is_active ? 'Khóa' : 'Mở khóa' }}
            </AppButton>
          </div>
        </template>
      </AppTable>

      <div v-if="data?.meta" class="px-4 border-t border-[#E5E7EB]">
        <AppPagination :meta="data.meta" :model-value="page" show-size-selector :size="size" @update:model-value="setPage" @update:size="setSize" />
      </div>
    </div>
  </div>
</template>
