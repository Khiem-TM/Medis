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
  <div>
    <h1 class="text-2xl font-bold text-[#111827] mb-1">Đăng ký</h1>
    <p class="text-sm text-[#6B7280] mb-6">Tạo tài khoản Medis của bạn</p>

    <!-- Success state -->
    <AppAlert v-if="success" type="success" title="Đăng ký thành công!">
      Chúng tôi đã gửi email xác nhận đến <strong>{{ form.email }}</strong>. Vui lòng kiểm tra hộp thư và xác nhận tài khoản.
    </AppAlert>

    <template v-else>
      <AppAlert v-if="errorMessage" type="error" class="mb-4">{{ errorMessage }}</AppAlert>

      <form @submit.prevent="onSubmit" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
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

        <AppInput
          v-model="form.password"
          :type="showPassword ? 'text' : 'password'"
          label="Mật khẩu"
          placeholder="Mật khẩu mạnh"
          :error="errors.password"
          required
          hint="Ít nhất 6 ký tự, có chữ hoa, chữ thường, số và ký tự đặc biệt"
        />

        <AppInput
          v-model="form.confirm_password"
          :type="showPassword ? 'text' : 'password'"
          label="Xác nhận mật khẩu"
          placeholder="Nhập lại mật khẩu"
          :error="errors.confirm_password"
          required
        />

        <label class="flex items-center gap-2 text-sm text-[#374151] cursor-pointer select-none">
          <input v-model="showPassword" type="checkbox" class="rounded" />
          Hiện mật khẩu
        </label>

        <AppButton type="submit" :loading="isPending" full>Đăng ký</AppButton>
      </form>

      <p class="text-center text-sm text-[#6B7280] mt-6">
        Đã có tài khoản?
        <router-link to="/login" class="text-[#10B981] font-medium hover:text-[#059669]">Đăng nhập</router-link>
      </p>
    </template>
  </div>
</template>
