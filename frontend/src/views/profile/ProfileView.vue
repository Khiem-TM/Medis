<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { watch } from 'vue'
import { useRouter } from 'vue-router'
import { z } from 'zod'
import { useAuthStore } from '@/stores/auth.store'
import { useCurrentUserQuery, useUpdateProfileMutation, useChangePasswordMutation, useUploadAvatarMutation } from '@/api/users.api'
import { updateProfileSchema, changePasswordSchema } from '@/schemas/profile.schema'
import { useToast } from '@/composables/useToast'
import { useFileUpload } from '@/composables/useFileUpload'
import AppInput from '@/components/ui/AppInput.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppAvatar from '@/components/ui/AppAvatar.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppTabNav from '@/components/ui/AppTabNav.vue'

const router = useRouter()
const authStore = useAuthStore()
const toast = useToast()
const { preview, file, error: uploadError, onFileChange, reset: resetFile } = useFileUpload()
const fileInput = ref<HTMLInputElement | null>(null)
const activeTab = ref('info')

const { data: user, isLoading } = useCurrentUserQuery()
const { mutate: updateProfile, isPending: updatingProfile } = useUpdateProfileMutation()
const { mutate: changePassword, isPending: changingPassword } = useChangePasswordMutation()
const { mutate: uploadAvatar, isPending: uploadingAvatar } = useUploadAvatarMutation()

const profileForm = reactive({
  full_name: '',
  phone: '',
  date_of_birth: '',
  gender: '' as 'male' | 'female' | 'other' | '',
  address: '',
  occupation: '',
})

const profileErrors = reactive<Record<string, string>>({})
const pwForm = reactive({ old_password: '', new_password: '', confirm_password: '' })
const pwErrors = reactive<Record<string, string>>({})

watch(user, (u) => {
  if (!u) return
  profileForm.full_name = u.full_name ?? ''
  profileForm.phone = u.phone ?? ''
  profileForm.date_of_birth = u.date_of_birth ?? ''
  profileForm.gender = (u.gender as 'male' | 'female' | 'other') ?? ''
  profileForm.address = u.address ?? ''
  profileForm.occupation = u.occupation ?? ''
}, { immediate: true })

const tabs = [
  { key: 'info', label: 'Thông tin cơ bản' },
  { key: 'security', label: 'Bảo mật' },
]

const genderOptions = [
  { label: 'Nam', value: 'male' },
  { label: 'Nữ', value: 'female' },
  { label: 'Khác', value: 'other' },
]

const roleLabel = computed(() => user.value?.role === 'admin' ? 'Quản trị viên' : 'Người dùng')
const roleBg = computed(() => user.value?.role === 'admin' ? 'bg-secondary-container text-secondary' : 'bg-primary-fixed text-primary')

function validateProfile() {
  Object.keys(profileErrors).forEach((k) => delete profileErrors[k])
  try {
    updateProfileSchema.parse(profileForm)
    return true
  } catch (e) {
    if (e instanceof z.ZodError) e.issues.forEach((err) => { if (err.path[0]) profileErrors[err.path[0] as string] = err.message })
    return false
  }
}

function saveProfile() {
  if (!validateProfile()) return
  const payload = Object.fromEntries(Object.entries(profileForm).filter(([, v]) => v !== ''))
  updateProfile(payload, {
    onSuccess: () => { toast.success('Cập nhật hồ sơ thành công'); authStore.fetchCurrentUser() },
    onError: (e) => toast.error((e as { message?: string })?.message || 'Cập nhật thất bại'),
  })
}

function validatePw() {
  Object.keys(pwErrors).forEach((k) => delete pwErrors[k])
  try {
    changePasswordSchema.parse(pwForm)
    return true
  } catch (e) {
    if (e instanceof z.ZodError) e.issues.forEach((err) => { if (err.path[0]) pwErrors[err.path[0] as string] = err.message })
    return false
  }
}

