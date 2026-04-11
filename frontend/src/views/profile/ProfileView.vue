<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { z } from 'zod'
import { useAuthStore } from '@/stores/auth.store'
import { useCurrentUserQuery, useUpdateProfileMutation, useChangePasswordMutation, useUploadAvatarMutation } from '@/api/users.api'
import { updateProfileSchema, changePasswordSchema } from '@/schemas/profile.schema'
import { useToast } from '@/composables/useToast'
import { useFileUpload } from '@/composables/useFileUpload'
import AppInput from '@/components/ui/AppInput.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppAlert from '@/components/ui/AppAlert.vue'
import AppAvatar from '@/components/ui/AppAvatar.vue'
import AppSkeleton from '@/components/ui/AppSkeleton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'

const authStore = useAuthStore()
const toast = useToast()
const { preview, file, error: uploadError, onFileChange, reset: resetFile } = useFileUpload()
const fileInput = ref<HTMLInputElement | null>(null)

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

// Populate form when user loads
import { watch } from 'vue'
watch(user, (u) => {
  if (!u) return
  profileForm.full_name = u.full_name ?? ''
  profileForm.phone = u.phone ?? ''
  profileForm.date_of_birth = u.date_of_birth ?? ''
  profileForm.gender = (u.gender as 'male' | 'female' | 'other') ?? ''
  profileForm.address = u.address ?? ''
  profileForm.occupation = u.occupation ?? ''
}, { immediate: true })

const genderOptions = [
  { label: 'Nam', value: 'male' },
  { label: 'Nữ', value: 'female' },
  { label: 'Khác', value: 'other' },
]

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
    onSuccess: () => {
      toast.success('Cập nhật hồ sơ thành công')
      authStore.fetchCurrentUser()
    },
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
    onSuccess: () => {
      toast.success('Đổi mật khẩu thành công')
      Object.assign(pwForm, { old_password: '', new_password: '', confirm_password: '' })
    },
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
  <div class="max-w-2xl mx-auto space-y-6">
    <h1 class="text-2xl font-bold text-[#111827]">Hồ sơ cá nhân</h1>

    <!-- Avatar section -->
    <div class="bg-white rounded-2xl border border-[#E5E7EB] p-6">
      <h2 class="text-base font-semibold text-[#111827] mb-4">Ảnh đại diện</h2>
      <div class="flex items-center gap-6">
        <AppAvatar :src="preview ?? user?.avatar_url" :name="user?.full_name" size="xl" />
        <div>
          <div class="flex items-center gap-3">
            <input ref="fileInput" type="file" accept="image/jpeg,image/png,image/webp" class="hidden" @change="onFileChange" />
            <AppButton variant="outline" size="sm" @click="triggerFileInput">Chọn ảnh</AppButton>
            <AppButton v-if="file" variant="primary" size="sm" :loading="uploadingAvatar" @click="doUpload">Lưu ảnh</AppButton>
          </div>
          <p v-if="uploadError" class="text-xs text-[#EF4444] mt-1">{{ uploadError }}</p>
          <p v-else class="text-xs text-[#9CA3AF] mt-1">JPEG, PNG hoặc WebP. Tối đa 2MB.</p>
          <div class="flex items-center gap-2 mt-2">
            <AppBadge :variant="user?.role === 'admin' ? 'purple' : 'info'">{{ user?.role }}</AppBadge>
            <AppBadge :variant="user?.is_active ? 'success' : 'danger'">{{ user?.is_active ? 'Đang hoạt động' : 'Đã khóa' }}</AppBadge>
          </div>
        </div>
      </div>
    </div>

    <!-- Profile form -->
    <div class="bg-white rounded-2xl border border-[#E5E7EB] p-6">
      <h2 class="text-base font-semibold text-[#111827] mb-4">Thông tin cá nhân</h2>
      <template v-if="isLoading">
        <div class="space-y-4">
          <AppSkeleton class="h-10 w-full" />
          <AppSkeleton class="h-10 w-full" />
          <AppSkeleton class="h-10 w-full" />
        </div>
      </template>
      <form v-else @submit.prevent="saveProfile" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <AppInput v-model="profileForm.full_name" label="Họ tên" placeholder="Nguyễn Văn A" :error="profileErrors.full_name" />
          <AppInput v-model="profileForm.phone" label="Số điện thoại" placeholder="0901234567" :error="profileErrors.phone" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <AppInput v-model="profileForm.date_of_birth" type="date" label="Ngày sinh" :error="profileErrors.date_of_birth" />
          <AppSelect v-model="profileForm.gender" label="Giới tính" placeholder="Chọn giới tính" :options="genderOptions" />
        </div>
        <AppInput v-model="profileForm.address" label="Địa chỉ" placeholder="Số nhà, đường, quận, tỉnh..." />
        <AppInput v-model="profileForm.occupation" label="Nghề nghiệp" placeholder="Kỹ sư, bác sĩ..." />

        <!-- Readonly fields -->
        <div class="grid grid-cols-2 gap-4 pt-2 border-t border-[#E5E7EB]">
          <div>
            <label class="text-sm font-medium text-[#374151]">Tên đăng nhập</label>
            <p class="mt-1 text-sm text-[#6B7280]">{{ user?.username }}</p>
          </div>
          <div>
            <label class="text-sm font-medium text-[#374151]">Email</label>
            <p class="mt-1 text-sm text-[#6B7280]">{{ user?.email }}</p>
          </div>
        </div>

        <div class="flex justify-end pt-2">
          <AppButton type="submit" :loading="updatingProfile">Lưu thay đổi</AppButton>
        </div>
      </form>
    </div>

    <!-- Change password (local auth only) -->
    <div v-if="user?.auth_provider === 'local'" class="bg-white rounded-2xl border border-[#E5E7EB] p-6">
      <h2 class="text-base font-semibold text-[#111827] mb-4">Đổi mật khẩu</h2>
      <form @submit.prevent="savePw" class="space-y-4">
        <AppInput v-model="pwForm.old_password" type="password" label="Mật khẩu hiện tại" :error="pwErrors.old_password" required />
        <AppInput v-model="pwForm.new_password" type="password" label="Mật khẩu mới" :error="pwErrors.new_password" required hint="Ít nhất 6 ký tự, có chữ hoa, chữ thường, số và ký tự đặc biệt" />
        <AppInput v-model="pwForm.confirm_password" type="password" label="Xác nhận mật khẩu mới" :error="pwErrors.confirm_password" required />
        <div class="flex justify-end">
          <AppButton type="submit" variant="outline" :loading="changingPassword">Đổi mật khẩu</AppButton>
        </div>
      </form>
    </div>
  </div>
</template>
