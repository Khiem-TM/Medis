<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { z } from 'zod'
import { useResetPasswordMutation } from '@/api/auth.api'
import { resetPasswordSchema } from '@/schemas/auth.schema'
import AppInput from '@/components/ui/AppInput.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppAlert from '@/components/ui/AppAlert.vue'

const route = useRoute()
const router = useRouter()

const token = computed(() => route.query.token as string || '')
const form = reactive({ new_password: '', confirm_new_password: '' })
const errors = reactive<Record<string, string>>({})
const success = ref(false)
const showPassword = ref(false)

const { mutate: resetPassword, isPending, error: apiError } = useResetPasswordMutation()

const errorMessage = computed(() => {
  const err = apiError.value as { message?: string } | null
  return err?.message || null
})

// Password strength
const passwordStrength = computed(() => {
  const p = form.new_password
  if (!p) return 0
  let score = 0
  if (p.length >= 6) score++
  if (/[A-Z]/.test(p)) score++
  if (/[a-z]/.test(p)) score++
  if (/[0-9]/.test(p)) score++
  if (/[@$!%*?&]/.test(p)) score++
  return score
})

const strengthLabel = computed(() => {
  const s = passwordStrength.value
  if (s <= 1) return { text: 'Rất yếu', color: 'bg-error' }
  if (s === 2) return { text: 'Yếu', color: 'bg-warning' }
  if (s === 3) return { text: 'Trung bình', color: 'bg-yellow-400' }
  if (s === 4) return { text: 'Mạnh', color: 'bg-tertiary' }
  return { text: 'Rất mạnh', color: 'bg-tertiary' }
})

function validate() {
  Object.keys(errors).forEach((k) => delete errors[k])
  try {
    resetPasswordSchema.parse(form)
    return true
  } catch (e) {
    if (e instanceof z.ZodError) {
      e.issues.forEach((err) => { if (err.path[0]) errors[err.path[0] as string] = err.message })
    }
    return false
  }
}

function onSubmit() {
  if (!token.value) return
  if (!validate()) return
  resetPassword(
    { token: token.value, new_password: form.new_password },
    {
      onSuccess: () => {
        success.value = true
        setTimeout(() => router.push('/login'), 2500)
      },
    },
  )
}
</script>

<template>
  <div class="min-h-screen bg-surface flex flex-col items-center justify-center px-4 py-12">
    <!-- Decorative blobs -->
    <div class="fixed top-0 left-0 w-96 h-96 rounded-full bg-primary-fixed/40 blur-3xl -translate-x-1/2 -translate-y-1/2 pointer-events-none" />
    <div class="fixed bottom-0 right-0 w-80 h-80 rounded-full bg-secondary-container/30 blur-3xl translate-x-1/3 translate-y-1/3 pointer-events-none" />

    <div class="relative w-full max-w-md bg-card rounded-2xl shadow-sm border border-outline-variant p-8">
      <!-- Logo -->
      <div class="flex items-center gap-2 mb-8">
        <div class="w-9 h-9 bg-primary rounded-xl flex items-center justify-center">
          <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <span class="text-xl font-bold text-on-surface">Medis</span>
      </div>

      <!-- Icon -->
      <div class="w-14 h-14 bg-primary-fixed rounded-2xl flex items-center justify-center mb-5">
        <svg class="w-7 h-7 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
        </svg>
      </div>

      <h1 class="text-2xl font-bold text-on-surface mb-1">Đặt lại mật khẩu</h1>
      <p class="text-sm text-outline mb-6">Nhập mật khẩu mới của bạn</p>

      <!-- Invalid token -->
      <AppAlert v-if="!token" type="error" title="Liên kết không hợp lệ">
        Token đặt lại mật khẩu không tìm thấy.
        <router-link to="/forgot-password" class="underline ml-1">Yêu cầu lại</router-link>
      </AppAlert>

      <!-- Success -->
      <AppAlert v-else-if="success" type="success" title="Đổi mật khẩu thành công!">
        Đang chuyển hướng về trang đăng nhập...
      </AppAlert>

      <template v-else>
        <AppAlert v-if="errorMessage" type="error" class="mb-4">{{ errorMessage }}</AppAlert>

        <form @submit.prevent="onSubmit" class="space-y-4">
          <div>
            <AppInput
              v-model="form.new_password"
              :type="showPassword ? 'text' : 'password'"
              label="Mật khẩu mới"
              :error="errors.new_password"
              required
              hint="Ít nhất 6 ký tự, có chữ hoa, chữ thường, số và ký tự đặc biệt"
            />
            <!-- Password strength bar -->
            <div v-if="form.new_password" class="mt-2">
              <div class="flex gap-1 mb-1">
                <div v-for="i in 5" :key="i" :class="['h-1 flex-1 rounded-full transition-colors', i <= passwordStrength ? strengthLabel.color : 'bg-outline-variant']" />
              </div>
              <p class="text-xs text-outline">Độ mạnh: <span :class="strengthLabel.color.replace('bg-', 'text-')">{{ strengthLabel.text }}</span></p>
            </div>
          </div>

          <AppInput
            v-model="form.confirm_new_password"
            :type="showPassword ? 'text' : 'password'"
            label="Xác nhận mật khẩu mới"
            :error="errors.confirm_new_password"
            required
          />

          <label class="flex items-center gap-2 text-sm text-on-surface-variant cursor-pointer select-none">
            <input v-model="showPassword" type="checkbox" class="rounded border-outline-variant" />
            Hiện mật khẩu
          </label>

          <AppButton variant="gradient" type="submit" :loading="isPending" full size="lg">
            Đặt lại mật khẩu
          </AppButton>
        </form>
      </template>

      <p class="text-center text-sm text-outline mt-6">
        <router-link to="/login" class="text-primary hover:text-primary-dk font-medium">
          ← Quay lại đăng nhập
        </router-link>
      </p>
    </div>
  </div>
</template>