function savePw() {
  if (!validatePw()) return
  changePassword({ old_password: pwForm.old_password, new_password: pwForm.new_password }, {
    onSuccess: () => { toast.success('Đổi mật khẩu thành công'); Object.assign(pwForm, { old_password: '', new_password: '', confirm_password: '' }) },
    onError: (e) => toast.error((e as { message?: string })?.message || 'Đổi mật khẩu thất bại'),
  })
}

function triggerFileInput() { fileInput.value?.click() }

function doUpload() {
  if (!file.value) return
  uploadAvatar(file.value, {
    onSuccess: () => { toast.success('Cập nhật ảnh đại diện thành công'); resetFile(); authStore.fetchCurrentUser() },
    onError: () => toast.error('Upload ảnh thất bại'),
  })
}
</script>

<template>
  <div class="max-w-3xl mx-auto space-y-6">
    <!-- Profile header card -->
    <div class="bg-card rounded-2xl border border-outline-variant overflow-hidden shadow-sm">
      <!-- Gradient banner -->
      <div class="h-24 bg-gradient-to-r from-primary-fixed to-surface-container-high relative">
        <div class="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent" />
      </div>
      <!-- Avatar + info -->
      <div class="px-6 pb-6 -mt-12 flex flex-col sm:flex-row sm:items-end gap-4">
        <div class="relative flex-shrink-0">
          <div class="w-20 h-20 rounded-2xl ring-4 ring-card overflow-hidden shadow-lg">
            <AppAvatar :src="preview ?? user?.avatar_url" :name="user?.full_name" size="xl" class="w-full h-full" />
          </div>
          <button
            @click="triggerFileInput"
            class="absolute -bottom-1 -right-1 w-7 h-7 bg-primary text-white rounded-xl flex items-center justify-center shadow-md hover:scale-105 transition-transform"
            title="Đổi ảnh"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
          </button>
          <input ref="fileInput" type="file" accept="image/jpeg,image/png,image/webp" class="hidden" @change="onFileChange" />
        </div>

        <div class="flex-1 mt-2 sm:mt-0">
          <div class="flex flex-wrap items-center gap-2 mb-1">
            <h2 class="text-xl font-bold text-on-surface">{{ user?.full_name || user?.username }}</h2>
            <span :class="['px-2.5 py-0.5 text-xs font-bold rounded-full', roleBg]">{{ roleLabel }}</span>
            <span :class="['px-2.5 py-0.5 text-xs font-bold rounded-full', user?.is_active ? 'bg-tertiary-fixed text-tertiary' : 'bg-error-container text-error']">
              {{ user?.is_active ? 'Đang hoạt động' : 'Đã khóa' }}
            </span>
          </div>
          <p class="text-sm text-outline">{{ user?.email }}</p>
        </div>

        <div v-if="file" class="flex items-center gap-2 mt-2 sm:mt-0">
          <AppButton variant="gradient" size="sm" :loading="uploadingAvatar" @click="doUpload">Lưu ảnh</AppButton>
          <AppButton variant="ghost" size="sm" @click="resetFile">Hủy</AppButton>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <AppTabNav :tabs="tabs" v-model="activeTab" />

    <!-- Tab: Basic Info -->
    <div v-show="activeTab === 'info'" class="bg-card rounded-2xl border border-outline-variant p-6 shadow-sm">
      <h3 class="text-base font-semibold text-on-surface mb-5">Thông tin cá nhân</h3>

      <template v-if="isLoading">
        <div class="space-y-4">
          <AppSkeleton v-for="i in 5" :key="i" class="h-11 rounded-xl" />
        </div>
      </template>

      <form v-else @submit.prevent="saveProfile" class="space-y-4">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <AppInput v-model="profileForm.full_name" label="Họ tên" placeholder="Nguyễn Văn A" :error="profileErrors.full_name" />
          <AppInput v-model="profileForm.phone" label="Số điện thoại" placeholder="0901234567" :error="profileErrors.phone" />
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <AppInput v-model="profileForm.date_of_birth" type="date" label="Ngày sinh" :error="profileErrors.date_of_birth" />
          <AppSelect v-model="profileForm.gender" label="Giới tính" placeholder="Chọn giới tính" :options="genderOptions" />
        </div>
        <AppInput v-model="profileForm.address" label="Địa chỉ" placeholder="Số nhà, đường, quận, tỉnh..." />
        <AppInput v-model="profileForm.occupation" label="Nghề nghiệp" placeholder="Kỹ sư, bác sĩ..." />

        <!-- Readonly account info -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-outline-variant">
          <div class="bg-surface-container-low rounded-xl px-4 py-3">
            <p class="text-xs font-semibold text-outline uppercase tracking-wide mb-1">Tên đăng nhập</p>
            <p class="text-sm text-on-surface font-medium">{{ user?.username }}</p>
          </div>
          <div class="bg-surface-container-low rounded-xl px-4 py-3">
            <p class="text-xs font-semibold text-outline uppercase tracking-wide mb-1">Email</p>
            <p class="text-sm text-on-surface font-medium">{{ user?.email }}</p>
          </div>
        </div>

        <p v-if="uploadError" class="text-xs text-error">{{ uploadError }}</p>

        <div class="flex justify-end pt-2">
          <AppButton variant="gradient" type="submit" :loading="updatingProfile">Lưu thay đổi</AppButton>
        </div>
      </form>
    </div>

    <!-- Tab: Security -->
    <div v-show="activeTab === 'security'" class="space-y-4">
      <!-- Change password (local auth only) -->
      <div v-if="user?.auth_provider === 'local'" class="bg-card rounded-2xl border border-outline-variant p-6 shadow-sm">
        <h3 class="text-base font-semibold text-on-surface mb-5">Đổi mật khẩu</h3>
        <form @submit.prevent="savePw" class="space-y-4">
          <AppInput v-model="pwForm.old_password" type="password" label="Mật khẩu hiện tại" :error="pwErrors.old_password" required />
          <AppInput v-model="pwForm.new_password" type="password" label="Mật khẩu mới" :error="pwErrors.new_password" required hint="Ít nhất 6 ký tự, có chữ hoa, chữ thường, số và ký tự đặc biệt" />
          <AppInput v-model="pwForm.confirm_password" type="password" label="Xác nhận mật khẩu mới" :error="pwErrors.confirm_password" required />
          <div class="flex justify-end">
            <AppButton type="submit" variant="outline" :loading="changingPassword">Đổi mật khẩu</AppButton>
          </div>
        </form>
      </div>

      <!-- Google OAuth info -->
      <div v-else class="bg-card rounded-2xl border border-outline-variant p-6 shadow-sm">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-surface-container rounded-xl flex items-center justify-center">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
          </div>
          <div>
            <p class="text-sm font-semibold text-on-surface">Đăng nhập bằng Google</p>
            <p class="text-xs text-outline">Tài khoản của bạn được quản lý qua Google. Đổi mật khẩu trong tài khoản Google của bạn.</p>
          </div>
        </div>
      </div>

      <!-- Quick links -->
      <div class="bg-card rounded-2xl border border-outline-variant p-5 shadow-sm">
        <h3 class="text-sm font-semibold text-on-surface mb-3">Quản lý dữ liệu</h3>
        <div class="space-y-2">
          <button
            @click="router.push('/profile/health-profiles')"
            class="w-full flex items-center justify-between p-3 hover:bg-surface-container-low rounded-xl transition-colors text-left"
          >
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 bg-tertiary-fixed rounded-xl flex items-center justify-center">
                <svg class="w-4 h-4 text-tertiary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
              </div>
              <span class="text-sm font-medium text-on-surface">Hồ sơ sức khỏe</span>
            </div>
            <svg class="w-4 h-4 text-outline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
          <button
            @click="router.push('/profile/prescriptions')"
            class="w-full flex items-center justify-between p-3 hover:bg-surface-container-low rounded-xl transition-colors text-left"
          >
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 bg-primary-fixed rounded-xl flex items-center justify-center">
                <svg class="w-4 h-4 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <span class="text-sm font-medium text-on-surface">Đơn thuốc của tôi</span>
            </div>
            <svg class="w-4 h-4 text-outline" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
