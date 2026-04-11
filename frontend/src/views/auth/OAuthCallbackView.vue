<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppAlert from '@/components/ui/AppAlert.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const error = ref('')

onMounted(async () => {
  const accessToken = route.query.access_token as string
  const refreshToken = route.query.refresh_token as string

  if (!accessToken || !refreshToken) {
    error.value = 'Đăng nhập Google thất bại. Vui lòng thử lại.'
    return
  }

  try {
    authStore.setTokens(accessToken, refreshToken)
    await authStore.fetchCurrentUser()
    router.push('/dashboard')
  } catch {
    error.value = 'Không thể lấy thông tin người dùng. Vui lòng thử lại.'
    authStore.clearAuth()
  }
})
</script>

<template>
  <div class="text-center py-8">
    <div v-if="!error" class="flex flex-col items-center gap-4">
      <AppSpinner size="lg" class="text-[#10B981]" />
      <p class="text-[#6B7280]">Đang xác thực tài khoản Google...</p>
    </div>
    <div v-else>
      <AppAlert type="error" title="Đăng nhập thất bại" class="mb-4">{{ error }}</AppAlert>
      <router-link to="/login" class="text-sm text-[#10B981] hover:text-[#059669]">← Quay lại đăng nhập</router-link>
    </div>
  </div>
</template>
