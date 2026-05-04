<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { z } from 'zod'
import { useForgotPasswordOtpMutation } from '@/api/auth.api'
import AppInput from '@/components/ui/AppInput.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppAlert from '@/components/ui/AppAlert.vue'

const router = useRouter()
const form = reactive({ email: '' })
const errors = reactive<Record<string, string>>({})

const { mutate: sendOtp, isPending, error: apiError } = useForgotPasswordOtpMutation()

const errorMessage = computed(() => {
  const err = apiError.value as { message?: string } | null
  return err?.message || null
})

function validate() {
  Object.keys(errors).forEach((k) => delete errors[k])
  if (!form.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    errors.email = 'Email không hợp lệ'
    return false
  }
  return true
}

function onSubmit() {
  if (!validate()) return
  sendOtp({ email: form.email }, {
    onSuccess: () => {
      router.push({ path: '/verify-otp', query: { email: form.email } })
    },
  })
}
</script>

<template>
  <div class="min-h-screen bg-surface flex flex-col items-center justify-center px-4 py-12">
    <!-- Decorative blobs -->
    <div class="fixed top-0 left-0 w-96 h-96 rounded-full bg-primary-fixed/40 blur-3xl -translate-x-1/2 -translate-y-1/2 pointer-events-none" />
    <div class="fixed bottom-0 right-0 w-80 h-80 rounded-full bg-secondary-container/30 blur-3xl translate-x-1/3 translate-y-1/3 pointer-events-none" />

    <!-- Card -->
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
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      </div>

      <h1 class="text-2xl font-bold text-on-surface mb-1">Quên mật khẩu?</h1>
      <p class="text-sm text-outline mb-6">
        Nhập địa chỉ email đã đăng ký. Chúng tôi sẽ gửi mã OTP 6 chữ số để xác nhận.
      </p>

      <AppAlert v-if="errorMessage" type="error" class="mb-4">{{ errorMessage }}</AppAlert>

      <form @submit.prevent="onSubmit" class="space-y-4">
        <AppInput
          v-model="form.email"
          type="email"
          label="Địa chỉ email"
          placeholder="email@example.com"
          :error="errors.email"
          required
          autocomplete="email"
        />
        <AppButton variant="gradient" type="submit" :loading="isPending" full size="lg">
          Gửi mã OTP
        </AppButton>
      </form>

      <!-- Info box -->
      <div class="mt-6 bg-primary-fixed/60 border border-primary/20 rounded-xl p-4">
        <p class="text-xs text-primary font-medium mb-1">Lưu ý:</p>
        <p class="text-xs text-on-surface-variant">Mã OTP có hiệu lực trong 10 phút. Kiểm tra cả thư mục spam nếu không nhận được email.</p>
      </div>

      <p class="text-center text-sm text-outline mt-6">
        <router-link to="/login" class="text-primary hover:text-primary-dk font-medium">
          ← Quay lại đăng nhập
        </router-link>
      </p>
    </div>
  </div>
</template>
