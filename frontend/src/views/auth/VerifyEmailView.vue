<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { authApi } from '@/api/auth.api'
import AppSpinner from '@/components/ui/AppSpinner.vue'
import AppAlert from '@/components/ui/AppAlert.vue'
import AppButton from '@/components/ui/AppButton.vue'

const route = useRoute()
const token = computed(() => route.query.token as string || '')
const status = ref<'loading' | 'success' | 'error'>('loading')
const errorMsg = ref('')

onMounted(async () => {
  if (!token.value) {
    status.value = 'error'
    errorMsg.value = 'Token xác nhận không hợp lệ'
    return
  }
  try {
    await authApi.verifyEmail(token.value)
    status.value = 'success'
  } catch (e) {
    status.value = 'error'
    errorMsg.value = (e as { message?: string })?.message || 'Xác nhận email thất bại'
  }
})
</script>

<template>
  <div class="text-center">
    <!-- Loading -->
    <div v-if="status === 'loading'" class="flex flex-col items-center gap-4 py-8">
      <AppSpinner size="lg" class="text-primary" />
      <p class="text-outline">Đang xác nhận email...</p>
    </div>

    <!-- Success -->
    <div v-else-if="status === 'success'" class="py-6">
      <div class="w-16 h-16 bg-tertiary-fixed rounded-full flex items-center justify-center mx-auto mb-4">
        <svg class="w-8 h-8 text-tertiary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <h2 class="text-xl font-bold text-on-surface mb-2">Email đã được xác nhận!</h2>
      <p class="text-sm text-outline mb-6">Tài khoản của bạn đã được kích hoạt. Bạn có thể đăng nhập ngay bây giờ.</p>
      <AppButton full>
        <router-link to="/login">Đăng nhập</router-link>
      </AppButton>
    </div>

    <!-- Error -->
    <div v-else class="py-6">
      <AppAlert type="error" title="Xác nhận thất bại" class="mb-6">{{ errorMsg }}</AppAlert>
      <router-link to="/login" class="text-sm text-primary hover:text-primary-dk">← Quay lại đăng nhập</router-link>
    </div>
  </div>
</template>
