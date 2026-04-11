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

const { mutate: resetPassword, isPending, error: apiError } = useResetPasswordMutation()

const errorMessage = computed(() => {
  const err = apiError.value as { message?: string } | null
  return err?.message || null
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
        setTimeout(() => router.push('/login'), 2000)
      },
    },
  )
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-[#111827] mb-1">Đặt lại mật khẩu</h1>
    <p class="text-sm text-[#6B7280] mb-6">Nhập mật khẩu mới của bạn</p>

    <AppAlert v-if="!token" type="error" title="Liên kết không hợp lệ">
      Token đặt lại mật khẩu không tìm thấy.
      <router-link to="/forgot-password" class="underline">Yêu cầu lại</router-link>
    </AppAlert>

    <AppAlert v-else-if="success" type="success" title="Đổi mật khẩu thành công!">
      Đang chuyển hướng về đăng nhập...
    </AppAlert>

    <template v-else>
      <AppAlert v-if="errorMessage" type="error" class="mb-4">{{ errorMessage }}</AppAlert>

      <form @submit.prevent="onSubmit" class="space-y-4">
        <AppInput v-model="form.new_password" type="password" label="Mật khẩu mới" :error="errors.new_password" required hint="Ít nhất 6 ký tự, có chữ hoa, chữ thường, số và ký tự đặc biệt" />
        <AppInput v-model="form.confirm_new_password" type="password" label="Xác nhận mật khẩu mới" :error="errors.confirm_new_password" required />
        <AppButton type="submit" :loading="isPending" full>Đặt lại mật khẩu</AppButton>
      </form>
    </template>
  </div>
</template>
