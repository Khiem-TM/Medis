<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useVerifyResetOtpMutation, useForgotPasswordOtpMutation } from '@/api/auth.api'
import OtpInput from '@/components/ui/OtpInput.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppAlert from '@/components/ui/AppAlert.vue'

const route = useRoute()
const router = useRouter()

const email = computed(() => route.query.email as string || '')
const otp = ref('')
const resendSeconds = ref(60)
let timer: ReturnType<typeof setInterval> | null = null

const { mutate: verifyOtp, isPending, error: apiError } = useVerifyResetOtpMutation()
const { mutate: resendOtp, isPending: isResending } = useForgotPasswordOtpMutation()

const errorMessage = computed(() => {
  const err = apiError.value as { message?: string } | null
  return err?.message || null
})

function startTimer() {
  resendSeconds.value = 60
  timer = setInterval(() => {
    resendSeconds.value--
    if (resendSeconds.value <= 0 && timer) {
      clearInterval(timer)
      timer = null
    }
  }, 1000)
}

function onResend() {
  if (resendSeconds.value > 0 || !email.value) return
  resendOtp({ email: email.value }, {
    onSuccess: () => { startTimer() },
  })
}

function onSubmit() {
  if (otp.value.length < 6) return
  verifyOtp({ email: email.value, otp: otp.value }, {
    onSuccess: (data) => {
      router.push({ path: '/reset-password', query: { token: data.reset_token } })
    },
  })
}

onMounted(() => {
  if (!email.value) {
    router.replace('/forgot-password')
    return
  }
  startTimer()
})
onUnmounted(() => { if (timer) clearInterval(timer) })
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

      <!-- Icon badge -->
      <div class="w-14 h-14 bg-primary-fixed rounded-2xl flex items-center justify-center mb-5">
        <svg class="w-7 h-7 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      </div>

      <h1 class="text-2xl font-bold text-on-surface mb-1">Nhập mã xác nhận</h1>
      <p class="text-sm text-outline mb-2">
        Mã gồm 6 chữ số đã được gửi đến
      </p>
      <p class="text-sm font-semibold text-primary mb-6">{{ email }}</p>

      <AppAlert v-if="errorMessage" type="error" class="mb-6">{{ errorMessage }}</AppAlert>

      <!-- OTP inputs -->
      <OtpInput v-model="otp" :disabled="isPending" class="mb-6" />

      <!-- Submit button -->
      <AppButton
        variant="gradient"
        :loading="isPending"
        :disabled="otp.length < 6"
        full
        size="lg"
        @click="onSubmit"
      >
        Xác nhận
      </AppButton>

      <!-- Resend -->
      <div class="mt-5 text-center">
        <p class="text-sm text-outline">
          Chưa nhận được mã?
          <button
            v-if="resendSeconds > 0"
            disabled
            class="ml-1 text-outline cursor-not-allowed"
          >
            Gửi lại sau {{ resendSeconds }}s
          </button>
          <button
            v-else
            @click="onResend"
            :disabled="isResending"
            class="ml-1 text-primary font-medium hover:text-primary-dk disabled:opacity-50"
          >
            {{ isResending ? 'Đang gửi...' : 'Gửi lại mã' }}
          </button>
        </p>
      </div>

      <!-- Info -->
      <div class="mt-5 bg-primary-fixed/60 border border-primary/20 rounded-xl p-4">
        <p class="text-xs text-on-surface-variant">
          💡 Mã OTP có hiệu lực trong <strong class="text-primary">10 phút</strong>. Kiểm tra cả thư mục spam nếu không nhận được.
        </p>
      </div>

      <p class="text-center text-sm text-outline mt-5">
        <router-link to="/forgot-password" class="text-primary hover:text-primary-dk font-medium">
          ← Nhập email khác
        </router-link>
      </p>
    </div>
  </div>
</template>
