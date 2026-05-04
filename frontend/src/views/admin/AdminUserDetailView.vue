<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAdminUserDetail, useUpdateAdminUserMutation, useToggleUserActiveMutation } from '@/api/admin.api'
import { useToast } from '@/composables/useToast'
import { formatDateTime, formatDate } from '@/utils/format'
import AppButton from '@/components/ui/AppButton.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
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

function getAvatarInitials(name: string | null, username: string) {
  if (name) return name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
  return username.slice(0, 2).toUpperCase()
}
</script>

<template>
  <div class="max-w-3xl mx-auto space-y-5">
    <div class="flex items-center gap-3">
      <AppButton variant="ghost" size="sm" @click="router.back()">
        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Quay lại
      </AppButton>
    </div>

    <div v-if="isLoading" class="bg-card rounded-2xl border border-outline-variant p-6 space-y-4 shadow-sm">
      <AppSkeleton class="h-8 w-64" />
      <AppSkeleton :lines="6" />
    </div>

    <AppAlert v-else-if="error" type="error">Không tìm thấy người dùng</AppAlert>

    <template v-else-if="user">
      <!-- Profile header -->
      <div class="bg-card rounded-2xl border border-outline-variant p-6 shadow-sm">
        <div class="flex items-start justify-between flex-wrap gap-4">
          <div class="flex items-center gap-4">
            <div class="w-16 h-16 rounded-2xl bg-primary-fixed flex items-center justify-center text-2xl font-bold text-primary flex-shrink-0">
              {{ getAvatarInitials(user.full_name, user.username) }}
            </div>
            <div>
              <h1 class="text-xl font-bold text-on-surface">{{ user.full_name || user.username }}</h1>
              <p class="text-sm text-outline mt-0.5">@{{ user.username }}</p>
              <div class="flex flex-wrap items-center gap-2 mt-2">
                <span :class="[
                  'px-2.5 py-0.5 rounded-full text-xs font-bold',
                  user.role === 'admin' ? 'bg-secondary-container text-secondary' : 'bg-surface-container text-outline',
                ]">{{ user.role === 'admin' ? 'Admin' : 'User' }}</span>
                <span :class="[
                  'px-2.5 py-0.5 rounded-full text-xs font-bold',
                  user.is_active ? 'bg-tertiary-fixed text-tertiary' : 'bg-error-container text-error',
                ]">{{ user.is_active ? 'Hoạt động' : 'Đã khóa' }}</span>
                <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-primary-fixed text-primary">{{ user.auth_provider }}</span>
              </div>
            </div>
          </div>
          <div class="flex gap-2">
            <button
              @click="doToggle"
              :disabled="toggling"
              :class="[
                'px-3 py-1.5 text-xs font-medium rounded-lg border transition-colors disabled:opacity-50',
                user.is_active
                  ? 'text-error border-error/30 hover:bg-error hover:text-white'
                  : 'text-tertiary border-tertiary/30 hover:bg-tertiary hover:text-white',
              ]"
            >
              {{ user.is_active ? 'Khóa tài khoản' : 'Mở khóa' }}
            </button>
            <button
              @click="openRoleEdit"
              class="px-3 py-1.5 text-xs font-medium text-primary border border-primary/30 rounded-lg hover:bg-primary hover:text-white transition-colors"
            >
              Đổi vai trò
            </button>
          </div>
        </div>
      </div>

      <!-- Role edit panel -->
      <div v-if="showRoleEdit" class="bg-card rounded-2xl border border-outline-variant p-4 flex items-center gap-3 shadow-sm">
        <p class="text-sm font-medium text-on-surface">Vai trò mới:</p>
        <AppSelect v-model="editRole" :options="roleOptions" class="w-40" />
        <AppButton size="sm" variant="gradient" :loading="updating" @click="saveRole">Lưu</AppButton>
        <AppButton variant="ghost" size="sm" @click="showRoleEdit = false">Hủy</AppButton>
      </div>

      <!-- Info -->
      <div class="bg-card rounded-2xl border border-outline-variant p-6 shadow-sm">
        <h2 class="text-base font-semibold text-on-surface mb-4">Thông tin tài khoản</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
          <div class="bg-surface-container-low rounded-xl p-3">
            <p class="text-xs text-outline mb-0.5">Email</p>
            <p class="font-medium text-on-surface">{{ user.email }}</p>
          </div>
          <div class="bg-surface-container-low rounded-xl p-3">
            <p class="text-xs text-outline mb-0.5">Số điện thoại</p>
            <p class="font-medium text-on-surface">{{ user.phone ?? '—' }}</p>
          </div>
          <div class="bg-surface-container-low rounded-xl p-3">
            <p class="text-xs text-outline mb-0.5">Ngày sinh</p>
            <p class="font-medium text-on-surface">{{ user.date_of_birth ? formatDate(user.date_of_birth) : '—' }}</p>
          </div>
          <div class="bg-surface-container-low rounded-xl p-3">
            <p class="text-xs text-outline mb-0.5">Giới tính</p>
            <p class="font-medium text-on-surface">{{ user.gender ?? '—' }}</p>
          </div>
          <div class="bg-surface-container-low rounded-xl p-3">
            <p class="text-xs text-outline mb-0.5">Nghề nghiệp</p>
            <p class="font-medium text-on-surface">{{ user.occupation ?? '—' }}</p>
          </div>
          <div class="bg-surface-container-low rounded-xl p-3">
            <p class="text-xs text-outline mb-0.5">Địa chỉ</p>
            <p class="font-medium text-on-surface">{{ user.address ?? '—' }}</p>
          </div>
          <div class="bg-surface-container-low rounded-xl p-3">
            <p class="text-xs text-outline mb-0.5">Ngày tạo</p>
            <p class="font-medium text-on-surface">{{ formatDateTime(user.created_at) }}</p>
          </div>
          <div class="bg-surface-container-low rounded-xl p-3">
            <p class="text-xs text-outline mb-0.5">Cập nhật</p>
            <p class="font-medium text-on-surface">{{ formatDateTime(user.updated_at) }}</p>
          </div>
        </div>
      </div>

      <!-- Stats -->
      <div v-if="user.stats" class="grid grid-cols-3 gap-4">
        <div class="bg-card rounded-2xl border border-outline-variant p-5 text-center shadow-sm">
          <p class="text-2xl font-bold text-on-surface">{{ user.stats.prescription_count }}</p>
          <p class="text-xs text-outline mt-1">Đơn thuốc</p>
        </div>
        <div class="bg-card rounded-2xl border border-outline-variant p-5 text-center shadow-sm">
          <p class="text-2xl font-bold text-on-surface">{{ user.stats.health_profile_count }}</p>
          <p class="text-xs text-outline mt-1">Hồ sơ khám</p>
        </div>
        <div class="bg-card rounded-2xl border border-outline-variant p-5 text-center shadow-sm">
          <p class="text-2xl font-bold text-on-surface">{{ user.stats.activity_log_count }}</p>
          <p class="text-xs text-outline mt-1">Hoạt động</p>
        </div>
      </div>
    </template>
  </div>
</template>
