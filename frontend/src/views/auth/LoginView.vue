<script setup lang="ts">
import { reactive, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { z } from 'zod'
import { useAuthStore } from '@/stores/auth.store'
import { useLoginMutation } from '@/api/auth.api'
import { loginSchema } from '@/schemas/auth.schema'
import AppInput from '@/components/ui/AppInput.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppAlert from '@/components/ui/AppAlert.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const form = reactive({ username: '', password: '' })
const errors = reactive<Record<string, string>>({})
const showPassword = ref(false)

import { ref } from 'vue'

const { mutate: login, isPending, error: apiError } = useLoginMutation()

const errorMessage = computed(() => {
  if (!apiError.value) return null
  const err = apiError.value as { message?: string }
  return err.message || 'Đăng nhập thất bại'
})

function validate() {
  Object.keys(errors).forEach((k) => delete errors[k])
  try {
    loginSchema.parse(form)
    return true
  } catch (e) {
    if (e instanceof z.ZodError) {
      e.issues.forEach((err) => {
        if (err.path[0]) errors[err.path[0] as string] = err.message
      })
    }
    return false
  }
}

function onSubmit() {
  if (!validate()) return
  login(form, {
    onSuccess: (data) => {
      authStore.setTokens(data.access_token, data.refresh_token)
      authStore.fetchCurrentUser().then(() => {
        const redirect = route.query.redirect as string | undefined
        router.push(redirect || '/dashboard')
      })
    },
  })
}

const googleLoginUrl = `${import.meta.env.VITE_API_URL}/auth/google/login`
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-[#111827] mb-1">Đăng nhập</h1>
    <p class="text-sm text-[#6B7280] mb-6">Chào mừng bạn trở lại!</p>

    <AppAlert v-if="errorMessage" type="error" class="mb-4" dismissible @dismiss="() => {}">
      {{ errorMessage }}
    </AppAlert>

    <form @submit.prevent="onSubmit" class="space-y-4">
      <AppInput
        v-model="form.username"
        id="username"
        label="Tên đăng nhập"
        placeholder="Nhập tên đăng nhập"
        :error="errors.username"
        required
        autocomplete="username"
      />

      <div class="flex flex-col gap-1">
        <AppInput
          v-model="form.password"
          id="password"
          label="Mật khẩu"
          :type="showPassword ? 'text' : 'password'"
          placeholder="Nhập mật khẩu"
          :error="errors.password"
          required
          autocomplete="current-password"
        >
          <template #suffix>
            <button type="button" @click="showPassword = !showPassword" class="text-[#9CA3AF] hover:text-[#374151]">
              <svg v-if="showPassword" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
              </svg>
              <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </button>
          </template>
        </AppInput>
        <div class="flex justify-end">
          <router-link to="/forgot-password" class="text-xs text-[#10B981] hover:text-[#059669]">
            Quên mật khẩu?
          </router-link>
        </div>
      </div>

      <AppButton type="submit" :loading="isPending" full>Đăng nhập</AppButton>
    </form>

    <!-- Divider -->
    <div class="flex items-center gap-3 my-6">
      <div class="flex-1 h-px bg-[#E5E7EB]" />
      <span class="text-xs text-[#9CA3AF]">hoặc</span>
      <div class="flex-1 h-px bg-[#E5E7EB]" />
    </div>

    <!-- Google OAuth -->
    <a :href="googleLoginUrl" class="flex items-center justify-center gap-3 w-full border border-[#E5E7EB] rounded-lg px-4 py-2.5 text-sm font-medium text-[#374151] hover:bg-[#F9FAFB] transition-colors">
      <svg class="w-5 h-5" viewBox="0 0 24 24">
        <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
        <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
        <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
        <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
      </svg>
      Đăng nhập với Google
    </a>

    <!-- Register link -->
    <p class="text-center text-sm text-[#6B7280] mt-6">
      Chưa có tài khoản?
      <router-link to="/register" class="text-[#10B981] font-medium hover:text-[#059669]">Đăng ký ngay</router-link>
    </p>
  </div>
</template>
