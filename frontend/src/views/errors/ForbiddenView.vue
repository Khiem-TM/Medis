<script setup lang="ts">
import { useRouter } from 'vue-router'
import AppButton from '@/components/ui/AppButton.vue'

const router = useRouter()
</script>

<template>
  <div class="min-h-screen bg-[#F9FAFB] flex items-center justify-center p-6">
    <div class="text-center max-w-md">
      <div class="w-24 h-24 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-6">
        <svg class="w-12 h-12 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      </div>
      <h1 class="text-2xl font-bold text-[#111827] mb-2">Không có quyền truy cập</h1>
      <p class="text-[#6B7280] mb-6">Bạn không có quyền truy cập vào trang này. Vui lòng liên hệ quản trị viên.</p>
      <div class="flex gap-3 justify-center">
        <AppButton variant="outline" @click="router.back()">Quay lại</AppButton>
        <AppButton @click="router.push('/dashboard')">Về trang chủ</AppButton>
      </div>
    </div>
  </div>
</template>
