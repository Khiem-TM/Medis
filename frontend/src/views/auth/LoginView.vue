<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
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
  <div class="min-h-screen flex">
    <!-- Left panel — gradient (hidden on mobile) -->
    <div class="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary to-primary-container relative overflow-hidden flex-col justify-between p-12">
      <!-- Decorative blurred circles -->
      <div class="absolute -top-24 -right-24 w-80 h-80 rounded-full bg-white/10 blur-3xl" />
      <div class="absolute bottom-12 -left-16 w-64 h-64 rounded-full bg-white/10 blur-2xl" />

      <!-- Logo -->
      <div class="relative flex items-center gap-3">
        <div class="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur-sm">
          <svg class="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <span class="text-2xl font-bold text-white">Medis</span>
      </div>

      <!-- Main content -->
      <div class="relative">
        <h2 class="text-4xl font-extrabold text-white leading-snug mb-4">
          Quản lý sức khỏe<br />thông minh hơn
        </h2>
        <p class="text-primary-fixed text-base leading-relaxed mb-10">
          Tra cứu thuốc, kiểm tra tương tác, và nhận tư vấn AI cá nhân hóa chỉ trong một nền tảng.
        </p>
        <div class="space-y-4">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center flex-shrink-0">
              <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
            </div>
            <span class="text-white/90 text-sm">Cơ sở dữ liệu thuốc toàn diện</span>
          </div>
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center flex-shrink-0">
              <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <span class="text-white/90 text-sm">Kiểm tra tương tác thuốc tức thì</span>
          </div>
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center flex-shrink-0">
              <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <span class="text-white/90 text-sm">Chatbot AI tư vấn sức khỏe 24/7</span>
          </div>
        </div>
      </div>

      <!-- Footer text -->
      <p class="relative text-white/50 text-xs">© 2026 Medis. Quản lý sức khỏe thông minh.</p>
    </div>

    <!-- Right panel — form -->
    <div class="w-full lg:w-1/2 flex items-center justify-center p-8 bg-card">
      <div class="w-full max-w-md">
        <!-- Mobile logo -->
        <div class="lg:hidden mb-8 flex items-center gap-2">
          <div class="w-9 h-9 bg-primary rounded-xl flex items-center justify-center">
            <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <span class="text-xl font-bold text-on-surface">Medis</span>
        </div>

        <!-- Tab toggle -->
        <div class="flex rounded-xl bg-surface-container-low p-1 mb-8">
          <router-link to="/login" class="flex-1 text-center py-2 text-sm font-semibold rounded-lg bg-card text-primary shadow-sm">
            Đăng nhập
          </router-link>
          <router-link to="/register" class="flex-1 text-center py-2 text-sm font-medium rounded-lg text-outline hover:text-on-surface transition-colors">
            Đăng ký
          </router-link>
        </div>

        <h1 class="text-2xl font-bold text-on-surface mb-1">Chào mừng trở lại</h1>
        <p class="text-sm text-outline mb-6">Đăng nhập để tiếp tục sử dụng Medis</p>

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
                <button type="button" @click="showPassword = !showPassword" class="text-outline hover:text-on-surface-variant">
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
              <router-link to="/forgot-password" class="text-xs text-primary hover:text-primary-dk">
                Quên mật khẩu?
              </router-link>
            </div>
          </div>

          <AppButton variant="gradient" type="submit" :loading="isPending" full size="lg">Đăng nhập</AppButton>
        </form>

        <!-- Divider -->
        <div class="flex items-center gap-3 my-6">
          <div class="flex-1 h-px bg-outline-variant" />
          <span class="text-xs text-outline">hoặc</span>
          <div class="flex-1 h-px bg-outline-variant" />
        </div>

        <!-- Google OAuth -->
        <a :href="googleLoginUrl" class="flex items-center justify-center gap-3 w-full border border-outline-variant rounded-xl px-4 py-2.5 text-sm font-medium text-on-surface-variant hover:bg-surface-container-low transition-colors">
          <svg class="w-5 h-5" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Đăng nhập với Google
        </a>
      </div>
    </div>
  </div>
</template>
