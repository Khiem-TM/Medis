<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { z } from 'zod'
import { useForgotPasswordMutation } from '@/api/auth.api'
import { forgotPasswordSchema } from '@/schemas/auth.schema'
import AppInput from '@/components/ui/AppInput.vue'
import AppButton from '@/components/ui/AppButton.vue'
import AppAlert from '@/components/ui/AppAlert.vue'

const form = reactive({ email: '' })
const errors = reactive<Record<string, string>>({})
const success = ref(false)

const { mutate: forgotPassword, isPending, error: apiError } = useForgotPasswordMutation()

const errorMessage = computed(() => {
  const err = apiError.value as { message?: string } | null
  return err?.message || null
})

function validate() {
  Object.keys(errors).forEach((k) => delete errors[k])
  try {
    forgotPasswordSchema.parse(form)
    return true
  } catch (e) {
    if (e instanceof z.ZodError) {
      e.issues.forEach((err) => { if (err.path[0]) errors[err.path[0] as string] = err.message })
    }
    return false
  }
}

function onSubmit() {
  if (!validate()) return
  forgotPassword(form, { onSuccess: () => { success.value = true } })
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-[#111827] mb-1">Quên mật khẩu</h1>
    <p class="text-sm text-[#6B7280] mb-6">Nhập email để nhận liên kết đặt lại mật khẩu</p>

    <AppAlert v-if="success" type="success" title="Đã gửi email!">
      Kiểm tra hộp thư <strong>{{ form.email }}</strong> để nhận liên kết đặt lại mật khẩu (có hiệu lực 1 giờ).
    </AppAlert>

    <template v-else>
      <AppAlert v-if="errorMessage" type="error" class="mb-4">{{ errorMessage }}</AppAlert>

      <form @submit.prevent="onSubmit" class="space-y-4">
        <AppInput v-model="form.email" type="email" label="Email" placeholder="email@example.com" :error="errors.email" required />
        <AppButton type="submit" :loading="isPending" full>Gửi liên kết đặt lại</AppButton>
      </form>

      <p class="text-center text-sm text-[#6B7280] mt-4">
        <router-link to="/login" class="text-[#10B981] hover:text-[#059669]">← Quay lại đăng nhập</router-link>
      </p>
    </template>
  </div>
</template>
