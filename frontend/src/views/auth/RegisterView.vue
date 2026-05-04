<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { z } from 'zod'
import { useRegisterMutation } from '@/api/auth.api'
import { registerSchema } from '@/schemas/auth.schema'
import AppInput from '@/components/ui/AppInput.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppAlert from '@/components/ui/AppAlert.vue'

const form = reactive({
  full_name: '',
  phone: '',
  email: '',
  username: '',
  password: '',
  confirm_password: '',
})
const errors = reactive<Record<string, string>>({})
const showPassword = ref(false)
const success = ref(false)

const { mutate: register, isPending, error: apiError } = useRegisterMutation()

const errorMessage = computed(() => {
  if (!apiError.value) return null
  const err = apiError.value as { message?: string }
  return err.message || 'Đăng ký thất bại'
})

// Password strength
const passwordStrength = computed(() => {
  const p = form.password
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
    registerSchema.parse(form)
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
  const { confirm_password: _, ...payload } = form
  register(payload, {
    onSuccess: () => {
      success.value = true
    },
  })
}
</script>

<template>
  <div class="min-h-screen flex">
    <!-- Left panel — gradient (hidden on mobile) -->
    <div class="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary to-primary-container relative overflow-hidden flex-col justify-between p-12">
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
          Tham gia cộng đồng<br />chăm sóc sức khỏe
        </h2>
        <p class="text-primary-fixed text-base leading-relaxed mb-8">
          Tạo tài khoản miễn phí và bắt đầu hành trình quản lý sức khỏe toàn diện cùng Medis.
        </p>
        <div class="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
          <p class="text-white font-semibold mb-3">Tính năng dành cho bạn:</p>
          <ul class="space-y-2 text-white/90 text-sm">
            <li class="flex items-center gap-2">
              <svg class="w-4 h-4 text-tertiary-fixed flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
              </svg>
              Lưu trữ đơn thuốc cá nhân
            </li>
            <li class="flex items-center gap-2">
              <svg class="w-4 h-4 text-tertiary-fixed flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
              </svg>
              Hồ sơ khám bệnh đầy đủ
            </li>
            <li class="flex items-center gap-2">
              <svg class="w-4 h-4 text-tertiary-fixed flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
              </svg>
              Gợi ý thuốc từ AI
            </li>
            <li class="flex items-center gap-2">
              <svg class="w-4 h-4 text-tertiary-fixed flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
              </svg>
              Nhắc nhở uống thuốc hàng ngày
            </li>
          </ul>
        </div>
      </div>

      <p class="relative text-white/50 text-xs">© 2026 Medis. Quản lý sức khỏe thông minh.</p>
    </div>

    <!-- Right panel — form -->
    <div class="w-full lg:w-1/2 flex items-center justify-center p-8 bg-card overflow-y-auto">
      <div class="w-full max-w-md py-4">
        <!-- Mobile logo -->
        <div class="lg:hidden mb-6 flex items-center gap-2">
          <div class="w-9 h-9 bg-primary rounded-xl flex items-center justify-center">
            <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <span class="text-xl font-bold text-on-surface">Medis</span>
        </div>

        <!-- Tab toggle -->
        <div class="flex rounded-xl bg-surface-container-low p-1 mb-6">
          <router-link to="/login" class="flex-1 text-center py-2 text-sm font-medium rounded-lg text-outline hover:text-on-surface transition-colors">
            Đăng nhập
          </router-link>
          <router-link to="/register" class="flex-1 text-center py-2 text-sm font-semibold rounded-lg bg-card text-primary shadow-sm">
            Đăng ký
          </router-link>
        </div>

        <h1 class="text-2xl font-bold text-on-surface mb-1">Tạo tài khoản</h1>
        <p class="text-sm text-outline mb-6">Điền thông tin để bắt đầu sử dụng Medis</p>

        <!-- Success state -->
        <AppAlert v-if="success" type="success" title="Đăng ký thành công!">
          Chúng tôi đã gửi email xác nhận đến <strong>{{ form.email }}</strong>. Vui lòng kiểm tra hộp thư và xác nhận tài khoản.
        </AppAlert>

        <template v-else>
          <AppAlert v-if="errorMessage" type="error" class="mb-4">{{ errorMessage }}</AppAlert>

          <form @submit.prevent="onSubmit" class="space-y-4">
            <div class="grid grid-cols-2 gap-3">
              <AppInput v-model="form.full_name" label="Họ tên" placeholder="Nguyễn Văn A" :error="errors.full_name" required />
              <AppInput v-model="form.phone" label="Số điện thoại" placeholder="0901234567" :error="errors.phone" required />
            </div>

            <AppInput v-model="form.email" type="email" label="Email" placeholder="example@email.com" :error="errors.email" required />

            <AppInput
              v-model="form.username"
              label="Tên đăng nhập"
              placeholder="username (3-30 ký tự)"
              :error="errors.username"
              required
              hint="Chỉ dùng chữ cái, số và gạch dưới"
            />

            <div>
              <AppInput
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                label="Mật khẩu"
                placeholder="Mật khẩu mạnh"
                :error="errors.password"
                required
              />
              <!-- Password strength bar -->
              <div v-if="form.password" class="mt-2">
                <div class="flex gap-1 mb-1">
                  <div v-for="i in 5" :key="i" :class="['h-1 flex-1 rounded-full transition-colors', i <= passwordStrength ? strengthLabel.color : 'bg-outline-variant']" />
                </div>
                <p class="text-xs text-outline">Độ mạnh: <span :class="strengthLabel.color.replace('bg-', 'text-')">{{ strengthLabel.text }}</span></p>
              </div>
            </div>

            <AppInput
              v-model="form.confirm_password"
              :type="showPassword ? 'text' : 'password'"
              label="Xác nhận mật khẩu"
              placeholder="Nhập lại mật khẩu"
              :error="errors.confirm_password"
              required
            />

            <label class="flex items-center gap-2 text-sm text-on-surface-variant cursor-pointer select-none">
              <input v-model="showPassword" type="checkbox" class="rounded border-outline-variant" />
              Hiện mật khẩu
            </label>

            <AppButton variant="gradient" type="submit" :loading="isPending" full size="lg">Đăng ký ngay</AppButton>
          </form>
        </template>
      </div>
    </div>
  </div>
</template>
