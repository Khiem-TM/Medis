<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAdminUserDetail, useUpdateAdminUserMutation, useToggleUserActiveMutation } from '@/api/admin.api'
import { useToast } from '@/composables/useToast'
import { formatDateTime, formatDate } from '@/utils/format'
import AppButton from '@/components/ui/AppButton.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppAlert from '@/components/ui/AppAlert.vue'
import AppSelect from '@/components/ui/AppSelect.vue'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const id = computed(() => route.params.id as string)

const { data: user, isLoading, error } = useAdminUserDetail(id)
const { mutate: updateUser, isPending: updating } = useUpdateAdminUserMutation()
const { mutate: toggleActive, isPending: toggling } = useToggleUserActiveMutation()

const editRole = ref<'user' | 'admin'>('user')
const showRoleEdit = ref(false)

const roleOptions = [
  { label: 'Người dùng', value: 'user' },
  { label: 'Admin', value: 'admin' },
]

function openRoleEdit() {
  editRole.value = user.value?.role ?? 'user'
  showRoleEdit.value = true
}

function saveRole() {
  updateUser({ id: id.value, data: { role: editRole.value } }, {
    onSuccess: () => { toast.success('Đã cập nhật vai trò'); showRoleEdit.value = false },
    onError: () => toast.error('Cập nhật thất bại'),
  })
}

function doToggle() {
  toggleActive(id.value, {
    onSuccess: () => toast.success('Đã cập nhật trạng thái'),
    onError: () => toast.error('Cập nhật thất bại'),
  })
}
</script>

<template>
  <div class="max-w-3xl mx-auto space-y-4">
    <div class="flex items-center gap-3">
      <AppButton variant="ghost" size="sm" @click="router.back()">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Quay lại
      </AppButton>
    </div>

    <div v-if="isLoading" class="bg-white rounded-2xl border border-[#E5E7EB] p-6 space-y-4">
      <AppSkeleton class="h-8 w-64" />
      <AppSkeleton :lines="6" />
    </div>

    <AppAlert v-else-if="error" type="error">Không tìm thấy người dùng</AppAlert>

    <template v-else-if="user">
      <!-- Header -->
      <div class="bg-white rounded-2xl border border-[#E5E7EB] p-6">
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-4">
            <div class="w-16 h-16 rounded-full bg-[#D1FAE5] flex items-center justify-center text-2xl font-bold text-[#065F46]">
              {{ (user.full_name || user.username).charAt(0).toUpperCase() }}
            </div>
            <div>
              <h1 class="text-xl font-bold text-[#111827]">{{ user.full_name || user.username }}</h1>
              <p class="text-sm text-[#6B7280]">@{{ user.username }}</p>
              <div class="flex items-center gap-2 mt-1">
                <AppBadge :variant="user.role === 'admin' ? 'warning' : 'default'">{{ user.role }}</AppBadge>
                <AppBadge :variant="user.is_active ? 'success' : 'danger'">{{ user.is_active ? 'Hoạt động' : 'Đã khóa' }}</AppBadge>
                <AppBadge variant="info">{{ user.auth_provider }}</AppBadge>
              </div>
            </div>
          </div>
          <div class="flex gap-2">
            <AppButton variant="outline" size="sm" :loading="toggling" @click="doToggle">
              {{ user.is_active ? 'Khóa tài khoản' : 'Mở khóa' }}
            </AppButton>
            <AppButton size="sm" @click="openRoleEdit">Đổi vai trò</AppButton>
          </div>
        </div>
      </div>

      <!-- Role edit panel -->
      <div v-if="showRoleEdit" class="bg-white rounded-2xl border border-[#E5E7EB] p-4 flex items-center gap-3">
        <p class="text-sm font-medium text-[#111827]">Vai trò mới:</p>
        <AppSelect v-model="editRole" :options="roleOptions" class="w-40" />
        <AppButton size="sm" :loading="updating" @click="saveRole">Lưu</AppButton>
        <AppButton variant="ghost" size="sm" @click="showRoleEdit = false">Hủy</AppButton>
      </div>

      <!-- Info -->
      <div class="bg-white rounded-2xl border border-[#E5E7EB] p-6">
        <h2 class="text-base font-semibold text-[#111827] mb-4">Thông tin tài khoản</h2>
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div><span class="text-[#6B7280]">Email:</span> <span class="font-medium">{{ user.email }}</span></div>
          <div><span class="text-[#6B7280]">Số điện thoại:</span> <span class="font-medium">{{ user.phone ?? '—' }}</span></div>
          <div><span class="text-[#6B7280]">Ngày sinh:</span> <span class="font-medium">{{ user.date_of_birth ? formatDate(user.date_of_birth) : '—' }}</span></div>
          <div><span class="text-[#6B7280]">Giới tính:</span> <span class="font-medium">{{ user.gender ?? '—' }}</span></div>
          <div><span class="text-[#6B7280]">Nghề nghiệp:</span> <span class="font-medium">{{ user.occupation ?? '—' }}</span></div>
          <div><span class="text-[#6B7280]">Địa chỉ:</span> <span class="font-medium">{{ user.address ?? '—' }}</span></div>
          <div><span class="text-[#6B7280]">Ngày tạo:</span> <span class="font-medium">{{ formatDateTime(user.created_at) }}</span></div>
          <div><span class="text-[#6B7280]">Cập nhật:</span> <span class="font-medium">{{ formatDateTime(user.updated_at) }}</span></div>
        </div>
      </div>

      <!-- Stats -->
      <div v-if="user.stats" class="grid grid-cols-3 gap-4">
        <div class="bg-white rounded-2xl border border-[#E5E7EB] p-4 text-center">
          <p class="text-2xl font-bold text-[#111827]">{{ user.stats.prescription_count }}</p>
          <p class="text-xs text-[#6B7280] mt-1">Đơn thuốc</p>
        </div>
        <div class="bg-white rounded-2xl border border-[#E5E7EB] p-4 text-center">
          <p class="text-2xl font-bold text-[#111827]">{{ user.stats.health_profile_count }}</p>
          <p class="text-xs text-[#6B7280] mt-1">Hồ sơ khám</p>
        </div>
        <div class="bg-white rounded-2xl border border-[#E5E7EB] p-4 text-center">
          <p class="text-2xl font-bold text-[#111827]">{{ user.stats.activity_log_count }}</p>
          <p class="text-xs text-[#6B7280] mt-1">Hoạt động</p>
        </div>
      </div>
    </template>
  </div>
</template>
